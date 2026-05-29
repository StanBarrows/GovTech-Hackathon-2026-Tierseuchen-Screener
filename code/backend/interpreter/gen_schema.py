"""
Generate a dataclass schema file from a SystemPrompt.md file.

Reads the `# Output schema` section of the prompt, parses each top-level
field line (`- name (type): description`), and writes a Python file
containing a single `ExtractionSchema` dataclass with one None-defaulted
field per schema entry. Nested sub-bullets (indented) are intentionally
ignored — only top-level fields matter for the empty-record shape.

Usage:
    python gen_schema.py SystemPrompt.md
    python gen_schema.py SystemPrompt_full.md -o schema_full.py
"""

import argparse
import re
from pathlib import Path

# Matches lines like:  "- disease_name (string): primary disease named ..."
FIELD_RE = re.compile(r"^- (\w+) \(([^)]+)\):\s*(.*)$")

TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "date": "str",  # ISO date string
    "object": "dict",
    "array of string": "list[str]",
    "array of object": "list[dict]",
    "array": "list",
}


def parse_schema_fields(md_text: str) -> list[tuple[str, str, str]]:
    """Return [(name, type_str, short_desc), ...] from the # Output schema section."""
    section = re.search(
        r"^#\s*Output schema\s*\n(.*?)(?=^#\s+(?!#))",
        md_text,
        re.MULTILINE | re.DOTALL,
    )
    if not section:
        raise ValueError("No '# Output schema' section found in prompt.")
    fields = []
    for line in section.group(1).splitlines():
        m = FIELD_RE.match(line)
        if not m:
            continue
        name, type_str, desc = m.groups()
        fields.append((name, type_str.strip(), desc.strip()))
    if not fields:
        raise ValueError("No fields found under '# Output schema'.")
    return fields


def map_type(type_str: str) -> str:
    s = re.sub(r"\s*\|\s*null\s*", "", type_str, flags=re.IGNORECASE).strip().lower()
    if s in TYPE_MAP:
        return TYPE_MAP[s]
    # Longest-prefix match for things like "array of string"
    for key in sorted(TYPE_MAP, key=len, reverse=True):
        if s.startswith(key):
            return TYPE_MAP[key]
    return "object"


def render(fields, source_name: str) -> str:
    lines = [
        f'"""Auto-generated from {source_name} — do not edit by hand."""',
        "from dataclasses import dataclass, asdict",
        "",
        "",
        "@dataclass",
        "class ExtractionSchema:",
    ]
    for name, type_str, desc in fields:
        py_type = map_type(type_str)
        short = desc.rstrip(".").split(".")[0][:80]
        comment = f"  # {short}" if short else ""
        lines.append(f"    {name}: {py_type} | None = None{comment}")
    lines += [
        "",
        "    @classmethod",
        "    def empty(cls) -> dict:",
        '        """Return all schema fields as a dict with None values."""',
        "        return asdict(cls())",
        "",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("prompt", help="Path to the SystemPrompt markdown file")
    p.add_argument(
        "-o",
        "--out",
        help="Output Python file. Default: schema.py next to the prompt.",
    )
    args = p.parse_args()

    src = Path(args.prompt)
    text = src.read_text(encoding="utf-8")
    fields = parse_schema_fields(text)
    out = Path(args.out) if args.out else src.parent / "schema.py"
    out.write_text(render(fields, src.name), encoding="utf-8")
    print(f"wrote {out} ({len(fields)} fields)")


if __name__ == "__main__":
    main()