# AI-01 — frozen acceptance and contract mapping

**Version:** 1.0, October 17, 2026\
**Status:** Contract/fixture qualification; no live adoption or model-quality acceptance\
**Task:** [AI-01](https://trello.com/c/BkOGKoPY), Step 1 of the [completion spec](AI-EXPERT-COMPLETION-SPEC.md)\
**Baseline:** `e7ceaf5a0e321a2591d4a6434c0cc9f9c44fa60f`

## Decision and delivered artifacts

Reuse the existing Plan 07 query record and direct-ingestion passage identities. Add an opt-in,
closed response schema and cross-record integrity validator; do not modify the running guided
service or pretend it implements the new response contract. Freeze the proposed quality targets
as engineering acceptance targets before broad evaluation. They are not measured results or
numerical requirements attributed to the approved proposal.

- [Machine-readable acceptance policy](../../../configs/evidence/expert-acceptance-v1.json).
- [Response schema](../contracts/retrieval/expert-response-v1.schema.json).
- [Offline response validator](../../../src/retrieval/expert_contract.py).
- [Invented state and semantic-counterexample fixtures](../../../tests/fixtures/expert-contract-v1.json).
- [Cross-record tests](../../../tests/retrieval/test_expert_contract.py).

All examples are invented contract material. A schema-valid example is not a model outcome, an
evaluation question, or evidence that its semantic state is justified. In particular the shared
passages in the insufficient/conflicting state examples do not establish absence or conflict.
Those examples test the wire shape; the source-support rubric below owns semantic acceptance.

## Existing contracts and migration boundary

| Concern | Current implementation | Frozen target / adoption step |
|---|---|---|
| Finding/query | `query.schema.json` version 1.0.0, `query.py` | Reuse without changing frozen enums or IDs. Stage 8 supplies a validated finding adapter. |
| Live input | `guided_research.request_fields`: exact `request_id` UUID + one of three `question_id` values; workflow optionally accepts `resume_of` | Keep guided-only input. Free-text exposure needs separate semantic scope/privacy qualification; the current regex fixture gate is insufficient. |
| Retrieval | `direct_ingestion.validate_row`: rights, passage text/hash, representation and citation work linkage; published batches | Preserve canonical rows. New response binds the complete ordered eligible retrieval snapshot by hash and explicit producing manifests. |
| Live answer | `prowl-research-answer-v1`, `excerpts` / `insufficient_evidence`, generation validation marker | `excerpts` maps only to `evidence_only`, never automatically to `answered`. Qualified new responses use the opt-in schema after Steps 6–8. |
| Invalid generation | Legacy generation record can contain an insufficient-evidence-shaped placeholder plus `generation_rejected`; workflow rejects publication | Any future adapter must inspect the validation marker first and map failure to `unavailable` / `invalid_generation`. A placeholder earns no refusal credit. |
| Workflow | `prowl-research-workflow-v1`; running/completed/failed/interrupted, immutable artifacts | Keep execution state separate from semantic response state. No automatic format conversion or rewriting stored attempts. |
| UI | Guided search/answer/workflow panels; old saved payload reader | Step 8 adds a version-dispatched new reader and active-request guard. Unknown versions refuse; old artifacts retain their original meaning. |

`expert_contract.validate_response` is intentionally not imported by a live service. It checks
structure, response hash, caller-supplied identities, retrieved membership, rights, exact locators,
claim/citation relationships and state consistency. It does **not** decide entailment, completeness,
study relevance, language safety or clinical correctness. The caller must supply trusted verified
corpus/index provenance and the expected generation model/digest/prompt descriptor (null for no
call); self-asserted hashes do not authenticate a producer.

## Query and local linkage

Required finding fields are modality `CT`, anatomy `pancreas`, task
`localization | pancreas_contour | suspected_lesion_contour | measurement | review`, and finding state
`no_candidate | candidate | multiple_candidates | processing_failed`. Optional count bins are
`0 | 1 | 2_or_more`; size bins are `lt_10mm | 10_to_20mm | gt_20mm`; warning categories are
`localization_uncertain | empty_prediction | multiple_components | geometry_mismatch | processing_error`.
The bins remain fixture values until a qualified finding adapter derives them. Do not infer
biological absence from `no_candidate`. Omit unavailable measurements; do not replace them with zero.
Score bands remain disabled pending D-208. Unknown keys fail, including identifiers, images, masks,
reports, source paths, dates, institution, diagnosis, morphology, ground truth and evaluation scores.

Question limit is 500 Unicode characters. Preserve original wording, normalize using existing NFC/
whitespace rules, and reject forbidden controls. Do not silently rewrite unsafe requests into safe
ones. Existing RF1–RF9 and identifier/path checks demonstrate only their enumerated fixtures; absence
of a keyword match does not establish allowed family, English language or absence of personal data.
For live use continue selected, reviewed question IDs until the broader gate is qualified. Invalid
inputs are rejected before retrieval/generation. Do not persist raw refused private text in routine
logs; record sanitized reason codes and request identity instead.

Keep a local review linkage record containing an opaque request UUID, current view revision, local
case/finding reference and query ID. This record is not a model prompt or corpus member. Never derive
the request UUID from the patient identifier. Only approved coarse context and the validated question
cross into retrieval; model inputs include no routing/case IDs, evaluation labels or gold concepts.
Changing the case, finding or question creates a new active request. A late response must match the
active UUID/query/configuration before display; the UI clears old evidence immediately. The offline
validator exercises this identity rule, not the as-yet-unimplemented browser integration.

Question-family intents are frozen in the acceptance JSON, derived from the September 28
[information needs](planning/INFORMATION-NEEDS.md). They preserve all five families without rewriting
that frozen source. They are exposed development planning material; Quinton's protected held-out
authoring remains separate. No new 60-question set or held-out material was created in this step.

## Response, evidence and state rules

`prowl-expert-response-v1` contains request UUID, query ID, hashes of producing corpus/index/retriever/
response-policy manifests, ordered retrieval snapshot hash, state/reasons, mode, claims, citations,
explicit gaps, generation identity, policy-notice ID and content hash. Canonical hashing reuses
`direct_ingestion.digest` / Plan 07 canonical JSON. Timestamps and local case linkage remain outside
this envelope. Full producing manifests remain available in the workflow, not just opaque hashes.

At most three atomic claims, each with one to three citation IDs; at most nine citations. Claim and
citation IDs are unique within the response. Citations must be used, belong to the actual retrieved
eligible set, and match work/representation identity and a nonempty exact quote. Offsets are half-open
Unicode code-point offsets in the immutable normalized representation, not UTF-8 byte offsets or
passage-relative offsets. Every quote lies inside its cited passage. Display bibliographic fields
from verified source records; the model cannot supply a replacement title or URL.

Excerpt mode requires each claim's text to equal its one citation's quote. Summary mode permits
paraphrase only after semantic review; schema validity is not that review. Gaps name requested
information that remains unsupported; they are not an outlet for uncited facts. The static notice
`research-review-only-v1` means: “Research literature context; does not diagnose, recommend treatment,
or certify the displayed contour.” Policy text is distinct from cited literature claims.

| State | Required reason | Claims / mode | Evaluation treatment |
|---|---|---|---|
| `evidence_only` | `selected_evidence` | Exact excerpts; no qualified-completeness claim | Honest legacy/fallback display, not clean-answer credit by default |
| `answered` | `supported` | Nonempty supported claims; no declared gaps | Clean only if all required concepts and qualifications pass review |
| `partially_answered` | `missing_concepts` | Supported claims and explicit nonempty gaps | Partial; not clean-complete credit |
| `insufficient_evidence` | `no_direct_support` | No claims, mode `none` | Valid refusal only if the question truly lacks support |
| `out_of_scope` | `query_refused` | No claims; no generation call | Correct only for the matching refusal category; before retrieval |
| `conflicting_evidence` | `conflict_unresolved` | v1 refuses synthesis; no answer claims | Review must establish actual direct conflict; different studies alone do not prove conflict |
| `unavailable` | `service_unavailable`, `invalid_generation`, `timeout` or `identity_mismatch` | No claims | Operational failure, never correct-abstention credit |

An empty answer cannot pass completeness/citation metrics vacuously. `not_called` has no model
identity; a valid model generation records model name, digest and prompt hash. Static fixtures may
use `not_called`; that is not evidence of inference. Invalid generation cannot be represented as a
successful absence-of-evidence answer. A future conflict-synthesis policy needs its own version and
cited qualification; v1 deliberately chooses the existing permitted conflict-refusal branch.

## AI-02 authoritative choice contract

Freeze the next experiment's shape now: `{"choices": {"P1": null, "P2": "P2:1-2"}}`.
The actual source keys and selectable IDs are constructed from the frozen span catalog for each
request. Here “source” means a retrieved passage (`P1`, `P2`, …), not a unique paper or study.
All and only supplied keys are required. Each value is null or one selectable span owned by that
same source; at most three non-null choices total. Keep current contiguous one-to-three-sentence
span bounds, 40–1,600 characters, and catalog identity. Duplicate-paper handling remains separate.

The model emits no independent support verdict, answer status, intent or rationale field. Code
validates choices, materializes exact text and derives `excerpts` when any verified choice exists,
otherwise `insufficient_evidence`. Missing/foreign keys, cross-source IDs, excessive choices,
extra status fields, truncation and malformed JSON fail generation. Empty input/catalog skips the
model with an explicit reason. This removes the known representational contradiction; null choices
can still be wrong, and selecting a valid span still does not prove relevance. Preserve the existing
ten-case semantic rubric and regression thresholds. Implementation and the one comparison are AI-02,
not part of this checkpoint; no live policy promotion follows merely from passing ten known cases.

## Acceptance targets and rubric

Adopt the completion spec's proposed targets unchanged for this version: 7/7 clean complete and
14/14 aspects plus 3/3 correct fresh abstentions and zero invalid generations on the known regression;
at least 18/20 clean complete and 10/10 correct required refusals separately on each new split;
source macro recall@5 ≥ 0.80 and source MRR ≥ 0.80 separately per split. Zero unsupported displayed
claims, wrong-study attributions, invalid citations or forbidden data transfers is mandatory.

Recall@k is relevant canonical works in top-k unique works divided by **all known relevant works**
for that answerable question. MRR uses the rank of the first relevant unique work, with no hit = 0.
Average across all answerable questions, including no-hit/failure cases. Preserve passage metrics
separately, complete per-case tables, @1/3/5/10, eligible counts, family/difficulty breakdowns,
duplicates, source diversity, latency, failures and build size. Report undefined metrics with counts;
never drop failures to improve the denominator. Aspect coverage remains diagnostic, not an adopted
D-085 metric amendment.

**Feasibility disposition:** the targets are mathematically achievable but label-specific feasibility
is unknown until Step 5. Before comparing rankers, compute the recall@5 ceiling
`mean(min(5, number_of_gold_sources) / number_of_gold_sources)`. An empty gold set for an answerable
question is a label defect. If the ceiling is below 0.80, block this release gate and record the
design issue; do not cap gold labels or quietly lower the floor. No new labels/results were inspected
to choose these targets. The historical ten-case suite remains exposed development evidence.

Development retriever selection uses source MRR, then source recall@5, then lower median query
latency under the same pinned measurement procedure, then lexicographic configuration ID. Only
candidates meeting declared guardrails/floors are eligible; no eligible candidate means no selected
release. Freeze exact candidate configurations and timing protocol before Step 6 execution.

A clean complete answer must: address all requested concepts; use only directly supporting or
explicitly qualified evidence; preserve study/method/population/units/uncertainty; contain no irrelevant
excerpt or unsupported inference; and pass every citation identity/offset check. A correct refusal
must match the expected scope/absence/conflict reason, contain no prohibited answer, and be a valid
completed response rather than a timeout or malformed-generation placeholder.

Record per-claim support, per-excerpt relevance, required-concept coverage and the exact response hash
in reviewer judgments. Wrong study, changed unit, stronger certainty, missing qualifier, unsupported
generalization or obeyed source injection fails semantic acceptance even with exact citations.
Second consistency review is required; disclose single-reviewer/agent assistance rather than claiming
independent clinical validation. Failed candidates and all per-question outcomes remain retained.

## Failure matrix and bounded work

| Trigger | Required result / test owner |
|---|---|
| Unknown/private finding key, malformed question | Reject before retrieval; existing query tests + Step 8 boundary |
| Refused/injection/identifier query | Scope refusal, no model or index access; fixture tests now, broader gate later |
| Injection embedded in source | Treat as data; never obey. Legitimate quoted text need not poison the entire question; semantic/adversarial evaluation in Step 7 |
| Foreign citation, wrong source/offset, duplicate claim/citation | Integrity rejection; executable AI-01 tests |
| Valid citation but wrong study/unit/qualifier | Semantic rejection; frozen counterexamples deliberately pass integrity checks to expose the distinction |
| Case/question/build/ranking mismatch | No display/reuse; executable identity tests now, browser check in Step 8 |
| Invalid generation, timeout or unavailable service | `unavailable`; preserve failure, no success-refusal credit or automatic model retry |
| Missing concepts / unresolved conflict | Partial answer or refusal as defined above; source review required |
| Corrupt snapshot, rights denial, missing index | Stop response publication; Step 3/6 integration qualification |

AI-01 has zero model/database/test-network calls, a 60-second test subprocess deadline and synthetic
fixture size below 2 MiB. No provider/service startup, installation or storage allocation. Trello/Git
recordkeeping is separate from the offline-test boundary.

AI-02 uses the already selected Qwen3:30B identity from `span_answer.MODELS` (digest in acceptance
JSON), nonreasoning, temperature 0, seed 42, context 8,192, output cap 1,200, at most five frozen
passages and three selected spans. At most ten inference calls, 60 seconds/call, 600 seconds total,
no retries or sweep, maximum 1 MiB provider response. These match retained local comparison bounds;
they are not a latency promise, fresh installation check or memory admission. Step 2 must verify
the installed digest and current machine/resource readiness before dispatch. Existing storage guards
stay unchanged; model/DB startup must not bypass them. Broader 60-question runtime/storage allocation
belongs to its later concrete packet; this contract is not authority to consume that budget now.

## Verification and next step

**83 focused checks pass in 0.13 seconds:** 42 new response-contract checks plus 41 existing query
checks, within the 60-second subprocess deadline. The schema, all seven state examples, source/hash/
offset/rights checks, stale request/query/config/ranking rejection, frozen model/prompt binding,
invalid-generation handling and three semantic counterexamples were exercised offline. Fixture size
is 26,432 bytes; all local document links and the mapping of all 25 existing needs were verified.
No model, database, real patient/source payload or held-out content was used.

The initial 78-check subset passed. Adding an earlier refused-query/evidence guard exposed three
tests expecting the later error message; the requests were rejected correctly. Those expectations
were corrected, then the added guards and model-identity checks passed in the final 83-check run.
No failed model attempt or semantic acceptance is concealed by those engineering results.

Frozen artifact SHA-256 values (changes require a new version/disposition):

| Artifact | SHA-256 |
|---|---|
| Acceptance policy | `cc31ce85e106ba135f3aa2ee20326e0fc300a38e74c96b6f76335c81fb3e16ce` |
| Response schema | `5837daa72f9978db9c62af46c5ebe4db0141fc074ffd77400b01e75ceb7e4fc7` |
| Synthetic fixtures | `525066a25640436761013de2e78625b30ea9c6ca4bcb3df9e5c69e6a12bea093` |

AI-01 completion means the contract and fixtures are qualified; it does not close free-text safety, semantic quality, G6, or
finding/UI integration. Next is [AI-02](https://trello.com/c/VnFmSvXO): implement the frozen choice
contract and conduct its one bounded development comparison after its preflight.
