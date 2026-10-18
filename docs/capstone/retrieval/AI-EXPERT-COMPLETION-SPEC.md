# AI expert completion specification

**Version:** 1.34 — October 18, 2026 (bounded record search active; answer integration pending)\
**Owners:** Quinton Evans and this DAG/RAG development chat\
**State:** Steps 1–4 complete for their bounded scopes; disease-reference source slice built/rebuilt separately: 14 papers, 1,179 passages. Development v5 review is complete for the prior ten-source scope. Live development literature search and local cited synthesis preview are delivered under user-authorized sequencing amendments; source-impact review is complete and development v6 proposes both disease questions in a 30-case set. Next review the changed evidence/membership and resolve independent protected labeling before the evaluation freeze. Protected freeze, response quality and measurement integration remain open.\
**Implementation baseline:** `369a9ba38eb36216e24ae8289abd78949196657f`

October 18 retrieval-to-record selection: [plan](RECORD-SEARCH-PLAN-2026-10-18.md) and
[results](RECORD-SEARCH-RESULTS-2026-10-18.md). The new **Find sources** action retrieves reviewed disease
records from typed questions, expands their canonical qualification passages, and preserves dense
fallback for unmatched wording. A bounded English topic grammar and lexical source index replace the
harness-supplied intents for this path; no exact question lookup or evaluation labels in production.
First HTTP attempt failed at canonical transport hashing and is preserved; correction adds the actual
FrozenLiterature boundary regression. 57 Python / 33 UI checks pass. Corrected exposed screen24/24:
12 positives select the intended records,12 boundaries select none;7.528s total,0.419s maximum request,
zero answer calls. Two live UI questions and citation opening verified. Source policy is active on8016;
**Ask question** remains dense/v6.1. Finite grammar and three records are not broad semantic/clinical
qualification. Volume routing, readable fact-answer integration, independent evaluation and measurement
extension remain open. Next qualify the readable answer adapter without dropping source limitations.

October 18 disease-comparison extension: [plan](DISEASE-FACT-PLAN-2026-10-18.md) and
[results](DISEASE-FACT-RESULTS-2026-10-18.md). Three reviewed records preserve focal-mass scope,
MFCP/PDAC overlap and combined-feature limits, MRCP identity, calcification morphology and focal-AIP
portal-venous CT/duct/atrophy qualifications. 46 focused tests pass. One canary: two source-only searches,
zero model calls, 0.838s. Fresh dense search selects 0/3 structured record requests; retained R8+context
selects 2/3; deliberately seeded canonical anchors assemble 3/3. Seeds are not retrieval successes.
Fifteen source-statement instances source-reviewed by one engineering agent; independent review pending.
This qualifies bounded deterministic assembly, not free-text routing, model reasoning or full answers.
Next retrieval-to-record selection/intent binding (especially focal-AIP coverage), then a qualified
output adapter; live dense/v6.1 remains unchanged. Existing evaluation/measurement gates remain open.

October18 source-linked fact prototype: [plan](SOURCE-FACT-PLAN-2026-10-18.md) and
[results](SOURCE-FACT-RESULTS-2026-10-18.md). Two separately reviewed MRI study-group records now
retain sample count, method, SEM meaning, matching and applicability limits through deterministic
assembly.33focused tests pass; one real source-only search expands missing context, both records
render completely, seven mismatched typed requests select nothing. Zero model calls. This fixes the
tested omissions in code-controlled assembly, not LLM reasoning or free-text selection. Eight statements
source-reviewed by one engineering agent; independent review pending. Live dense/v6.1 unchanged.
Next qualitative disease records, then qualified natural-language selection/output adapter; current
four-statement/four-source prototype does not automatically fit the existing generation contract.

October18 controlled experiment approved and completed: [plan](EVIDENCE-ISOLATION-PLAN-2026-10-18.md)
and [results](EVIDENCE-ISOLATION-RESULTS-2026-10-18.md). Three unchanged exposed questions, actual dense
top5 versus checked passages versus identical checked passages with explicit relationships. Fixed
model/prompt, nine drafts/eighteen chat responses, no revisions/timeouts, no promotion. Eight focused
tests pass. Manual16paragraph review separates6supported/6unsupported/4uncertain; factual reviewer
falsely approves5definite errors and rejects1supported but nonresponsive paragraph. All nine drafts
remain incomplete under original requirements. Links improve volume citation binding, but identical
answer wording still omits count/MRI/SEM/limits; head drafts are identical too. Retrieval, generation
and validation all contribute failures. Next proposed prototype binds measured object and required
qualifiers in source-linked fact records and code-controlled assembly, then separately tests selection
and rendering. No further prompt sweep, implementation or UI promotion is implied by this checkpoint.
Independent evaluation, original gates and measurement extension remain required. Baseline dense/v6.1
stays selected; candidate server stopped/reaped, model store retained.

October18 requested three-part implementation/checkpoint is complete: [V22 results](SEPARATE-REVIEW-V22-RESULTS-2026-10-18.md).
Complete validation feedback now feeds one revision; factual-support, completeness and readability
have separate calls/schemas/inputs, with no later unchecked rewrite.12new+7existing tests pass.
One cold-load attempt was stopped and retained; one readiness-corrected ten-case run completed:
0summaries/5withheld/1empty/4scopeblocks,35chatattempts/32responses/277.555s. Manual review of all
11withheld draft paragraphs finds unsupported source qualifications and same-model false approvals.
Three timeouts show the added review cost. No quality improvement or formal acceptance claimed;
V22 is rejected and not promoted. Baseline dense/v6.1 demo restored, candidate server stopped.
Next evidence-bound metadata/criterion issues and measured review latency, not another prompt sweep.

October18 checkpoint: [instruction-model results](INSTRUCTION-ANSWER-RESULTS-2026-10-18.md).
V15–V21 remain unpromoted. Citation-isolated review, paper focus, complete numerical feedback and
source-locked rendering improve two narrow regression examples, but full V20/V21 runs fail quality.
V20 displays an over-broad disease comparison; V21 produces zero summaries/five withheld answers,
one empty result/four scope blocks. Preserve false refusals and unsupported drafts as failures.
19 new focused tests and24 restored live search/HTTP tests pass; no formal quality acceptance.
External candidate model is hash-verified and retained, isolated server stopped/reaped. Live dense/
v6.1 API and UI remain selected. Offline feedback collection now passes seven new checks and two retained-trace regressions with
zero model calls; it is not integrated/promoted. Next integrate criterion-specific review reasons
and qualify preservation by semantic role before any fresh bounded model run; no model/prompt sweep. Independent evaluation and measurements stay open.

October17 autonomous improvement amendment: Quinton explicitly requests continued autonomous work
until engineering confidence. [Section retrieval](SECTION-RETRIEVAL-RESULTS-2026-10-17.md) finds
useful disease sections that provisional labels omit, but original coverage gates remain unmet.
[Answer experiments](SECTION-ANSWER-RESULTS-2026-10-17.md) demonstrate that same-model approval is
insufficient: v6.2/v9–v14 are rejected for source scope, qualifications, readability or runtime.
Do not deploy these candidates or infer independent acceptance. The [V15 plan](INSTRUCTION-MODEL-V15-PLAN-2026-10-17.md)
records one bounded instruction-model download/comparison in an isolated external store; this
narrowly amends the older new-download exclusion, not training/selector/protected evaluation rules.
Live dense/v6.1 remains unchanged during investigation. Finish the named comparison, source review
and integration gates before selecting any replacement; preserve all failed attempts and labels.

October17 development sequencing amendment: Quinton's continuation after the recommendation to
recover disease evidence authorizes the [bounded comparison](RETRIEVAL-DEVELOPMENT-COMPARISON-2026-10-17.md)
ahead of formal Step6. [Results](RETRIEVAL-DEVELOPMENT-RESULTS-2026-10-17.md):20exposed answerable
questions, fixed dense/keyword/hybrid; neither candidate meets promotion criteria. Keep live dense
and answer policyv6.1. This narrowly supersedes earlier no-tuning sequencing for this recorded local
development experiment; it does not accept v6labels, waive protected freeze or complete Step6.
Next improve candidate coverage/source context before more prompt experiments. Formal gates below
remain unchanged. Producing baseline for this experiment is30f3e74.

October 17 continuation: [targeted coverage and evaluation checkpoint](TARGETED-COVERAGE-UPDATE-2026-10-17.md).
Corpus v2/development v5 retain their accepted baseline identities. The [disease-reference update](DISEASE-REFERENCE-CORPUS-2026-10-17.md) creates a separate candidate; its scope and labels must be reconciled before the next freeze. No tuning before the applicable evaluation freeze.

October 17 direction approved: retain PanTS and prioritize pancreatitis/pancreatic-cancer evidence,
then dedicated cystic-lesion coverage. The expert serves scan-centered radiologist tasks: verified
measurements, inspectable findings and cited general disease context. General anatomy trivia is not
the product focus. Quinton supplies natural questions; engineering arranges evidence labeling and
independent verification. Do not require him to search articles or enter offsets. Current private
worksheets are historical technical references pending that revised workflow.

The [shared scan-centered question list](SCAN-CENTERED-DEVELOPMENT-QUESTIONS.md) records five assistant
examples accepted for product relevance plus three Quinton-authored variants, grouped into five tasks.
These are exposed development drafts, not new gold labels or a replacement evaluation freeze. Quinton
offers to author 30 independent questions later; technical evidence labeling remains engineering work.

The [routing foundation](QUESTION-ROUTING-FOUNDATION-2026-10-17.md) now supplies closed request/plan
schemas and deterministic offline planning. Measurement/comparison tools are unavailable; literature
routes need scope review. All routes remain unexecuted. 155 targeted checks pass; live guided behavior
and the frozen query contract are unchanged. This is not free-text or disease-answer qualification.

The [literature adapter checkpoint](LITERATURE-ADAPTER-2026-10-17.md) binds reviewed requests and
supplied rankings to canonical corpus evidence without generating answers. 127 targeted checks and
two actual-corpus membership replays pass. Ten source spans for two disease questions remain
provisional; independent review and answerability adjudication are pending. A 44-wording exposure
supplement is recorded for integration before private authoring. No search/tuning release follows.

October 17 sequencing amendment: Quinton explicitly requested autonomous work until a typed literature
question returns real inspectable results in the local UI. [Live development search](LIVE-DEVELOPMENT-SEARCH-2026-10-17.md)
is now delivered as [AI-09](https://trello.com/c/AcXlKWQg), before final evaluation. It uses the unchanged
14-source corpus and existing dense exact top5 configuration. This supersedes the earlier no-live-search
sequencing statements only for this local source-excerpt interface. No configuration tuning, generation,
protected-set access, clinical acceptance or measurement integration follows. Steps 5–9 and their
thresholds remain open. The earlier offline reviewed-question path keeps its admission contract.

October 17 presentation requirement: Quinton requests an easily interpreted text response first,
with citations behind a separate Sources button. The local search now shows original passages in a
readable text view with numbered source buttons; source details and exact excerpts are separate.
This is presentation only. AI-04 must deliver the remaining concise plain-language synthesis:
short direct response, claim-level source references, optional technical detail, explicit missing
information, and no unsupported inference. The local embedding model already powers search;
Ollama generation remains absent from this new endpoint. Existing summary/evaluation gates remain.

October 17 synthesis amendment: Quinton explicitly asks the local AI to formulate human-readable
answers from retrieved evidence now. [Natural-answer development](NATURAL-ANSWERS-2026-10-17.md)
adds an ephemeral local Qwen3 draft/review path and answer-first UI under a separate development
contract. This supersedes the earlier generation sequencing for this preview only. Frozen retrieval,
protected evaluation and formal AI-04 acceptance remain open; engineering checks and model self-review
cannot certify factual correctness. Original gates and prior rejected trials remain preserved.

October 17 reliability repair: [answer failure diagnosis](ANSWER-FAILURE-REPAIR-2026-10-17.md)
replaces model-copied quotations with source-ID selection and code-bound exact retrieved passages.
Policy v6 keeps exact membership/numeric checks and a concise separate model review, adds a shared
60-second generation budget, elapsed UI feedback and distinct failure explanations. The reported
function question now completes in the real UI. This focused repair is not a broad quality pass;
jargon, source-support reliability and formal evaluation remain AI-04 work. Prior trials stay intact.

October 17 fixed [answer-quality checkpoint](ANSWER-QUALITY-CHECKPOINT-2026-10-17.md): ten serial
requests under unchanged v6/corpus/ranking, no retries. Six literature requests yielded two summaries
and four generation failures; four scope blocks were correct. Only one answer covered its intended
content, with unexplained jargon; another overstated a recommendation and missed its disease focus.
Both disease questions missed all known direct spans despite their presence in the corpus. Disease
labels v2 expand five contexts and preserve v1; independent review remains pending. This diagnostic
is not formal acceptance or tuning authority. Next complete label/exposure/independent-review
reconciliation, then compare retrieval configurations and address ranked answer-policy failures.
Readable actual outcomes and evidence pack are linked from the checkpoint. AI-03/AI-04 remain open.

October 17 [public evaluation reconciliation](EVALUATION-RECONCILIATION-2026-10-17.md) consolidates
262 exposure entries / 136 normalized wordings / 31 known intent IDs. Public preflight now consumes
that inventory and the 14-source target; the private command stops before private prompts until a
new admission is qualified. All80 prior span identities and56direct passage containments remain
valid. Scope ledger retains30prior cases plus2candidates without declaring a32-case final set.
Four-source impact review (80new source/case judgments),2gap rechecks, final membership and independent
labeling/review remain pending. Protected schema/operator reconciliation is explicit; Quinton is not
assigned source-search/JSON/offset work. This does not release tuning or change live search behavior.

October 17 [disease-source review](DEVELOPMENT-DISEASE-REVIEW-2026-10-17.md) completes 80 added-source
judgments, 28 disease-source judgments and two gap rechecks. Proposed development v6 replaces the
phase-timing/TAGS-detail cases with both disease questions, retaining 20 answered/8 refused/2 gaps
and all five families. Needs v3 adds the accepted general disease-context direction as N1.6. All100
spans validate,73direct; exposure v3 retains292entries/136wordings/33intentIDs. New draft/review
schemas preserve old behavior and user authorship. 132 distinct focused checks pass across retained
attempts. Human review remains pending with zero v6 events; prior approvals are preserved. Read the
short local change packet and supplied evidence in one pass; no article search or offset work.
This supersedes the preceding checkpoint's pending engineering work, not its historical evidence.

October 17 live-quality direction: Quinton requested moving to live answer quality now. This permits
bounded development policy repairs before the final evaluation, without accepting pending labels,
releasing retrieval tuning or closing formal gates. [Two prompt candidates failed](LIVE-ANSWER-QUALITY-RESULTS-2026-10-17.md)
and were not promoted. Current live v6.1 preserves v6 prompts/model/options and adds mechanical
mandatory-strength/population-word checks; both observed offending drafts are blocked. Browser
head-size smoke rejects the overstated draft; function answer/source navigation works but retains
jargon.89distinct final-code Python checks across attempts/27UIchecks/build pass. Retrieval coverage,
readability and independent quality acceptance remain unresolved. Next recover existing source
context under the applicable evaluation protocol, not another unbounded prompt iteration.

## 1. Outcome and authority

A reviewer can select a structured imaging finding, ask an allowed literature question, inspect
relevant source evidence and a short supported response, and understand when PROWL cannot answer.
Each displayed claim must resolve to the exact retrieved evidence that supports it. Literature
failure must leave imaging review usable.

The approved [proposal v3.8](../../../Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx) and
[technical appendix v3.1](../../../Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx)
remain the source of truth; see [approved-source registry](../../../references/governance/APPROVED-SOURCES.md).
This specification sequences the remaining work in [Plan 07](../implementation/07-literature-retrieval.md)
and the literature portion of [Plan 04](../implementation/04-workflow-orchestration.md).
It does not replace their release gates or declare the full cross-project DAG complete.

**October 17 user-authorized scope addition:** the [measurement-aware expert extension](MEASUREMENT-AWARE-EXPERT-PLAN.md)
is required in the final deliverable, after accepted core RAG Steps 1–9. Steps 10–12 add verified
measurements, cited reference comparisons, explanations and reviewed training feedback. This dated
amendment does not rewrite the approved proposal files or imply institutional approval of new scope.

The [information needs v2 amendment](planning/INFORMATION-NEEDS-V2.md), incorporating unchanged frozen v1,
[query contract](QUERY-AND-RETRIEVAL.md), and
[question/evaluation protocol](QUESTION-SET-AND-EVALUATION.md) remain binding.
Changes to a frozen contract create a new version and a recorded reason.

## 2. Starting point

This is the baseline at specification creation. Current checkpoint results are in the execution
table below, including the [rejected AI-02 comparison](CHOICE-SELECTION-2026-10-17.md).

| Area | Evidence already delivered | Remaining acceptance gap |
|---|---|---|
| Corpus | 41,226,017 imported PubMed metadata records; bounded index has 274 passages from two CC BY 4.0 reviews, PMIDs 35406426 and 37173876 | Metadata is not a rights-cleared full-text library. Coverage of all five information-need families remains unproven. |
| Retrieval | Local pgvector, pinned 384-dimensional MiniLM embeddings, source/offset/hash provenance | Select a configuration using lexical/dense comparisons and the frozen evaluation set; complete D-202 evidence. |
| Demo | Guided research questions and exact source quotations | Structured findings are not yet connected to the literature query; quotations alone do not prove relevance or completeness. |
| Workflow | Retrieve → select → validate → save; immutable artifacts, verified reuse and explicit linked recovery | Qualify corpus/index rebuild, invalidation and the final literature integration boundary. |
| Recovery | Controlled HTTP interruption after selection recovered in a fresh process without another model call | This is evidence for that boundary, not power-loss durability or global exactly-once publication. |
| Answer quality | Ten known development cases expose study mixing, omitted context and false abstentions | No candidate has passed the complete quality bar; no held-out result exists. |

The latest assessed-selection candidate was rejected: **1/7 clean complete answers, 3/14 required
aspects, 3/3 correct missing-evidence abstentions and five invalid generations**. Live v2 was not
changed. The best earlier experimental result was 5/7 clean, still below acceptance. Preserve every
failed attempt; do not combine favorable outputs from different runs into a reported score.

Evidence: [selection comparison](ASSESSED-SELECTION-2026-10-17.md),
[workflow implementation](EXPERT-WORKFLOW-2026-10-17.md),
[live check](WORKFLOW-LIVE-CHECK-2026-10-17.md),
[restart check](WORKFLOW-RECOVERY-CHECK-2026-10-17.md).
These are dated observations, not a fresh service-health assertion.

## 3. Core product contract

1. The reviewer chooses a finding and a question within the five frozen families: CT appearance,
   measurement/contour review, anatomy, AI limitations, and review workflow/uncertainty.
2. Software constructs the query from allowlisted context: CT modality, pancreas anatomy, task,
   finding state, coarse count/size bins and warning category. The reviewer can see the context used.
3. The retrieval boundary rejects raw images/masks, reports, identifiers, ground truth, diagnostic
   conclusions and unsupported fields. Free-text questions receive the same scope/privacy checks;
   an allowlisted structured object alone does not make arbitrary question text safe.
4. Retrieval returns ranked public-literature evidence with stable source, representation, passage
   and corpus/index identities. Source notices and limitations remain visible.
5. The response contains only claims supported by the retrieved text. Study identity, modality,
   population, measurement units and qualifiers must stay attached to the correct evidence.
6. Citation selection opens the exact excerpt and bibliographic source. A quotation's exactness is
   checked separately from whether it answers the question.
7. The UI distinguishes supported, partial, insufficient, out-of-scope, conflicting and unavailable
   outcomes. These are semantic requirements, not a demand to rename existing wire enums. Step 1
   maps them to versioned schemas. Invalid generation is a failure, never a successful abstention.
8. A case/question change cannot display stale evidence as the new answer. Run identity and loading,
   timeout, cancellation, retry and recovery behavior remain explicit. Imaging stays available.

Keep case linkage in the local review/workflow record; pass only approved coarse context to retrieval
and generation. Do not expose case identifiers in model prompts or literature indexes. Evidence text
is untrusted input, including instructions embedded in articles. Literature never certifies a contour
as correct or safe and never produces patient-specific diagnosis, staging, prognosis or treatment.

## 4. Acceptance rules

### Mandatory release conditions

- Every displayed factual claim and citation passes source-support review; zero fabricated citations,
  wrong-study attributions, unsupported clinical claims or forbidden patient-data transfers.
- Every required-refusal case refuses for the correct reason. Service failures and invalid outputs
  are reported separately from valid insufficient-evidence responses.
- Corpus, labels, retriever, response policy, model identity and software commit are versioned together.
  Rebuild and recovery checks preserve source identity and never publish an unvalidated response.
- Publish the complete per-question results, denominators and limitations in the permitted form.
  Small, single-reviewer evaluation is not clinical validation or evidence of generalization.

### Quality targets frozen in Step 1

These are **engineering acceptance targets**, not numerical promises in the approved proposal and
not achieved results. [AI-01](AI-EXPERT-CONTRACT-V1.md) adopted the original proposed values unchanged
before broader evaluation and froze definitions, budgets and the feasibility procedure. Label-specific
recall feasibility remains a Step 5 check; a failure blocks the gate without pruning gold labels.

| Measure | Frozen target | Interpretation |
|---|---|---|
| Current ten-case regression | 7/7 clean complete answers; 14/14 aspects; 3/3 correct abstentions; zero invalid generations | Known, corpus-informed development check only; passing does not authorize live promotion. |
| Frozen 30-question development and 30-question held-out splits | At least 18/20 clean complete answerable responses in each; 10/10 correct required refusals in each | Partial responses and false abstentions do not count as clean complete answers. Safety conditions above apply even when coverage misses. |
| Source-level retrieval | Macro recall@5 ≥ 0.80 and MRR ≥ 0.80 on answerable questions, separately per split | Use the existing known-relevant-set formula; do not substitute hit rate for recall. Report passage metrics separately. |
| Citation support | 100% of displayed claims supported; 100% citation identity/locator validity | Report counts; an empty response cannot earn answerability credit by emitting no claims. |

Report recall@1/3/5/10, MRR, duplicates, source diversity, family breakdown, empty/failure counts,
latency and rebuild size regardless of pass/fail. AI-01 freezes bounded test/next-comparison budgets
from the retained local configuration; execution still requires fresh admission. This specification
promises no unmeasured latency. Diagnostic span/
concept measures do not silently replace official D-085 metrics or approve its proposed amendments.
Targets cannot be relaxed after observing evaluation results to manufacture a pass.

## 5. Ordered execution plan

Work one step at a time. Each step ends with a reviewed artifact, relevant checks, a coherent Git
checkpoint and a Trello result. A rejected experiment can complete an investigation task while its
quality gate remains open. Only advance past it when the next step does not depend on that gate.

| Step | Work / Trello owner | Exit evidence | Current status |
|---|---|---|---|
| 1 | Freeze acceptance and query/response contracts — [AI-01](https://trello.com/c/BkOGKoPY) | [Contract, fixtures and 83-check result](AI-EXPERT-CONTRACT-V1.md) | **Complete — contract scope** |
| 2 | Test one authoritative evidence choice per source — [AI-02](https://trello.com/c/VnFmSvXO) | [One comparison and rejection evidence](CHOICE-SELECTION-2026-10-17.md): 4/7 clean, 10/14 aspects, 2/3 correct abstentions, one invalid generation | **Complete — investigation; quality failed** |
| 3 | Close literature DAG and rebuild behavior — [W04-01](https://trello.com/c/Z9QSh78P) | [Inventory, invalidation, recovery and exact rebuild evidence](LITERATURE-WORKFLOW-CLOSURE-2026-10-17.md) | **Complete — bounded literature scope; broader G3 open** |
| 4 | Fill corpus coverage gaps and freeze the index — [W02-07](https://trello.com/c/fGxysGgy), [W05-02](https://trello.com/c/OqxGSjju) | [Seven-source freeze and coverage limits](CORPUS-FREEZE-2026-10-17.md); 693 passages, exact rebuild | **Complete — bounded candidate; 4 coverage gaps retained** |
| 4b | Build pancreatitis/cancer reference sources — [AI-08](https://trello.com/c/HmDLnOYF) | [Source qualification and exact rebuild](DISEASE-REFERENCE-CORPUS-2026-10-17.md); preserve accepted baseline | **Complete — source slice; product integration pending** |
| 5 | Author, adjudicate and freeze the evaluation set — [AI-03](https://trello.com/c/NctoNxr8) | 30 development + 30 protected held-out questions, complete labels and second consistency pass | **In progress — development review complete; independent protected authoring/freeze pending** |
| 6 | Measure and select retrieval — [W06-02](https://trello.com/c/zDFlThwi) | Development lexical/dense/hybrid comparison and frozen selection with D-202 disposition | Queued after 5 |
| 7 | Qualify short grounded responses and refusal — [AI-04](https://trello.com/c/dWDF81CH), under W06-02 | Claim/citation coverage and semantic review on development, chosen policy or explicit fallback | Development preview implemented by explicit amendment; formal qualification remains after 6 |
| 8 | Connect finding → question → evidence in the viewer — [W07-01](https://trello.com/c/IM0zPvP9) | Browser-tested finding/context/citation flow and all failure states | Queued after 7 disposition |
| 9 | Run protected core acceptance and package the baseline — [W08-01](https://trello.com/c/s827dTBE), [W07-02](https://trello.com/c/cfVFZT2a) | Frozen held-out report, final integration/recovery evidence, walkthrough and operator handoff | Queued after 8; all release dependencies required |
| 10 | Qualify measurements and summary adapter — [AI-05](https://trello.com/c/Ob3VE0MN) | REQ-X01 verified geometry, measurements and lineage | Required; queued after accepted core Step 9 |
| 11 | Add eligible reference comparisons and explanations — [AI-06](https://trello.com/c/TKCLH5PZ) | REQ-X02–X03 cited comparison and failure/refusal evidence | Required; queued after 10 |
| 12 | Integrate reviewed training feedback and accept extension — [AI-07](https://trello.com/c/pL25Swot) | REQ-X04, separate extension assessment, viewer and final handoff | Required; queued after 11 |

### Step 1 — Acceptance and contracts

Produce an implementation-ready contract covering allowed structured fields, free-text handling,
local case linkage, retrieved evidence, atomic claims/citations, semantic response states, version
identities and failure codes. Reuse existing schemas where they fit and explicitly map any migration.
Create synthetic answered/partial/refused/conflicting/unavailable examples and rejection cases for
foreign passages, wrong offsets, wrong study/units, omitted qualifiers, injection, identifiers and
stale case responses. Freeze question-family intents before broad retrieval tuning, with provenance.
Record the numerical target disposition and a bounded run/test budget. No model call is needed to
finish this step. This is the next implementation task, not another open-ended planning exercise.

### Step 2 — One bounded selection repair

Replace contradictory independent assessment/status/span decisions in the experimental candidate
with one authoritative evidence choice per source; derive final status in code. Validate the synthetic
contract first. Pin the model/prompt/schema, inputs and budgets before one ten-case comparison:
maximum ten calls, 60 seconds per call, 600 seconds total, zero automatic retries or sweep. Retain
raw requests/responses privately and publish permitted scores/identities. This is a hypothesis, not
a proven fix. Passing the regression bar still requires broader evaluation before promotion.

If it fails, stop this experiment and record the failure. Do not add another reviewer model or loop
through prompts in this task. Continue independent corpus/workflow work using fixture or clearly
labeled evidence-only behavior; the response-quality gate remains open for Step 7. Live v2 remains
an unqualified development demo until a separately recorded promotion passes the required gates.

### Step 3 — Literature workflow closure

Reuse the delivered adapter. Define stage inputs/outputs and invalidation when corpus, embeddings,
query, model or response policy changes. Verify rebuild from canonical files and pinned embeddings,
count/hash/query parity, explicit recovery at remaining publication boundaries, missing/corrupt
artifacts, concurrent run IDs, unavailable DB/Ollama and storage admission. Verify imaging remains
usable. Preserve valid existing evidence instead of rerunning unchanged tests without reason.
Record the Plan 04 runner/tool decision and which literature obligations are met; broader imaging
orchestration and G3 remain separately assessed. Core Step 9 rechecks affected integration paths; Step 12 qualifies the extension.

### Step 4 — Coverage and corpus freeze

Use the five information-need families and Step 1 intents to identify missing support. The two-review
demo is the starting slice, not a sufficient library by assumption. Prefer a bounded, documented
source expansion with per-source rights, correction/retraction checks, normalized representation
hashes and exact locators. Record exclusions and coverage that remains absent. Freeze the search
protocol/cutoff, corpus, passages and embeddings before the new labels/index comparison.

The full journal selector on [W02-06](https://trello.com/c/LxvwMa3s) stays **parked**. It is not an
implicit prerequisite for bounded permitted-source work. If a gap truly requires full selection,
record the concrete dependency and return that scope decision to Quinton; do not launch it from this
specification. W02-07/W05-02 completion must state the bounded corpus scope actually delivered.

### Step 5 — Question and label freeze

**Current next action:** review the proposed v6 membership, added-source evidence and consistency
delta, then resolve independent protected labeling/operator/schema under a new evaluation admission.
Engineering source review and exposure consolidation are complete; semantic independence review remains. The count/family design below is the
preserved protocol, not an instruction to manufacture answerable questions or assign technical
labeling to Quinton. Any replacement criteria must be versioned before results; prior accepted v5
review cannot approve new disease labels. No held-out questions are requested during this reconciliation.

October 17 user requirement: qualify everyday questions and readable answers under the
[plain-language demo plan](PLAIN-LANGUAGE-DEMO-PLAN.md). Before final freeze, review anatomy/size
coverage and version selected plain-language development questions. Preserve the 60-case design,
all five families and existing specialist evidence tests; no tuning before the revised freeze.

Follow the existing evaluation protocol: 20 answerable + 10 unanswerable/out-of-scope per split;
all five families, varied difficulty, required concepts, direct/partial/limiting evidence, exact
normalized source spans, answerability/refusal reasons, provenance and adjudication. Keep related
intents/paraphrases in one split and complete the required second consistency pass.

Use the [development review workflow](DEVELOPMENT-REVIEW-WORKFLOW.md) to record explicit wording/
answer, evidence-label and second-pass decisions against the exact draft/case/answer hashes.
The current v5 record has three explicit events plus inherited v4 decisions, completing all30 human review stages for the prior scope. It does not grant tuning release or replace the final split-freeze artifact.

Expected answers are evaluation references only: never index them as literature or attach them to
the generation prompt. [Six boundary checks](ANSWER-KEY-BOUNDARY-2026-10-17.md) pass for the current
guided quotation path; future free-text/summary adapters must qualify this separation themselves.

The existing exposed ten-case suite stays a separate development regression; do not relabel it
held-out. Quinton owns protected held-out authoring/storage under the existing encrypted-image,
independent-backup and read-only evaluation procedure. Agents receive schemas, synthetic fixtures,
development data and held-out hashes/counts, never the held-out questions/labels or mount credentials.
The independent labeling arrangement must be resolved without assigning source-search/offset work to Quinton; agent-generated
questions already exposed to development cannot substitute for it. No image/storage allocation is
authorized merely by listing the task. Git excludes held-out content and restricted source text.

### Step 6 — Retrieval selection

Measure lexical FTS and dense retrieval on frozen development labels, then a bounded hybrid candidate
if justified. Separate retrieval failures from selection/response failures. Use official recall/MRR
definitions, deterministic source deduplication and all required diagnostics. Freeze the primary
selection metric and tie-breaks before comparisons; choose the measured valid configuration, even
if lexical wins. Pin the full producing configuration and resolve D-202 with retained evidence.
Held-out questions remain unopened during selection.

### Step 7 — Grounded response acceptance

Implement short claim-level supported summaries with citations and explicit limits. Test study
identity, omitted qualifications, units, multi-source support/conflict, irrelevant excerpts, false
abstentions and adversarial text. Score the frozen development set with a second source-consistency
pass; report that labels/judgments are single-reviewer rather than independent clinical review.
Freeze one selected response policy, model identity and contract before final held-out execution.

If summaries fail the gate, retain ranked source excerpts/refusal as the Plan 07 fallback and label
the release mode explicitly. A fallback can protect capstone delivery; it does not mean the requested
short-summary capability passed. Do not mark this full feature complete while that gap remains.

### Step 8 — Finding-to-evidence integration

Connect existing saved prediction/review fixtures first, then an eligible saved case. Show the
allowlisted context, question, response status, exact evidence, citations and limitations. Verify
case-switch isolation, keyboard-accessible citation inspection, empty/partial/conflicting results,
timeouts, model/DB outages and explicit retry/reload. Static fixtures and live responses use the
same versioned contract. Keep W07-01's wider durable review-decision obligations separate; this
literature subtask alone does not close that entire card.

### Step 9 — Core RAG acceptance and handoff

Freeze the release commit, corpus/index/model/policy identities and rubrics before Quinton's logged
held-out evaluation. Lock retrieval rankings, then evaluate responses against them without tuning.
Record all results, failed gates and limitations. A disappointing result is not permission to reuse
held-out examples for tuning; a genuine implementation defect follows the documented rerun process.

Recheck affected end-to-end, recovery, rebuild and privacy paths; record a stakeholder walkthrough
with answered, partial, refused and unavailable examples. Deliver startup/shutdown, health checks,
resource prerequisites, restore/rebuild/recovery instructions, troubleshooting, pinned dependencies
and a demonstration script. Quinton reviews the outcome; each broader capstone card closes only
when its own complete acceptance criteria are met.

### Steps 10–12 — Required measurement-aware extension

Implement the [extension plan](MEASUREMENT-AWARE-EXPERT-PLAN.md) only after Step 9 satisfies its
core quality gates. Require actual accepted RAG behavior, not a functioning demo or excerpt fallback.
Deliver REQ-X01–X04 and separately evaluate the expanded release. Exact measurement summaries need
a new validated contract; current coarse inputs stay unchanged until then. Reviewed training feedback
is required, but this plan does not start training or promise a fine-tuning/performance gain.

## 6. Schedule, scope and progress control

Proposal milestones remain Week 4 (October 26–November 1) for workflow qualification, Week 5
(November 2–8) for the versioned queryable prototype, Week 6 (November 9–15) for retrieval metrics,
Week 7 (November 16–22) for reviewer integration/walkthrough, and Week 8 (November 23–29) for core
integration/evaluation/documentation. Week 9 is stabilization; Week 10 is delivery. These are
planning targets, not new runtime or completion guarantees. Beginning early is useful; feature
completion is measured by evidence, not by the calendar or number of passing engineering tests.

Only one implementation task is active in this lane. Steps 1–2 are complete in their stated scopes;
Steps 3–4 are complete for the bounded literature adapter and corpus, expanded to ten sources before freeze; Step 5 development review is complete for the prior scope; the new disease-source slice is complete, and capability/labeling reconciliation now precedes protected authoring/backup/freeze. Other new tasks stay
in Backlog. The full-selector card is parked in Backlog, and W02-08 retains the existing prototype
history pending its scoped closeout. Existing milestone cards remain the roll-up records; new AI
cards are execution subtasks, not replacement project milestones. Broader-card dates stay unchanged.

At each checkpoint, update this table and the corresponding Trello card with: changes, evidence
paths, checks/results, pass/reject/blocked decision, commit and the next step. Commit reviewed files
in coherent increments and push under the user's standing publication instruction. Preserve failed
experiments and unrelated changes. Never infer human working hours from agent or machine runtime.

| Checkpoint | State | Evidence / next action |
|---|---|---|
| Completion specification v1.0 | Documented October 17 | This spec; Trello links in execution table. No implementation or model run performed by this planning checkpoint. |
| Step 1 / AI-01 | Complete October 17 — contract scope | [Frozen mapping/schema/fixtures/rubric](AI-EXPERT-CONTRACT-V1.md); 83 offline checks pass; live services unchanged. |
| Step 2 / AI-02 | Complete October 17 — rejected investigation | [Comparison](CHOICE-SELECTION-2026-10-17.md); 50 checks and ten exact offline replays; no promotion or second model run. |
| Step 3 / W04-01 literature slice | Complete October 17 — broader card/G3 remains open | [Closure report](LITERATURE-WORKFLOW-CLOSURE-2026-10-17.md); 63 Python and three imaging component checks, exact 274-passage rebuild and three-query parity; zero generation calls. |
| Step 4 / W02-07 | Complete October 17 — bounded candidate | [Freeze report](CORPUS-FREEZE-2026-10-17.md): 7 sources / 693 passages, 35 offline checks, exact rebuild/three-query parity; coverage 6 direct / 15 partial / 4 gaps. W05-02 broader roll-up open. |
| Step 4b / AI-08 | Complete — source slice only | Four disease references added to a separate14-source/1,179-passage collection; exact rebuild, old inventories and58tests verified. [Report](DISEASE-REFERENCE-CORPUS-2026-10-17.md). |
| Step 5 / AI-03 | In progress — proposed v6 engineering review complete; changed-scope human review pending | Three explicit v5 events accept changed wording/evidence and full 30-case consistency; unchanged v4 approvals preserved. [Private authoring quickstart](PRIVATE-EVALUATION-QUICKSTART.md), blank templates, ten-source reading pack and offline checker delivered. 28 private-validator and 36 public-checkpoint tests pass. Actual protected authoring/validation/backup/freeze remain pending; public receipt stays not_created. No protected content accessed or tuning release. |
| Controlled answer diagnosis / AI-04 | Experiment complete; feature In Progress | [Three-by-three results](EVIDENCE-ISOLATION-RESULTS-2026-10-18.md): all nine drafts observed without timeout, zero complete answers, evidence omissions and semantic/citation/reviewer failures isolated. No replacement promoted. Next source-linked fact records and explicit qualifier assembly, subject to its own bounded plan. |
| Source-linked volume facts / AI-04 | Bounded assembly pass; feature In Progress | [Results](SOURCE-FACT-RESULTS-2026-10-18.md): two complete reviewed group examples,33mutation/selection checks, seven actual-corpus typed mismatches rejected, one source query/zero model calls. Qualitative records, free-text selection, output adapter and independent evaluation remain open; no UI promotion. |
| Steps 10–12 / AI-05–AI-07 | Required; not started | [Measurement-aware extension](MEASUREMENT-AWARE-EXPERT-PLAN.md); only after core acceptance; final release includes REQ-X01–X04. |
| Development source search / AI-09 | Complete — sequencing amendment | Typed general literature questions return real source excerpts in the local UI; 127 Python / 22 UI checks, production build and real browser verification. [Report](LIVE-DEVELOPMENT-SEARCH-2026-10-17.md). No answer-quality acceptance. |
| Steps 6–9 | Open | Await complete Step 5 freeze before retrieval tuning. Response quality gate remains open for Step 7. |

Excluded from this completion plan: actual training/fine-tuning runs (reviewed feedback integration is required), autonomous clinical decisions, broad report
drafting, raw patient-data retrieval, an unrestricted chatbot, automatic full-selector continuation,
new model downloads, and unbounded prompt/model sweeps. Existing storage and source-rights controls
still apply. A needed scope change is documented before execution rather than hidden inside a card.

## 7. Definition of done

The expanded feature is complete when Steps 1–12 have accepted evidence, REQ-X01–X04 are verified,
Plan 07 G6 is satisfied, the finding
workflow works in the reviewer UI, the frozen development and protected evaluation meet the declared
quality contract, and an operator can reproduce/recover the supported release. Core RAG acceptance
is a prerequisite, not final completion of the required extension. Training-feedback integration
is required; actual retraining remains a separately scoped experiment. Trello, this progress
record and the Git checkpoint must agree. If a required gate fails, report **partial/blocked with a
specific remaining gap**, even when the demo is usable. No percentage-complete estimate substitutes
for those results.
