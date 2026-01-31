import ast
import os
import re
from pathlib import Path

# Import arcadeactions to get its location
import arcadeactions

arcadeactions_path = Path(arcadeactions.__file__).parent.parent
print(f"Scanning: {arcadeactions_path}")

# Common C extensions that might need explicit inclusion
potential_c_extensions = {
    "math",
    "random",
    "array",
    "itertools",
    "collections",
    "struct",
    "hashlib",
    "json",
    "pickle",
    "_json",
    "datetime",
    "decimal",
    "csv",
    "binascii",
    "zlib",
    "gzip",
    "bz2",
    "lzma",
    "sqlite3",
    "mmap",
    "secrets",
    "statistics",
    "time",
    "zoneinfo",
}

found_modules = set()


def scan_file(filepath):
    """Scan a Python file for import statements."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Try parsing as AST
        try:
            tree = ast.parse(content, filename=str(filepath))

            class ImportCollector(ast.NodeVisitor):
                def visit_Import(self, node):
                    for alias in node.names:
                        if alias.name not in {"arcade", "pyglet", "arcadeactions", "__main__"}:
                            found_modules.add(alias.name)

                def visit_ImportFrom(self, node):
                    if node.module and node.module not in {"arcade", "pyglet", "arcadeactions", "__main__"}:
                        found_modules.add(node.module)

            ImportCollector().visit(tree)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            for line in content.split("\n"):
                match = re.match(r"^\s*(import|from)\s+(\w+)", line)
                if match and match.group(2) not in {"arcade", "pyglet", "arcadeactions", "__main__"}:
                    found_modules.add(match.group(2))
    except Exception:
        pass


# Scan all Python files in arcadeactions package
for root, dirs, files in os.walk(arcadeactions_path):
    # Skip __pycache__ and other hidden dirs
    dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

    for file in files:
        if file.endswith(".py"):
            scan_file(os.path.join(root, file))

# Find C extensions that might need inclusion
c_extensions_found = found_modules & potential_c_extensions

print("\n=== Standard library C extensions found in arcadeactions ===")
if c_extensions_found:
    for mod in sorted(c_extensions_found):
        print(f"  - {mod}")
    print("\nSuggested include-module setting:")
    print(f"  include-module: {','.join(sorted(c_extensions_found))}")
else:
    print("  (none found)")

print("\n=== All unique module imports found ===")
for mod in sorted(found_modules):
    print(f"  - {mod}")
