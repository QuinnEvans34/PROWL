# Reviewed disease sources now resolve from typed questions

**Find sources** is active at `http://127.0.0.1:5180/research`. It searches the three reviewed disease
records and returns their original finding passages plus all linked qualifications. The previous
head-size and inflammation-versus-tumor questions now find the required evidence without a supplied
structured intent or seeded passage. **Ask question** still uses the earlier dense/v6.1 model path;
this checkpoint does not claim better generated answers or full AI-expert acceptance.

Implementation checkpoint `03a976c` added the bounded topic grammar, lexical record index, exact source
expansion, dense fallback, separate source-only HTTP dispatch and UI action. No exact question lookup,
evaluation labels, paper IDs or passage ordinals enter the routing/ranking policy. Finding anchors come
from the catalog record retrieved by the new index. The corpus remains 14 papers / 1,179 passages.

## Preserved failure and correction

Attempt 1 stopped on its first HTTP request with503. A local reproduction against FrozenLiterature
identified a transport digest mismatch: the fact-record digest omits the canonical trailing newline.
The evidence boundary correctly rejected it before returning evidence. Synthetic boundary stubs had
missed this integration error. Correction `0cdeba6` imports the transport digest and adds a regression
through the actual frozen evidence boundary. No guard or expected outcome was weakened.

The failed receipt and producing snapshots remain in `outputs/prowl/record-search-v1-20261018/`.
One explicitly corrected attempt used the same frozen 24 questions in a fresh directory. No answer-model
calls occurred in either attempt. Initial UI test collection also failed under system Node20; the already
installed Node24.19.0 passed without changing dependencies.

## Corrected actual-corpus screen

| Check | Result |
|---|---|
| Positive questions and paraphrases | 12/12 select exactly the intended records |
| Boundary questions | 12/12 select no reviewed disease record |
| Existing scope refusals | 4; provider not invoked |
| General-search fallbacks | 8; clearly labeled, unassessed dense results |
| Canonical source identity and complete context | Pass for every response |
| Answer/model-generation calls | 0 |
| Total bounded screen | 7.528 seconds |
| Slowest source request | 0.419 seconds |
| Focused/affected checks | 57 Python and33 UI pass; Vite build passes |

These are 24 exposed engineering examples, not a protected or independent evaluation. They include
old wording and new paraphrases. The topic grammar is finite and rule based; these results do not
establish arbitrary-language comprehension, exhaustive unsupported-disease detection or clinical safety.
The browser uses the same closed request shape: question and request ID, with no client-supplied route.

The head question returns Schima2020 ordinals7,9,4,37: focal enlargement, overlapping head location,
appearance overlap and the single-feature/combined-feature limit. The broad comparison returns
22,24,37,39,4,44,43: inflammatory duct findings, MRCP, combined features, PDAC context, overlap and
focal-AIP portal-venous CT plus duct/atrophy context. Both now resolve the gaps observed in the preceding
live dense canary. AIP-only wording returns44/43; chronic/MFCP wording returns22/24/37/39/4.

One engineering agent inspected all24 scope decisions and re-read those nine canonical source passages.
The broad question returns named MFCP/PDAC and focal-AIP/PDAC examples; it does not equate every tumor
with PDAC. All repeated bundles match canonical evidence. Independent review remains pending. Returning
full original passages exposes additional author context, including rates and management statements;
Find sources does not turn those statements into generated advice or newly accepted fact records.

## Live integration and limits

After the gate passed, the verified idle8016 baseline process71656 was replaced with the same server
plus `--record-search`. New PID25716 / owned execsession35480 is live. Source health reports
`source-linked-record-search-v1`; answer retrieval remains `dense-exact-cosine-v1`, answer policyv6.1.
Both owned8017 candidates were stopped/reaped (expected SIGTERM exit143); port8017 is no longer used.
The original process is absent. No database/config migration or Ollama lifecycle operation occurred.
Rollback restarts the server without `--record-search`; original dense config remains intact.

Two live browser queries verified the original head and comparison questions. The first displayed four
source passages, the second seven. Clicking **View source6** opened the correct PMID32703312 source
and original body-20 excerpt, with the portal-venous CT phase and duct/atrophy qualifiers visible.
A display-only follow-up replaced the internal `focal_AIP` label with “focal AIP”; hot refresh verified
it without another query. The live screenshot and promotion receipt are retained locally.

The UI validates canonical record membership and complete linked passage sets before showing the source
result. Its expanded source contract cannot be used as an AI-answer envelope. HTTP dispatch tests prove
`/query` does not invoke the answer service and `/answer` still uses the original service. Source search
always retains baseline input/scope/database checks; no match preserves original dense fallback.

General volume/reference queries still use dense search; volume-record question routing is pending.
Unsupported/negated wording may still return related general passages, explicitly unassessed. The rule
grammar and three curated records are a bounded improvement, not a universal disease expert. Next qualify
a readable fact-answer adapter from selected records, keeping source qualifications and support checks;
then broaden intent validation and complete the independent evaluation. Measurement integration remains
required after core acceptance. AI-04 remains In Progress.

## Evidence and Git/workspace handling

Tracked aggregate: `configs/evidence/record-search-results-v1.json`. Actual requests/responses, receipt,
source copies, producing pins, screenshot, readable question table and promotion evidence:
`outputs/prowl/record-search-v1-attempt2-20261018/`. Source-query counts: one failed first attempt,
24 corrected screen requests and two live browser requests; no answer requests or generation calls.

The shared checkout moved from main to `codex/prowl-ui-redesign` during this task. Retrieval commits
contain only this task's paths. Untracked `PROWL_LOGO.png` and `docs/capstone/interface/ui-redesign/`
were preserved. Do not reset, switch or sweep those files. Publish the retrieval checkpoint separately
without changing the active shared branch. Earlier corpus/labels/failed outputs stay intact; no training,
full selector, protected data, downloads, ingestion, patient arrays or human-hours credit.
