# Expected answers stay outside RAG evidence

**October 17, 2026:** Quinton asked whether prepared expected answers would make the RAG evaluation
artificial, then authorized continuation after the distinction was explained. He said the updated
questions look great. This records positive question feedback, not inferred source-label adjudication.

The expected-answer document is an evaluation reference. It is **not additional searchable corpus
data**, a source to cite, a model prompt attachment, or model-weight training data. The production
response path must use the question and retrieved literature. Afterwards, evaluation compares the
result with separately stored required concepts, evidence labels and expected behavior. Wording
need not match the review examples. Development results are not independent generalization evidence;
the separately authored protected test set remains required.

## Current implementation checked

`ResearchStore.save` passes the guided question label into retrieval, then the question and returned
passages into generation. `grounded_answer.generate_answer` constructs its user message from only
the question and passage IDs/text; the system instruction is the generic quotation-selection policy.
Neither component loads the Q&A document or development evaluation labels. The guided retrieval
catalog includes manually specified query facets for two questions; it is a curated demo, not proof
of unrestricted question performance. A separate synthetic fixture adapter has prepared content and
must continue to be described as a fixture rather than live RAG.

The current response policy selects exact quotations and verifies that they occur in cited passages.
It does not yet produce the polished plain-language reference answers. Exact substring validation
also does not prove relevance or completeness; those remain semantic evaluation responsibilities.

## Six new offline regression checks

`tests/retrieval/test_answer_key_boundary.py` passes **6/6** using invented article text, a fake search
function and a fake Ollama transport:

- Extra answer-key/concept/gold-source metadata is excluded from the actual model message.
- A simulated model output containing the answer-key canary without retrieved support is rejected.
- Three separate request fields cannot inject expected answers, gold passage IDs or concepts; each
  fails before retrieval or generation.
- The actual guided-search/store/generator composition publishes the supplied source quotation;
  a fresh empty retrieval abstains without calling the model despite an available catalog canary.

These tests exercise existing production functions without changing their behavior. They are not a
live database/model run or an audit of every future adapter. They do not detect semantic contamination
if someone deliberately inserts an answer key into article text. Corpus admission/provenance remains
a separate control: the frozen corpus and its previous evidence pins were unchanged in this checkpoint.
Future free-text and summary adapters must preserve this separation and qualify their own boundaries.

Local test receipt: `outputs/prowl/answer-key-boundary-20261017/tests.xml`.
No model, database, index, service, training or protected-store operation occurred. No human approval
event or frozen evaluation set was created. Complete the existing human review/protected-authoring
steps before retrieval selection; do not describe these engineering tests as RAG accuracy results.
