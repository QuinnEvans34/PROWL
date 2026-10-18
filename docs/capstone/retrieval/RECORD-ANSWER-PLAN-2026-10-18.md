# Source-record answer integration — October 18, 2026

The user's screenshot shows the old dense/v6.1 answer path rejecting a draft despite the separately
qualified record search. Implement `source-record-answer-v1` behind `--record-answers`, retaining
`--record-search` and the legacy default as rollback options. No new corpus, labels, protected inputs,
training, model download, or human-hour claim.

## Contract and scope

The local Qwen3 8B model (existing pinned 500a1f06… Q4_K_M) selects one of two reviewed phrasings per
source unit and groups the units into paragraphs. It does **not** invent or freely paraphrase medical
claims. This is deliberately bounded composition, not a claim of solved unrestricted generation.
Wording is reusable source knowledge, not a question/expected-answer table. Each unit binds source
fact indices; every fact and qualification must appear exactly once, with code-attached citations.
Source interpretation digests and the wording file are pinned. The frontend reconstructs the exact
text and citation union; it rejects missing limitations, changed prose, crossed records or false
model attribution. Hashes establish identity, not medical truth. Independent review remains pending.

One call, thinking disabled, temperature0/seed42, context8192/output768 tokens, **30 seconds total**
including inventory and load. No same-model factual judge, retry or rewrite loop. Model failure gives
a complete, explicitly application-assembled source summary; it never masquerades as model-written
text. Source-integrity failure still fails closed rather than assembling from suspect evidence.
Outside reviewed-record coverage, return existing dense passages and explicitly state no model was
called. This activation narrows the answer surface to the three qualified disease records; it does
not silently use the previously failing free-generation path. Original default server remains available.

## Wording review

Read all9 canonical Schima2020 passages (ordinals4,7,9,22,24,37,39,43,44) and both variants of every
unit.20 wording variants cover15 source-fact instances across10 units. They retain occasional focal
head enlargement; PDAC/MFCP scope and CT/MRI overlap; single-feature/combined-present-or-absent limits;
smooth duct narrowing without abrupt/complete blockage and MRCP; calcification morphology plus the
duct sign; complete duct obstruction OR soft-tissue arterial encasement comparison; focal-AIP
portal-venous CT, ≤5mm **upstream main duct**, absent proximal atrophy and PDAC mimicry. No percentages,
individual diagnosis or head-size threshold. Wording review is one engineering reviewer, not independent
clinical validation. Original extraction records and frozen source spans remain unchanged.

## Fixed exposed check and promotion gate

After implementation checkpoint, one run of8 HTTP requests: the user's exact screenshot question,
head-enlargement/disease, MFCP/PDAC and focal-AIP/PDAC comparisons; average-volume, unrepresented
neuroendocrine comparison, scan measurement and prompt/database disclosure boundaries. Four real
composition calls maximum; other four must make zero calls. No protected evaluation or new gold labels.
Save producer snapshots, raw model plans, request/response, timing, canonical evidence and readable
review locally under `outputs/prowl/record-answer-v1-20261018/`. Total240seconds/output20MiB; original
Ollama11434 existing model store; no concurrent model at preflight. Model residency recorded, not a
cold-machine benchmark. Local preview on8016 remains source-only during the check.

Promotion requires4/4 genuine complete model compositions,4/4 correct non-generation boundaries,
exact source/fact/citation bindings, manual review of every returned paragraph and source link, no
unsupported wording, each request<40seconds, focused Python/UI tests and build passing. Then enable
8016, make one live browser request (the screenshot question), inspect source navigation and retain
proof. Up to one additional live browser request only if needed to verify a specific UI correction.
A failure is retained; no automatic sweep, silent fallback counted as AI success, or generalization
claim. Report the bounded nature and coverage tradeoff. Update spec/handoff/AI-04 and commit results.

Initial test attempt:79pass/1fail because the invented fixture accidentally shared its citation object
with its expected source. Corrected fixture copies that object; the actual immutable canonical path
was not implicated. Added provider-shape checks. Subsequent80Python/47UI checks pass before live run.

Attempt1 stopped at startup before HTTP/model work: PostgreSQL closed the connection during
`pg_database_size`;0chat calls/0cases/8.166s. Logs show one backend exit2 and automatic PostgreSQL
recovery, not a container restart or reported OOM. Cause is unproven; similar earlier events retained.
Fresh read-only size/inventory/floor checks pass after recovery. Keep the original receipt/log/snapshots.
Add explicit attempt2 output namespace only; same cases/model/prompts/criteria, no generation from
attempt1 to tune against. This is a service-recovery continuation, not a model/prompt sweep.
