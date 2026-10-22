# Frozen answer evaluation — October 22

The frozen assistant did not generalize to the reviewed question set: **0/20 complete answers**.
Seventeen answerable questions received no composed answer. Three received the same supported but
wrong-task disease comparison. No model, retrieval, policy or wording changes were made during or
after the evaluation. These results are preserved before deciding a repair.

| Check | Result | Meaning |
|---|---:|---|
| First requests completed | 30/30 | All HTTP200; no service errors or retries |
| Complete answers | 0/20 | The exposed development 20/20 did not predict broader coverage |
| Answerable questions blocked before search | 7/20 | Topic, clinical-scope, measurement and negation rules misclassified requests |
| Search completed without composition | 10/20 | Dense evidence did not qualify for the curated answer route |
| Wrong-task composed answers | 3/20 | Same MFCP/AIP-versus-PDAC explanation used for different requests |
| Canonical passage instances verified | 81/81 | Returned text/metadata match the frozen corpus |
| Exact citation links | 24/24 | All resolve to returned canonical passages |
| Source-supported displayed claim blocks | 12/12 | Manual inspection; four repeated blocks in each of three answers |
| Fully covered required concepts | 0/74 | One concept was partly addressed; no answer was complete |
| Boundary requests receiving an unwanted answer | 0/10 | Withholding is distinct from correct explanation |
| Complete expected boundary/gap explanations | 0/10 | Generic wrong or incomplete reasons; two refusal messages acknowledge missing case context |
| Saved responses accepted by current UI validator | 30/30 | Offline validation; no additional candidate requests |

The three generated answers are readable technical prose but fail question focus. No-answer cases
are not awarded readability, factual-support or citation credit. Manual scoring is by the development
assistant and remains subject to Quinton's review; it is not an independent clinical assessment.

All-request median was 0.176s; generated-answer median 7.169s, maximum 8.817s; total batch 27.802s.
The short all-request median mainly reflects blocked/search-only requests. It is not a useful-answer
latency claim. No timeouts, unavailable-model outputs, invented citations or patient-specific
clinical recommendations were observed in this batch.

## What the failures show

The frozen route is a limited reviewed-record selector. In `record_search.py`, a cancer/comparison
match can choose the two inflammatory comparison records without requiring the other named entity
or the actual requested task to match. That explains the wrong-task answers. It does not show that
the model invented facts: the facts were grounded in evidence for the wrong comparison.

`development_search.py` and `question_interpretation.py` apply broad keyword gates before retrieval.
They miss pancreatic abbreviations/procedure vocabulary, interpret general research as current-scan
measurement, and reject ordinary negation or treatment-related literature wording. This is evidence
of interpretation failures, not proof that the requested information is absent from the corpus.

Ten searched questions then fall outside the small answer-record catalog. In three of these, returned
passages contain labeled spans linked to every required concept, yet composition never runs. That
span linkage is a delivery diagnostic, not proof that all qualifications are present. Adding more
papers alone cannot resolve this answer-path restriction.

## Recommendation

Consolidate question interpretation and the evidence-to-answer path. First prevent an unrelated
reviewed record from answering a named comparison or different task. Then distinguish literature
questions from individual clinical requests and allow a bounded evidence-based composition path
for relevant retrieved passages outside the curated catalog. Keep source verification, explicit
missing-evidence responses and patient-specific limits. Do not add one prepared answer per failed
question or launch another prompt sweep without isolating a demonstrated failure.

The current assistant remains a bounded development preview, not a qualified general literature
expert. This checkpoint does not promote a replacement or change the live runtime. Repair work
must preserve this result and treat used questions as regression material; a subsequent held-out
assessment needs fresh questions. Formal 50-passage source Recall@k/MRR has not been evaluated here.

## Provenance and retained evidence

- Candidate: `74782f71532cf571b6925617bd71db33bba1317b`; 174 runtime files matched before and
  throughout capture. Frozen Qwen3:8b digest and 14-source/1,179-passage corpus verified.
- Separate Claude chat authored/prepared the questions; Quinton reviewed questions/evidence and
  consistency. October22 amendment authorized this development assistant to administer and score.
- The two source drafts have identical review bodies. The larger copy adds introductory narration
  and differs in final newline. Original documents remain unchanged.
- Thirty question strings and all required-concept descriptions match the reviewed draft.
  Existing schema/quote/balance/exposure checks passed: 20 answerable / 5 refusal / 5 gap, 103 exact quotes,
  five families / four difficulties. The author's narrative 121-quote count is not the verified count.
- Nine author overlap flags remain visible. Four concern answerable items; excluding them still
  gives 0/16 complete. Human overlap acceptance is retained, not treated as mathematical proof of
  semantic independence. This is a held-out frozen-candidate assessment, not a fully independent audit.
- The encrypted workspace retains original inputs, validated copy, prerequest plan/rubric, capture
  script, each first request/raw response/timing, original response hash manifest, manual per-case
  judgments, offline UI checks and a readable 30-question packet. No question payload is in this report.
- Aggregate receipt: `configs/evidence/evaluation/frozen-answer-results-20261022.json`.
  The existing draft-only backup and verified complete-input image are both preserved. A separate
  closed-image results backup is recorded in the aggregate receipt after copying.
