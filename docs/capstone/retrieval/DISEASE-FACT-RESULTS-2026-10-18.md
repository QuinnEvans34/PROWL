# Disease facts retain qualifications; current live retrieval misses their anchors

Three source-linked comparison records now preserve the qualifications lost in earlier generated
answers. The bounded assembly check passes, but **this is not a working live disease-answer path**:
current dense retrieval selected none of the three records. No UI replacement was promoted.

Implementation `18b1875` preceded one completed canary: two source-only searches, zero model calls,
0.838 seconds overall. Source search times were 0.346 / 0.367 seconds; this is not generation latency or a
cold-start benchmark. All 1,179 canonical passages and selected hit identities were checked. Forty-six
focused invented-fixture tests pass. The baseline API remained dense/v6.1 before/after; UI returned 200.
No services were restarted, stopped or reconfigured.

## Separate rendering from retrieval

| Evidence mode | Focal head mass | MFCP versus PDAC findings | Focal AIP versus PDAC |
|---|---|---|---|
| Two fresh live dense searches | No eligible record | No eligible record | No eligible record |
| Retained R8 plus section-context replay | Selected; 2 context passages added | Selected; 3 context passages added | No eligible record |
| Deliberately seeded canonical finding anchors | Complete assembly | Complete assembly | Complete assembly |

These are three structured selection requests over two exposed questions, not three independent
questions. Replay uses pinned prior outputs, not a new reranker run. Seeds use canonical ordinals 7, 22, 44
only to isolate assembly. Their success is not retrieval success. A missing anchor produces no eligible
record, rather than an answer using unrelated results. Seeded expansion adds 3 / 4 / 1 passages respectively.
Five assembled outputs across replay/seed modes reduce to three distinct envelopes; repeated record
outputs are identical. No free-text router supplied these intents; the harness declares them explicitly.

The live head-question top 5 contains ordinals 27(PMID35877639),18(36834922),11(34698963),4(25950180),
37(33925859). The findings-question top 5 contains 65(37173876),161/12/16(35406426),16(33925859).
None is a required Schima 2020 finding anchor. This is a narrow record-coverage failure, not a claim
that all retrieved passages are irrelevant or a broad retrieval benchmark. Retained R8 evidence reaches
head and duct findings in Schima 2020, but still lacks its focal-AIP enhancement passage 44.

## Qualification and source audit

The records use the existing Schima et al. 2020 narrative review, PMID 32703312. Each curated relation
binds disease scope, feature, relationship strength, method/phase and exact canonical spans. Separate
engineering-review hashes preserve the interpretation; they do not establish semantic truth.

| Required qualification | Retained assembly behavior |
|---|---|
| Focal mass versus numerical head size | Occasional inflammatory focal enlargement is described; no head-size cutoff inferred |
| Inflammation/cancer overlap | MFCP and focal AIP can resemble PDAC; PDAC is not broadened to all tumors |
| Combined findings | MFCP/PDAC single-feature limitation and combination requirement stay present |
| MRCP identity | Duct-penetrating sign explicitly labeled as best seen with MRCP |
| Calcification morphology | Diffuse spotted/coarse tissue calcification or duct calcification stays paired with duct-penetrating sign |
| PDAC feature context | Complete duct obstruction by a mass and arterial encasement by a soft-tissue mass remain comparative findings |
| Focal AIP phase and cluster | Portal-venous CT enhancement, smooth duct/no abrupt cutoff, mild upstream main-duct dilation≤5 mm and absent proximal atrophy retained |
| Individual scan limits | Separate application policy prevents interpreting these examples as current-patient findings or diagnoses |

One engineering agent manually inspected every rendered statement and its cited original spans:
15 source-statement instances across three distinct answers (12 unique sentence texts), all supported
within their stated scope; three separately labeled application-limit instances. Review notes and exact
text hashes are in `configs/evidence/source-facts-disease-v1-results.json`. Independent/human source
acceptance remains pending. Uncurated incidence/accuracy numbers, management recommendations and
patient-level probabilities are not added. The≤5 mm observation concerns upstream main-duct dilation,
not pancreatic-head or lesion diameter.

The head assembly covers the unchanged exposed quality-01 concepts. MFCP and focal-AIP assemblies
together cover quality-02's concepts, but current live search supplies neither and replay supplies only
MFCP. This therefore does not pass the end-to-end answer evaluation or alter its labels. Source findings
are curated reusable relations, with no question strings/expected-answer lookup in catalog or renderer.
This is code-controlled fact assembly, not evidence that an LLM has learned to retain qualifications.

Tests exercise missing overlap/combined-feature/single-feature roles, incorrect MRCP/CT phase, source
or review drift, unsupported scope/use, forged hits and post-render qualifier/citation changes. Exact
regeneration rejects a later model/editor rewrite. First pytest collection failed on reserved parameter
name `request`; renamed before execution. No tests/HTTP/model work occurred in that failed collection.
During preparation, calcification wording was tightened to retain morphology before any canary or commit.
No actual canary failed or was retried; original corpus, volume prototype and prior failures stay intact.

## Artifacts and next step

Readable answers with exact source evidence:
`outputs/prowl/source-facts-disease-v1-20261018/readable-review.md`.
The same local directory retains requests/responses, separate mode selections, answers, receipt and
producing snapshots/pins (388,721bytes at canary completion). Tracked catalog, review and results sit
under `configs/evidence/source-facts-disease-v1*.json`. Code is the opt-in
`src/retrieval/disease_fact_records.py`; plan is [DISEASE-FACT-PLAN-2026-10-18.md](DISEASE-FACT-PLAN-2026-10-18.md).

Next qualify retrieval-to-record selection and free-text intent binding, especially the focal-AIP
anchor gap, before adapting these envelopes to the UI. The existing service's three-claim contract
was not relaxed: these prototypes have6 / 8 / 4 statements including policy, with4 / 5 / 2 source passages.
Independent source review, broader coverage, protected evaluation, readable output integration and the
required measurement-aware extension remain open. AI-04 stays In Progress. No new source ingestion,
Ollama calls/lifecycle changes, training/full selector, patient arrays or human-hours credit occurred.
