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
