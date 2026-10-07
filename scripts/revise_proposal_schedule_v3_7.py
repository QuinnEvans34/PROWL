#!/usr/bin/env python3
"""Create proposal v3.7 by revising only the ten-week schedule text."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SOURCE = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.6.docx")
OUTPUT = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.7.docx")


REPLACEMENTS = {
    "The schedule commits to measurable outcomes while leaving implementation choices open until the evidence needed to make them is available.":
        "The plan targets completion of the committed system by the end of Week 9, leaving Week 10 as protected buffer and delivery time. UI design has dedicated work in Weeks 7–8. Unit tests are added with each component, followed by full unit, integration, and regression testing in Week 9. Stretch work will not consume the buffer.",

    ">Data design<": ">Data and test design<",
    "Confirm the data model, storage plan, validation rules, and compute approach before implementation.":
        "Confirm data and storage design, validation rules, compute approach, UI requirements, and the unit/integration test plan.",
    "Approved data design and validation checklist.":
        "Approved data design, validation checklist, UI requirements, and test plan.",
    "Core data rules or storage decisions remain unresolved.":
        "Core decisions, acceptance criteria, or the test plan remain unresolved.",

    ">Protected data splits<": ">Protected splits and unit tests<",
    "Move training, validation, and test membership into a controlled data layer. Ensure that every patient appears in only one group.":
        "Implement protected splits and unit tests for patient exclusivity, manifest validation, and repeatable membership.",
    "Existing splits reproduced and automated checks prevent patient overlap.":
        "Existing splits reproduced; automated tests prevent overlap and malformed records.",
    "Any patient can appear in both training and evaluation data.":
        "A patient can cross groups or a data-control test fails.",

    ">Second imaging source<": ">Second-source integration<",
    "Ingest the additional imaging source, reconcile labels and identifiers, and record annotation quality and origin.":
        "Ingest the second imaging source; reconcile labels, identifiers, and provenance; add duplicate and mapping tests.",
    "Validated source integration with documented exclusions and duplicate checks.":
        "Validated integration with documented exclusions and passing source tests.",
    "Source differences cannot yet be explained or tested.":
        "Source differences or exclusions cannot be explained or tested.",

    "Complete preprocessing, validation, and efficient access to the combined training data.":
        "Complete reproducible preprocessing and access; test transforms, label mapping, and source history.",
    "Reproducible training input with source and label history preserved.":
        "Reproducible training input with source history and passing pipeline tests.",
    "Training data cannot be reproduced from the recorded configuration.":
        "Training input cannot be reproduced or a pipeline test fails.",

    "Train and evaluate new models for pancreas localization and the full localization-to-segmentation path without a provided region.":
        "Train and evaluate the autonomous localization-to-segmentation baseline; add inference and artifact-output smoke tests.",
    "First held-out autonomous baseline and error analysis.":
        "First held-out baseline, error analysis, and passing inference tests.",
    "The new pipeline cannot be evaluated end to end.":
        "The baseline cannot run end to end or an inference test fails.",

    ">Model experimentation<": ">Experiment and tradeoff<",
    "Select the highest-value experiment from the baseline error analysis and compare it fairly with the fixed baseline.":
        "Run one controlled comparison selected from baseline errors; evaluate patient-level sensitivity and specificity thresholds.",
    "At least one controlled comparison with a documented result and decision.":
        "Documented model decision and patient-level operating-point results.",
    "No result can be compared directly with the baseline.":
        "The experiment is not comparable with the baseline or lacks a usable tradeoff result.",

    ">False-alarm tradeoff<": ">UI design and stakeholder review<",
    "Evaluate how decision thresholds balance detected tumors against false alarms; hold the stakeholder review session.":
        "Design the review workflow, create wireframes, build the NiiVue viewer prototype, and hold the stakeholder session.",
    "Patient-level tradeoff results and documented stakeholder feedback.":
        "Reviewed UI design, functional viewer prototype, and documented stakeholder feedback.",
    "No usable comparison or stakeholder feedback is available.":
        "The accept/edit/reject flow is not usable or stakeholder feedback is unavailable.",

    ">Knowledge retrieval<": ">Knowledge retrieval and UI build<",
    "Build the literature index and test whether relevant source passages are retrieved for representative questions.":
        "Build and test the literature index; implement the worklist, measurements, evidence display, and saved review decisions.",
    "Queryable literature source with measured retrieval quality.":
        "Measured retrieval quality and an interface connecting the core review functions.",
    "The system cannot reliably retrieve supporting passages.":
        "Retrieval remains unreliable or the UI cannot complete the core review flow.",

    ">System integration<": ">Integration, testing, and evaluation<",
    "Connect scan processing, measurements, review, stored decisions, and the evidence-grounded assistant.":
        "Connect all components; run unit, integration, and regression tests; complete held-out evaluation and documentation drafts.",
    "End-to-end demonstration from scan arrival to recorded review decision.":
        "End-to-end demonstration, passing test suite, locked metrics, and documentation drafts.",
    "Major components still require separate manual operation.":
        "A core path requires manual operation, tests fail, or evaluation is incomplete.",

    ">Evaluation and delivery<": ">Protected buffer and delivery<",
    "Run the held-out evaluation, complete documentation, and prepare the demonstration and presentation.":
        "Add no new committed features. Absorb overruns, fix defects, rerun affected tests or evaluation, and finish the demonstration and presentation.",
    "Metrics, limitations, model card, user guidance, and presentation materials.":
        "Stable tested release with metrics, limitations, model card, user guidance, and presentation materials.",
    "Evaluation or documentation remains incomplete.":
        "A core blocker remains unresolved by the middle of the buffer week.",

    "The committed scope is the autonomous imaging pipeline, validated multi-source data layer, controlled model experimentation, patient-level evaluation, recorded review workflow, evidence-grounded literature retrieval, and professional documentation. Optional work begins only after those capabilities are functioning.":
        "The committed scope is the autonomous imaging pipeline, validated multi-source data layer, controlled model experimentation, patient-level evaluation, recorded review workflow, evidence-grounded literature retrieval, and professional documentation. Optional work begins only after those capabilities are functioning and passing their tests. Week 10 is reserved for schedule recovery, defect correction, re-evaluation, and delivery; it is not assigned to new stretch work.",
    "The estimates below describe hands-on implementation time after the committed system is functioning. They do not include waiting for an outside reviewer, and no stretch opportunity is presented as a guaranteed improvement.":
        "The estimates below describe hands-on implementation time after the committed system is functioning and passing its tests. They do not include waiting for an outside reviewer, and no stretch opportunity is presented as a guaranteed improvement. Stretch work may begin only when it will not consume the protected Week 10 buffer.",
}


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


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source file: {SOURCE}")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {OUTPUT}")

    with ZipFile(SOURCE, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml").decode("utf-8")

        for old, new in REPLACEMENTS.items():
            occurrences = document_xml.count(old)
            if occurrences != 1:
                raise SystemExit(
                    f"Expected one occurrence but found {occurrences}: {old}"
                )
            document_xml = document_xml.replace(old, new, 1)

        with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as output_zip:
            for info in source_zip.infolist():
                data = (
                    document_xml.encode("utf-8")
                    if info.filename == "word/document.xml"
                    else source_zip.read(info.filename)
                )
                output_zip.writestr(clone_info(info), data)

    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
