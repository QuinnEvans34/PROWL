# Reviewer persistence walkthrough — October 27

W04-04 remains in progress. The real review UI and API passed a browser exercise
using an isolated, invented package and literature capture. No real scan, model,
live review record or teacher process was changed.

## Observed results

| Check | Result |
| --- | --- |
| Save commits but acknowledgement is lost | Draft retained; retry offered |
| Retry the same save | One revision, no duplicate |
| Attach literature to revision 1 | Original capture retained byte-for-byte |
| Open answer and citation | Invented quote and source visible |
| Save a different decision | Revision 2 appended; revision 1 retained |
| Restart API and reopen archived package | Both revisions readable |
| Reopen original attachment after restart | Still attached only to revision 1 |

Post-run store history validation passed. There are exactly two events and one
attachment. Revision 2 supersedes revision 1; the attachment binds revision 1's
event ID. Capture SHA256:
`ec71d2530ce87faea4b5c7e36f8c6e918b205028fb2e892f7a8f69ac66ee8039`.
Evidence is retained in `outputs/prowl/testing/reviewer-walkthrough-20261027/`:
`summary.json`, `injected-failures.jsonl`, `lost-ack.png`, and
`reopened-after-restart.png`. The isolated API and Vite processes were stopped;
ports 8020 and 5186 were verified closed.

## Reproduce

Use a fresh output directory below `outputs/prowl/testing`. The helper imports
existing public test fixtures and requires the retrieval test environment.

```sh
PYTHONPATH=. .venv-retrieval/bin/python scripts/diagnostics/serve_reviewer_walkthrough.py --root outputs/prowl/testing/reviewer-walkthrough-NEW --node /absolute/path/to/node24
```

In `ui`, run Node 24 with `node_modules/vite/bin/vite.js --config
tests/reviewer-walkthrough.vite.config.js`, then open port 5186. Create
`lose-next-save-ack` in the isolated output directory before saving to inject one
lost acknowledgement after a successful commit. Upload that directory's
`capture.json` through the attachment control. Stop and restart the API using the
same directory to check persistence. The fixture proxy adapts loopback origins;
this does not qualify the production proxy's origin handling.

## Remaining acceptance

This verifies persistence and interaction, not clinical correctness or independent
answer quality. It does not exercise real contours, measurement qualifications,
inference, or answer latency. Those W04-04 checks remain open and must preserve
failures. GPU answer checks wait for an authorized resource window. Teacher
generation continues under its existing supervision and frozen recipe.

## Live saved-case slice — October 27

Exercised the existing exposed validation example `PanTS_00009005` in the real
port5180 workbench while teacher continuation07 remained active. No new inference,
answer-model call, clinical decision, or real saved-review mutation was performed.
The previous synthetic persistence evidence above remains separate.

| Check | Observed result |
| --- | --- |
| Load saved case | CT planes loaded; 128 axial slices; prediction available |
| Switch to 3D and Go to pancreas | Prepared CT and prediction surface rendered; pancreas focus worked |
| Check status | Source search ready; teacher GPU reservation displayed |
| How big is this pancreas? | Local saved-outline calculation:60.33mL; explicitly not verified whole-organ volume |
| Measurement provenance |128³grid,3.375mm³voxel volume, decoded CT/prediction hashes; legacy units and missing checkpoint hash disclosed |
| Is this pancreas big or small? | Numerical comparison with published82.6mL study mean;14-person MRI population and method/crop/model limitations preserved; no normal/small/enlarged classification |
| What is the diameter of this lesion? | Explicitly unavailable; no equivalent-sphere diameter substituted for a measured dimension |

Fixed a demonstrated readiness-message defect: GET Check status previously said it
was starting missing services. It now says Checking local service status, while
POST Prepare retains the service-starting message. Button and timeout wording also
identify the actual operation. Verified the corrected pending message in the live UI.
No endpoint, resource gate, or preparation behavior changed. Existing readiness and
measurement tests:77passed across3files. `git diff --check` passed.

Local evidence: `outputs/prowl/testing/saved-case-walkthrough-20261027/` contains
comparison text/screenshot, dimension-boundary text, and focused3D text/screenshot.
This qualifies interaction and disclosed limitations, not model measurement accuracy
or clinical validity. The narrow browser viewport also showed crowded header status
text; responsive header polish remains a follow-up, not a blocked measurement path.

Teacher safety check: supervisor1351/worker2683 remained owned and live, all329
repository producing pins matched, no resource/guardian failure report existed.
Progress reached533/1333 with the next case at100/144tiles. No teacher files changed.
W04-04 remains In Progress: live cited-answer quality/latency in Research and
Workbench, and the user's final walkthrough, remain open for a suitable GPU window.

## Responsive header follow-up

Resolved the crowded header observed above. Navigation no longer shrinks underneath
service status; link labels remain on one line. At760px and below, navigation moves
to a separate48px row, preserving all five destinations. Status text truncates within
its own space rather than overlapping links, and the About button stays in bounds.

Browser geometry checks at390,760,761,784and1280px confirmed no header overflow or
navigation/status overlap. All five links fit at390px; clicking Research reached the
correct route with its active indicator. Inspected desktop and phone screenshots;
viewport override reset afterward. Evidence in
`outputs/prowl/testing/header-responsive-20261027/`: `bounds.json`,
`desktop-784.png`, `phone-390.png`. Vite production build passed; existing large-chunk
warning remains. No new tests added for this CSS-only repair.

Teacher progressed to535/1333 while checking the layout. The stylesheet is outside
its producing pins. No model calls, scientific changes or service restarts occurred.
This closes the header-polish follow-up; remaining W04-04 acceptance is unchanged.


## Production proxy transport follow-up

Closed the Origin-header transport gap noted in the original fixture walkthrough.
`tests/test_review_production_proxy.py` starts an isolated actual FastAPI review
service and Vite proxy on ephemeral loopback ports. The Node harness imports the
production Vite configuration's review proxy options, changing only its target to
the isolated service. It does not remove Origin or rewrite Host. Browser-equivalent
5180 Host/Origin headers are supplied over HTTP; this is a transport integration
check, not a new browser walkthrough or hosted-deployment qualification.

Observed: foreign Origin, foreign Host and cross-site POSTs each return403 without
creating a review. A valid local save succeeds, identical retry returns the same
receipt, and saved/archive reopening returns exactly one revision. Both supported
loopback hostnames work. The fixture contains invented transport bytes and uses
only a temporary record store; no production record is created. The isolated Vite
process is waited/reaped and API thread stopped in cleanup. Other application
plugins/endpoints are intentionally not invoked; no model or service preparation
is triggered.

With Node24 on PATH,21 tests passed in4.02s across the proxy, store and literature
API suites (two existing Starlette deprecation warnings). Initial proxy test failure
was a helper incorrectly parsing Vite's plain-text403 as JSON; response parsing was
corrected without changing production policy. A second run passed17 checks but had
four attachment fixture setup errors because PATH selected Node20; Node24 fixed
the test environment. Attempts are retained separately under
outputs/prowl/testing/review-production-proxy-20261027-01 through03.

Teacher remained live at556/1333 with the next case50/72tiles; all329 producing
repository pins matched. No production code or teacher files were changed.
W04-04 still requires the live answer-quality/latency window and user walkthrough.


## Citation attachment through production proxy

Extended the real proxy test to include the actual literature attachment service
and Node24 capture validator. After saving revision1, the test uploads an invented
cited answer through the unchanged production proxy options, retries it and checks
there is exactly one catalog reference. A foreign-origin upload and a mismatched
review receipt are rejected before publication. Saving revision2 does not move the
attachment: revision2's list stays empty, while reopening the original artifact
returns revision1 and the original parsed capture with its exact byte hash.
Both review revisions remain in history.

The proxy/store/attachment API/attachment storage suites pass36 tests in11.50s;
two existing Starlette deprecation warnings remain. Retained isolated artifacts:
outputs/prowl/testing/review-proxy-citations-20261027-01. The test API and Vite
process are cleaned up; no live records or production code changed. This is a
transport/integrity proof using invented evidence, not factual citation review,
model quality, measurement qualification or the final human walkthrough.
Teacher07 remained live at557/1333, next case50/210tiles; all329 producing pins
matched. Remaining GPU-dependent W04-04 work is unchanged.


## Explicit question cancellation and draft isolation

User reported that changing a question appeared to leave the old request in control.
Inspection found every edit implicitly aborted/reset the UI, hiding loading while
backend work could continue. Research and Workbench now keep separate draft and
submitted question text. Editing during an answer/source request keeps loading and
its elapsed indicator visible, with submit/Enter blocked until completion or Cancel.
The operation label uses the submitted question even when the draft changes.

Cancel invalidates active ownership before abort, keeps the draft and immediately
allows a fresh request with a new request ID. Existing controller identity checks
prevent old success, failure and finally callbacks from affecting the replacement.
The cancellation notice explicitly distinguishes stopping UI waiting from backend
inference termination: the previous local model call may still finish. No backend
termination protocol or instantaneous GPU release is claimed. Question-rephrasing
edits retain their existing stale-suggestion cancellation behavior.

Regression cases cover both UI variants, editing while loading, Enter blocking,
cancel/resubmit, old success arriving during a replacement, and old success/failure
after the new answer completes.90 tests passed,2 skipped across6 related UI suites;
Vite production build passed with the existing large-chunk warning. An initial
failure expected the old pending label; it was updated to Processing question.
No live inference was needed for these controlled delayed-response tests. Teacher
remains paused for the demo. Backend latency and live answer correctness are separate
from this interaction repair.
