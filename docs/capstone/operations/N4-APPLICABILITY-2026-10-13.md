# Legacy N4 applicability review — October 13

## Disposition

The N4 actual-volume rehearsal is **not a dependency of the currently selected catalog,
seed lookup or pgvector platform path**. Keep its original qualification unverified in Backlog;
do not rerun the retired sizing workflow merely to complete a card. This review closes the
question of current applicability, not the missing primary-loss/fallback rehearsal itself.
If the old Run S/S1 binding is selected again, its qualification and live-binding requirements
must be revisited before relying on it. No production safeguard or historical receipt changes.

## Evidence reviewed

- `src/operations/literature_sizing_binding_v1.py` implements the invented N4 qualification
  through `literature_storage_v1` and `sizing_v1.runner`. Its separate diagnostic launcher is
  `scripts/diagnostics/literature_sizing_binding_qualification_v1.py`.
- `scripts/retrieval/run_s_sizing_v1.py` still explicitly refuses live execution. N4 closure
  alone would not turn it into the selected full-catalog acquisition path.
- `scripts/retrieval/process_pubmed_corpus.py` calls `src/retrieval/streaming_corpus.py`, which
  uses `pubmed_catalog` and `topic_selection`, not the N4 storage binding. The completed import
  and the pending selector have their own transaction, identity and resource behavior.
- `scripts/retrieval/verify_seed_candidates.py` uses read-only SQLite, checkpoint identities
  and shared/exclusive locks. It does not call N4. Its checkpoint remains paused.
- The pgvector platform scripts use the selected Docker Compose/preflight configuration and
  dedicated bind directories, not the N4 executor or its fallback journal.
- The downloader does reuse `sizing_v1.listings` parsing helpers. Reusing these listing parsers
  is not using the N4 writer/executor; do not characterize the entire sizing package as unused.

This is static source/dependency and retained-evidence review. It performs no rehearsal, database
startup, download, external write, full-catalog scan or new source qualification.

## Recovery coverage and limits

The retained [pgvector qualification](../retrieval/PGVECTOR-PHASE2-RESULTS-2026-10-12.md)
shows clean restart/process-crash recovery and an exact 100k-row dump/restore into a separate
container/directory. Source, dump and restored database reside on the same external volume.
They are separate database instances, **not independent physical failure domains**.

Consequently these checks do not replace N4's primary-loss/internal-fallback guarantee, nor prove
USB removal, power loss, or loss of the external volume is recoverable. The completed PubMed
import also does not prove that guarantee. No equivalent protection is claimed.

Before relying on a durable real-corpus service in Phase 5, specify which artifacts can be rebuilt,
which need independently stored backups, their capacity/retention and an actual recovery check.
The selected implementation must retain explicit failed/incomplete states on unavailable storage.
That future service qualification belongs to its own phase; it is not a reason to execute obsolete
N4 machinery or block resuming the already-checkpointed citation lookup.

## Tracking

W01-04 remains deferred/unverified for the legacy binding, with this applicability decision linked.
W02-05 retains source-unit/anatomy issues, cross-machine evidence, confirmed hours and Sunday review.
The immediate AI task is still the paused seed lookup, then citation review/freeze before selection.
No processing resumes until Quinton requests it.
