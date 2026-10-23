# Evidence-led answer repair — October 22

Quinton authorized repair until the test cases work. The failed frozen evaluation remains **0/20**;
its 30 cases are now exposed regression material. The original requests, responses, scoring and
closed-image backup remain unchanged. Passing these cases cannot establish held-out generalization.
The runtime never reads the evaluation suite, expected answers, concepts or evidence labels.

The candidate `--evidence-answers` removes the curated-record prerequisite. It combines the existing
dense results with lexical source-section navigation, lets the pinned local Qwen3:8b select relevant
sections, binds their complete canonical passages, and composes an answer. It distinguishes ordinary
negative/general clinical research wording from individual diagnosis, treatment and private-data
requests. Specific refusals explain the boundary; evidence gaps remain distinct from service errors.
No source corpus, embedding model, expected label or training run changes.

Support, completeness and readability are separate review criteria. One revision receives every
reported issue. Its review receives the original question/evidence and revised draft only, not the
previous critique. Each paragraph's citations collectively support its clauses; each citation need
not independently support the entire paragraph. Canonical identity checks are mechanical integrity
checks, not proof of factual correctness. Same-model review still requires manual citation inspection.

Initial diagnostics are retained in the encrypted regression workspace. Attempt 1 stopped on a
missing request ID in the trusted adapter ticket; invented-source tests reproduced and fixed it.
Attempt 2 retrieved relevant sections, but the reviewer listed positive support as errors, expanded
questions into unrelated tasks and reused stale feedback. Two later requests had transient database
connection errors; database readiness subsequently passed. No failed draft was promoted to the UI.
The narrower task/review contract and compressed source menu are undergoing the next bounded check.

The UI accepts a separate evidence-answer contract and reuses its existing answer/source tabs.
Invented-source tests cover altered records, unknown citations, client-injected labels, complete
feedback repair, failure withholding and source-only operation. Frontend tests verify response
identity, corpus/model/citation binding, readable display and source navigation. Backend deadline
is 120 seconds; browser cancellation is 150 seconds to allow transport overhead. This is a ceiling,
not an acceptable typical-latency target. Actual useful-answer latency will be reported separately.

Candidate promotion requires manual support/completeness/citation/boundary checks, comparison with
existing public development cases, and UI validation. The frozen record-based service stays live
on port 8016 while the candidate is tested on 8019. Results are pending; no 20/20 claim is made.

## Subsequent repair probes (not promotion)

The encrypted workspace retains each attempted configuration and its responses. The section-menu
selector, both fast models, and a 30B reasoning variant did not qualify. Failures included unrelated
section selection, false evidence gaps, unsupported morphology, missing qualifications, contradictory
review feedback, token exhaustion and database interruptions. The separate database repair is recorded
in RELIABILITY-CLOSEOUT-2026-10-20.md (commit68161f0); it does not establish answer quality.

A lexical+dense retrieval diagnostic initially overlapped61/74 required concept spans in12/20 complete
sets; the existing cross-encoder overlapped54/74 in10/20. These are permissive **span-delivery checks**,
not Recall@k, complete conceptual support or answer accuracy. Adding adjacent canonical context changed
the six-section result to60/74 in11/20; bounded budgets of8/10/12 sections yielded62/68/69 spans and
12/15/16 complete sets respectively. No expected label or corpus changed. Query reformulation was also
probed; it did not resolve several missing-evidence cases and is not integrated.

The candidate now selects exact source sentences, removes duplicate sentences, requests one required
rewritten unit per selected fact, and binds citations in code. It checks numeric preservation separately
from the model's support/completeness/readability review. Reference and figure/table numbers are excluded
from that mechanical check. This catches some dropped qualifications but is not semantic proof: selecting
irrelevant facts still produces an irrelevant answer. Additional context is restricted to selected source
section parts. The original whole-library selection experiment remains available only as a nondefault
constructor option; default selection is lexical+dense.

A demonstrated gap-review defect is repaired: when no facts are selected, the reviewer now receives the
retrieved original passages, rather than an empty source list. It must distinguish a correctly explained
missing fact from an incomplete answer to an available fact. Drafts/selection traces are excluded from
ordinary responses; explicit `--evidence-trace` is for the private local regression harness only. The
candidate on8019 remains separate from the live8016 service. No broader answer-accuracy claim follows
from schema, UI or source-integrity tests.

## Model compatibility correction and next controlled comparison

Local `/api/show` on Ollama0.40.2 identifies the installed `qwen3:30b` digestad815644… as
`general.finetune=Thinking`, version2507. Its template unconditionally opens a thinking block.
The [publisher tag inventory](https://ollama.com/library/qwen3/tags) maps that digest to
`30b-a3b-thinking-2507-q4_K_M`; the instruction variant has digest19e422b0…. Thus the earlier
30B non-thinking probes are incompatible-mode failures, **not** a fair comparison of instruction
models. An explicit non-thinking prefix also failed and is retained; no template override was
installed. The candidate now rejects that unsupported mode. Genuine reasoning mode exceeded token
budgets or took81–94seconds in retained probes and did not qualify.

The previously admitted Qwen2.5-14B instruction model was reused from its existing external store;
all six stored blobs were hash-verified again. It generated focused prose, but subsequent evidence
selection/review still failed. This exposed another repair defect: fixing prose could not remove
wrong facts because the required unit schema kept them. Review feedback now returns to evidence
selection before the one rewrite attempt, and completeness review receives the complete retrieved
passages. The extra context-selection call was removed after it repeatedly added unrelated facts.

Under Quinton's current autonomous repair request, one correctly named instruction variant is being
prepared: `qwen3:30b-a3b-instruct-2507-q4_K_M`, registry manifest SHA256
`19e422b0231392335cfc49cfd172de7034bb1aeabb08aa307cce745c60b272fe`,18,556,699,186 declared bytes.
Separate external scratch store `answer-instruct-20261022/ollama`,24GiB cap,20minute download cap,
unchanged104GiB internal/408GiB external free-space floors; isolated loopback11436, cloud disabled,
one loaded model/request. Existing stores/models are preserved. This is inference-only qualification,
not training or an open model sweep. Hash and capability verification precede use; no promotion yet.

First pull stopped after0.031seconds at the storage guard, before reported model-byte transfer.
The generated ignored UI build (197files,215,150,663bytes) was copied to the new external scratch area,
verified file-by-file by SHA256, then removed internally; Vite5180 serves source, not that directory.
Receipt and member hashes are retained. A separately recorded second pull follows the resolved
admission, without changing the floor or overwriting the failure. Experimental servers/models were
stopped/unloaded before the download. Receipts: `outputs/prowl/answer-instruct-20261022/`.

Public retrieval-suite check:1740passed,5skipped,2previously recorded failures (repository-wide
absolute-path scan and stale12-schema count versus23 present). Focused feedback-reselection checks
pass. No private preparation/evaluation rerun or label change follows from these engineering checks.

The second pull stopped at190.369seconds when internal free space again crossed the unchanged
reserve; approximately4.58GB transferred at its last progress sample. Its partial files and separate
failure receipt remain, and the isolated download server was stopped. No new model has been loaded.
Quinton has been asked to choose between freeing space himself and moving the existing unused
thinking-model weights to the external drive with verified content and preserved Ollama name. Read-only
inspection found one18,556,685,856byte internal blob referenced only by `qwen3/30b`; nothing in that
shared store has been moved or deleted. Other apps were not stopped. The live service was not promoted.

Latest focused checks:59backend and57UI tests pass. An offline boundary-only check of the five
clinical/privacy/fabrication regression requests produced the intended explanations; this is not a
30-case end-to-end pass. Original reviewed-draft and transcription hashes remain unchanged. The new
regression artifacts remain in the working encrypted image; a fresh independent backup is pending
closeout, and existing frozen-input/result backups remain preserved.

### Direct composition comparison

An opt-in `--evidence-composition direct` candidate now composes from the complete retrieved
passages, then performs the same separate support/completeness/readability review. One bounded
revision receives all feedback and original sources. Citation IDs are restricted to retrieved
canonical passages; unknown numeric values in a paragraph’s cited sources force rejection. This
removes forced sentence-by-sentence rewriting from the comparison without relaxing acceptance
criteria. The existing units method remains the default and the live service is unchanged.
65 focused backend tests pass, including invented citations/numbers, repeated incompleteness and
repair feedback. These are engineering checks, not a semantic accuracy result.

Quinton approved relocating the unused thinking-model weights. The exact18,556,685,856byte
blob was copied to `PROWL/artifacts/retained-models/qwen3-thinking-2507` on the registered external
drive, checked during copying and independently reread against SHA25658574f2e…c8eabf, then linked
atomically at its original Ollama location. Only `qwen3/30b` references that blob; Ollama tags/show
remained identical and8B stayed internal. Internal free space increased from111,856,410,624 to
130,410,762,240bytes (about18.55GB recovered). The thinking model now requires the external drive.
Receipt: `outputs/prowl/answer-instruct-20261022/thinking-relocation.json`. No storage floor was
lowered. Download attempt03 resumes retained instruction-model partials within the remaining1009
seconds of the original20minute active budget. Earlier failed receipts remain unchanged.

A bounded retrieval-only comparison used the same20exposed supported questions: reciprocal-rank
fusion of20dense hits and lexical section scores delivered58/74labeled concept spans, with all spans
for10/20questions, versus69/74and16/20for the existing12-section hybrid. These overlap diagnostics
are not answer accuracy or proof of full semantic support. The weaker fusion was not integrated.
The live8016health check again reports backend checked after storage recovery.

The direct candidate now also supports an explained semantic refusal when the initial narrow
wording checks do not match. It cannot attach assertions to that refusal, and review distinguishes
prohibited requests from ordinary literature questions or evidence gaps.67focused backend tests pass.
Download03 transferred the full blobs but its client timed out at608.448seconds during Ollama’s
server-side verification. The failure receipt is retained; no inference follows until manifest,
all blob hashes and model capabilities are independently verified.

Ollama completed installation immediately after the download client’s timeout; the pinned tag
appeared with exact registry digest19e422b0…. An independent full reread verified all six blobs,
including weights, config, template, license, parameters and embedded registry manifest. The first
verification script then rejected an overly broad assumption that the template contained no think
tags anywhere. Inspection confirmed those tags parse historical assistant messages; the actual
generation prefix does not open a thinking block, and GGUF metadata explicitly says Instruct2507.
That failed assumption and the corrected capability inspection are retained separately. No template
override or blob modification was made. Controlled instruction-model inference can now proceed.

The new instruction model’s chat endpoint still produced reasoning content with `think:false`,
incomplete drafts and false review complaints. Direct raw ChatML generation produced structured
answers from its first token and preserved an ANC exception previously lost, but also included
unsupported context. The opt-in candidate now uses that explicit format only for the pinned
instruction model, with all untrusted `<` characters JSON-escaped to prevent role-token injection.
68focused backend tests pass. This transport change is not semantic qualification; the first
end-to-end raw answer still failed support/completeness review, with both real answer errors and
contradictory reviewer complaints retained. No live promotion.

The instruction-model navigation-menu probe was weaker on the four remaining retrieval-gap cases:
only5/15concept-span overlaps, versus10/15under the current hybrid. It was not integrated.
Official references used to inspect the transport: https://docs.ollama.com/api/generate and
https://raw.githubusercontent.com/ollama/ollama/v0.40.2/server/routes.go (raw format applies from
the first token); https://github.com/QwenLM/Qwen3/blob/main/docs/source/getting_started/quickstart.md
(Instruct2507 uses non-thinking mode). The exact cause of chat-mode reasoning output is unproven.

### Reviewed context relationships

Further broad rewrites were rejected: question-facet expansion delivered57/74span overlaps across
20supported cases (10all-covered), and splitting every representation paragraph into an independent
retrieval group delivered58/74(11all-covered). Neither was integrated. The12-part hybrid remains.

The repeated failure is that a result can be retrieved without the same paper’s methodological
qualification. `source-context-links-v1.json` adds four engineering-reviewed relationships within
two existing papers: cyst-model results→selection/validation limitations; clinical risk models→
screening context; performance comparisons→overfitting/external testing; and technical approaches→
segmentation, data requirements and fusion context. These are canonical passage IDs only, with no
questions, expected answers, labels or generated claims. Current exposed failures motivated this
curation; it is development work, not a new independent evaluation. No corpus or label changed.

Links activate only from primary retrieved passages, never recursively. They are admitted with
their anchors inside the existing50passage/38,000character/three-paper bounds; all citations still
bind to immutable canonical records. Cross-paper and unknown references are rejected. Context links
are included in the configuration digest. Neighbor expansion now stays within the selected section
family. A closer source inspection also showed that same-title merged groups can themselves contain
multiple conditions, so adjacency alone was not the cause of the earlier wrong-condition borrowing.

The linked-context diagnostic delivered overlapping labeled evidence for74/74concepts and20/20
supported cases, versus69/74and16/20before. This permissive span-delivery result does not prove full
concept coverage or correct answers.72focused backend checks pass. The instruction/units canary
returned one supported but incomplete answer and rejected two; full answer qualification remains
open. The next retained regression uses the complete source path, with independent dimension review.
