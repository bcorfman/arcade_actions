"""Code position parser for Dev tools.

Parses Python source to find sprite position assignments such as
`sprite.left = X`, `sprite.top = Y`, `sprite.center_x = X` and
`arrange_grid(...)` calls. Returns structured results including file/line
information for use by the DevVisualizer.

Uses libCST for robust parsing and formatting-preserving edits later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider


@dataclass
class PositionAssignment:
    file: str
    lineno: int
    col: int
    target_expr: str
    attr: str
    value_src: str


@dataclass
class ArrangeCall:
    file: str
    lineno: int
    col: int
    call_src: str
    kwargs: dict
    tokens: list


class _AssignVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, module: cst.Module):
        self._module = module
        self.assignments: List[PositionAssignment] = []
        self.arrange_calls: List[ArrangeCall] = []

    def visit_Assign(self, node: cst.Assign) -> None:
        # Each target can be an attribute like `sprite.left`
        for assign_target in node.targets:
            target = assign_target.target
            if isinstance(target, cst.Attribute):
                # attribute name (right-most identifier)
                attr_name = None
                if isinstance(target.attr, cst.Name):
                    attr_name = target.attr.value
                # interested in coordinate attributes
                if attr_name in ("left", "top", "center_x"):
                    pos = self.get_metadata(PositionProvider, node)
                    try:
                        value_src = self._module.code_for_node(node.value)
                    except Exception:
                        value_src = ""
                    try:
                        target_src = self._module.code_for_node(target.value)
                    except Exception:
                        target_src = ""

                    self.assignments.append(
                        PositionAssignment(
                            file="",
                            lineno=pos.start.line,
                            col=pos.start.column,
                            target_expr=target_src,
                            attr=attr_name,
                            value_src=value_src,
                        )
                    )

    def visit_Call(self, node: cst.Call) -> None:
        # Detect arrange_grid calls by name
        func = node.func
        func_name = None
        if isinstance(func, cst.Name):
            func_name = func.value
        elif isinstance(func, cst.Attribute) and isinstance(func.attr, cst.Name):
            func_name = func.attr.value

        if func_name == "arrange_grid":
            pos = self.get_metadata(PositionProvider, node)
            try:
                call_src = self._module.code_for_node(node)
            except Exception:
                call_src = ""

            # Extract keyword args mapping (as source strings) for common params
            kwargs = {}
            for arg in node.args:
                if arg.keyword is not None:
                    try:
                        kwargs[arg.keyword.value] = self._module.code_for_node(arg.value)
                    except Exception:
                        kwargs[arg.keyword.value] = ""

            # Tokenize identifiers appearing in the call source to aid mapping to runtime tags
            import re

            tokens = re.findall(r"\b\w+\b", call_src)

            self.arrange_calls.append(
                ArrangeCall(
                    file="",
                    lineno=pos.start.line,
                    col=pos.start.column,
                    call_src=call_src,
                    kwargs=kwargs,
                    tokens=tokens,
                )
            )


def parse_source(source: str, filename: str = "<string>") -> tuple[List[PositionAssignment], List[ArrangeCall]]:
    """Parse a source string returning coordinate assignments and arrange calls.

    The returned PositionAssignment.file/ArrangeCall.file will be set to the provided
    `filename` value for convenience for callers that use file-based parsing.
    """
    module = cst.parse_module(source)
    wrapper = MetadataWrapper(module)
    visitor = _AssignVisitor(module)
    wrapper.visit(visitor)

    # Set file on results
    for a in visitor.assignments:
        a.file = filename
    for c in visitor.arrange_calls:
        c.file = filename

    return visitor.assignments, visitor.arrange_calls


def parse_file(path: str) -> tuple[List[PositionAssignment], List[ArrangeCall]]:
    """Parse a file on disk and return assignments and arrange calls."""
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    return parse_source(src, filename=path)


__all__ = ["PositionAssignment", "ArrangeCall", "parse_source", "parse_file"]
