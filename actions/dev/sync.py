"""Reverse sync utilities: update source files based on visual edits.

Provides helpers to update simple attribute assignments like `forcefield.left = X`.
Uses libcst to perform AST edits while preserving formatting and comments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper


class UpdateResult:
    def __init__(self, *, file: Path, changed: bool, backup: Optional[Path]) -> None:
        self.file = file
        self.changed = changed
        self.backup = backup


class _ArrangeCallTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, lineno: int, arg_name: str, new_value_src: str):
        self.lineno = lineno
        self.arg_name = arg_name
        self.new_value_src = new_value_src
        self.made_change = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        # Check function name
        func = updated_node.func
        func_name = None
        if isinstance(func, cst.Name):
            func_name = func.value
        elif isinstance(func, cst.Attribute) and isinstance(func.attr, cst.Name):
            func_name = func.attr.value

        if func_name != "arrange_grid":
            return updated_node

        # Check position
        try:
            pos = self.get_metadata(PositionProvider, original_node)
        except Exception:
            pos = None
        if pos is None or pos.start.line != self.lineno:
            return updated_node

        # Replace keyword arg if present
        new_args = []
        replaced = False
        for arg in updated_node.args:
            if arg.keyword and arg.keyword.value == self.arg_name:
                try:
                    new_expr = cst.parse_expression(self.new_value_src)
                except Exception:
                    new_expr = cst.Integer(value=str(self.new_value_src))
                new_arg = arg.with_changes(value=new_expr)
                new_args.append(new_arg)
                self.made_change = True
                replaced = True
            else:
                new_args.append(arg)

        # If arg not found, add it
        if not replaced:
            try:
                new_expr = cst.parse_expression(self.new_value_src)
            except Exception:
                new_expr = cst.Integer(value=str(self.new_value_src))
            new_arg = cst.Arg(keyword=cst.Name(self.arg_name), value=new_expr)
            new_args.append(new_arg)
            self.made_change = True

        if self.made_change:
            return updated_node.with_changes(args=new_args)
        return updated_node


class _SetAttrTransformer(cst.CSTTransformer):
    def __init__(self, target_name: str, attr_name: str, new_value_src: str):
        self.target_name = target_name
        self.attr_name = attr_name
        self.new_value_src = new_value_src
        self.made_change = False

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
        # Iterate targets - only replace when a target is an Attribute with matching name
        for t in updated_node.targets:
            target = t.target
            if isinstance(target, cst.Attribute):
                if isinstance(target.attr, cst.Name) and target.attr.value == self.attr_name:
                    # Check base name
                    base = target.value
                    if isinstance(base, cst.Name) and base.value == self.target_name:
                        # Replace value expression
                        try:
                            new_expr = cst.parse_expression(self.new_value_src)
                        except Exception:
                            # Fallback: use a simple number literal parse
                            new_expr = cst.Integer(value=str(self.new_value_src))
                        self.made_change = True
                        return updated_node.with_changes(value=new_expr)
        return updated_node


def update_position_assignment(
    file_path: str | Path, target_name: str, attr_name: str, new_value_src: str
) -> UpdateResult:
    """Update the first matching assignment `target_name.attr_name = ...` in the file.

    Creates a backup at `<file>.bak` before writing changes. Returns UpdateResult.
    """
    file_path = Path(file_path)
    src = file_path.read_text(encoding="utf-8")
    module = cst.parse_module(src)

    transformer = _SetAttrTransformer(target_name, attr_name, new_value_src)
    new_module = module.visit(transformer)

    if not transformer.made_change:
        return UpdateResult(file=file_path, changed=False, backup=None)

    # Backup original (do not overwrite existing .bak to preserve initial state)
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(src, encoding="utf-8")

    # Write transformed code
    new_code = new_module.code
    file_path.write_text(new_code, encoding="utf-8")

    return UpdateResult(file=file_path, changed=True, backup=backup)


def update_arrange_call(file_path: str | Path, lineno: int, arg_name: str, new_value_src: str) -> UpdateResult:
    """Update a keyword argument on an arrange_grid(...) call at the given line.

    Creates a backup at `<file>.bak` before writing changes. Returns UpdateResult.
    """
    file_path = Path(file_path)
    src = file_path.read_text(encoding="utf-8")
    module = cst.parse_module(src)

    wrapper = MetadataWrapper(module)
    transformer = _ArrangeCallTransformer(lineno, arg_name, new_value_src)
    new_module = wrapper.visit(transformer)

    if not transformer.made_change:
        return UpdateResult(file=file_path, changed=False, backup=None)

    # Backup original (do not overwrite existing .bak to preserve initial state)
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(src, encoding="utf-8")

    # Write transformed code
    new_code = new_module.code
    file_path.write_text(new_code, encoding="utf-8")

    return UpdateResult(file=file_path, changed=True, backup=backup)


class _ArrangeCellTransformer(cst.CSTTransformer):
    """Transformer to add or append a cell override to an arrange_grid(...) call.

    The transformer will find the arrange_grid call at the specified line and add or
    update a keyword `overrides` containing a list of dicts with keys
    `row`, `col`, `x`, and `y`.
    """

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, lineno: int, row: int, col: int, x: int, y: int):
        self.lineno = lineno
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.made_change = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        # Check function name
        func = updated_node.func
        func_name = None
        if isinstance(func, cst.Name):
            func_name = func.value
        elif isinstance(func, cst.Attribute) and isinstance(func.attr, cst.Name):
            func_name = func.attr.value

        if func_name != "arrange_grid":
            return updated_node

        # Check position
        try:
            pos = self.get_metadata(PositionProvider, original_node)
        except Exception:
            pos = None
        if pos is None or pos.start.line != self.lineno:
            return updated_node

        # Build a Dict node for the new override
        new_dict = cst.Dict(
            [
                cst.DictElement(cst.SimpleString("'row'"), cst.Integer(str(self.row))),
                cst.DictElement(cst.SimpleString("'col'"), cst.Integer(str(self.col))),
                cst.DictElement(cst.SimpleString("'x'"), cst.Integer(str(self.x))),
                cst.DictElement(cst.SimpleString("'y'"), cst.Integer(str(self.y))),
            ]
        )

        # Search for existing 'overrides' arg
        new_args = []
        found = False
        for arg in updated_node.args:
            if arg.keyword and arg.keyword.value == "overrides":
                found = True
                val = arg.value
                if isinstance(val, cst.List):
                    # Deduplicate or update existing override for same (row, col)
                    elements = list(val.elements)  # type: ignore[attr-defined]
                    replaced = False
                    new_elements: list[cst.Element] = []
                    for el in elements:
                        node = el.value
                        if isinstance(node, cst.Dict):
                            # Try to find 'row' and 'col' entries
                            r = None
                            c = None
                            for de in node.elements:
                                key = de.key
                                valnode = de.value
                                if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "row"):
                                    if isinstance(valnode, cst.Integer):
                                        try:
                                            r = int(valnode.value)
                                        except Exception:
                                            r = None
                                if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "col"):
                                    if isinstance(valnode, cst.Integer):
                                        try:
                                            c = int(valnode.value)
                                        except Exception:
                                            c = None
                            if r == self.row and c == self.col:
                                # replace this element with the new dict
                                new_elements.append(cst.Element(new_dict))
                                replaced = True
                                self.made_change = True
                                continue
                        # default: keep existing element
                        new_elements.append(el)
                    if not replaced:
                        new_elements.append(cst.Element(new_dict))
                        self.made_change = True
                    new_val = val.with_changes(elements=new_elements)
                else:
                    # If overrides is not a list, convert it to a list containing existing value and new dict
                    new_val = cst.List([cst.Element(val), cst.Element(new_dict)])
                    self.made_change = True
                new_args.append(arg.with_changes(value=new_val))
            else:
                new_args.append(arg)
        if not found:
            # Add a new overrides argument at the end
            new_arg = cst.Arg(keyword=cst.Name("overrides"), value=cst.List([cst.Element(new_dict)]))
            new_args.append(new_arg)
            self.made_change = True

        if self.made_change:
            return updated_node.with_changes(args=new_args)
        return updated_node


def update_arrange_cell(file_path: str | Path, lineno: int, row: int, col: int, x: int, y: int) -> UpdateResult:
    """Add or update a per-cell override for an arrange_grid call.

    Creates a backup at `<file>.bak` before writing changes. Returns UpdateResult.
    """
    file_path = Path(file_path)
    src = file_path.read_text(encoding="utf-8")
    module = cst.parse_module(src)

    wrapper = MetadataWrapper(module)
    transformer = _ArrangeCellTransformer(lineno, row, col, x, y)
    new_module = wrapper.visit(transformer)

    if not transformer.made_change:
        return UpdateResult(file=file_path, changed=False, backup=None)

    # Backup original (do not overwrite existing .bak to preserve initial state)
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(src, encoding="utf-8")

    # Write transformed code
    new_code = new_module.code
    file_path.write_text(new_code, encoding="utf-8")

    return UpdateResult(file=file_path, changed=True, backup=backup)


class _ArrangeCellRemoveTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, lineno: int, row: int, col: int):
        self.lineno = lineno
        self.row = row
        self.col = col
        self.made_change = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        # Check function name
        func = updated_node.func
        func_name = None
        if isinstance(func, cst.Name):
            func_name = func.value
        elif isinstance(func, cst.Attribute) and isinstance(func.attr, cst.Name):
            func_name = func.attr.value

        if func_name != "arrange_grid":
            return updated_node

        # Check position
        try:
            pos = self.get_metadata(PositionProvider, original_node)
        except Exception:
            pos = None
        if pos is None or pos.start.line != self.lineno:
            return updated_node

        new_args = []
        removed = False
        for arg in updated_node.args:
            if arg.keyword and arg.keyword.value == "overrides":
                val = arg.value
                if isinstance(val, cst.List):
                    elements = list(val.elements)  # type: ignore[attr-defined]
                    new_elements: list[cst.Element] = []
                    for el in elements:
                        node = el.value
                        keep = True
                        if isinstance(node, cst.Dict):
                            r = None
                            c = None
                            for de in node.elements:
                                key = de.key
                                valnode = de.value
                                if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "row"):
                                    if isinstance(valnode, cst.Integer):
                                        try:
                                            r = int(valnode.value)
                                        except Exception:
                                            r = None
                                if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "col"):
                                    if isinstance(valnode, cst.Integer):
                                        try:
                                            c = int(valnode.value)
                                        except Exception:
                                            c = None
                            if r == self.row and c == self.col:
                                # drop this element
                                keep = False
                                removed = True
                                self.made_change = True
                        if keep:
                            new_elements.append(el)
                    if new_elements:
                        new_val = val.with_changes(elements=new_elements)
                        new_args.append(arg.with_changes(value=new_val))
                    else:
                        # remove the overrides arg entirely by skipping appending
                        pass
                else:
                    # if single value and matches target, remove arg
                    node = val
                    removed_single = False
                    if isinstance(node, cst.Dict):
                        r = None
                        c = None
                        for de in node.elements:
                            key = de.key
                            valnode = de.value
                            if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "row"):
                                if isinstance(valnode, cst.Integer):
                                    try:
                                        r = int(valnode.value)
                                    except Exception:
                                        r = None
                            if isinstance(key, cst.SimpleString) and (key.value.strip("\"'") == "col"):
                                if isinstance(valnode, cst.Integer):
                                    try:
                                        c = int(valnode.value)
                                    except Exception:
                                        c = None
                        if r == self.row and c == self.col:
                            removed_single = True
                            removed = True
                            self.made_change = True
                    if not removed_single:
                        new_args.append(arg)
            else:
                new_args.append(arg)

        if self.made_change:
            return updated_node.with_changes(args=new_args)
        return updated_node


def delete_arrange_override(file_path: str | Path, lineno: int, row: int, col: int) -> UpdateResult:
    """Remove a per-cell override for an arrange_grid call.

    Creates a backup at `<file>.bak` before writing changes. Returns UpdateResult.
    """
    file_path = Path(file_path)
    src = file_path.read_text(encoding="utf-8")
    module = cst.parse_module(src)

    wrapper = MetadataWrapper(module)
    transformer = _ArrangeCellRemoveTransformer(lineno, row, col)
    new_module = wrapper.visit(transformer)

    if not transformer.made_change:
        return UpdateResult(file=file_path, changed=False, backup=None)

    # Backup original (do not overwrite existing .bak to preserve initial state)
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(src, encoding="utf-8")

    # Write transformed code
    new_code = new_module.code
    file_path.write_text(new_code, encoding="utf-8")

    return UpdateResult(file=file_path, changed=True, backup=backup)


def list_arrange_overrides(file_path: str | Path, lineno: int) -> list[dict]:
    """Return a list of override dicts for the arrange_grid call at lineno.

    Each entry will contain keys 'row','col','x','y' (ints when parseable), otherwise values may be None.
    """
    file_path = Path(file_path)
    src = file_path.read_text(encoding="utf-8")
    module = cst.parse_module(src)

    wrapper = MetadataWrapper(module)
    overrides: list[dict] = []

    class _Visitor(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (PositionProvider,)

        def visit_Call(self, node: cst.Call) -> None:
            func = node.func
            func_name = None
            if isinstance(func, cst.Name):
                func_name = func.value
            elif isinstance(func, cst.Attribute) and isinstance(func.attr, cst.Name):
                func_name = func.attr.value
            if func_name != "arrange_grid":
                return
            try:
                pos = self.get_metadata(PositionProvider, node)
            except Exception:
                pos = None
            if pos is None or pos.start.line != lineno:
                return
            for arg in node.args:
                if arg.keyword and arg.keyword.value == "overrides":
                    val = arg.value
                    if isinstance(val, cst.List):
                        for el in val.elements:
                            node = el.value
                            if isinstance(node, cst.Dict):
                                entry = {"row": None, "col": None, "x": None, "y": None}
                                for de in node.elements:
                                    key = de.key
                                    valnode = de.value
                                    if isinstance(key, cst.SimpleString):
                                        k = key.value.strip("\"'")
                                        if isinstance(valnode, cst.Integer):
                                            try:
                                                entry[k] = int(valnode.value)
                                            except Exception:
                                                entry[k] = None
                                        else:
                                            # try to parse literal
                                            try:
                                                entry[k] = int(str(valnode))
                                            except Exception:
                                                entry[k] = None
                                overrides.append(entry)
                    else:
                        node = val
                        if isinstance(node, cst.Dict):
                            entry = {"row": None, "col": None, "x": None, "y": None}
                            for de in node.elements:
                                key = de.key
                                valnode = de.value
                                if isinstance(key, cst.SimpleString):
                                    k = key.value.strip("\"'")
                                    if isinstance(valnode, cst.Integer):
                                        try:
                                            entry[k] = int(valnode.value)
                                        except Exception:
                                            entry[k] = None
                                    else:
                                        try:
                                            entry[k] = int(str(valnode))
                                        except Exception:
                                            entry[k] = None
                            overrides.append(entry)

    visitor = _Visitor()
    wrapper.visit(visitor)
    return overrides


__all__ = [
    "update_position_assignment",
    "UpdateResult",
    "update_arrange_call",
    "update_arrange_cell",
    "delete_arrange_override",
    "list_arrange_overrides",
]
