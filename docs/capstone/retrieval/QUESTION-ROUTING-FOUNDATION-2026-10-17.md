# Question routing foundation

Version 1 — October 17, 2026. Implemented and checked offline; not connected to the live demo.

Quinton approved the next request/response-contract and routing step after reviewing the shared
scan-centered questions. This delivers an opt-in planner, not a new answer generator or retrieval
configuration. The eight examples guide implementation; they are not indexed knowledge or answers.

## Delivered interface

`src/retrieval/question_routing.py` exposes `plan_request(request)` and
`verify_plan(plan, request=request)`. The two closed JSON schemas are
[expert-request-v1](../contracts/retrieval/expert-request-v1.schema.json) and
[expert-route-v1](../contracts/retrieval/expert-route-v1.schema.json).

The request contains only `schema_version`, a canonical UUID `request_id`, and a nonempty question
of at most 500 characters. Unknown fields are rejected, including client-supplied measurements,
findings, case IDs, reports, expected answers, gold labels, citations, corpus selectors and route
hints. The planner preserves original wording and records whitespace-normalized wording. Matching
also applies Unicode NFKC, case folding and apostrophe normalization; the original is never rewritten.
This is not a de-identification service. Do not persist arbitrary real-user input through this module.

The response is a **routing plan**, with request/content hashes, policy version, route, status,
reason and required capabilities. Its answer is always null, citations empty and execution
`not_started`. It cannot represent an answered state. Verification recomputes the whole decision
from the caller's trusted request; rehashing a substituted route or question cannot pass verification.
Hashes provide integrity and identity, not authentication or semantic validity.

| Task | Current result | Inputs needed before a future answer |
|---|---|---|
| Head size | Measurement unavailable | Valid geometry, qualified head definition/outline and defined measurement method. |
| Lesion size/location | Measurement unavailable | Selected outline, measurement method and independently qualified location when requested. |
| Comparison with average/enlargement | Comparison unavailable | Validated measurement and an eligible reference statistic/definition; above-average is not automatically abnormal. |
| General disease associations or differentiating findings | Literature candidate requiring scope review | Qualified retrieval and supported citations; no case conclusion. |
| Disease question referring to this pattern/scan or supplying a number | Verified findings required | Trusted finding adapter; user wording is not verified scan evidence. |
| Mixed, negated or unknown request | Clarification needed | Resolve the intended task without silently dropping clauses. |
| Recognized scope/privacy violation | Refused | No tool execution. |

Actual plans for all eight agreed wordings are in the
[development examples](../../../configs/evidence/question-routing-v1-examples.json).
The lesion size-and-location variant retains both required capabilities. These plans contain no
medical answers or measurements. Missing tools mean unavailable, not insufficient literature.

## Routing policy and boundaries

`scan-question-routing-v1` uses bounded English keyword rules rather than a question catalog.
Paraphrases are checked, but this is not a general natural-language classifier or a qualified
privacy/security boundary. Unknown, compound and negated requests can require clarification even
when a human could understand them. A literature route only proposes evidence work; it never proves
that a question is in scope or answerable. Every route is non-executable in this foundation.

The planner reuses existing refusal checks, then adds local scope examples. Its only narrowing of an
inherited refusal is the general prefix “What diseases can/could/may cause/indicate …”, without a
case referent or number; other refusal reasons still apply. The frozen `query.py` policy remains
unchanged. Before integration, the future query/response policy must explicitly reconcile this new
interpretation; never pass a reworded question through the older gate to hide a refusal.

There are no retrieval, database, measurement, generation, network or persistence calls in the
planner. It does not read development question/answer catalogs at runtime. The live guided endpoint
still rejects free-text requests, and no web endpoint has been added. No corpus or model selection,
private question access, patient/report reads, training or full selector is involved.

## Verification

Final targeted run: **155 passed**, comprising 69 new routing checks, 41 existing query checks,
three existing guided-store checks and 42 existing response-integrity checks. Checks cover the eight
shared wordings, unseen-to-the-list paraphrases, compound/negated/unknown requests, refusal precedence,
Unicode matching, injected fields, invalid text/UUIDs, rehashed tampering and unchanged live input
restrictions. These are exposed engineering tests, not independent answer-quality scores.

The first run retained one failure and 151 passes: the inherited broad “what disease” rule rejected
a general literature question. Attempt-01 source/tests and the failed report are preserved. The new
policy narrowed that case, clarified measurement-intent matching and retained location in compound
routing checks; the second run passed all 155 checks. No threshold was changed.

Evidence: `outputs/prowl/question-routing-v1-20261017/`, with both JUnit reports and the first attempt
source snapshots. The versioned checkpoint receipt pins source, schemas, examples and verification.
Existing producing receipts, corpus and accepted v5 evidence remain historical and unchanged.

## Next implementation and evaluation work

The request-to-task foundation is complete for this bounded offline scope. Next prepare the
literature adapter contract and disease-focused development labels, including the new exposed
routing cases in a versioned exposure inventory. Resolve the independent evidence-labeling workflow
before asking Quinton for the protected questions. Quinton supplies question wording and product
feedback; he is not assigned article searching or offset entry. No protected set is created here.

Freeze the applicable task coverage, labels and response policy before retrieval comparison/tuning.
Then connect a qualified literature adapter and evaluate cited responses before enabling the live
free-text path. Measurement and comparison adapters follow core acceptance under the
[required extension](MEASUREMENT-AWARE-EXPERT-PLAN.md); this step does not satisfy that gate.
See [completion spec](AI-EXPERT-COMPLETION-SPEC.md) and [AI-03](https://trello.com/c/NctoNxr8).
