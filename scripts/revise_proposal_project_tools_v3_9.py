#!/usr/bin/env python3
"""Create proposal v3.9 with the approved GitHub and Notion language."""

from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import xml.etree.ElementTree as ET


SOURCE = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx")
OUTPUT = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.9.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
ET.register_namespace("w", W_NS)

MLOPS_ANCHOR = (
    "MLOps and scalable compute — MLflow, Docker, and local or rented GPU resources. "
    "Demonstrates versioned experiments, reproducible environments, registered models, "
    "and scalable training. Experience: Strong with experiment tracking and containers; "
    "less experience budgeting rented GPU training. Growth plan: Benchmark hardware first, "
    "set a spending ceiling, record cost per experiment, and stop rental use if the "
    "throughput benefit does not justify the expense."
)

PROJECT_TOOLS_LABEL = "Version control and project management — GitHub and Notion. "

PROJECT_TOOLS_BODY = (
    "GitHub will provide version "
    "control for code, configuration, documentation, and reproducibility records through "
    "focused branches, traceable commits, milestone pull requests, and tagged releases. "
    "Notion, supported by MCP integration, will manage the ten-week execution plan through a "
    "structured task database, weekly board, milestones, dependencies, and blocker tracking. "
    "MCP-assisted updates will create and maintain tasks from the approved implementation plans "
    "and connect completed work to the relevant GitHub change, acceptance criteria, testing "
    "evidence, and decision record. The GitHub repository will remain the technical source of "
    "truth, while Notion will communicate schedule and execution status."
)

PROJECT_TOOLS_TEXT = PROJECT_TOOLS_LABEL + PROJECT_TOOLS_BODY

SCHEDULE_ANCHOR = (
    "The plan targets completion of the committed system by the end of Week 8, leaving Week 9 "
    "as protected buffer and stabilization time and Week 10 for delivery and presentation. UI "
    "and UX refinement has dedicated work in Week 7. Unit tests are added with each component, "
    "followed by full unit, integration, and regression testing in Week 8. Stretch work will not "
    "consume the buffer."
)

TRACKING_TEXT = (
    "Progress, blockers, and completion evidence will be reviewed weekly in Notion and "
    "reconciled with the corresponding GitHub-linked implementation plans."
)


def clone_info(info: ZipInfo) -> ZipInfo:
    cloned = ZipInfo(info.filename, info.date_time)
    cloned.compress_type = info.compress_type
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.create_system = info.create_system
    cloned.create_version = info.create_version
    cloned.extract_version = info.extract_version
    cloned.flag_bits = info.flag_bits
    cloned.volume = info.volume
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    return cloned


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(f"{W}t"))


def insert_cloned_paragraph_after(
    root: ET.Element, anchor_text: str, new_run_texts: tuple[str, ...]
) -> None:
    parents = {child: parent for parent in root.iter() for child in parent}
    matches = [
        paragraph
        for paragraph in root.iter(f"{W}p")
        if paragraph_text(paragraph) == anchor_text
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one anchor paragraph but found {len(matches)}: {anchor_text[:80]}"
        )

    anchor = matches[0]
    cloned = deepcopy(anchor)
    text_nodes = list(cloned.iter(f"{W}t"))
    if len(text_nodes) < len(new_run_texts):
        raise SystemExit(
            f"Anchor paragraph has {len(text_nodes)} text nodes but "
            f"{len(new_run_texts)} are required: {anchor_text[:80]}"
        )
    for index, node in enumerate(text_nodes):
        node.text = new_run_texts[index] if index < len(new_run_texts) else ""

    parent = parents[anchor]
    index = list(parent).index(anchor)
    parent.insert(index + 1, cloned)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source file: {SOURCE}")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {OUTPUT}")

    with ZipFile(SOURCE, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml")
        root = ET.fromstring(document_xml)

        existing_text = "\n".join(paragraph_text(p) for p in root.iter(f"{W}p"))
        for new_text in (PROJECT_TOOLS_TEXT, TRACKING_TEXT):
            if new_text in existing_text:
                raise SystemExit(f"Text already exists in source: {new_text[:80]}")

        insert_cloned_paragraph_after(
            root, MLOPS_ANCHOR, (PROJECT_TOOLS_LABEL, PROJECT_TOOLS_BODY)
        )
        insert_cloned_paragraph_after(root, SCHEDULE_ANCHOR, (TRACKING_TEXT,))
        updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as output_zip:
            for info in source_zip.infolist():
                data = (
                    updated_xml
                    if info.filename == "word/document.xml"
                    else source_zip.read(info.filename)
                )
                output_zip.writestr(clone_info(info), data)

    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
