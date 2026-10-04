# Draft dispatch packet — Plan 07 S2 sizing tool

**DRAFT ONLY. Group C permission is not granted.** Prepared by Codex for Quinton to dispatch to
Claude, the retrieval implementer. This packet runs nothing and creates no implementation files.
No download, signature, install, database work, source activation or new literature reading.

## Objective and entry gate

Build and test only the downloader subset and sizing-only parser mode required by Run S in
[ACQUISITION-PLAN](../retrieval/planning/ACQUISITION-PLAN.md). Input plan SHA-256:
`a2be620c6b03373bc6a84b6cd88bf4f2177313bddc1992da7f3991ca713fc826`.
The verbatim authority annex below governs caps and checks. No run A downloader/event-log parser,
selection code, full snapshot, corpus, index or embeddings are included.

Entry requires Quinton's explicit S2 implementation dispatch. Claude checks that new allowlisted
paths are absent/unowned before writing. S1's concrete storage interface must be agreed before binding
an executable live writer; pure tests use invented volume/writer observations. Missing S1 is a
reported integration dependency, not permission to change Codex's adapter. R-01 imaging takes
priority; no MPS, real volumes, bulk storage or concurrent native resource trial.

## Proposed write allowlist for the dispatch

- `src/retrieval/sizing_v1/__init__.py`
- `src/retrieval/sizing_v1/listings.py`
- `src/retrieval/sizing_v1/transfer.py`
- `src/retrieval/sizing_v1/parser.py`
- `src/retrieval/sizing_v1/journal.py`
- `src/retrieval/sizing_v1/runner.py`
- `scripts/retrieval/run_s_sizing_v1.py`
- `tests/retrieval/test_sizing_v1_listings.py`
- `tests/retrieval/test_sizing_v1_transfer.py`
- `tests/retrieval/test_sizing_v1_parser.py`
- `tests/retrieval/test_sizing_v1_journal.py`
- `tests/retrieval/test_sizing_v1_runner.py`
- `tests/retrieval/fixtures/sizing_v1/*` — invented XML/listings/receipts only
- `docs/capstone/retrieval/CLAUDE-S2-HANDBACK-2026-10-03.md`
- Claude's own append-only `docs/capstone/retrieval/planning/RUNNING-LOG.md` entry at actual dispatch
  and handback; no other planning changes implied.

This is a proposed future allowlist, not authority to write now. Do not edit existing P3 producers,
schemas, tests, shared decisions, roots, operations or dependency manifests. If the final dispatch
date changes, explicitly name the dated handback path. No copied real PubMed records/abstracts.

## Required behavior and implementation boundaries

1. Separate transport, clock, memory probe, volume/capacity probe and writers behind injectable
   interfaces. Tests use fake chunk streams, fake times/RSS and disposable temporary directories.
   Deny actual network in the test harness, including DTD/entity resolution and unexpected sockets.
2. Resolve transfers only from the frozen listings and signed literal URLs. Refuse unexpected
   hosts/redirect destinations, types, names and ambiguous or missing identities; never substitute.
   Count bytes received from HTTP transactions, redirects, HEAD/listings/checksums, partials and
   retries under the same signed-copy counters. State exactly how the live transport measures bytes;
   do not silently equate payload Content-Length with all received response bytes.
3. Enforce byte limits before accepting/writing the next chunk, with cumulative scratch writes
   even when partial data is retained. Exactly one concurrent transfer, bounded attempts/stall/time
   limits, exclusive scratch creation, MD5 where published and local SHA-256 for every file.
4. Bind runs to a signed-copy hash. First-run counters start at zero only after proving no prior
   run exists for that copy; a second run requires the earlier terminal primary/fallback journal.
   Do not regenerate allowances or accept a missing/incomplete predecessor. At most two runs.
   Per-run 2-hour wall time resets; cumulative network and scratch allowances do not.
5. Emit sizing partitions in the same proposed fields/compression as the parsed-store format.
   Each file has local event rows only; no cross-file event log/final state. Preserve `sizing_only`
   on output and enforce refusal at export/consumption boundaries. A test must demonstrate that
   selection/promotion cannot accept the sizing output; do not edit P6 or add a fake valid snapshot.
6. Meet all parser guards in the annex, including RSS4 GiB, gzip20× and XML restrictions. Specify
   the exact finite internal expansion bound and safe parser settings in the handback; reject
   unsafe entity definitions rather than fetching a DTD. If existing dependencies/standard library
   cannot enforce the hard memory or XML requirements, stop and explain the gap for Quinton's
   dependency/platform decision. Do not weaken the contract or claim injected RSS tests prove an
   OS-level hard limit. No actual 4 GiB stress allocation is required by the synthetic packet.
7. Journal before transfers, after checks and on failures/signals. Exclusive JSONL creation,
   durable append and exactly one terminal status for a normally handled termination. A hard-killed
   process may leave no final status: it is incomplete, never completed or automatically retried.
   Fallback receives only remaining journal events; primary loss stops the run.
8. The CLI may validate invented signed-record fixtures and print readiness. It must reject a live
   execution without S1, exact tested-code identity, S3 and Quinton's signed copy. This dispatch does
   not permit the implementer to fill/sign a real run record or execute the network branch.

## Required synthetic tests — no network

| Group | Required oracles |
|---|---|
| Listings | Exactly1334 unique baseline names with matching MD5s; extras recorded; missing/duplicate/ambiguous sample refused; at least2 valid updates≥1335; choose2 highest from saved bytes, not a later live list |
| MeSH/precheck | HEAD size or1 GiB fallback; received bytes counted; over-size stopped; resolved names/sizes journaled before any sample; planned bytes over cap prevent transfer |
| Streaming | 10 GiB receive and40 GiB cumulative scratch boundaries, next-byte overflow, redirects/retries/partials/listings/MD5/HEAD included; exclusive collisions; one connection;2 attempts/file;5min stall;2h hard per-run deadline |
| Reruns | Fresh signed-copy case; valid second run with previous final status; missing/truncated/ambiguous primary/fallback; no allowance reset; third run refused; samples reusable only after checksums |
| Integrity | Valid/invalid published MD5, SHA-256, absent published MD5 noted; both failed attempts terminal; mismatch not reused or promoted |
| Volume/space | Start UUID/mount/floor+40 GiB; before-file and60s floor+remaining-cap checks; mount changes/loss/wrong role; no payload fallback |
| Parser | Independent nonconsecutive samples; record/delete counts; exact compressed/decompressed/parsed ratios; streaming release;20× and4 GiB guard stops; malformed XML refuses partial-ratio success |
| XML | PubMed-style external-DTD DOCTYPE parses with zero fetches; external entity refused; billion-laughs refused; finite internal-expansion bound tested; parser network disabled |
| Output | Same-field/compression sizing partitions, sizing-only marker required and rejected by selection/promotion, no final snapshot or global event-log output |
| Journal | Exclusive create/durable append, identity/counters/measurements, primary failure/fallback/stop, handled signal `interrupted`, missing final incomplete, completed only after every required file verified/measured |
| Representation | First/middle/last are file-sequence positions; observed years recorded; largest of five ratios×1.5 used for projection, never a guarantee |
| Scope | No real XML/abstracts, source activation, code imports that mutate another lane, live socket, install, DB, MPS or storage-root writes |

Record the focused test command, complete results, code hashes, invented fixture provenance, unresolved
native adapter/security limits and all changed paths. Native Mac qualification belongs to a separately
scheduled review; Linux sandbox results alone do not satisfy native writer/memory/volume acceptance.

## Stop point and handback

Stop after implementation plus invented tests and the handback. Report readiness or exact unmet
requirements. Do not dispatch another phase, obtain a signature, execute Run S, download anything,
install a dependency or enable S1 yourself. Quinton reviews the handback and any dependency questions;
Codex retains the shared storage integration. A subsequent tested-code/native review, S1 completion,
S3 reading and S4 signature precede a separately authorized Run S execution.

## Verbatim Run S authority annex

The following blocks are copied byte-for-byte from the pinned acquisition plan. The status and
"proposed figures" wording are historical planning authority; this draft carries4 GiB/20× forward
for review, and the later signed copy must explicitly confirm them. Sizing implementation dispatch
and acceptance do not themselves sign those figures or the run.

## Sizing-only parser mode

- Parses **each sampled file independently**, whatever its position in the sequence.
- Records per-file:
  - compressed and decompressed sizes;
  - record and delete counts;
  - parsed-output size ratio;
  - parse time;
  - peak scratch use.
- **Builds no event log and no final state, and claims no valid snapshot.** Outputs are marked
  `sizing_only`. Selection code and promotion refuse them (enforced by a flag, with a test).
- Nonconsecutive samples are expected in this mode. The production parser's sequence-gap refusal
  is unchanged.

## Run record S: sizing preflight (UNSIGNED; tightly bounded)

| Field | Value |
|---|---|
| Purpose | Measure what run A's capacity check needs, and nothing more |
| Actions | Fetch the publisher directory listings (file names and sizes) for the baseline and update directories. Download **exactly** the files in the file-choice rule below (**3 baseline + 2 update files**, plus their `.md5` files) and the MeSH 2026 descriptor file |
| File-choice rule (deterministic) | Baseline: exactly `pubmed26n0001`, `pubmed26n0667` (1334 / 2) and `pubmed26n1334`. Updates: the **two highest-numbered valid** update files in the **frozen listing** (preflight below). MeSH: the literal file name and URL written in the signed copy. Nothing is ever substituted |
| Sources | The **literal** baseline directory URL, update directory URL, MeSH file URL and MeSH file name, copied from NLM's [Download PubMed Data](https://pubmed.ncbi.nlm.nih.gov/download/) page and its MeSH download page at signing, and written into the signed copy. No other host. HTTPS where offered |
| Measurements | Listing totals (file count and bytes, baseline and updates separately); per-file download bytes and time, decompressed bytes and peak scratch; per-file parse ratio, record and delete counts, and time from the **sizing-only parser mode** |
| Caps | **Network:** at most 10 GiB received over the network, counting **every** byte: listings, `.md5` files, samples, MeSH, retries, partial and aborted transfers. **Scratch:** at most 40 GiB written, counting frozen listings, downloads, decompressed data and parser output (the journal lives in artifacts). **Time:** 2 hours wall-clock per run, enforced by the tool. **Also:** 1 concurrent transfer; at most 2 attempts per file; 5 minutes without progress aborts that attempt. Enforcement is set out below |
| Ongoing checks | **Supplementing** the streaming caps: before each file and every 60 s, the volume identity is unchanged and free space is at least headroom floor + the remaining scratch cap. Otherwise stop |
| Destination | `prowl_scratch/literature/sizing-<run-id>/`. **Not promoted.** Samples may be reused in run A only if their checksums match |
| Integrity | Publisher MD5 where NLM publishes one, plus local SHA-256 for every file. A file without a published MD5 (for example the MeSH file, or the `.md5` files themselves) gets SHA-256 only, noted in the receipt |
| Volume identity and capacity | Checked at start |
| Executed on | Quinton's Mac, by the approved sizing-only tool, run by Codex or by Quinton. **Not** from Claude's Cowork VM: on 2026-09-28 it had no network, and it may not be a controlled writer of `prowl_scratch` |
| Network etiquette | 1 connection. No personal data in request headers. A tool User-Agent naming the project. Any current NLM bulk-download guidance is followed |
| Stop conditions | Any cap reached; any file failing both attempts (checksum, timeout or HTTP error); volume change; unexpected file type or name; any preflight check failing; the parser memory, expansion or XML guards tripping; malformed XML in a sample |
| Post-run state | The scratch directory is kept until run A is signed or the S receipt is superseded. Deleting it needs Quinton's approval. Nothing is promoted, and sizing outputs are refused by selection and promotion (sizing-only flag) |
| Receipt | An append-only journal, defined under "Receipts, failure and interruption" below. It holds: run ID; who ran it; times; host; tool code hash; source URLs; frozen-listing hashes and totals; resolved file names; per-file bytes, MD5, SHA-256 and times; measurements; representativeness record; failures; cap and space readings; the final status. A summary goes in `RUNNING-LOG.md` |
| Authorization | Quinton signs (block below). **Not signed** |

### Run S prerequisites (status on 2026-09-28)

| # | Prerequisite | Owner | Status |
|---|---|---|---|
| S1 | `prowl_scratch` and `prowl_artifacts/literature/receipts/` exist, a controlled literature writer is enabled, and the volume-identity check is implemented | Codex (Plan 10) | **Not complete** (Codex, read-only observation, 2026-09-28). The registered scratch and artifacts directories exist and are not symlinks. `artifacts/literature/` and `artifacts/literature/receipts/` do **not** exist. No literature writer or source alias is enabled |
| S2 | Sizing-only tool packet: a downloader subset (checksums, caps, no promotion) plus the sizing-only parser mode, with tests passing on synthetic fixtures | Issued by Codex, dispatched by Quinton (SCOPE 12C) | **Not issued.** Group C permission, not granted |
| S3 | Capacity reading of the target volume at signing | The executor named in the signature block | At signing |
| S4 | Quinton signs this record | Quinton | **Not signed** |

S cannot be signed until S1-S3 are complete, and cannot run until S4 as well. **Writing this record
does not authorize the tool, the download, any directory creation or any install.**

### Run S preflight (at run start, before any sample transfer)

1. **Freeze the listings.** Fetch the baseline and update directory listings from the literal URLs
   in the signed copy. Save each response's raw bytes to the run's scratch directory, and record
   their SHA-256 in the journal. **All later resolution uses only these frozen bytes.** The saved
  listing bytes count against the network and scratch caps.
2. **Baseline identities.** Among its `pubmed26n*.xml.gz` and `.md5` entries, the frozen baseline
   listing must contain exactly the 1334 names `pubmed26n0001.xml.gz` to `pubmed26n1334.xml.gz`,
   each once, each with a matching `.md5`. Other entries (for example a README) are recorded in the
   journal and are not a stop condition. The
   three sample names must be present. Anything missing, duplicated or ambiguous stops the run. No
   other file is substituted.
3. **Update files.** A **valid** update file is named `pubmed26n<NNNN>.xml.gz` with NNNN of 1335 or
   more, appears once, and has a matching `.md5`. There must be **at least two distinct** valid
   update files, and the two highest-numbered are taken. Fewer than two, or an ambiguous listing,
   stops the run.
4. **MeSH size.** The MeSH file is not in the PubMed listings, so its size is taken from an HTTP
   `HEAD` `Content-Length` (the bytes count against the cap). If no size is given, a fixed
   allowance of **1 GiB** is reserved. If the transfer exceeds whichever applies, the run stops.
5. **Record before transfer.** The resolved names and sizes are written to the journal **before**
   the first sample transfer. A cap pre-check sums them: if the bytes received so far plus the
   planned transfers would exceed the network cap, the run stops without transferring.

### Run S cap enforcement (requirements for the S2 tool)

- **Cap scope:** the 10 GiB network cap and the 40 GiB scratch cap are **cumulative per signed
  copy**, across both permitted runs. A re-run does not get a fresh allowance.
  - It initializes its counters from the earlier run's journal (primary or fallback).
  - It refuses to start if that journal is missing or has no final status.
  - The 2-hour time cap is **per run**.
- **Network cap:** a running counter of bytes received, updated as data arrives. A transfer is
  aborted at once if the counter would pass 10 GiB. Retries, partials, redirects, listings and
  `.md5` files all count.
- **Scratch cap:** a running counter of bytes written to scratch, covering frozen listings,
  downloads, decompressed output and parser output. Writing stops at once if it would pass 40 GiB.
  The journal lives in artifacts, not scratch; it is small, and it is bounded by the run's events.
- **No overwrite in scratch:** every sample and output file is created exclusively. A name collision
  stops the run.
- **Time cap:** a hard 2-hour deadline, checked during transfers and parsing.
- The 60-second volume and free-space checks run in addition to these, never instead of them.

### Sizing parser safeguards (requirements for the S2 tool packet; not built here)

- **Proposed figures (Claude's, for Codex and Quinton to confirm in the tool packet):** 4 GiB and
  20 times, below. The ~9.6 GiB coexistence budget is itself still PROPOSED until P4a (SCOPE 12B).
- **Memory:** a hard cap of **4 GiB** resident memory for the parser process. Exceeding it stops the
  run with `stopped_memory_cap`. This sits inside the SCOPE 12B coexistence budget of about 9.6 GiB.
- **Streaming decompression:** gzip is decompressed as a stream, never fully into memory.
  Decompressed output per file may be at most **20 times** its compressed size, and it also counts
  against the scratch cap. Exceeding either stops the run (`stopped_expansion_guard`).
- **XML parsing:** streaming, with elements released as they are processed.
  - A `DOCTYPE` declaration is **tolerated but never fetched**. PubMed files name an external DTD
    (`pubmed_250101`), and that is not an error.
  - External entity resolution is refused, and the parser has no network access.
  - Internal entity expansion is bounded, and oversized expansion is refused.
  - The packet's tests must include three fixtures:
    1. a PubMed-style `DOCTYPE` with an external DTD reference, which parses **without any fetch**;
    2. an external-entity reference, which is **refused**;
    3. an entity-expansion ("billion laughs") case, which is **refused**.
- **Malformed XML** fails closed. The run stops with the file named, because partial ratios would
  not be representative.
- No new dependency is implied. If the standard library cannot meet these guards, that is a
  dependency question for Quinton.

### Representativeness record (written into the journal)

- **Sample positions:**
  - first, middle and last baseline files, as deterministic **file-sequence positions**. They
    are not claimed to span the oldest to the newest publication dates; the sizing receipt records
    any observed year distribution;
  - the two newest update files, covering update-shaped content, including deletions.
- **Same format as the store:** the sizing parser writes the **same fields and the same compression**
  as the proposed parsed-store partition format: one compressed JSON Lines file per source file,
  with that file's own event rows and parsed fields. It builds **no cross-file** event log and no
  final state (sizing-only mode).
  A ratio measured in any other format is not accepted for the capacity model.
- **Limitation, stated rather than assumed away:** 3 of 1334 baseline files and 2 update files are a
  small sample, and per-file ratios vary. The capacity model uses the **largest** sampled ratio
  × 1.5 as a projection, **not proof** that the store fits. Run A's and P5's runtime phase caps and
  stop conditions remain the actual safeguard.

### Receipts, failure and interruption

- **Journal:** append-only JSON Lines, one event per step: start, preflight, each file's start and
  end, each check, each stop.
  - **Primary location:** `prowl_artifacts/literature/receipts/run-S-<run-id>.jsonl`, which S1 must
    create.
  - The file is created exclusively (it fails if it already exists), and it is never overwritten.
- **Fallback:** if the primary volume disappears or becomes unwritable, the remaining events go to
  a fallback journal on the internal disk, and the run stops. The fallback path is written
  literally in the signed copy, outside Git and outside scratch.
- **Final status:** exactly one of:
  - `completed`, only after every file is verified and measured;
  - `stopped_<reason>`;
  - `interrupted` (written on a termination signal).

  **A missing final status means incomplete.** No `completed` marker is ever written for partial
  work.
- **Re-runs:** a re-run gets a new run ID and a new journal. At most 2 runs are allowed per signed
  copy. Earlier partial scratch data is kept until Quinton approves deleting it, and samples are
  reused only on a checksum match.

### Run S pre-run checklist (the executor confirms each item in the receipt)

1. The SHA-256 of the signed copy (below) matches the hash in `RUNNING-LOG.md`.
2. The volume identity (UUID/mount) matches the alias configuration.
3. Free space is at least the headroom floor plus 40 GiB.
4. The tool's code hash matches the tested packet, and its tests pass.
5. The listings were frozen, and the preflight resolved the exact names recorded (preflight
   steps 1-5).
6. No earlier S scratch directory is reused without a checksum match.

### Run S signature

**How signing works:**
1. At signing, the run S section is **copied** to a new file, `RUN-S-SIGNED-<date>.md`, next to
   this one. The copy includes:
   - the record table;
   - the "Sizing-only parser mode" section;
   - the preflight;
   - cap enforcement;
   - safeguards;
   - representativeness;
   - receipts;
   - the **pre-run checklist**;
   - the signature block. The S1-S4 status table is **replaced** by
   the readings taken at signing, so no stale status is frozen.
2. Every field in the copy is filled in with **literal values**:
   - the baseline and update directory URLs;
   - the MeSH file URL and file name;
   - the fallback journal path;
   - the confirmed parser memory cap and decompression-expansion limit, replacing the "proposed
     figures" wording;
   - the executor;
   - the tool code hash;
   - the capacity reading;
   - the signature.
3. Quinton signs the copy.
4. The copy's SHA-256 is recorded in `RUNNING-LOG.md`.

The copy is then never edited. This file, including runs A and B, stays editable; the signed copy is
the authority for run S.

| Field | Value |
|---|---|
| Signed by | *(Quinton Evans)* |
| Date | |
| Executor | *(Codex or Quinton, named)* |
| Tool code hash | *(the tested sizing-only packet's commit or tree hash)* |
| Baseline / update directory URLs | *(literal)* |
| MeSH file name and URL | *(literal)* |
| Fallback journal path | *(literal, internal disk, outside Git and scratch)* |
| Terms | "NLM download conditions reviewed" *(Quinton's words)* |
| Capacity at signing (S3) | *(volume identity, free bytes, headroom floor)* |
| Signed copy | `RUN-S-SIGNED-<date>.md`, SHA-256 *(recorded in RUNNING-LOG)* |

The run ID is assigned at start and recorded in the receipt, not in the signed copy.

---

