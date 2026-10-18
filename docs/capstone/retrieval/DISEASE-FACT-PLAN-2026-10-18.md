# Source-linked disease comparisons: bounded prototype

Quinton approved extending source-linked facts to disease comparisons, testing retained qualifications,
updating Trello and committing work. This opt-in prototype extends the volume approach without modifying
its producing files or the live dense/v6.1 policy. No patient data, models, training, protected evaluation,
new literature downloads, service lifecycle changes or inferred human-hours credit.

## Source and contract

Use the already retained Schima et al.2020 review, PMID32703312, in the unchanged14-paper/1179-passage
corpus. Curate three reusable comparison records: focal inflammatory head mass versus PDAC; MFCP versus
PDAC imaging findings; focal AIP versus PDAC imaging findings. No claim to cover every pancreatic disease.
PDAC means pancreatic ductal adenocarcinoma, not every pancreatic tumor. MFCP means mass-forming chronic
pancreatitis; AIP means autoimmune pancreatitis.

Each atomic relation has a subject, controlled relationship, object, imaging method/phase where applicable,
role and exact source spans. Reviewed spans include canonical passage/work IDs, ordinal, offsets and SHA256.
Separate review inventory binds each record and all referenced spans to the frozen corpus manifest. This
is engineering curation from a narrative review, not a new diagnostic accuracy study or independent gold.
Hashes preserve identity and reviewed interpretation; no automatic semantic-entailment claim.

Required roles preserve overlap and, for MFCP versus PDAC, the source's single-feature and combined-feature
limits. Focal AIP has its own overlap evidence; do not misapply the MFCP-specific limitation as an AIP
source claim. MRCP stays attached to the duct-penetrating sign. Portal-venous phase CT stays attached to
focal AIP homogeneous enhancement. Preserve the calcification pattern and the AIP duct/atrophy cluster;
≤5mm is upstream main-duct dilation, never head or lesion size. Omit uncurated accuracy/occurrence rates.
Application restrictions on patient diagnosis and numerical head-size thresholds are labeled separately,
without pretending they are quotations or additional author conclusions.

Deterministic assembly emits every admitted relation and qualification, with direct citations, plus the
application limit. Exact regenerated-envelope comparison rejects downstream edits, missing caveats and
citation substitution. This tests code-controlled rendering, not improved LLM behavior. No question text,
expected-answer text or evaluation labels enter records or renderer. Selected content is curated data,
not runtime extraction. Independent source review remains pending.

## Selection and checks

Selection requires explicit structured organ/comparison/topic/use plus a canonical retrieved finding or
method anchor. Overlap-only context or an incidental abstract cannot trigger the record. Expansion adds
all bound within-paper qualifications. Different disease pairs, numerical size questions and patient
interpretation do not silently reuse a comparison. Natural-language intent extraction remains unbuilt;
the diagnostic harness supplies intents openly. No production response adapter is qualified here: these
records exceed the deployed three-claim envelope, and the wider source/citation policy remains unchanged.

Use invented unit fixtures to test selection versus rendering separately, removal of mandatory roles,
method/phase corruption, unsupported use, source/review identity, false retrieval hits, changed semantic
relations and post-render omissions. Do not repeat unaffected successful volume checks.

After implementation commit, run one canary with a90second wall limit, at most two source-only HTTP
queries (existing exposed quality-01 and quality-02 wording), zero model calls and16MiB output ceiling.
Keep failures; no automatic retries. Query endpoint returns evidence only. Compare these distinct modes:

1. Fresh unchanged dense/v6.1 retrieval, with explicit head, MFCP-imaging and focal-AIP-imaging intents.
2. Previously retained R8+section-context retrieval for those questions; exact file pins, no fresh search
   or reranking. This is replay of development results, not independent retrieval evidence.
3. Three canonical finding-anchor assembly fixtures (ordinals7,22,44), explicitly seeded rather than
   retrieved. These isolate assembly when live retrieval misses; they must not count as live successes.

Verify all hit records against canonical provenance. Preserve producing code/config/test/plan snapshots
and pins, original requests/responses, mode-separated selections, added context and answers. Manually
review all distinct rendered claims against exact source spans and verify repeated outputs are identical.
Report retrieval misses even if seeded assembly is complete. Keep the live UI unchanged. Finish readable
local source-linked answers, tracked aggregate results, spec/handoff, Trello and a second Git checkpoint.

Preparation history: first pytest collection failed because `request` is a reserved parametrization name;
renamed to `requested` before execution. No tests or HTTP/model calls occurred in that collection attempt.
An initial draft of the curated calcification relation was tightened during source review to preserve
“diffuse spotted or coarse”; it was never used in a live canary or promoted.
