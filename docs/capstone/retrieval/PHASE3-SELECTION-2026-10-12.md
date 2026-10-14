# Phase 3 — journal selection readiness and execution

Status: seed citation lookup resumed at Quinton's request on October 13 from 37,630,000 of
41,226,017 records (91.3%). Verify native activity for current state; full topic selector not launched.
Owner: Quinton + Mac development. Trello: https://trello.com/c/LxvwMa3s.

## Required sequence

1. Resolve the approved working seed list against the completed local snapshot. Preserve conflicts,
   missing identifiers and ambiguities; verify actual MeSH presence and direct-need scope.
2. Resolve any review decisions, then freeze the seeds and record their hash before the first selection
   run. Information needs v1 is already frozen. Do not change policy terms to fit seed findings.
3. Fix reserve/development/confirmation keys under section 11.6 of the approved selection policy;
   initialize the exposure ledger from the existing disclosures. Keep confirmation records protected.
4. Run journal-only selection v0.1 against the completed catalog with a concrete output/time/disk packet.
   Reconcile every disposition, source/policy hash, global WORKFLOW cap and seed recall.
5. Review aggregate results and unresolved coverage before later sampling/rights/passages work.

The previous simplified plan understated the pending seed work. The approved SEED-SET rule 4 requires
freeze before the first selection run, not merely before relevance evaluation. This is now the active
entry prerequisite; downloaded/imported data alone did not complete it.

## Initial lookup (historical; resumable attempt and latest pause recorded below)

- Tool: `scripts/retrieval/verify_seed_candidates.py`; five focused tests pass.
- Exact approved 21 working candidates plus conditional C-25/C-36, from SEED-CANDIDATES draft 8.
- Source: completed catalog-streaming-20261010/catalog.sqlite, opened read-only in a transaction;
  no abstract text is exported or displayed. Candidate titles are matched under approved normalization.
- Title lookup is a locator, not complete DOI resolution. Matches retain supplied PMID/DOI comparisons,
  title/year/venue checks, source hashes and MeSH presence. Unmatched/conflicting entries require
  follow-up; do not auto-correct citations or label this output a frozen seed set.
- Budget: at most 7,200 seconds; 32 MiB SQLite cache, streamed titles, small matched-metadata output.
  No database write, selection, sampling, embedding, training or corpus-sized output.
- Owned exec session: `31687`; native Python PID `69081` confirmed active at 26 seconds elapsed.
  IDs are historical observations: verify actual command identity before acting on them.
- Evidence: `outputs/prowl/seed-verification-20261012-01/`, candidate input and producing source copies.
  `status.json` updates every 100,000 records and at exit; `matches.json` appears only on completion.
  The lookup is not resumable; diagnose a stopped run before considering a new pass.

External UUID `22750B93-2F3F-499D-87F5-902981BFAB59` verified before launch; no competing replay,
selector or seed-lookup process was present. Final replay status remains complete for 1,656 files /
41,226,017 documents. No full catalog rehash or original XML replay is performed.

Next review: completed metadata matches, unresolved identifier/citation outcomes, MeSH-absence count,
and conditional scope decisions. Only after that review can the seed-freeze prerequisite be closed.

## User-requested stop — October 12

Quinton requested a pause. Sent SIGINT to the command-verified seed lookup PID69081;
owned session31687 exited130 (intentional KeyboardInterrupt). Final status is stopped,
with the last periodic count 4,000,000 titles. Raw download/catalog remain complete and untouched.
The reported count is progress evidence, not a resumable checkpoint; this implementation cannot
continue from that exact point. No restart is authorized until Quinton requests continuation.

## User-requested continuation — October 12

Quinton returned after a fire alarm and requested continuation. Old attempt01 is preserved.
Added atomic checkpoints every 10,000 titles, containing the last complete rowid, match lists,
record count and catalog-stat/metadata/candidate/code identity. Resume refuses identity changes;
shared catalog-writer lock and exclusive output lock prevent conflicting cooperating processes.
Six focused tests pass, including interrupted/resumed equivalence with rowid gaps and mismatched
identity refusal. An interrupted partial batch is replayed from the last published checkpoint.

The old progress-only record cannot supply a safe resume position, so attempt02 starts at zero.
It uses a four-hour invocation limit; future continuation uses the same output plus `--resume`.
No change to seed rules or selection scope. Correct volume UUID and no competing process verified.
Owned session27840 / native PID77782 confirmed live; first10,000-title checkpoint saved.
Evidence/source snapshots: `outputs/prowl/seed-verification-20261012-02/`.
Original lookup's non-resumable description above applies only to attempt01.

## Transport pause — October 12

Quinton requested a pause after class. Verified PID77782 command and sent SIGINT; session27840
finished exit1 with SQLite OperationalError: interrupted (user-requested, not spontaneous failure).
PID77782 and caffeinate77783 confirmed absent. Atomic checkpoint retains24,140,000 records,
last_rowid24179582 and5 title matches. Script/candidate hashes and catalog size/mtime still match.
Continue later with the SAME attempt02 output and `--resume`, after drive identity checks;
no restart from zero is needed. Do not resume until Quinton requests it. Drive was not unmounted
by this pause; use normal eject before physical disconnection.

## Resume after transport — October 12

Quinton requested resume. Verified external UUID, no competing process, unchanged catalog size/mtime
and candidate/script hashes. Preserved transport-pause-status.json. Started SAME attempt02 with
`--resume --seconds 14400`, owned session39397, native PID24477 confirmed active. Initial resumed
status retains24,140,000 records / last_rowid24179582 /5 matches; no restart from zero. This is a
four-hour per-invocation ceiling, not an ETA. Prior session27840 remains finished.

## October 13 status and safe unmount

User asked whether work was finished and whether the external drive could be unplugged.
Lookup session39397 exited1 at its four-hour deadline (14402.22s; SQLite interrupted).
Checkpoint/status retain36,800,000 titles and20 matches; no matches.json/final lookup completion.
Native inspection found no seed lookup/import/download process. Work is NOT complete; remaining
approximately4.43M titles can resume later from attempt02. No automatic restart for this request.
Verified expected external UUID, then normal `diskutil unmount /Volumes/PROWL-Data` succeeded:
Volume PROWL-Data on disk5s1 unmounted. Safe to unplug. Completed raw download/catalog unaffected.
The overnight import automations checked the already-completed import, not this separate seed lookup.

## October 13 continuation after four-hour stop

Quinton explicitly requested getting the remaining work running. Drive remounted with expected UUID;
checkpoint code/candidate/catalog stat identities unchanged; no competing lookup found. Preserved
four-hour-stop-status.json. Resumed same attempt02 at36,800,000 records/last_rowid37154235/20matches
with a12-hour invocation ceiling (--seconds43200), not a completion-time estimate. Owned session97663,
native PID84408 confirmed live; caffeinate84410 follows that job. No restart from zero, no source
mutation, no policy change, no selection/embedding/training. Previous39397 is finished.
Trello logging deferred because read requests were unavailable/unresponsive; repository record retained.

## User-requested handoff pause — October 13

Quinton requested a pause to pass something off. Command-verified PID84408 received SIGINT;
owned session97663 finished exit1 (intentional SQLite interruption). PID84408/caffeinate84410
are absent and the lookup lock is released. Checkpoint retains37,630,000 records,
last_rowid38168341 and20 title matches (91.28% of41,226,017). Script/candidate hashes and
catalog size/mtime match checkpoint identity. Status reports stopped; completion remains pending.
Resume SAME attempt02 with --resume only when requested; no restart from zero. Drive remains
mounted; normal eject is required before disconnection. No selection, embeddings or training started.

## Resume after class — October 13

Quinton connected the drive and explicitly requested continuation. Worktree was already clean;
UI update d67e93c and storage review77232e6 are committed. Verified external UUID
22750B93-2F3F-499D-87F5-902981BFAB59, approximately2.26TB free, no competing corpus process,
unchanged script/candidate/catalog stat/metadata identity and available locks. Preserved the stopped
status under a fresh timestamped pause-before-resume receipt. Same attempt02 resumes at37,630,000
records/last_rowid38168341/20matches, --resume --seconds43200. Owned session10195, native
Python36048/caffeinate36049 confirmed live; 12h is an invocation ceiling, not an ETA. Prior97663
remains finished. No restart from zero, selector, embeddings or training.

## Resumable selector design — October 13

Engineering Phase 1 is documented in [the resumable selection design](RESUMABLE-SELECTION-DESIGN-2026-10-13.md).
Quinton selected keeping Expat. The design specifies transactional evaluation checkpoints, exact
resume identities, global ranking, recoverable exports, resource bounds and acceptance tests.
Design review precedes Phase 2 implementation; seed review/freeze still precedes real selection.
This documentation does not change the active lookup or completed replay implementation.

## Resumable selector Phase 2 — October 13

[Phase 2 results](RESUMABLE-SELECTION-PHASE2-2026-10-13.md) document the new isolated evaluation
module/CLI, atomic checkpoints, explicit resume, identities and locks. Synthetic regression suite:
69 passed. Evaluation stops at ranking pending; no final selection receipt or actual corpus run.
Next review is engineering Phase 3 ranking/export recovery. Existing replay and lookup code unchanged.

## Resumable selector engineering Phase 3 — October 13

[Ranking/export results](RESUMABLE-SELECTION-PHASE3-2026-10-13.md): global winners committed,
numbered recoverable export attempts, byte verification and completion summary published last.
84 synthetic/regression checks pass, including publication crash boundaries and prior-selector
byte equivalence. No real selection run. Next is engineering Phase 4 recovery/performance review;
SQLite temporary spill accounting remains a specific resource qualification item before launch.

## Resumable selector engineering Phase 4 — October 13

[Recovery/resource/performance results](RESUMABLE-SELECTION-PHASE4-2026-10-13.md): 102 tests pass,
including nine actual SIGINT/SIGTERM/SIGKILL recovery cases. Open-unlinked descriptor accounting
now detects real SQLite spill; cooperative limits still require launch headroom. Eighteen bounded
synthetic benchmark runs match reference output hashes; keep Expat and batch 1,000. Internal
invocation logs added to the CLI. No real selection launched. Next: Phase 5 concrete launch packet
after seed review/freeze and other admission prerequisites, with real sizing as needed.

## Engineering Phase 5 packet prepared — October 13

[Draft launch packet](RESUMABLE-SELECTION-PHASE5-LAUNCH-2026-10-13.md) records exact proposed paths,
command, identity pins, resource limits and pause/resume/completion procedure. Native PID36048
confirmed running the existing lookup; status advanced39.77M to39.78M/41.226M during checks.
Correct external UUID and~2.26TB free verified. No matches.json yet; seed review/freeze and reserve/
exposure artifacts remain prerequisites. Real output capacity still needs review. Packet is
explicitly non-executable; no actual selector, new corpus scan, seed freeze or key generation.

## Seed prerequisites in progress — October 13

[Provisional seed review](planning/SEED-READINESS-2026-10-13.md) examines the21 already-located
records by direct PMID lookup: citation/supplied-DOI checks pass, but all21 have MeSH. C-29/C-42
remain pending the full scan. C-25/C-36 local abstract scope checks completed; recommendations
submitted to Quinton. Initialized32 exposure events/31 distinct PMIDs and retained17 explicit
identifier mappings plus chaining groups as unresolved. No seed freeze or reserve keys yet.
Missing-MeSH coverage requires additional reviewed candidates or an explicit protocol decision.

## Transport pause — October 13 afternoon

Quinton requested pause before going home. Command-verified Python36048 received SIGINT;
owned session10195 finished exit1 with intentional SQLite interruption. Python36048 and
caffeinate36049 confirmed absent; lookup lock released. Saved checkpoint40,510,000 titles
(98.26%), last_rowid44538617,23 title matches;716,017 titles remain. Candidate/script hashes
and catalog size/mtime still match. Timestamped transport-stop receipt retained in attempt02.
Resume SAME output with --resume only when Quinton requests continuation; no restart from zero.
Drive was not unmounted by this pause; normal eject remains required before disconnecting it.

## Home resume — October 13

Quinton requested continuation after the meeting. Verified the correct external UUID,
about 2.26 TB free, unchanged catalog stat/metadata and script/candidate hashes, available
locks and no competing processing job. Preserved pause-before-home-resume-20261013T220621Z.json.
Resumed SAME attempt02 with --resume --seconds43200 from40,510,000/41,226,017 titles
(98.26%), last_rowid44538617 and23 matches. Owned session51288; native Python51397 and
caffeinate51398 confirmed live, status scanning_titles. Prior10195 remains finished.
716,017 titles remain at restart;12h is an invocation ceiling, not an ETA. Seed review/freeze
still follows lookup completion; no real selection or embeddings launched. Trello W02-06 updated.

## Citation lookup completed — October 13

Owned session51288 exited0; native lookup/caffeinate processes confirmed absent. Status is
lookup_complete_review_pending: all41,226,017 titles scanned,23 title matches and23 matched
candidates. Final matches.json exists and parses; its SHA256 and exit evidence are retained in
attempt02/completion-observed-20261013.json. Final invocation took3934.49seconds (~65.6minutes).
This completes citation lookup only; seed review/freeze, outstanding coverage/scope decisions
and real-selection admission remain open. No selector or embeddings launched.

## Selection R01 launched — October13

Approved23seeds frozen,3withoutMeSH; see SELECTION-R01-LAUNCH-2026-10-13.md. Native session90578/Python6127/caffeinate6128 launched initial source validation. Exact evidence in outputs/prowl/selection-launch-r01. Cap768GiB/floor400GiB/12h/32MiBcache after bounded actual sizing. Sampling separately blocked on remaining exposure groups; no embeddings. Verify live process and checkpoint before reporting evaluation progress.

## Optimization pause and R02 — October13 evening

R01 stopped before evaluation; original code/output preserved. Enginev2 fuses count reconciliation with evaluation and adds ordered CPU workers.121tests pass;12worker CPU benchmark8.9x, full-path rates depend on disk cache. R02 session48921 launched with12workers/4096MiBcache/768GiBcap/400GiBfloor/11.58h ceiling. See SELECTION-PERFORMANCE-2026-10-13.md; confirm checkpoint before reporting progress.
