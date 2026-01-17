#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModuleMetrics:
    path: str
    sloc: int
    lloc: int
    cc_sum: float
    cc_max: float
    func_count: int
    coverage_pct: float | None  # 0..100, None if unknown
    score: float


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_path(p: str) -> str:
    # Radon paths are usually relative; coverage json may be absolute depending on config.
    # We'll normalize to posix and strip leading "./".
    p = p.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def extract_radon_raw(raw: dict[str, Any]) -> dict[str, dict[str, int]]:
    # raw[file] = {'loc':..,'lloc':..,'sloc':.., ...}
    out: dict[str, dict[str, int]] = {}
    for file_path, stats in raw.items():
        fp = normalize_path(file_path)
        out[fp] = {
            "sloc": int(stats.get("sloc", 0)),
            "lloc": int(stats.get("lloc", 0)),
        }
    return out


def extract_radon_cc(cc: dict[str, Any]) -> dict[str, tuple[float, float, int]]:
    # cc[file] = list of blocks; each has 'complexity' for functions/methods/classes
    # We focus on "function/method" blocks; in radon output, everything has a complexity number.
    # For refactor triage, summing all blocks is usually OK; but we'll ignore "module" blocks if present.
    out: dict[str, tuple[float, float, int]] = {}
    for file_path, blocks in cc.items():
        fp = normalize_path(file_path)
        cc_sum = 0.0
        cc_max = 0.0
        n = 0
        for b in blocks:
            typ = str(b.get("type", "")).lower()
            # Keep functions/methods; optionally include classes if you want.
            if typ in {"function", "method"}:
                c = float(b.get("complexity", 0.0))
                cc_sum += c
                cc_max = max(cc_max, c)
                n += 1
        out[fp] = (cc_sum, cc_max, n)
    return out


def extract_file_coverage(coverage_json: dict[str, Any]) -> dict[str, float]:
    """
    coverage.py JSON schema includes:
      - "files": { "<path>": { "summary": { "percent_covered": ... }, ... } }
    """
    files = coverage_json.get("files", {}) or {}
    out: dict[str, float] = {}
    for file_path, data in files.items():
        fp = normalize_path(file_path)
        summary = data.get("summary", {}) or {}
        pct = summary.get("percent_covered")
        if pct is None:
            continue
        out[fp] = float(pct)
    return out


def is_test_file(file_path: str) -> bool:
    """
    Check if a file path represents a test file.
    Excludes files in tests/ directories or files matching test naming patterns.
    """
    fp = normalize_path(file_path)
    # Check if path contains 'tests/' directory
    if "/tests/" in fp or fp.startswith("tests/"):
        return True
    # Check if filename starts with test_ or ends with _test.py
    path_parts = fp.split("/")
    filename = path_parts[-1] if path_parts else fp
    if filename.startswith("test_") or filename.endswith("_test.py"):
        return True
    return False


def best_match_coverage(file_path: str, cov_map: dict[str, float]) -> float | None:
    """
    Try a few matching strategies because coverage paths may be absolute.
    """
    fp = normalize_path(file_path)
    if fp in cov_map:
        return cov_map[fp]

    # Try matching by suffix (repo-relative)
    # Example: cov uses "/home/runner/work/repo/your_package/a.py"
    # while radon uses "your_package/a.py"
    candidates = [k for k in cov_map if k.endswith(fp)]
    if len(candidates) == 1:
        return cov_map[candidates[0]]
    if len(candidates) > 1:
        # Pick the shortest (closest) match
        candidates.sort(key=len)
        return cov_map[candidates[0]]

    return None


def compute_score(sloc: int, cc_sum: float, coverage_pct: float | None) -> float:
    # uncovered fraction U in [0..1]
    if coverage_pct is None:
        # treat unknown coverage as poor coverage (conservative)
        U = 1.0
    else:
        U = max(0.0, min(1.0, 1.0 - (coverage_pct / 100.0)))

    # Score formula:
    #   (ΣCC) × (1 + 4U) × log(1 + SLOC)
    # - (1 + 4U) scales from 1x at 100% coverage to 5x at 0% coverage
    size_factor = math.log(1.0 + max(0, sloc))
    return cc_sum * (1.0 + 4.0 * U) * size_factor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radon-raw", required=True, type=Path)
    ap.add_argument("--radon-cc", required=True, type=Path)
    ap.add_argument("--coverage-json", required=True, type=Path)
    ap.add_argument("--min-sloc", type=int, default=50)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--output", type=Path, help="Output file path (default: print to stdout)")
    args = ap.parse_args()

    raw = extract_radon_raw(load_json(args.radon_raw))
    cc = extract_radon_cc(load_json(args.radon_cc))
    cov = extract_file_coverage(load_json(args.coverage_json))

    all_files = sorted(set(raw.keys()) | set(cc.keys()))
    rows: list[ModuleMetrics] = []

    for fp in all_files:
        # Skip test files
        if is_test_file(fp):
            continue

        sloc = raw.get(fp, {}).get("sloc", 0)
        lloc = raw.get(fp, {}).get("lloc", 0)
        cc_sum, cc_max, n = cc.get(fp, (0.0, 0.0, 0))
        cov_pct = best_match_coverage(fp, cov)

        if sloc < args.min_sloc:
            continue

        score = compute_score(sloc, cc_sum, cov_pct)
        rows.append(ModuleMetrics(fp, sloc, lloc, cc_sum, cc_max, n, cov_pct, score))

    rows.sort(key=lambda r: r.score, reverse=True)

    # Markdown table (easy to print into CI logs / PR comments)
    output_lines = [
        "# Refactoring Priority Report",
        "",
        "This report ranks modules by refactoring priority based on:",
        "- Cyclomatic Complexity (CC)",
        "- Test Coverage",
        "- Source Lines of Code (SLOC)",
        "",
        "**Score Formula:** `(ΣCC) × (1 + 4×U) × log(1 + SLOC)`",
        "where U is the uncovered fraction (1 - coverage/100).",
        "",
        "| Rank | Module | Score | SLOC | ΣCC | MaxCC | Funcs | Cov% |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]

    for i, r in enumerate(rows[: args.top], start=1):
        cov_str = "?" if r.coverage_pct is None else f"{r.coverage_pct:.1f}"
        output_lines.append(
            f"| {i} | `{r.path}` | {r.score:.2f} | {r.sloc} | {r.cc_sum:.1f} | {r.cc_max:.1f} | {r.func_count} | {cov_str} |"
        )

    output_text = "\n".join(output_lines)

    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
