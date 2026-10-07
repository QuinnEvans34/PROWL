#!/usr/bin/env python3
"""Create proposal v3.8 with the agreed risk-aware ten-week schedule."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SOURCE = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.7.docx")
OUTPUT = Path("Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx")


REPLACEMENTS = {
    "The plan targets completion of the committed system by the end of Week 9, leaving Week 10 as protected buffer and delivery time. UI design has dedicated work in Weeks 7–8. Unit tests are added with each component, followed by full unit, integration, and regression testing in Week 9. Stretch work will not consume the buffer.":
        "The plan targets completion of the committed system by the end of Week 8, leaving Week 9 as protected buffer and stabilization time and Week 10 for delivery and presentation. UI and UX refinement has dedicated work in Week 7. Unit tests are added with each component, followed by full unit, integration, and regression testing in Week 8. Stretch work will not consume the buffer.",

    ">Data and test design<": ">Architecture and test planning<",
    "Confirm data and storage design, validation rules, compute approach, UI requirements, and the unit/integration test plan.":
        "Confirm data design, retrieval requirements, workflow DAG, UI-extension requirements, and the unit/integration test strategy.",
    "Approved data design, validation checklist, UI requirements, and test plan.":
        "Approved architecture, acceptance criteria, workflow design, and test plan.",
    "Core decisions, acceptance criteria, or the test plan remain unresolved.":
        "Data, retrieval, orchestration, or test criteria remain unresolved.",

    ">Protected splits and unit tests<": ">Protected data splits<",
    "Implement protected splits and unit tests for patient exclusivity, manifest validation, and repeatable membership.":
        "Reproduce cohorts and add unit tests for patient separation, manifests, and repeatability.",
    "Existing splits reproduced; automated tests prevent overlap and malformed records.":
        "Frozen cohorts with passing tests for patient separation, manifest validity, and reproducibility.",

    "Ingest the second imaging source; reconcile labels, identifiers, and provenance; add duplicate and mapping tests.":
        "Integrate PANORAMA with tested label mapping, provenance, exclusions, and duplicate controls.",
    "Validated integration with documented exclusions and passing source tests.":
        "Validated source integration with documented exclusions and passing reconciliation tests.",

    ">Unified training data<": ">Unified pipeline and orchestration<",
    "Complete reproducible preprocessing and access; test transforms, label mapping, and source history.":
        "Produce reproducible training inputs and implement the tested preprocessing and workflow DAG.",
    "Reproducible training input with source history and passing pipeline tests.":
        "Reproducible training inputs and a tested, restartable workflow DAG.",
    "Training input cannot be reproduced or a pipeline test fails.":
        "A pipeline stage cannot be reproduced, tested, or safely restarted.",

    ">Autonomous baseline<": ">Autonomous baseline and retrieval foundation<",
    "Train and evaluate the autonomous localization-to-segmentation baseline; add inference and artifact-output smoke tests.":
        "Establish the imaging baseline; use model-training time to ingest literature and create the retrieval-index prototype.",
    "First held-out baseline, error analysis, and passing inference tests.":
        "Held-out baseline, error analysis, and a versioned, queryable retrieval prototype.",
    "The baseline cannot run end to end or an inference test fails.":
        "The baseline cannot run end to end or the retrieval prototype is not queryable.",

    ">Experiment and tradeoff<": ">Model experiment and retrieval evaluation<",
    "Run one controlled comparison selected from baseline errors; evaluate patient-level sensitivity and specificity thresholds.":
        "Complete one controlled model comparison, evaluate the false-alarm tradeoff, and measure retrieval quality.",
    "Documented model decision and patient-level operating-point results.":
        "Documented model decision, operating-point results, and retrieval metrics.",
    "The experiment is not comparable with the baseline or lacks a usable tradeoff result.":
        "The model result is not comparable or retrieval quality cannot be measured.",

    ">UI design and stakeholder review<": ">UI refinement and stakeholder review<",
    "Design the review workflow, create wireframes, build the NiiVue viewer prototype, and hold the stakeholder session.":
        "Extend the existing interface, integrate representative model/evidence outputs, and conduct stakeholder review.",
    "Reviewed UI design, functional viewer prototype, and documented stakeholder feedback.":
        "Integrated review flow and documented stakeholder feedback.",

    ">Knowledge retrieval and UI build<": ">@@WEEK8_PRIMARY@@<",
    "Build and test the literature index; implement the worklist, measurements, evidence display, and saved review decisions.":
        "@@WEEK8_WORK@@",
    "Measured retrieval quality and an interface connecting the core review functions.":
        "@@WEEK8_DELIVERABLE@@",
    "Retrieval remains unreliable or the UI cannot complete the core review flow.":
        "@@WEEK8_SIGNAL@@",

    ">Integration, testing, and evaluation<": ">Protected buffer and stabilization<",
    "Connect all components; run unit, integration, and regression tests; complete held-out evaluation and documentation drafts.":
        "Absorb overruns, correct defects, rerun affected tests or evaluation, and lock the release. No new scope.",
    "End-to-end demonstration, passing test suite, locked metrics, and documentation drafts.":
        "Stable release candidate with resolved priority defects and rerun evidence.",
    "A core path requires manual operation, tests fail, or evaluation is incomplete.":
        "@@WEEK9_SIGNAL@@",

    ">Protected buffer and delivery<": ">Delivery and presentation<",
    "Add no new committed features. Absorb overruns, fix defects, rerun affected tests or evaluation, and finish the demonstration and presentation.":
        "Package the stable system, complete documentation, rehearse the demonstration, and present.",
    "Stable tested release with metrics, limitations, model card, user guidance, and presentation materials.":
        "Submitted package, model card, user guidance, and presentation-ready demonstration.",
    "A core blocker remains unresolved by the middle of the buffer week.":
        "Release changes extend beyond minor packaging or presentation corrections.",

    ">@@WEEK8_PRIMARY@@<": ">Integration, testing, and evaluation<",
    "@@WEEK8_WORK@@":
        "Complete end-to-end integration, full unit/integration/regression testing, held-out evaluation, and documentation drafts.",
    "@@WEEK8_DELIVERABLE@@":
        "End-to-end demonstration, passing test suite, locked metrics, and documentation drafts.",
    "@@WEEK8_SIGNAL@@":
        "A core path requires manual operation, tests fail, or evaluation is incomplete.",
    "@@WEEK9_SIGNAL@@":
        "A core blocker remains unresolved by the middle of the buffer week.",

    "The committed scope is the autonomous imaging pipeline, validated multi-source data layer, controlled model experimentation, patient-level evaluation, recorded review workflow, evidence-grounded literature retrieval, and professional documentation. Optional work begins only after those capabilities are functioning and passing their tests. Week 10 is reserved for schedule recovery, defect correction, re-evaluation, and delivery; it is not assigned to new stretch work.":
        "The committed scope is the autonomous imaging pipeline, validated multi-source data layer, controlled model experimentation, patient-level evaluation, recorded review workflow, evidence-grounded literature retrieval, and professional documentation. Optional work begins only after those capabilities are functioning and passing their tests. Week 9 is reserved for schedule recovery, defect correction, re-evaluation, and stabilization; Week 10 is reserved for delivery and presentation. Neither week is assigned to new stretch work.",
    "The estimates below describe hands-on implementation time after the committed system is functioning and passing its tests. They do not include waiting for an outside reviewer, and no stretch opportunity is presented as a guaranteed improvement. Stretch work may begin only when it will not consume the protected Week 10 buffer.":
        "The estimates below describe hands-on implementation time after the committed system is functioning and passing its tests. They do not include waiting for an outside reviewer, and no stretch opportunity is presented as a guaranteed improvement. Stretch work may begin only when it will not consume the protected Week 9 buffer or Week 10 delivery time.",
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
