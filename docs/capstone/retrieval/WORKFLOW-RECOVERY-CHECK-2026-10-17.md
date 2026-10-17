# HTTP workflow interruption and recovery — October 17, 2026

The approved controlled restart check passed. A real loopback HTTP server process was killed
with SIGKILL after synthetic evidence selection had been published to the workflow's
files and completed journal event. A fresh process on the same directory reported interruption;
explicit linked recovery reused retrieval and selection, then verified and saved one answer.
This is process-death recovery evidence, not filesystem durability under power loss.

## What changed

Added a test-only HTTP process helper using the existing production `ResearchWorkflow`, HTTP
handler and server. It uses synthetic retrieval/generation callbacks, an ephemeral loopback port,
and an isolated output directory. Its validation barrier blocks before validation publication,
after the selection artifact and completed event exist. Only the exact owned Popen child receives
SIGKILL. Restarted callbacks fail if retrieval or selection is called again; model API calls are
forbidden in both processes. No production engine, prompt, model, UI behavior or database changes.

The new subprocess regression checks real HTTP status before and after restart, missing-answer404,
same-ID idempotency, explicit recovery, artifact lineage and exactly one saved answer at this
specific interruption boundary. A new UI component regression separately exercises lost reply →
check same request → interrupted message → explicit linked retry → reused selection and prior-run link.
The component test uses mocked transport; no new real-browser recovery claim is made.

## Results

- Six HTTP tests passed in0.51seconds: one new process restart regression and five existing API checks.
- Eight workflow UI tests passed using Node24.21.0: one new interruption scenario and seven existing checks.
- Parent `0a76d19e-3967-4e8e-94ee-6de4f5f4386c`: five events; retrieve/select complete,
  validation running, save pending. GET reported running while owned, then interrupted after restart.
- Same-ID POST after restart remained a read: no new attempt, response or callback.
- Explicit recovery `3467b716-95e0-4323-877d-b93a9f558ba0`: six events; retrieve/select reused,
  validation/save completed. Both reused artifacts point to their exact original content hashes.
- One synthetic retrieve and one synthetic select total, both before interruption; zero repeated
  callbacks and zero real model calls. The restored response matches the synthetic generation.
- Exactly one response file exists, under the recovery ID. Repeated completed POST and response GET
  returned the identical result. Original history and recovery artifacts remained byte-identical.
- Both owned processes were reaped. Existing workflow8015, UI5180 and Ollama11434 returned200
  afterward. No production stop/restart, database connection, external-drive data access or training.
- No test failure or implementation repair was needed. Production code remains unchanged.

Local evidence: `outputs/prowl/workflow-recovery-20261017/` contains the pre-run plan,
HTTP JUnit report, final live-service health, and retained `pytest-attempt01/` artifacts. The process
case's hash-bound `verification.json` is under `test_http_process_kill_after_s0/`; its SHA256 payload
binding is `54f42352ecde598dcccd12f8e6bdac88ce922b7d37ddf1d71aa49ce1f2175405`.
Source hashes for the test/helper/UI test and unchanged workflow/HTTP producer are retained alongside.
The observed SIGKILL is deliberate fault injection, not a production crash. A source-hash receipt
command initially used system Python without jsonschema; rerunning only receipt creation in the
existing retrieval environment succeeded. No tests or scientific work were repeated for that error.

## Limits and next priority

This verifies one pre-publication interruption boundary on this macOS filesystem. It does not
establish power-loss durability, all possible crash timings, cross-host recovery, or global
exactly-once semantics. In particular, historical interruption after answer publication may preserve
an original answer plus a linked recovery answer; the one-response claim here applies only to the
selected boundary. Existing tests cover that distinct publication case without erasing history.

With the normal live path and this restart path checked, the next priority is answer relevance and
study identity. The live radiomics response still includes an unnecessary application excerpt;
other frozen evaluation cases mix study results. Keep that quality work separate from reliable
execution. No model-quality improvement, full Plan04/G3 completion, selector continuation, training
or human-hours credit is claimed by these tests.
