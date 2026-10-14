# Resumable selector Phase 5 — draft real-run packet

October 13, 2026. **Historical draft; superseded by [the actual R01 launch record](SELECTION-R01-LAUNCH-2026-10-13.md).** The draft JSON remains unchanged for provenance.
Tracking: [W02-06](https://trello.com/c/LxvwMa3s).
Engineering evidence: [Phase 4](RESUMABLE-SELECTION-PHASE4-2026-10-13.md).
Machine-readable draft: [captured identities and proposed settings](launch/selection-r01-draft-2026-10-13.json).
That JSON deliberately uses `selection-launch-draft-v1`, not the executable admission schema.

## Current state and dependency

Native process inspection confirms existing lookup Python PID36048 and caffeinate36049 match the
expected resume command. At this check the checkpoint advanced from39,770,000 to39,780,000 of
41,226,017 titles (approximately96.5%), with21 title matches. There is no matches.json yet. These
are historical observations; always verify fresh native activity before acting. The healthy lookup
was left running. No second reader scanning the corpus, writer or selector was launched.

Raw replay is already complete per its retained receipt:1,656 files,41,226,017 documents and10,817
deleted PMIDs (41,236,834 reconciliation records). This is distinct from seed lookup completion.
The current check reads small receipts and filesystem metadata, not a full catalog scan/rehash.
The draft marks current applied-ledger reverification false; fresh admission must check it.

The seed protocol's rule4 requires the seed list frozen before the FIRST real selection. Its rule3
requires unresolved/ambiguous/conflicting/deleted cases reported to Quinton rather than silently
repaired. Title-match count alone proves neither correct citations nor frozen seeds. Thus completing
engineering Phases1–4 does not remove this dependency.

## Review sequence when lookup finishes

1. Confirm lookup_complete_review_pending, matches.json, native process exit and retained session
   evidence. Check candidate/script/catalog identities against the lookup checkpoint.
2. Build a review table for all21 working candidates and conditional C-25/C-36: supplied and found
   PMID/DOI, exact title/year/venue checks, missing MeSH, unresolved/conflicting/deleted outcomes.
   A title scan alone does not establish DOI uniqueness or absence from PubMed; follow up explicit
   identifier conflicts without automatic citation corrections.
3. Check C-25/C-36 factual scope; reconcile15–25 accepted seeds, at least2 per family and at least3
   actual no-MeSH seeds. Report any shortfall and proposed response for Quinton's decision. Do not
   count related-background needs as direct coverage or change policy terms to fit outcomes.
4. Freeze the reviewed set with a new immutable receipt and SHA256 in planning/RUNNING-LOG.md.
   INFORMATION-NEEDS.md remains frozen v1; its current hash matches the recorded d71577c2…8ac0.
5. At P6 start, draw the three independent32-byte reserve/development/confirmation keys once under
   SEARCH-AND-SELECTION section11.6 and record them. No prior keys were found in the reviewed
   planning files; repeat that search immediately before creation. Never regenerate existing keys.
   Initialize the exposure ledger from the running-log disclosures, including PMID33840636 and
   resolved earlier DOI/PMCID exposures. Keep unresolved mappings explicit. No sampling yet.
6. Produce the real selection-admission-v1 packet with hashed seed_freeze, information_needs and
   reserve_exposure evidence. The draft packet here is not a substitute.

## Proposed inputs, output and limits

- Catalog: `/Volumes/PROWL-Data/PROWL/scratch/literature/catalog-streaming-20261010/catalog.sqlite`.
- Receipts: `/Volumes/PROWL-Data/PROWL/scratch/literature/pubmed-2026-20261009/receipts.jsonl`.
- MeSH: `/Volumes/PROWL-Data/PROWL/scratch/literature/mesh-2026-20261010/desc2026.xml`;
  expected SHA256 `449792ed59ba4d60035e44724352f7361ec0dc945b67dcd821a50ff32f81bcdb`.
  The existing verified asset is312,952,703bytes. No redundant XML hash read during this lookup;
  production loading must verify its hash before processing.
- Expected volume UUID: `22750B93-2F3F-499D-87F5-902981BFAB59`; verified mounted at this check.
- Cutoff listing year2026; journal policyv0.1, including unchanged base-policy document.
- Proposed fresh output: `/Volumes/PROWL-Data/PROWL/scratch/literature/selection-journals-v01-r01`.
  Verified absent; directory not created. Never repurpose an existing partial run.
- Internal receipts/log directory: `outputs/prowl/selection-launch-r01/`, not yet created.
- Proposed per-invocation12hours,256GiB output logical-byte cap,400GiB free-space floor,
 32MiB cache per connection, one worker, default1,000-record/10-second commit interval.

Observed external free space approximately2.26TB; internal approximately121GB (decimal). Values
are captured exactly in the JSON and must be refreshed at launch. The output cap plus free-space
floor fits this observed free space, but **256GiB has not been proven sufficient for the actual
selection ledger, indexes and exports**. Synthetic row size cannot establish full-corpus capacity.
Before launch, choose a separately reviewed bounded real sizing measurement after seed freeze,
or explicitly review a conservative larger allocation. Keep retained attempts and hidden spill
in the calculation; internal logs stay on the confirmed internal device. No optimistic ETA.

## Candidate command — inactive until prerequisites and review close

Run from `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL` only after the admission
file and fresh log parent have been prepared. They intentionally do not exist yet.

```sh
caffeinate -i .venv-prowl/bin/python scripts/retrieval/select_pubmed_corpus.py \
  --catalog /Volumes/PROWL-Data/PROWL/scratch/literature/catalog-streaming-20261010/catalog.sqlite \
  --receipts /Volumes/PROWL-Data/PROWL/scratch/literature/pubmed-2026-20261009/receipts.jsonl \
  --mesh-path /Volumes/PROWL-Data/PROWL/scratch/literature/mesh-2026-20261010/desc2026.xml \
  --mesh-sha256 449792ed59ba4d60035e44724352f7361ec0dc945b67dcd821a50ff32f81bcdb \
  --cutoff-year 2026 \
  --expected-volume-uuid 22750B93-2F3F-499D-87F5-902981BFAB59 \
  --output /Volumes/PROWL-Data/PROWL/scratch/literature/selection-journals-v01-r01 \
  --packet-path outputs/prowl/selection-launch-r01/admission.json \
  --log-path outputs/prowl/selection-launch-r01/invocation-01.jsonl \
  --hours 12 --max-gib 256 --free-gib 400 --cache-mib 32
```

This is a full-stage selector command, not a benchmark or a current launch instruction. Record
stdout/stderr separately and retain owned session/PID and actual exit code. Fresh native preflight
must confirm AC, volume identity, free space, catalog completion/contiguous ledger/receipt matches,
all code and policy pins, admission evidence, output absence and source/output locks. Do not run
while the existing citation lookup remains incomplete. No code mutation while a selector runs.

## Pause, resume and completion

For a requested pause: verify the exact owned Python command/PID, send SIGINT once, wait for exit
and connection cleanup, inspect the committed checkpoint and preserve status/logs. Only then use
normal drive eject. Do not claim safe unplug solely from a stopped JSON message.

For explicit continuation: repeat fresh native identity/resource checks; use the same command,
output and admission with `--resume`, changing only the log to a fresh invocation-02.jsonl (then03,
etc.). A12-hour stop is not an automatic restart instruction. Diagnose unexpected failure before
retrying; never change identity hashes or remove a held lock to force continuation.

Completion requires summary.json plus matching records/candidate files, verified hashes/counts,
SQLite checkpoint complete, status complete and actual process exit. A re-invoked completed resume
validates the result without overwriting it. Reconcile all41,236,834 source records, the WORKFLOW
cap and seed recall before marking corpus selection reviewed. Rights qualification/passages/vector
loading remain later stages. Preserve failed attempts and every producing receipt.

## Phase 5 status

Draft packet and operational plan delivered. Still pending: completed seed lookup and review,
freeze/coverage/MeSH decisions, reserve/exposure artifacts, real storage sizing and final fresh
launch review. No executable admission was fabricated, keys drawn, seeds frozen or job launched.
Next useful action is the completed seed-results review; until then leave the healthy lookup running.
