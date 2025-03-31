import ast
from pathlib import Path

import pandas as pd

Triple = tuple[str, str, str]


class TripletLinter(ast.NodeVisitor):
    def __init__(self, source: str):
        self.tree = ast.parse(source)
        self.violations: list[str] = []
        self.source = source

    def lint(self, triples: list[Triple]):
        for source, relation, target in triples:
            self._check(source, relation, target)
        return self.violations

    def _check(self, source: str, relation: str, target: str):
        parts = source.split(".")
        class_name = parts[0]
        method_name = parts[1] if len(parts) > 1 else None

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                if relation == "inherits_from":
                    if not any(
                        (isinstance(base, ast.Name) and base.id == target)
                        or (isinstance(base, ast.Attribute) and base.attr == target)
                        for base in node.bases
                    ):
                        self.violations.append(f"{class_name} should inherit from {target}")
                elif relation == "contains":
                    class_src = ast.get_source_segment(self.source, node) or ""
                    if target not in class_src:
                        self.violations.append(f"{class_name} should contain {target}")
                elif method_name:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == method_name:
                            method_src = ast.get_source_segment(self.source, item) or ""
                            if relation == "calls" and target not in method_src:
                                self.violations.append(f"{source} should call {target}")
                            elif relation == "requires" and target not in method_src:
                                self.violations.append(f"{source} should require {target}")
                            elif relation == "modifies" and target not in method_src:
                                self.violations.append(f"{source} should modify {target}")


def generate_test_case(class_name: str, method: str, relation: str, target: str) -> str:
    test_name = f"test_{class_name.lower()}_{method.lower()}_{relation.replace(' ', '_')}_{target.replace('.', '_')}"
    return f"""
def {test_name}():
    obj = {class_name}()
    assert hasattr(obj, '{method}'), \"Expected method not found: {method}\"
    # Contract assertion stub for: {relation} {target}
"""


def generate_prompt_context(triples_df: pd.DataFrame):
    grouped = triples_df.groupby("Source")
    lines = [
        """You are working with a Python library called ArcadeActions, designed for advanced sprite actions in the Arcade 3.x game framework. The architecture is inspired by Cocos2D but restructured to run inside Arcade's per-frame update loop.\n\nThe following knowledge graph describes class relationships and behavioral contracts. Preserve these relationships in any code changes or generation tasks:\n\n-- KNOWLEDGE GRAPH --\n"""
    ]
    for source, group in grouped:
        lines.append(f"{source}:")
        for _, row in group.iterrows():
            lines.append(f"  - {row['Relation']} {row['Target']}")
        lines.append("")
    lines.append("""
-- DESIGN PRINCIPLES --
- All IntervalAction subclasses must call update(t) via step(dt)
- start() must reset internal state like _elapsed
- All actions must support .clone() and use the @auto_clone decorator
- All actions must be used through sprite.do(action) and never shared without cloning
- Arcade 3.x only: do not reference Arcade 2.x methods

Refer to this context when modifying, validating, or generating code.
""")
    Path("arcadeactions_prompt_context.txt").write_text("\n".join(lines))


if __name__ == "__main__":
    triple_file = Path("arcadeactions_knowledge_graph.tsv")
    if not triple_file.exists():
        raise FileNotFoundError("Knowledge graph TSV file not found: arcadeactions_knowledge_graph.tsv")

    triples_df = pd.read_csv(triple_file, sep="\t")
    triples: list[Triple] = list(triples_df.itertuples(index=False, name=None))

    python_files = list(Path(".").rglob("*.py"))
    errors = []
    test_lines = ["# Auto-generated contract tests"]

    for path in python_files:
        if path.name.endswith("_test.py") or path.name.startswith("test_"):
            continue
        code = path.read_text()
        linter = TripletLinter(code)
        violations = linter.lint(triples)
        for src, rel, tgt in triples:
            if "." in src:
                class_name, method = src.split(".")
                test_lines.append(generate_test_case(class_name, method, rel, tgt))

        if violations:
            errors.append((path.name, violations))

    with open("test_contracts.py", "w") as f:
        f.write("\n".join(test_lines))

    generate_prompt_context(triples_df)

    if errors:
        for fname, vlist in errors:
            print(f"Violations in {fname}:")
            for v in vlist:
                print("  ", v)
        exit(1)
    else:
        print("All triples satisfied. Contract tests written to test_contracts.py. Prompt context exported.")
