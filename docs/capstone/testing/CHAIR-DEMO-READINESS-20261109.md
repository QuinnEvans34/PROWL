# Check-in demonstration readiness — November 9

## Battery follow-up before the meeting

The earlier AC-powered check below passed but missed the battery case. Quinton's
later Prepare attempt ran on battery: the answer candidate exited at the existing
`AC power required` gate, while the preparer had already loaded the model and
then obscured that exit as a generic readiness timeout. The drive/database was
not the blocker. The original traceback was preserved in
`outputs/prowl/expert-startup-20261109/literature-before.log`.

Preparation now admits power before starting/warming the model and uses the same
checked search backend in explicit CPU sources-only mode on battery or while
another job owns the GPU. Direct answer/help routes reject generation in that
mode; the UI/proxy also name the charger requirement. Source search and citations
remain available, including from the internal database without the external drive.
Unknown services are not killed. On AC, only the exact verified helper-owned
sources-only process may be replaced after successful model preparation.
Ownership is recorded again after health admission because macOS can rewrite
Python's executable name during startup. Unverified identities remain a blocker.

Actual battery verification: Prepare succeeded; the exposed boundary question
returned source passages; View source opened its retained citation and excerpt.
Direct and UI-proxied answer/interpret requests returned409, and Ollama reported
no loaded model. One verified owned CPU stop/replacement checked service recovery
and stable ownership; a repeated preparation retained the same replacement PID.
The saved native-CT review service was also restored locally for the meeting.
No scientific inference/training or production review write was started here.

19preparation Python tests and72UI tests passed, including actual bounded HTTP
source-only routing and battery Enter/Ask/Help/source-search behavior. Production
build passed with its existing viewer-chunk advisory. One initial UI test invocation
used the older default Node runtime and failed before jsdom workers could start;
the supported existing Node24 runtime passed. No dependency change was made.

Private evidence and screenshot: `outputs/prowl/expert-startup-20261109/`.
The CPU source and review services are now deliberately **left running for the
meeting**; the cleanup statement at the end of this report describes the earlier
12:37check only. The idle user-started Ollama daemon is retained with no model
allocated. Full battery generation is unavailable, not qualified or simulated.
Use the [battery runbook and scope plan](../weeks/REMAINING-SCOPE-AND-DEMO-20261109.md).

This is a bounded engineering/demo check, not stakeholder acceptance, a clinical
review, a new segmentation evaluation or a formal answer-quality benchmark.
Lenovo's existing training, frozen producer and hourly monitor are unchanged.

## Findings and repairs

The Training page was showing a November7 result export and a November3 Lenovo
hours ledger. Both are now replaced by verified current snapshots with dated raw
exports retained. The continuation is shown as10,571new/12,000phase updates and
global22,571/24,000, with phase-only runtime. Best rawDice.4305 at18k and latest
.4122 at22k are visible. The page shows646.1training-session hours, including177.0
estimated historical hours, and91.0teacher-target hours separately. Counter
reconciliation and exact import hashes are in the
[accounting report](../operations/TRAINING-ACCOUNTING-REFRESH-20261109.md).

Actual browser refresh exposed a stale endpoint cache: a new retained export
could update the built-in client but the endpoint kept serving the older in-memory
snapshot. It now reads/admit-checks the retained export on each request, preserving
the last valid state on corrupt/regressed data. An actual reload showed the new
results with no fallback warning. A regression covers refresh without restarting
the server and refusal to rewrite a completed score.

Research and review services initially were stopped. The existing research
preparation path restored the database/search but returned with the model unloaded:
the answer candidate had already taken the lifetime accelerator lock before
preparation attempted model warmup. Preparation now warms the pinned local model
under the same exclusive lock **before** starting that candidate. The lock is
checked again before selecting the answer/source-only service. A competing
trainer still prevents loading the model. No automatic process kill, model
download, lock bypass, memory-limit change or replacement container was added.

For actual qualification, only the candidate created during this check was
identified by exact command and stopped, with exit verified before one corrected
preparation. The preparation then reported drive/database/search/Ollama/model
ready. Prior failed/incomplete startup evidence stays in local logs.

## Actual UI checks

- Research: sent the existing exposed question “Why can pancreas boundaries be
  hard to outline on CT?” once. A single summary completed, the draft cleared,
  and its citation opened the exact retained source passage. The answer still
  included unexplained “PC” and a broad misdiagnosis statement from that passage;
  source binding is working, but this does not establish adequate answer quality.
  Add that example to the formal Week6 relevance/scope/clarity review. No new
  numerical latency claim was measured during this check. The prior user-reported
  2–4seconds remains a dated development observation.
- Saved scan: restored the existing loopback review service and opened the exact
  archived package by manifest identity. The default `/saved` has no configured
  demo source and the reviewed-package list is empty because this source has no
  recorded decisions. Use the direct link below; do not fabricate a decision to
  populate that list. Native CT/three planes and predicted layers rendered.
- The documented question “How big is this pancreas?” returned **about76.36mL**
  from predicted labels, with the anatomical-completeness limitation. The alternate
  “What is the pancreas volume?” is outside the current closed grammar and was
  refused. Use the documented question for the demo; broader language coverage
  remains a usability follow-up rather than weakening the clinical-question gate.
- No review was saved, edited or adjudicated. Existing predicted source files
  and the absence of a production decision remain unchanged. Save/reopen/revision
  evidence is the separate November7 engineering exercise, not today's read-only
  presentation check.

Direct saved-package URL:
`http://127.0.0.1:5180/saved?review=b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5`.

## Repeat the demo

The Training page's retained result and hours snapshots work without the external
drive. They do not automatically advance while Lenovo trains. Live Research uses
the already qualified **internal** database profile, local encoder and pinned
model; bulk CT/training artifacts remain external. Click **Prepare AI expert**
before the meeting. A saved screenshot must be described as saved. This is not
a new external-to-internal speed experiment: the October28 measurements already
showed generation, rather than vector SQL, dominated the delay.

The saved scan is local. If its read/review service is not running, the existing
operator command is:

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
  .venv-retrieval/bin/python scripts/serve_reviews.py \
  --root outputs/prowl/review-records \
  --saved-package outputs/prowl/week05-review-transfer-20261103-01/native-view \
  --port 8018
```

This is the existing private development store, not a new participant session.
Do not write a test decision to it. Port conflict or failed integrity admission
requires inspection rather than killing an unidentified service.

## Verification and scope

75focusedUI tests across9suites passed, covering training/result freshness and
review-state/navigation regressions. Eight accounting tests and12preparation tests
passed using existing dependency directories. Vite production/Sites build passed
with its existing large-viewer-chunk advisory. An initial bare Python test command
could not find pytest; the unchanged existing test-dependencies directory supplied
it. No package installed and no scientific environment modified.

Private proof lives in `outputs/prowl/chair-checkin-20261109/`: before-service
status, source import verification, combined accounting, screenshots and final
cleanup/verification. No imaging data or conversation payload is committed here.
The [check-in notes](../weeks/DEGREE-CHAIR-CHECKIN-20261109.md) are prepared for
Quinton's review, not a record of a meeting that has already happened.

Cleanup at 12:37 p.m. MST: the pinned model was unloaded, the three exact owned demo
processes exited, and only the internal literature container started for this
check was stopped. The GPU lock is free. All five source package files still
match the original manifest and no production review event exists. Temporary
demo tabs closed; the refreshed Training page remains open. No local training or
inference was left running. Prepare the live services again before demonstrating;
the Training page and saved screenshots remain usable without those services.
