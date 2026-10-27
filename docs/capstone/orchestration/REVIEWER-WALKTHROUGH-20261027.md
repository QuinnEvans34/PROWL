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
