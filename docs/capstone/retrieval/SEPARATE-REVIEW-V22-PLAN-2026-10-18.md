# V22 — integrate feedback and separate review responsibilities

Quinton explicitly requests autonomous completion of feedback integration, separate factual-support/
completeness/readability checks, and a bounded quality check with manual citation inspection. Promote
only on a pass. This authorizes this named implementation/test; older no-more-sweeps language is not
permission for a new model or repeated tuning. Preserve V15–V21 and all original labels/results.

Implementation: integrate `collect_claim_feedback` into one draft/review/revise orchestration. Three
separate review calls have distinct schemas and inputs. Factual support inspects each claim's exact
citations and diagnoses scope/strength/population errors; completeness inspects responsiveness and
necessary task qualifiers against cited evidence; readability sees claim text only and cannot approve
facts. Every outcome requires an explanation. Collect all mechanical and three review findings before
one revision. Any final failed criterion withholds the draft. No partial claims escape a failed draft.
Remove the separate style-rewrite pass: revised text is checked by all three reviewers before display,
so there is no later rewrite to drop quantities/qualifiers. A general physiology statement does not
need numerical study metadata; a numerical example does. Omission of scanner field strength alone is
not a failure unless needed for the question/claim. No blanket numerical-token equality rule.

Use the existing pinned Qwen2.5:14b model on isolated11435/external store, temperature0/seed42/16384
context, first-ranked-paper evidence with original canonical rank/citation identities. No download,
training, source/label change, or protected evaluation. Same-model review remains fallible and is not
an independent judge. No expected answers or rubric concepts enter generation or model reviews.

Bounds: ten existing exposed questions exactly once with retained V9 canonical evidence, no ranking
replay; at most8generationcalls/request (draft+3reviews, then one revision+3reviews),48total,6unloads.
55seconds inference+5seconds unload per literature request;15minute batch;18GiB sampled owned RSS;
internal104GiB/external100GiB floors and registered-volume check. Scope blocks0providercalls. Pin source,
configuration, corpus, traces and complete responses; preserve errors and unsuccessful attempts.

Promotion gate: all five answerable cases must be source-supported, responsive, readable and preserve
required original concepts/limits; zero unsupported displayed assertions; the gap must be an honest
empty result, all four scope blocks correct, no provider/deadline failure. Generation failure is not
successful refusal. Manually audit every displayed assertion against its bound citation, and compare
completeness with the unchanged original rubric. All mechanical/integration tests must pass. If this
fails, finish the report and keep the selected live policy; do not rerun/tune another candidate here.
If it passes, separately record a small live retrieval/UI/paraphrase check before UI promotion. R8's
original retrieval gates and formal independent acceptance stay open; do not claim full feature release.

Services found stopped at start; restore the existing baseline without changing its selection. The
isolated candidate service is stopped after a rejected run. Preserve data, model stores and Docker
volumes. Do not start training or the full selector; no human hours inferred.

## Readiness correction before attempt 2

Attempt1's first request timed out after60.006s during cold model loading, without a draft response.
A second request had already started; the worker was intentionally stopped, and the provider log
records100 generated tokens before cancellation (no response delivered). Supervisor113.135s,
12,568,412,160B peak/reaped. Original receipt remains started/partial with a separate stop receipt;
do not rewrite it as completed. The model subsequently reports resident and the provider log says
all slots idle. No download, model change or prompt change is warranted.

The custom test transport also used60s for inference, bypassing the candidate's intended55s socket
bound. Correct the harness to give inference55s and reserve5s solely for cleanup. Run one fresh
attempt2 only with pinned model/16384context already resident, recording readiness before execution.
Do not silently replay attempt1. At most50chat attempts across both attempts (2previous+48new), six
new unloads, unchanged memory/storage bounds,15minutes for attempt2. This measures ready-model
quality; cold-start readiness remains a separate integration requirement before any UI promotion.
No extra model warm-up generation is needed: record the existing resident-model readiness response.
