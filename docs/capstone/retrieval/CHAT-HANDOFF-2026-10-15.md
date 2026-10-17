# PROWL development handoff — October 15, 2026

**October17 Step3 literature workflow qualified:**
[Closure report](LITERATURE-WORKFLOW-CLOSURE-2026-10-17.md): corpus inventory/catalog now pinned;
repeatable-read verification before retrieval; unchanged storage floors enforced before attempts/stages.
63Python and3imaging component checks pass, including four artifact/event interruption boundaries,
changed dependencies, missing artifacts, unavailable services and a real synthetic partial-batch resume.
First test attempt52pass/5serializationfail retained and repaired. Separate real rebuild274passages/
9batches/2sources in3.901734s; three guided query outputs exactly equal; originalresearch-v1 unchanged.
No passage re-embedding/generation/training/full selector. Inventory415ca84294b21864c1a12c1a24effec3fd99b3f64be04576cf35c41cd400acc9.
Existing sequential repository runner retained for this literature slice; general D-201/Prefect trial,
broader imaging G3 and answer quality remain open. Historical completed responses remain readable;
old failed runs require new requests after the producer-binding change. Owned workflow service now
execsession11852/PID49262 on8015; oldPID3190 verified idle/stopped.8015/5180/11434health200, saved
response exact after restart. Evidence outputs/prowl/workflow-closure-20261017/; rebuild and four
syntheticDBrows retained. **Next Step4/W02-07 + W05-02: coverage review and bounded corpus freeze.**
No inferred human hours. Earlier next-step/service statements remain historical.

**October17 AI-02 complete — choice candidate rejected:**
[Comparison](CHOICE-SELECTION-2026-10-17.md): ten calls/16.250867s,6/7nonempty positive responses,
4/7clean,10/14aspects,9/13relevant exact excerpts,2/3correct abstentions,one invalid generation.
nCLE selects four spans and is rejected; CT mixes studies/omits context; PROWL-validation falsely
answers with unrelated retrospective-study text. No promotion or further model experiment.
50focused checks and ten exact offline generation/request/input replays pass; public score retained.
Owned comparison finished/absent; Ollama slots idle; live v2 unchanged. Specv1.2 marks Step2 complete
as an investigation, not quality acceptance. **Next Step3/W04-01: literature DAG invalidation,
rebuild and remaining recovery qualification**, using fixtures/evidence-only behavior. Full selector,
training, held-out and human-hours remain untouched. Earlier proposed-next statements are historical.

**October17 AI-01 complete — contracts and acceptance frozen:**
[Contract v1](AI-EXPERT-CONTRACT-V1.md) maps existing guided/query/response/workflow versions,
adds opt-in response schema and cross-record validator, seven invented state examples and three
semantic counterexamples.83focused offline checks pass (42new/41existing query); exact identity,
source/rights/offset/model/prompt checks do not certify relevance or entailment. Existing guided
live input stays closed; fixture regex is not unrestricted free-text safety. Proposed numerical
targets adopted unchanged with explicit pre-evaluation recall-feasibility check; all25need mappings
retained. Specv1.1 marks only Step1 complete. **Next AI-02:** one choice/null per supplied passage,
code-derived status; frozen shape/budget in contract. No selector implementation/model comparison
or live integration performed here. No service changes/full selector/training/hours credit.

**October17 completion specification and Trello sequence documented:**
[Completion spec v1.0](AI-EXPERT-COMPLETION-SPEC.md) is the current execution plan: nine ordered
steps from contracts through quality, literature DAG/rebuild, corpus coverage, protected evaluation,
finding integration and final acceptance. Four new cards AI-01–AI-04 cover missing execution tasks;
existing milestone cards retain their wider scope and have linked updates. W02-06 is parked in
Backlog; W02-08 is queued in To Do for prototype closeout. No feature gate is marked complete.
**Next is Step1/AI-01: versioned query/response mapping, synthetic examples, metric/rubric and budget
freeze.** New numerical targets are proposals to dispose before broad tuning, not achieved results.
The protected held-out authoring boundary stays with Quinton. This checkpoint changes documentation
and Trello only; no new model run, code, service operation, selector, training or human-hours credit.
Earlier proposed-next passages below are historical; retain their experiment evidence.

**October17 assessed selection comparison rejected:**
[Quality comparison](ASSESSED-SELECTION-2026-10-17.md). New experimental single-call passage
assessment plus span selector:10calls/37.043s,2/7supported,1/7clean,3/14aspects,3/3fresh abstentions,
5invalid generations. Each invalid output marks evidence direct then emits no spans; guard rejects.
PET improves; CT method context still missing; nCLE assessment also mislabels another EUS study.
No promotion; live v2 unchanged.43focused tests and10exact offline replay/request/input checks pass;
public score recomputes. Next recommended: one authoritative evidence choice per source with status
derived by code, frozen contract/tests before one comparison. No next run or extra reviewer stack.
Full selector/training remain parked; no hours credit.

**October17 controlled HTTP restart recovery passed:**
[Recovery verification](WORKFLOW-RECOVERY-CHECK-2026-10-17.md). Killed only an isolated synthetic
HTTP service after selection publication; a fresh process reported interruption. Explicit linked
retry reused retrieval/selection, verified and saved exactly one answer at this pre-publication
boundary. Same-ID delivery stays read-only; original history and artifact hashes unchanged.
Six HTTP and eight workflow UI checks pass; both owned processes reaped, no real inference/DB
connection or production changes. Live workflow/UI/Ollama health200 afterward. This does not prove
power-loss durability or global exactly-once publication. Next priority: relevance/study identity,
with normal execution and this restart path now qualified. Full selector/training stay parked.

**October17 approved cache cleanup and live workflow passed:**
[Live verification](WORKFLOW-LIVE-CHECK-2026-10-17.md). Deleted exactly37 reviewed private build-cache
records; Docker reports9.162GB freed,34 shared records retained, container/image/volume inventories
unchanged. Host recovered to~105.46GiB; unchanged admission passed. Docker restart fixed stale drive
sharing; XML-Adventure restored and PROWL DB healthy. Added existing workflow panel to `/research`.
One browser radiomics run completed all4stages in10.890196s;3exact quotes, one loosely related.
Same-ID POST/GET reuse identical with no new inference or artifact writes;274passages/9batches and
DB fingerprints unchanged. Build passes. DB55433/workflow8015/Ollama11434/UI5180 running; old8013/8014
offline. Quality unresolved. Next proposed: controlled real-service interruption/recovery check using
retained/synthetic generation before broader workflow scope. No full selector/training/hours credit.
Earlier blocked/pending statements below are historical.

**October17 live integration blocked by storage / cache review complete:**
[Storage review](LOCAL-STORAGE-REVIEW-2026-10-17.md). Quinton approved one live question/reuse check;
normal database startup refused95.547GiB internal free versus104GiB requirement before Compose.
No inference or DB start. Docker inventory shows9.162GB private old Astro/Airflow build cache;
its relocated source project exists, but historical cached snapshots have not been compared to backups.
Quinton requested verification before deleting anything: no cache/data deleted; cleanup permission
pending. Do not bypass floors or use broad pruning. Ollama available; workflow/UI/old answer services
offline at preflight. One-question live verification remains outstanding; selector/training parked.


**October17 first expert workflow delivered:** [Implementation and verification](EXPERT-WORKFLOW-2026-10-17.md).
Separate local adapter/panel exposes retrieve→select→validate→save, immutable artifacts/events,
verified reuse, and explicit linked retry. Invalid generation fails without publishing an answer;
valid insufficient evidence completes.45distinct Python and47distinct UI checks pass; real-browser
synthetic HTTP failure/recovery/reload passes, as does the build. Abrupt process death and interruption
after response publication recover without repeating verified generation. Existing v2 policy unchanged.
Production8015 service/database not started this turn; next is one bounded live integration check.
This is a research workflow slice, not full Plan04/G3 or semantic-quality acceptance. No framework
selection, new inference-quality run, selector continuation, training or human-hours credit.


**October17 reasoning diagnostic complete / rejected:** [Results](REASONING-DIAGNOSTIC-2026-10-17.md).
Five selected cases, five calls,113.255seconds. PET recovers; radiomics/CT/nCLE each exhaust2048tokens
with empty final JSON. Supported1/4,clean1/4,aspects2/8,unsupported abstention1/1,three invalid
outputs; no promotion.59focused tests,15exact offline replays,five request comparisons and score
recomputation pass. No retries or budget expansion. Ollama restored/idle; answerAPI8014 offline,
other demo services not reverified. Earlier healthy-service statements are historical. Next proposed:
explicit retrieve→select→validate→save stage status/reuse and failure/retry slice, distinguishing
invalid generation from insufficient evidence. Pause model/prompt experiments; quality remains open.
Full selector and training remain parked. No human-hours credit or raw-output publication.


**Direct30B selection baseline complete / not promoted:** [Comparison](DIRECT-SPAN-COMPARISON-2026-10-15.md)
changes only the span-selection model on the same frozen passages/prompt/schema. Ten fresh calls,
12.699seconds:5/7supported,4/7clean,9/14aspects,6/6relevant exact excerpts,3/3fresh correct abstentions,
zero invalid generations. nCLE study mixing resolves, but radiomics/PET falsely abstain and CT method
context remains omitted. No quality acceptance or live change.56focused checks and20exact offline
replays pass; all10request pairs differ only in model. Client finished/Ollama idle/API healthy.
Next proposed: bounded30Breasoning diagnosis of the two false abstentions and missing context, with
positive/unsupported controls, before additional stages. Not run; no prompt/model sweep or full corpus
selector/training. Older proposed-next entries below preserve history.

**Source-linked evidence experiment complete / rejected:** [Design/results](STUDY-EVIDENCE-2026-10-15.md)
adds question-independent study records with exact parent-sentence anchors, adjacent context,
explicit explanation/study kinds and separate matching. Ten cases/15calls/24.311seconds;8valid records.
Quality regresses from30Bscope5/7clean to3/7clean,6/14aspects;5of8useful selections lost. EUS/PET false
abstentions; nCLE/CT field-unit violations rejected, including a neighboring-study cohort attribution.
Only radiomics cleanup improves.70focused tests and10offline generation replays/15request hashes pass;
no semantic qualification. No demo change; client finished, Ollama idle, answer API healthy.
Next recommended: direct30Bevidence-span selection on frozen passages with the existing selection
prompt/schema, to measure the missing simpler baseline before more stages. Not yet run. Full corpus
selector/training stay parked. Earlier proposed-next paragraphs below are historical.

**Evaluator-capability comparison complete:** [30B comparison](EVALUATOR-COMPARISON-2026-10-15.md)
uses installed pinned Qwen3:30B with the same frozen selections/nonreasoning scope prompt. Ten cases,
twelve calls,28.427seconds:7/7 supported,5/7 clean,14/14 aspects,8/10 relevant exact quotations,
zero invalid assessments. All eight useful selections retained; only two of four irrelevant selections
removed. Three abstentions preserved without reviewer calls. Not promoted: wrong nCLE study and
irrelevant definition/application evidence still pass.56 focused checks,20 offline replays, ten shared
request comparisons and score recomputation pass. Live v2 demo unchanged; client finished/Ollama idle.
Next proposed repair: source-linked study/method/cohort/result evidence with adjacent paragraph
context and explicit question intent, before expert DAG integration. No more model/prompt sweep
or full selector/training follows automatically. Older next-step paragraphs below are historical.

**Scope-verification follow-up:** [Implementation/results](SCOPE-VERIFICATION-2026-10-15.md)
adds experimental per-excerpt checks and same-source context expansion. Reasoning-off8b review
loses useful evidence:5/7 supported answers,4/7 clean,9/14 aspects,2 invalid assessments; it also
accepts an unrelated CT study. Reasoning-on4096-token profile stopped early after a budget failure:
four cases completed, six unscored. Neither profile is promoted. Original quotation API remains
unchanged. Fixed repeated-text occurrence/context binding;53 focused checks pass and14 retained
raw-response replays preserve evaluated behavior. Next is a bounded evaluator-capability comparison,
not another review-stage stack or corpus expansion. Owned evaluation clients are stopped.

**Structured-selector follow-up:** [Implementation/comparison](STRUCTURED-SELECTION-2026-10-15.md)
adds experimental `span_answer.py` + `evidence_spans.py`, explicitly selected by the evaluation CLI.
Ten-case comparison:7/7 supported answers,12/12 exact citations,0 generation rejections,3/3 correct
abstentions; clean complete answers remain4/7 and strict relevance falls to8/12. Not promoted:
study mixing remains and radiomics relevance regresses. Live default stays byte-identical v2.
39 focused checks pass;10 offline raw-response replays match after module separation. Next is
separate study-scope verification using these spans, not another prompt sweep or larger corpus.

**Latest development evaluation:** Ten frozen cases were run after Docker/demo recovery.
See [evaluation and decision](DEVELOPMENT-EVALUATION-2026-10-15.md). Baseline has7/7 supported
reference hits,4/7 complete relevant answers,3/3 correct missing-evidence abstentions. One prompt
candidate regressed to3/7 clean answers and was rejected; production source remains v2 and the
demo is unchanged. Frozen suite/harness checkpoint442daee precedes both runs. Both runs and raw
failures are retained locally; hash-bound judgments are in configs/evidence/evaluation/. Next is
structured source-span selection with study context, then explicit expert DAG reuse/recovery.
Do not treat the older pending evaluation or original uncommitted-state notes below as current.

**Checkpoint follow-up:** Quinton subsequently assigned this chat DAG/RAG ownership and requested
the reviewed Git checkpoint. See [review and verification](REVIEW-CHECKPOINT-2026-10-15.md) for
the two failure-handling repairs, current checks, remaining startup issues and checkpoint scope.
The uncommitted-state and proposed-queue descriptions below preserve the original handoff snapshot.
Ollama was also unavailable at takeover. Trello records the resulting commit/publication identities.

## Start here

Continue development with Quinton in this repository:
`/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
Timezone: America/Denver. Read applicable AGENTS.md instructions, but distinguish historical
training/run records from current scope and actual process state. This chat owns application,
data-consumption, research-evidence and workflow integration. **Training and PANORAMA execution
belong to another laptop/chat.** Quinton reports PANORAMA training is running there; do not claim
it is unimplemented just because its handback has not been inspected here.

Quinton wants a collaborative, visible process: explain purpose and tradeoffs, show what changed,
what passed, what remains, and the next step. One implementation phase at a time. He is frustrated
by days spent on corpus processing and excessive preparatory work. Favor useful vertical slices,
bounded checks, and existing implementations. Do not introduce more gates or long jobs without a
concrete reason. Never infer human project hours from machine runtime.

## Latest discussion and proposed next work

Quinton asked whether finishing the full selector was the best next move. Recommendation was **no**:
we already have a working direct embedding → pgvector → UI → local extractive-answer path.
The selector would expand the candidate pool, not directly repair answer quality.

Proposed sequence, not yet executed:
1. Review and commit the accumulated work in focused commits, creating a recoverable baseline.
2. Time-box an evaluation with roughly10 new questions: supported evidence, missing evidence and
   scope boundaries; record relevance, citations, abstention and latency. Fix the highest-impact issue.
3. Make the AI-expert DAG stages explicit: retrieve → select evidence → validate → save, with stage
   status, reuse and a demonstrated failure/retry path. Reuse current code rather than introducing
   a new orchestration framework.
4. Reconcile Week2 closeout and obtain the other laptop's cohort/PANORAMA evidence.

The user then requested this handoff, not execution of that entire queue. Start with a short recap
and verify current startup state. Do not automatically resume the parked selector or launch training.
The broader DAG and the AI expert are separate responsibilities; an expert DAG alone does not
satisfy the entire Week4 project milestone.

## Actual status checked while writing this handoff

These are observations on October15, not guarantees for the next chat:
- Branch `main`; HEAD `a833ccb` (Record confirmed selection continuation after resume fix).
  Previous commits `9ac6af3`, `a2d75f8`.
- **All direct-ingestion, research UI, answer and retrieval-improvement work remains uncommitted.**
  `git status --short` shows modified and untracked source/config/tests/docs. Preserve it.
- External `/Volumes/PROWL-Data` exists/mounted. Required UUID:
  `22750B93-2F3F-499D-87F5-902981BFAB59`; reverify before DB operations.
- **`prowl-literature-db-1` is STOPPED: Exited(0), approximately8hours before check.**
  Earlier statements that the database is running are historical. It was not restarted for handoff.
- Answer API PID28694: `scripts/serve_research_evidence.py --answers`, port8014.
- Retrieval API PID28720: `scripts/serve_research_evidence.py`, port8013.
  Historical owned sessions25018 and17869 respectively; verify native identity, not just old IDs.
- PROWL Vite PID33722 runs `--host127.0.0.1 --port5180 --strictPort --open false`.
  **Current HTTP Origin allowlist permits localhost5173,127.0.0.1:5173 and127.0.0.1:5179,
  not5180.** Before a real UI demo, reconcile intended local origin/port without broadly disabling
  origin protection. Existing browser tests ran on5179 and did not establish5180 works.
- No matching replay/selector process appeared in the process inspection. Full selector is parked.
- Unrelated XML-Adventure Docker container and a BCI Vite process are running; leave them alone.
- API process existence does not prove a successful request: DB is stopped and UI origin differs.

## What now exists

### Real corpus and embeddings

`research-v1` contains274 passages from two previously retained CC BY4.0 JATS papers:
PMID35406426/PMC8997008 (quantitative imaging/radiomics review), and
PMID37173876/PMC10177524 (AI in pancreatic cystic lesions/adenocarcinoma review).
Nine atomic batches; no synthetic vectors in this collection. Other test/rebuild collections exist.

Encoder: sentence-transformers/all-MiniLM-L6-v2,
revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`,384dimensions, normalized masked mean pooling,
CPU float32/4threads/256token max. Pinned file hashes in configs/evidence/encoder-minilm-v1.json.
Model already downloaded (~87MiB); no need to download it again.

Every passage retains text, exact normalized offsets, source/revision hashes, stable IDs, rights,
PMID/PMCID/DOI/title/authors/year, attribution and source URL. Source bundles retain original
paragraph mappings. Only permitted abstract/body prose, excluding figures/tables/references.
Rights and notice status reflect retained snapshots, not live retraction certification.

Loader supports atomic batch publication, idempotent retry, collection encoder/source identity
checks, immutable canonical vector artifacts, and rebuild without re-embedding. Different grouping
of overlapping passage IDs is refused; keep batch size32 for this build. Newly reviewed works can
be appended. Existing one-sentence-overlap chunking includes a bounded character fallback for long
sentences; no silent encoder truncation. Initial limits include8GiBDB,104GiBinternal/408GiBexternal
admission floors. These are admission checks, not filesystem quotas or a permanent corpus limit.

Dedicated Docker project `prowl-literature`, localhost55433, database/user `prowl_literature`,
2CPU/2GiB. Image pinned in infra/retrieval/compose.literature.yaml.
Data: `/Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-direct-01`.
Private config `infra/retrieval/.env.ingestion.json` is ignored; it contains paths, not the password.
Password file is private/ignored. Never print it. Canonical source/vector artifacts:
`outputs/prowl/direct-ingestion-20261014/batches/` (~3MiB).

### UI and saved responses

Three separate panels in the existing reviewer workspace:
1. Grounded research answers — local model-selected quotations.
2. Research passage search — raw real retrieval.
3. Guided evidence questions — clearly labelled synthetic fixture demonstration.

**The live UI accepts THREE FIXED questions, not arbitrary conversational/free-text chat.**
Prior voice statement that one can “ask it questions” should not be interpreted as free-form chat.
Question catalog: configs/evidence/research-questions-v1.json (radiomics,EUS,CTdetection).
No patient context sent. Local development proxies only; static deployed sites have no such backend.

One immutable JSON result per request UUID, identical retry, conflicting reuse409, unexpected fields400,
foreign Origin403, unavailable backend503. Citation links expand source passages. Saved responses
include provenance and content hashes, remain immutable across improvements, and are downloadable.

### Local answer model and limits

Installed Ollama `qwen3:8b` Q4_K_M, digest:
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
No new generation-model download was necessary. qwen3:30b is also installed but unused.
Local Ollama11434; tag/digest checked before calls. Structured output, thinkFalse,temperature0,
seed42,num_ctx8192,num_predict900,90secondHTTP timeout,5minute keep_alive.

**This is extractive answer selection, not free-form synthesis.** Model selects up to3 quotations;
server checks exact text against cited passage IDs. Invalid/truncated output gives explicit abstention;
model unavailable returns service failure. Empty retrieval skips model. Policy verified-extracts-v2
removes later quotes repeating a substantive full sentence>=40characters from an earlier quote.
Citation integrity is NOT truth, completeness, semantic support or relevance verification.
No patient diagnosis/treatment routing beyond the fixed-question interface has been implemented.

### Retrieval improvement

Whole-question semantic top5 initially returned generic intros/search-method passages; broad
radiomics/EUS questions abstained even though relevant material existed in the274passages.
`guided-facets-v1` adds two explicit query facets for each of those questions, including EUS acronym.
CTdetection keeps its original query. Reserve top result per query then reciprocal-rank fusion
(constant60); stable ID ties; remove word-set Jaccard>0.8 overlap; return5 results. No hardcoded
result IDs. Each result records query/rank/cosine/fusion score and plan hash.

All3questions then produced checked excerpts; unsupported randomized-trial survival-benefit probe
abstained. Generation roughly9–14seconds in that comparison. Model initially repeated an EUS study
with an adjacent MRI comparison; retained evidence and final deterministic deduplication reduce that
answer to2quotes. CT results can still include PET/CT neuroendocrine material: subtype/task scope
requires scrutiny. **These are corpus-informed development checks, not held-out relevance evidence.**
Do not label a new set independent if you repeatedly tune against it. Preserve failed outputs.

## Files to read / preserve

Reports (docs/capstone/retrieval/):
- DIRECT-INGESTION-PLAN-2026-10-14.md
- DIRECT-INGESTION-RESULTS-2026-10-14.md
- RESEARCH-UI-RESULTS-2026-10-14.md
- GROUNDED-ANSWERS-2026-10-14.md
- RETRIEVAL-REVIEW-2026-10-14.md
- BOTTLENECK-TRIAGE-2026-10-14.md

Implementation:
- src/retrieval/direct_ingestion.py: source/rights/chunks/encoder/vector artifacts/DB loader/search
- src/retrieval/guided_research.py: immutable retrieval/answer response store
- src/retrieval/grounded_answer.py: pinned local model, prompt, quotation checks/abstention/dedup
- src/retrieval/guided_retrieval.py: versioned guided query facets/fusion
- scripts/retrieval/direct_corpus.py: start/stop/ingest/load/search
- scripts/serve_research_evidence.py: retrieval or --answers API
- scripts/serve_evidence_fixture.py: shared loopback HTTP handler, fixture-compatible defaults
- ui/src/components/ResearchEvidencePanel.jsx; GuidedEvidencePanel.jsx integrates panels
- ui/vite.config.js and ui/tests/fixture.vite.config.js: local API proxies
- configs/evidence/{direct-source-batch-v1,encoder-minilm-v1,research-questions-v1}.json
- infra/retrieval/compose.literature.yaml; requirements/retrieval.in and overlay version snapshot
- tests/retrieval/test_{direct_ingestion,guided_research,grounded_answer,guided_retrieval}.py
- ui/tests/browser/{research-evidence,grounded-answer}.spec.js

Ignored local evidence includes direct-ingestion-20261014/,grounded-answer-20261014/,
retrieval-review-20261014/{comparison,answers,reviewed-answers}.json,
research-evidence/responses/,research-answers/responses/ under outputs/prowl/.
Do not commit credentials, model bytes, article text, vectors, or local runtime artifacts.

## Verification and commands

Historical verified checks (not blanket current-repo certification):
-17direct-ingestion tests including live PG checks;9batch retry, exact274record rebuild and clean
 restart passed. No new full power-loss claim; first CLI failure preserved.
-Latest31focused Python tests for guided retrieval/answers/store and fixture regression passed.
-7existing UI unit tests passed during UI integration.
-Latest2live Chromium scenarios passed after retrieval updates; prior fixture regression also passed.
-Node24 production build passed; existing large-chunk advisory remains.

Use Node24.21.0 (`ui/.nvmrc`), not shell Node20 (jsdom failed before tests on20).
Separate `.venv-retrieval` reuses foundation `.venv-prowl` through a local .pth file; transformers4.57.1,
psycopg3.2.10 overlay. Requirements snapshot is version-pinned, not a hashed portable lock.
No foundation/training environment modification was required.

```sh
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json start
.venv-retrieval/bin/python scripts/retrieval/direct_corpus.py --config infra/retrieval/.env.ingestion.json stop
.venv-retrieval/bin/python scripts/serve_research_evidence.py
.venv-retrieval/bin/python scripts/serve_research_evidence.py --answers
.venv-retrieval/bin/python -m pytest -q tests/retrieval/test_guided_retrieval.py tests/retrieval/test_grounded_answer.py tests/retrieval/test_guided_research.py tests/test_guided_evidence_fixture.py
```

Do not launch duplicate APIs. Verify process commands and ports before starting/stopping.
Live browser tests require explicit PROWL_LIVE_RESEARCH=1 and PROWL_LIVE_ANSWERS=1, mounted drive,
DB and APIs. They use synthetic viewer/no patient arrays with real research/model backends.

## Parked selector / large catalog

Raw downloads and full PubMed replay completed:1656entries,41,226,017records,~510GBcatalog.
Catalog `/Volumes/PROWL-Data/PROWL/scratch/literature/catalog-streaming-20261010/catalog.sqlite`.
Full topic selector parked around39,351,230records (~95.4%), NOT completed. Old session46696 exited130
intentionally. Receipt outputs/prowl/selection-launch-r02/parked-direct-ingestion.json.
A resume integrity scan had taken hours; fixed bounded validation and separated full audits. Subsequent
random external-disk I/O remained slow. User chose to move on. Keep raw data, partial outputs and
receipts. Do not consume unfinished selection as complete, delete it, or silently restart it.
Old recurring overnight import prompts were obsolete; no new monitoring automation is requested.

## Weekly commitments / ownership

Read docs/capstone/weeks/WEEK-02-WORK-PLAN.md and PROJECT-DELIVERY-OUTLINE-2026-10-09.md.
Some tables predate October14 direct-ingestion pivot; later retrieval reports supersede that dependency.
-Week2 Oct12–18: protected/frozen portable cohorts, separation/repeatability. Local cohort package
 and saved-prediction viewer delivered. Seven unknown CT-unit cases, head-study annotation question,
 cross-machine confirmation, confirmed hours and Sunday closeout need honest disposition. Environment
 reproduction has later successful follow-ups; do not repeat older claims that it is wholly broken.
-Week3 Oct19–25: PANORAMA label mapping/provenance, overlap/duplicate exclusions,reconciliation counts,
 mixed-source smoke. Other laptop owns execution; Quinton reports training with PANORAMA now.
-Week4 Oct26–Nov1: reproducible training inputs and unified DAG,stage reuse/invalidation/failure recovery.
 AI-expert workflow here is one portion; training checkpoint resume alone is insufficient.
-Week5 Nov2–8: autonomous baseline/error analysis and versioned queryable literature prototype;
 select controlled experiment and confirm stakeholder session/fallback. Preserve protected-test gates.
-Week6 Nov9–15: controlled model comparison,detection/false-alarm results,retrieval metrics,cited/refusal tests.
-Week7 Nov16–22: inspect→evidence→accept/correction-required/reject,persistent history,stakeholder findings.
-Week8 Nov23–29: full integration/evaluation,release candidate and documentation drafts.
-Week9 Nov30–Dec6: stabilization/buffer; Week10 Dec7–13: delivery/demo.

Six project areas: data; training/evaluation; inference/native alignment/measurements; reviewer UI;
AI expert; DAG orchestration. Reviewer decisions can inform experiments but are not automatically
training labels. Held-out cases remain protected. No new model/training performance claims here.

## Trello and communication

User explicitly requires Trello logging for grading; meaningful updates belong on existing cards.
[W02-08] Build the first pgvector retrieval slice: https://trello.com/c/nqTumUtb
ARI ari:cloud:trello::card/workspace/659744245e561cf84747c752/6acd07d49faff2bb9990713b.
Comments record each delivery; latest retrieval review comment6ad02700e6a040992860ff6c.
Card remains open; do not mark whole feature accepted just from smoke checks.
W02-06selector: https://trello.com/c/LxvwMa3s ; W02-07passages: https://trello.com/c/fGxysGgy.
Board PROWL — Quinton Evans — Capstone. Completed work goes in Week2Complete, then Week3Complete
next week; avoid an additional generic Done column. Inspect current lists before moving cards.
No unrelated remote messages, public push, model runs or automation are authorized by this handoff.

First response should briefly acknowledge this state, flag DB/origin startup checks, and propose
finishing the focused Git checkpoint followed by the bounded evaluation. Do not redo the corpus
pipeline or present all historical steps as fresh required work.
