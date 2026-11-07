# Reviewer-flow engineering checks — November 7

The bounded pre-walkthrough reviewer checks passed. This is engineering evidence
for the November14 session, not participant feedback, contour adjudication,
clinical validation or complete G7 acceptance.

## Defects demonstrated and repaired

Four new UI regressions failed before the repair: three same-prediction save
responses changed the submitted action, note or reviewer but still showed success,
and a duplicated revision was accepted as valid history. The client now compares
the returned action, reasons, note, reviewer/role and predecessor with the pending
request before clearing the draft. A mismatch retains the same request for an
idempotent retry; it cannot show a successful save. History must have consecutive
revisions, unique event IDs and the correct predecessor chain.

A further regression verifies that a 409 conflict preserves the draft, requires
history reload and explicit reconfirmation, and submits a new request bound to the
now-current predecessor. Late responses after a prediction switch remain isolated.

The actual restart test exposed a missing JSON import attribute in the native
measurement loader. The explicit JSON type now works with Node24 as well as the
Vite build. Two Python test files now honor `PROWL_TEST_NODE` consistently rather
than choosing Node20 from the shell despite the requested Node24 runtime. Original
test failures are retained in the tool history; the four UI failures are also
saved locally. No production storage or origin policy was relaxed.

The isolated fixture uses its own Vite dependency cache so it can coexist with
the main development server. It displays a loading/error state instead of a
silent blank page, and accurately labels its decisions as engineering test
records. The earlier blank fixture was resolved after isolating its cache; this
does not establish a general application-rendering defect.

## Verification performed

- **164 UI tests / 15 suites passed**, including conversation edits, cancellation,
  late-response isolation, citations, review identity, save/reopen/revise,
  conflict recovery, navigation and the explicitly selected saved-package check.
- **38 backend tests passed**: durable/idempotent writes, service restart and
  released-session recovery, actual production Vite proxy/origin policy, literature
  attachment identity, failed publication recovery and retained revisions.
- Vite production build and Sites build preparation passed. The existing large
  viewer/codec chunk advisory and FastAPI test-client deprecation remain; no
  dependencies were updated.
- Actual isolated browser flow: save engineering revision1, reopen the exact
  prediction, stop/restart only the dedicated review API **without registering
  the original source**, reopen revision1, append revision2 with a required Other
  note, then reload and verify both decisions. The backend independently checked
  their predecessor chain and event/receipt SHA256 values.
- The private development package manifest SHA256 remains
  `b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5`.
  All five original files match their pre-check hashes. Its actual CPU loader
  returned pancreas-mask76.360628mL and lesion-mask15.170559mL, reproducing the
  retained measurements; these are predicted-mask volumes, not anatomical truth.

Private evidence: `outputs/prowl/testing/reviewer-flow-20261107-01/`, including
`source-before.json`, `physical-package.json`, `browser-review-verification.json`,
two browser PNGs and the separate `engineering-reviews` store. No test decision
was added to a production review store or source package. No new model inference,
training, reference-label loading or participant record was created.

## Test boundary and remaining session checks

The browser used the existing isolated review fixture. Its proxy removes Origin
for its separate test port; the separate **production proxy** test preserves and
verifies the real origin/header policy. Do not present the fixture alone as proof
of production transport security or a full live imaging/assistant walkthrough.

The saved scan was hash/geometry/measurement checked on CPU. No new WebGL contour
inspection, model answer-quality/latency benchmark or stakeholder task was performed.
Before November14, confirm services, current viewer presentation, participant role,
time and permissions; identify any saved-answer playback clearly. The existing
Plan11 script and session record remain authoritative. All participant outcome
fields stay empty until the participant acts.

Backend command (existing isolated dependency directory; no installation):

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
PROWL_TEST_NODE=/Users/quintonevans/.nvm/versions/node/v24.21.0/bin/node \
  .venv312/bin/python -m pytest tests/test_review_store.py tests/test_review_restart.py \
  tests/test_review_production_proxy.py tests/test_review_literature_attachments.py \
  tests/test_review_literature_api.py -q
```

The UI suites and explicit private-package opt-in command are described in
[Plan11](../implementation/11-stakeholder-validation.md). Normal CI never
discovers private imaging files. Lenovo's scientific worker, receipt pins and
hourly monitoring were not changed by these checks.
