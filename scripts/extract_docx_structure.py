#!/usr/bin/env python3
"""Print Word paragraphs and tables in document order for revision analysis."""

from pathlib import Path
import sys

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


if len(sys.argv) != 2:
    raise SystemExit("usage: extract_docx_structure.py FILE.docx")

document = Document(Path(sys.argv[1]))
for block in document.iter_inner_content():
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if text:
            style_name = block.style.name if block.style is not None else "No style"
            print(f"[{style_name}] {text}")
    elif isinstance(block, Table):
        print(f"[TABLE {len(block.rows)}x{len(block.columns)}]")
        for row in block.rows:
            cells = [" ".join(cell.text.split()) for cell in row.cells]
            print(" | ".join(cells))
        print("[/TABLE]")
