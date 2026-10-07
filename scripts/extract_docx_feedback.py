#!/usr/bin/env python3
"""Extract Word comments, their highlighted text, and paragraph context."""

from collections import defaultdict
from io import BytesIO
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


if len(sys.argv) != 2:
    raise SystemExit("usage: extract_docx_feedback.py FILE.docx")

docx_path = Path(sys.argv[1])
with zipfile.ZipFile(docx_path) as archive:
    document_xml = archive.read("word/document.xml")
    comments_xml = archive.read("word/comments.xml")

comments_root = ET.fromstring(comments_xml)
comments = {}
authors = {}
for comment in comments_root.findall(f"{W}comment"):
    comment_id = comment.attrib[f"{W}id"]
    comments[comment_id] = "\n".join(
        "".join(text.text or "" for text in paragraph.iter(f"{W}t"))
        for paragraph in comment.findall(f"{W}p")
    )
    authors[comment_id] = comment.attrib.get(f"{W}author", "")

active = set()
anchor_text = defaultdict(list)
contexts = defaultdict(list)
paragraph_text = []
paragraph_comment_ids = set()

for event, element in ET.iterparse(BytesIO(document_xml), events=("start", "end")):
    if event == "start" and element.tag == f"{W}p":
        paragraph_text = []
        paragraph_comment_ids = set(active)
    elif event == "start" and element.tag == f"{W}commentRangeStart":
        comment_id = element.attrib[f"{W}id"]
        active.add(comment_id)
        paragraph_comment_ids.add(comment_id)
    elif event == "start" and element.tag == f"{W}commentRangeEnd":
        comment_id = element.attrib[f"{W}id"]
        active.discard(comment_id)
        paragraph_comment_ids.add(comment_id)
    elif event == "end" and element.tag == f"{W}t":
        text = element.text or ""
        paragraph_text.append(text)
        for comment_id in active:
            anchor_text[comment_id].append(text)
            paragraph_comment_ids.add(comment_id)
    elif event == "end" and element.tag == f"{W}tab":
        paragraph_text.append("\t")
        for comment_id in active:
            anchor_text[comment_id].append("\t")
    elif event == "end" and element.tag == f"{W}br":
        paragraph_text.append("\n")
        for comment_id in active:
            anchor_text[comment_id].append("\n")
    elif event == "end" and element.tag == f"{W}p":
        context = "".join(paragraph_text).strip()
        for comment_id in paragraph_comment_ids:
            if context and context not in contexts[comment_id]:
                contexts[comment_id].append(context)

for number, comment_id in enumerate(comments, start=1):
    print(f"COMMENT {number} | ID {comment_id} | {authors[comment_id]}")
    print(f"ANCHOR: {''.join(anchor_text[comment_id]).strip()}")
    print(f"FEEDBACK: {comments[comment_id]}")
    print("CONTEXT:")
    for context in contexts[comment_id]:
        print(f"  {context}")
    print()

