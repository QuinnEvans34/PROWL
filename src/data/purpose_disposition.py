"""Reviewed purpose-specific denials using data-issue v1; never grant eligibility.

No source reads, publication, cohort selection or training integration. Evidence hashes
are independently supplied review anchors, not proof that a reviewer is correct.
"""
from copy import deepcopy
import re

from src.data.annotation_contract_v2 import validate_annotation_v2
from src.data.manifest_records import canonical, digest, file_reference, validate_schema
from src.data.protected_identity import pants_identity

VERSION = "purpose-denials-v1"
PURPOSES = frozenset(("pancreas_present_localizer", "geometry_dependent_training",
                      "anatomy_absent_robustness"))
RULES = {
    "PANCREAS_PRESENT_TARGET_EXCLUDED": (frozenset(("pancreas_present_localizer",)), "exclude"),
    "PHYSICAL_UNITS_UNRESOLVED": (PURPOSES, "quarantine"),
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
             "Independently reviewed SHA-256 required")
    return value


def _context(study, annotation, purpose):
    _require(purpose in PURPOSES, "Unsupported purpose")
    validate_schema("study-record", study)
    validate_annotation_v2(annotation)
    file_reference(study["image"])
    _require(study["source"] == annotation["source"] == "pants", "PanTS-only slice")
    identity = pants_identity(study["source_study_id"])
    _require((study["study_id"], study["subject_id"], study["source_partition"]) ==
             (identity.study_id, identity.subject_id, identity.source_partition),
             "Study identity/partition mismatch")
    _require(annotation["study_id"] == study["study_id"] and
             annotation["source_snapshot_id"] == study["source_snapshot_id"] and
             annotation["annotation_id"] in study["annotation_ids"], "Annotation linkage mismatch")
    _require(annotation["structure"] == "pancreas", "Pancreas target required")


def _bindings(study, annotation, purpose, decision_sha256, evidence_sha256):
    return [dict(kind="source_field", reference=k + "=" + v) for k, v in (
        ("policy", VERSION), ("purpose", purpose),
        ("study", study["study_id"]), ("snapshot", study["source_snapshot_id"]),
        ("ct_sha256", study["image"]["content_sha256"]),
        ("annotation_sha256", annotation["file"]["content_sha256"]))] + [
            dict(kind="manual_review", reference="decision_sha256=" + _hash(decision_sha256)),
            dict(kind="validator_output", reference="evidence_sha256=" + _hash(evidence_sha256))]


def make_purpose_issue(*, study, annotation, purpose, rule_code, decision_sha256,
                       evidence_sha256, issue_id, created_at):
    """Construct an UNATTESTED proposal; caller must review/pin it before consumption.

    IDs/times are explicit persisted inputs for replay. Existing records are never edited.
    Rule choice is a reviewed judgment, not inferred from a case number or empty mask.
    """
    _context(study, annotation, purpose)
    _require(rule_code in RULES, "Unsupported purpose rule")
    purposes, disposition = RULES[rule_code]
    _require(purpose in purposes, "Rule does not apply to requested purpose")
    issue = dict(schema_version="1.0.0", issue_id=issue_id, rule_code=rule_code,
                 entity_type="annotation", entity_id=annotation["annotation_id"],
                 severity="blocking", disposition=disposition,
                 message="Purpose-specific denial; originals and protected membership retained.",
                 evidence=_bindings(study, annotation, purpose, decision_sha256, evidence_sha256),
                 created_at=created_at)
    validate_schema("data-issue", issue)
    return issue


def check_purpose(*, study, annotation, purpose, protected_role, existing_issues,
                  purpose_issues, trusted_study_sha256, trusted_annotation_sha256,
                  trusted_issue_sha256, evidence_by_sha256, trusted_evidence_sha256):
    """Verify proposed denials and return explicit rejection, NEVER an allow result.

    All trusted pins must come from independently reviewed manifest/publication inputs.
    Do not populate them from untrusted records. Evidence bytes are retained decision and
    audit/review documents, not CT/mask payloads. Their interpretation remains human review.

    existing_issues is the exact union referenced by this study and annotation (not a
    whole manifest). purpose_issues are new append-only proposals, not yet attached.
    Resolution/supersession is deliberately unsupported in this first slice: later
    resolution needs separate reviewed evidence/implementation. Caller must additionally
    enforce subject/snapshot/manifest/cohort/geometry/mapping gates before any use.
    """
    _context(study, annotation, purpose)
    _require(protected_role == "train" and study["source_partition"] == "publisher_train",
             "Train-role input required; caller must verify frozen ancestry")
    for record, expected in ((study, trusted_study_sha256),
                             (annotation, trusted_annotation_sha256)):
        _require(digest(canonical(record)) == _hash(expected), "Reviewed record hash mismatch")
    prior, proposals = deepcopy(list(existing_issues)), deepcopy(list(purpose_issues))
    all_issues = prior + proposals
    ids = [r["issue_id"] for r in all_issues]
    _require(len(ids) == len(set(ids)), "Duplicate issue identity")
    _require(set(trusted_issue_sha256) == set(ids), "Issue pin inventory mismatch")
    for issue in all_issues:
        validate_schema("data-issue", issue)
        _require(digest(canonical(issue)) == _hash(trusted_issue_sha256[issue["issue_id"]]),
                 "Reviewed issue hash mismatch")
        _require(not issue.get("supersedes_issue_id") and not issue.get("resolution_artifact_id")
                 and issue["disposition"] != "resolved_by_new_artifact",
                 "Issue resolution requires separately reviewed implementation/evidence")
    expected_prior = set(study["issue_ids"]) | set(annotation["issue_ids"])
    _require({r["issue_id"] for r in prior} == expected_prior, "Dangling or extra existing issue")
    for entity, kind, key in ((study, "study", "study_id"), (annotation, "annotation", "annotation_id")):
        _require(len(entity["issue_ids"]) == len(set(entity["issue_ids"])), "Duplicate issue link")
        for issue in prior:
            if issue["issue_id"] in entity["issue_ids"]:
                _require((issue["entity_type"], issue["entity_id"]) == (kind, entity[key]),
                         "Issue attached to wrong entity")
    _require(set(evidence_by_sha256) == set(trusted_evidence_sha256), "Evidence pin inventory mismatch")
    for key, raw in evidence_by_sha256.items():
        _hash(key)
        _require(isinstance(raw, bytes) and digest(raw) == key, "Evidence bytes mismatch")
    reasons, used, seen_rules = set(), set(), set()
    # Recheck already attached purpose denials too; moving one to history cannot bypass it.
    denials = [r for r in prior if r["rule_code"] in RULES] + proposals
    for issue in denials:
        code = issue["rule_code"]
        _require(code in RULES and code not in seen_rules, "Unknown or duplicate purpose rule")
        seen_rules.add(code)
        purposes, disposition = RULES[code]
        _require(purpose in purposes, "Rule does not apply to requested purpose")
        _require((issue["entity_type"], issue["entity_id"], issue["severity"], issue["disposition"])
                 == ("annotation", annotation["annotation_id"], "blocking", disposition),
                 "Conflicting purpose disposition")
        refs = issue["evidence"]
        decisions = [r["reference"].removeprefix("decision_sha256=") for r in refs
                     if r["kind"] == "manual_review" and r["reference"].startswith("decision_sha256=")]
        audits = [r["reference"].removeprefix("evidence_sha256=") for r in refs
                  if r["kind"] == "validator_output" and r["reference"].startswith("evidence_sha256=")]
        _require(len(decisions) == len(audits) == 1, "Decision and evidence references required")
        expected = _bindings(study, annotation, purpose, decisions[0], audits[0])
        _require(sorted((r["kind"], r["reference"]) for r in refs) ==
                 sorted((r["kind"], r["reference"]) for r in expected), "Purpose evidence binding mismatch")
        _require({decisions[0], audits[0]} <= set(trusted_evidence_sha256), "Unreviewed evidence reference")
        used.update((decisions[0], audits[0]))
        reasons.add(code)
    _require(used == set(evidence_by_sha256), "Unused evidence supplied")
    for issue in prior:
        if issue["severity"] == "blocking":
            reasons.add("EXISTING_BLOCKING_ISSUE")
    if study["geometry"] is None:
        reasons.add("GEOMETRY_UNRESOLVED")
    if study["status"] != "eligible" or annotation["status"] != "eligible":
        reasons.add("RECORD_QUALIFICATION_PENDING")
    if "training_target" not in annotation["allowed_uses"]:
        reasons.add("TRAINING_TARGET_NOT_ALLOWED")
    if not denials:
        reasons.add("PURPOSE_DECISION_MISSING")
    # This deny-only slice deliberately has no clearance rule or promotion path.
    return dict(policy=VERSION, purpose=purpose, study_id=study["study_id"],
                annotation_id=annotation["annotation_id"], outcome="rejected",
                reasons=sorted(reasons), eligibility="not_granted", allowed_uses=[],
                protected_membership="unchanged", preserve_source=True,
                new_issues=sorted(proposals, key=lambda r: r["issue_id"]))
