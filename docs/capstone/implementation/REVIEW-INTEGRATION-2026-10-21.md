# Connected native prediction review — October 21

The first saved-review slice now connects the existing `/predict` and `/saved` native viewer,
measurement limitations, cited general-literature panel, and durable local reviewer decisions.
This advances [W07-01](https://trello.com/c/IM0zPvP9) early under Quinton's consolidation priority.
It is not completion of the entire reviewer interface or independent clinical/measurement acceptance.

## Delivered behavior

A research operator chooses Accept, Needs correction, or Reject with compatible reasons and an
optional note (required for Other). Confirmation shows the exact package, prediction and segmenter
identities. Only a verified server receipt produces “Saved locally.” A failed request retains the
draft; uncertain acknowledgments retry the same request ID. Stale revisions require reloading
history. Revisions append and name the prior event; they never overwrite it.

Saving also retains the exact CT, predicted mask, result and inference provenance on this Mac.
The `/saved` selector reopens that package after the original on-demand session has been released
or the service has restarted. Merely viewing/running a prediction does not archive it. No actual
human decision was entered during engineering tests. The original development package still has
no recorded decision until a person submits one.

General literature uses the existing answer/citation/refusal component, alongside the native
measurement panel. It does not infer a diagnosis from the scan or send scan identifiers/voxels to
the LLM. Existing geometry, boundary and missing-coverage limitations remain unchanged. An unavailable
measurement warning is visible before a question or review decision, so a reviewer does not have to
ask for volume to discover the limitation.

## Small local contract

`scripts/serve_reviews.py` serves loopback FastAPI on8018; Vite proxies `/review-records`.
`src/review/store.py` persists the unchanged `review-event.schema.json` v1 event. The native adapter
uses SHA256 of the exact manifest bytes for `case-package:<hash>` and `prediction:<hash>`; the
namespace distinguishes IDs while the hash binds the complete CT/mask/model/result/provenance
manifest. This is a native-package adapter, not a claim that the broader case-package DAG is done.
A different manifest is a different review target, even for the same study.

- GET `/targets/saved`, `/targets/job/<32hex>`, or `/targets/archive/<64hex>` returns target IDs,
  manifest hash and chronological event/receipt history. Source locations are operator-selected
  or fixed-loopback job endpoints, never a client-provided path or URL.
- POST to that target requires exactly `request_id` (UUIDv4), `manifest_sha256`,
  `expected_latest_id` (null initially), `reviewer`, `action`, `reason_codes`, and `note`.
  The server owns event ID, time, revision, supersession and client transport fields.
- Receipt: event ID, revision, canonical event SHA256, sequence, relative stored location, package
  and prediction IDs. Same request/content returns the original receipt; changed content with the
  same request ID is rejected. A stale latest-event ID cannot overwrite another decision.
- GET `/packages` lists retained reviewed results; `/packages/<hash>/files/<allowlisted-name>`
  serves hash-checked archived files for the existing native loader.

Storage uses process locks, flushed files, atomic create-without-replacement for event records,
and directory fsync before acknowledgment. Corrupt history/files fail closed. Retention is bounded
at20 packages,2GiB total package storage,1,000 events/package,64MiB/image,1MiB/provenance file and a
100GiB free-space floor. No automatic eviction. This is a local single-operator file writer, not
accounts, distributed concurrency, clinical deployment or an independent backup service.

## Verification and remaining acceptance

81 focused Python checks passed across review persistence, native packaging and the existing
contracts; the additional full-process restart check passed with invented data. The affected native
measurement/on-demand/saved-review UI checks pass (53), plus the connected-viewer integration check; the measurement-answer checks also passed
in the earlier61-pass run with one pre-existing skip. Production build passes with the existing
large-chunk advisory. Tests cover stale and concurrent submissions, incompatible reasons, changed
prediction bytes, history corruption, disk errors, lost acknowledgment, idempotent retry and
cross-origin refusal. No tests called a model or read protected evaluation questions.

The full-process check uses the existing invented native worker: save → stop review process →
remove temporary prediction → restart without source configuration → reload archived CT/mask through
the actual JavaScript native loader. Its8mm³ synthetic pancreas calculation and identity checks pass.
The test's initial expectation of a zero exit code on SIGTERM was corrected to accept the normal
−15 exit; a TIME_WAIT bind probe was corrected to probe a live listener. Neither failure justified
changing the writer's persistence semantics.

Remaining: Quinton's real walkthrough, manual browser/keyboard/layout checks, broader main-workbench
contract migration, failed-analysis review support and formal W07-01 acceptance. Browser automation
was not used because the session's earlier localhost automation denial remains respected. API,
component tests and production build do not substitute for that walkthrough. No held-out acceptance,
reliable whole-organ measurement or automatic training-feedback claim follows.

## Operation

From the repository, with the existing retrieval environment (FastAPI/jsonschema and Uvicorn; the
locally installed Uvicorn version is0.54.0):

```sh
.venv-retrieval/bin/python scripts/serve_reviews.py \
  --root outputs/prowl/review-records \
  --saved-package outputs/prowl/native-measurement-20261020/package
```

Use the same saved package for `PROWL_SAVED_PREDICTION_DIR` when starting Vite from `ui/`.
The review directory is ignored by Git and stays private. Existing on-demand service8017 is needed
only to archive a live job; an archived result can reopen without it. Literature8016/Ollama/database
remain optional for recording a review. Do not start duplicate listeners.

Trello W07-01 reads/board listing timed out; its status update is pending. W03-01 correction write
also timed out, and a subsequent read retained the older description. Local Week3 plan records the
pending corrections; no successful board-sync claim is made.

The local services were restored after finding them stopped. Docker's known external-drive bind
error recurred; the expected drive UUID/directory were present. Under existing Docker authorization,
Desktop was restarted and previously running XML-Adventure restored. The checked database start
returned ready without reinitialization. UI5180, review8018, configured inference8017, literature8016
and Ollama11434 are running. Proxy checks returned200, confirmed the configured manifest hash and
zero recorded real-case decisions. Retained operational check: `outputs/prowl/review-integration-20261021/activation.json`.
No real inference or generation request was made during this restoration.

Read-only live verification also loaded the actual configured CT/mask/result through the JavaScript
native loader and matched its manifest hash to the review API. It still reports measurement
unavailable because the outline touches the inference crop boundary. Zero real decisions were written.
