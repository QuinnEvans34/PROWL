# Readable source-record answers — October 18, 2026

**Active in the local UI:** Ask question now uses reviewed record retrieval and the existing local
Qwen3 8B model to select wording and organize readable, cited paragraphs. The user's exact question
about inflammation versus a pancreatic tumor works in the browser, with its focal-AIP citation
opening the correct portal-venous CT/duct/atrophy passage. A fresh head-enlargement question also
produces an AI-assisted answer with the combined-feature limitations intact.

This is **constrained composition**, not unrestricted medical text generation. The model selects
between reviewed sentence variants; application code attaches sources and requires all source facts
and qualifications. There are no exact-question answers or evaluation labels in the runtime. Twenty
reusable wording variants bind fifteen source-fact instances in three disease records. Both variants
of all ten units were checked against nine canonical Schima2020 passages by one engineering reviewer;
independent review is pending. The model cannot add a new clinical claim through this contract.

The limitation is explicit: only the three reviewed disease comparisons receive this answer path.
Other questions return dense search passages with a coverage message and **no model call**, including
average-volume questions until their record adapter is qualified. This intentionally supersedes the
old failing free-generation default when `--record-answers` is selected. If model composition fails,
a complete application-assembled source summary is clearly labeled; it is never counted as AI success.
Source admission failures still fail closed. The original server modes remain rollback options.

## Evidence and qualification

| Check | Observed result |
|---|---|
| Initial attempt | PostgreSQL backend exited during startup size check;0model calls/0cases/8.166s. Logs and failed receipt retained. |
| Recovery | PostgreSQL recovered automatically; container OOM=false/restarts0; fresh read-only inventory exactly matches1179passages and database size43,022,003bytes. Cause unproven. |
| Fixed HTTP attempt2 | 8requests/4model calls/4responses/25.148s. Three AI compositions, one explicit fallback, four correct no-generation boundaries. Initial gate **7/8 failed**. |
| Formatting diagnosis | Head answer retained all facts but used3paragraphs instead of2. No incorrect medical wording was needed to explain rejection. |
| Narrow correction | Validate all units/order/scope first, then join adjacent same-record/same-kind paragraphs. No model/prompt changes or prose repair. |
| Retained-plan check | All4 exact original model input/output pairs pass corrected adapter;0new model calls. Separate receipt; original failed gate unchanged. |
| Citation review | All10 corrected output paragraphs checked against source-bound facts/citations; all relevant units retained. Single engineering review, not independent gold. |
| Fresh live UI | Two new model requests: original screenshot question and head-format regression. Both show AI-assisted answers, with sources separate. Source6 navigation verified. |
| Software checks |81Python /47UI checks pass; build passes with existing bundle-size warning. |

Original comparison request8.765seconds; head4.071seconds (then fallback), MFCP4.141seconds,
focalAIP3.653seconds. These are exposed development observations, not percentile or general latency
claims. Browser comparison answer observed within14.573seconds including interaction overhead;
head browser locator wait hit its short tool deadline, then the completed AI answer was verified
without another submission. No application timeout there. Four canary calls plus two live UI calls
make six actual composition requests; retained replay adds none. Thirty-second generation deadline,
one call/no thinking/no retries, existing pinned model/store. No new downloads or training.

The normalization regression tests complete-but-extra paragraph breaks while rejecting added text;
other tests reject omitted qualifiers, wrong citation ranks/quotes, source mutation, cross-comparison
units, duplicate/reordered facts, changed wording/pins and false model attribution. The initial test
fixture shared a mutable citation with its expected object; that fixture defect was corrected and
the failed attempt recorded in the plan. No source-data repair was necessary.

## Artifacts and operations

- Implementation checkpoints: `a479c74`, recovery harness `3cab23f`, paragraph normalization `586d860`.
- `outputs/prowl/record-answer-v1-20261018/`: original failed receipt, producing files, DB log/recovery.
- `outputs/prowl/record-answer-v1-attempt2-20261018/`: original8HTTP results/raw plans/receipt/snapshots.
- Its `format-correction/` directory: corrected retained results, readable review and separate pins.
- Its `ui-comparison-answer.png`, `ui-source6.png`, `ui-head-answer.png`, `promotion.json`: live proof.
- Tracked aggregate: `configs/evidence/record-answer-results-v1.json`.

Selected server:8016PID38141/owned session83863, `--record-answers`. Prior source-only25716/session35480
stopped/reaped143. Candidate8017 belonged to the finished harness and was closed. Original Ollama11434
remains available with its existing models; no isolated11435 service was started. API retains loopback,
request validation, no-store, per-request source/storage/inventory checks and no question persistence.
UI loading text now avoids the old fixed60second claim. Rollback: stop the owned8016 process and launch
the same server with `--record-search` (sources-only improvement, legacy dense/v6.1 answers).

Shared checkout remains `codex/prowl-ui-redesign`; preserve the other chat's `70ad7a2` UI planning/logo
commit. Publish only this chat's scoped commits to `codex/retrieval-record-search` using a temporary
Git index, without switching/resetting the active checkout; retain the local-to-published commit mapping.

## Next work

Broaden reviewed evidence/intent coverage and qualify the volume adapter; keep answer success,
coverage, evidence support and readability separate. Investigate the recurring PostgreSQL backend
exit before calling service reliability accepted. No broad answer-quality, independent evaluation,
clinical-use or final capstone acceptance is claimed. AI-04 remains In Progress. The required
measurement-aware pancreas/lesion extension, independent review/freeze and formal retrieval evaluation
remain open. Corpus, original labels, protected inputs, training/full selector and human hours unchanged.
