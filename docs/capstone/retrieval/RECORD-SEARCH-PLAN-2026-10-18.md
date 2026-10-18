# Retrieve reviewed disease records from free text

Quinton approved improving retrieval and question-to-record selection and keeping Trello/Git current.
The prior disease canary found no eligible record from either live dense query. This change adds an
opt-in **source-only** search path; it does not qualify a replacement answer generator.

## Implementation

Index the existing reviewed disease records using their source relations and canonical finding-anchor
text. Use lexical term normalization and weighted overlap to rank matching records. No question strings,
expected answers, evaluation labels, paper IDs or passage ordinals appear in the routing/ranking policy.
Canonical anchor IDs come from retrieved catalog records, not a manually seeded evaluation harness.

An explicit, bounded English topic grammar extracts focal-head-mass or imaging-comparison intent and
limits the disease pair. Distinguish chronic/MFCP and autoimmune/AIP. General inflammatory-versus-cancer
questions can return both as named examples, not as an exhaustive list or a claim about all tumors.
PDAC/tumor synonym normalization is a retrieval aid; the source scope stays PDAC. Unrepresented disease
pairs, numeric/measurement/reference requests, individual-case language, negations and ambiguous topics
select no reviewed record. This is a rule-based development router, not broad semantic qualification.
Volume questions retain existing general search; volume-record routing is not delivered by this step.

Every selected record must pass the existing reviewed-source admission. Expand all its exact canonical
source passages, including qualifications. Deduplicate and cap at20passages. Original text/citation/
rights identities bind through FrozenLiterature. A response names matched comparison scopes and includes
no assembled answer. No match returns unchanged dense top5 as explicitly labeled general-search fallback.

Always run baseline input/scope/privacy and current database identity/resource checks. Keep its retrieval
and local AI answer service unchanged. The server's opt-in `--record-search` affects `/query` only;
`/answer` still uses dense/v6.1. Health exposes both identities. Add a separate **Find sources** UI action,
with expanded-evidence validation and citation access, while preserving **Ask question**. No automatic
passage expansion into an unqualified generation contract.

## Checks and execution bounds

Test independently of the actual corpus with invented records: paraphrases, ambiguous/unrepresented
requests, exact qualification expansion, altered evidence and scope denial. HTTP dispatch tests must
prove source requests do not invoke the answer service. UI tests must reject missing context/unknown
records and show source access without generating an answer. Run the affected existing API/UI checks.

Freeze a small exposed development screen of12positive and12boundary questions before the actual
run. Include former head/comparison wording, fresh paraphrases, narrow chronic/AIP requests, average
volume, unsupported tumor types, numeric/case requests and negation. Expected record IDs belong only
to the screen. This is neither a held-out test set nor proof of arbitrary phrasing. Do not alter frozen
evaluation labels or read protected inputs.

After implementation checkpoint, start one temporary source candidate on loopback8017 with the existing
embedding model and read-only database. One screen,24source-only requests, no retries,120second screen
limit,20MiB artifact limit. Preserve requests/responses/pins/latencies/errors locally; retain aggregate
IDs/verdicts in Git. Success: every positive question selects exactly its scoped records with all original
passages; every boundary question selects no record; no generation; no changed corpus identity;
maximum request under10seconds. Manually review question/scope and returned source relationships.

Only after these pass, replace the identified idle local8016search process with the opt-in command,
preserving config/store and rollback command without the flag. Recheck two original questions through
the live UI/API, inspect citation controls, and stop the owned8017candidate. No Ollama/training/full
selector, downloads, ingestion, patient arrays or inferred human hours. Record results/spec/handoff,
Trello and coherent commits. This authorizes the source-search change requested by the user, not a new
model answer policy or formal feature acceptance.

Preparation note: the first UI test invocation used system Node20 and failed before collecting tests
(`webidl.util.markAsUncloneable`). Use the already installed compatible runtime; no package replacement.

## Preserved first-attempt failure and correction

Implementation03a976c was committed before attempt1. Its first HTTP request returned503: a local,
model-free reproduction against the actual FrozenLiterature boundary found `Invalid trusted ticket
binding`. The new wrapper imported the fact-catalog digest (no trailing newline) rather than the
transport canonical digest (trailing newline). Synthetic boundary stubs had missed this integration
error. No evidence response or answer-model call occurred; one HTTP request is retained in
`outputs/prowl/record-search-v1-20261018/receipt.json`, including original producing snapshots.

Use the existing transport digest without weakening verification and add an actual FrozenLiterature
regression. Then explicitly run one corrected attempt2 in a fresh directory under the same24questions,
120second/20MiB bounds and promotion gates. This is a repair within the user-authorized implementation,
not an automatic retry or change to expected outcomes. Stop/reap the old owned8017candidate before
loading the correction. The original failure remains visible in final results and Trello.
