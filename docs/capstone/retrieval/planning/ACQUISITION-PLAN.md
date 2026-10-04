# Acquisition plan and run records

**Status:** PROPOSED, revision 8 (P2, 2026-09-28). All run records (S, A, B, P) are **unsigned**.
- **Revision 8** adds run record P, a one-file PANORAMA protocol PDF, approved in principle by
  Quinton and still unsigned. It also includes the file-sequence wording fix from the Codex
  re-review.
- **Revision 7 (Codex R3)** turns run S into a bounded execution contract:
  - a frozen listing, and strict filename resolution;
  - network and scratch caps enforced while streaming;
  - parser memory, decompression and XML safeguards for the tool packet;
  - a representativeness record;
  - failure and interrupt receipts with a durable fallback.
- **Run S is not ready to sign.** It becomes signable only when the tested code, the aliases, a
  capacity reading and the checks exist (S1-S3). PHASES' P2 exit wording ("ready for signature") is
  met here only as "envelope complete". Amending that wording is Quinton's decision.
No download is authorized. Revision 5 drafted run record S's envelope: a
deterministic file choice, the executing machine, a prerequisite status table, the pre-run checklist,
the post-run state and a signature block that signs a frozen copy.
The run A table is unchanged, and run B's table gains only a licence-allowlist row. Three related
edits:
- the prerequisite lists now read "before running", with signing as the explicit last step;
- run B's list gains the licence allowlist;
- the capacity model names the MeSH file and uses the largest sampled parse ratio.
**Route:** L-03, approved by Quinton on 2026-09-28 and recorded by Codex as **D-261**. D-261 keeps
E-utilities for bounded checks. The remaining channel-text items are in SCOPE section 10 (Codex).
**Rule:** every acquisition is a live network job under a run record Quinton has signed. Nothing
here records terms as accepted; Quinton accepts them at signing.

## Facts relied on (checked 2026-09-28)

- **PubMed 2026 baseline:**
  - released 2026-01-30 as `pubmed26n0001`-`pubmed26n1334` (XML, with MD5 files);
  - updates start at `pubmed26n1335`;
  - the baseline must be processed before any update;
  - updates carry new, revised and deleted citations;
  - DTD `pubmed_250101`.

  ([NLM bulletin](https://www.nlm.nih.gov/pubs/techbull/jf26/jf26_PubMed_2026_BaselineRelease.html);
  [Download PubMed Data](https://pubmed.ncbi.nlm.nih.gov/download/))
- **NLM conditions:** no signed licence; acknowledge NLM; do not imply endorsement; if
  redistributing, keep data current or disclose that it is not; no warranty. Abstracts may be
  publisher-copyrighted. ([NLM](https://www.nlm.nih.gov/databases/download.html))
- **PMC Cloud Service** (`pmc-oa-opendata`): anonymous access, per-article JSON metadata with
  licence, a daily inventory. Objects can change without a version change.
  ([NCBI Insights](https://ncbiinsights.ncbi.nlm.nih.gov/2026/02/12/pmc-article-dataset-distribution-services/);
  [PMC on AWS](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/))
- **Not guaranteed:** that this year's baseline files stay downloadable after the next annual
  baseline release, or that PMC bytes stay the same. Reacquisition is not a guaranteed recovery path
  (SCOPE 5.7).

## Prerequisites per run record (no run's prerequisites include itself)

Each list is what must be true **before the run starts**. Signing is always the last item, and it
can only happen once the earlier items are true. For run S, this is because the signature records
the tested tool's code hash. **Proposed reading, for Quinton to decide:** "ready for signature" in the PHASES P2
exit means the **envelope is complete**, not that the earlier items are met.

**Before running S (sizing preflight)** (the same items as the S1-S4 table below):
1. `prowl_scratch` and `prowl_artifacts/literature/receipts/` exist, a controlled literature writer
   is enabled, and the volume-identity check is implemented (S1).
2. A **sizing-only tool** passes tests on synthetic fixtures: a downloader subset (checksums, caps,
   no promotion) plus the **sizing-only parser mode** described below (S2).
3. A capacity reading of the target volume is taken at signing (S3).
4. Quinton signs run S (S4, after 1-3).

**Before running A (full baseline + updates + MeSH):**
1. Quinton confirms L-03 for recording, and Codex reconciles the channel text. **Done:** L-03 is
   recorded as D-261, and the channel text is reconciled in `CORPUS-AND-RIGHTS.md` and P07-05
   (Codex P2 review, 2026-09-28). This item concerns wording only; run A itself is unsigned.
2. Plan 10 aliases exist: `literature_source` (read-only after promotion), `prowl_scratch` and
   `prowl_artifacts/literature/`.
3. The **full downloader and event-log parser packet** is approved, with tests passing on synthetic
   fixtures. Required tests:

   **Downloader:**
   - checksum verification (MD5 and SHA-256);
   - resume from partial;
   - no overwrite;
   - bounded concurrency;
   - volume identity before every promotion;
   - receipts;
   - interruption leaves only scratch partials.

   **Parser / event log:**
   - additions;
   - replacements;
   - deletions (`DeleteCitation`);
   - repeated events (identical and changed content);
   - delete-then-re-add;
   - interrupted update application;
   - deterministic replay;
   - malformed XML fails closed;
   - order violations and sequence gaps refused.
4. **Run S completed**, and its receipt reviewed.
5. The capacity check passes using S's measurements plus the projections and caps below.
6. Quinton signs run A (after 1-5).

**Before running P (PANORAMA protocol PDF, one file):** the receipt path is fixed and exists, the
executor is named, and Quinton signs the copy (run record P).

**Before running B (PMC objects):**
1. The stage-1 bibliographic candidate set is frozen (`SEARCH-AND-SELECTION.md` section 5).
2. The capacity is rechecked.
3. The licence allowlist for "permitted full text" is written into run record B
   (`SEARCH-AND-SELECTION.md` section 9).
4. Quinton signs run B (after 1-3).

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

## Source revisions and the event log

- **Revision identity:** `revision_id` = SHA-256 of the canonicalized record XML (stable
  serialization of the `PubmedArticle` element). Bibliographic version fields are recorded but
  never assumed to identify an update uniquely.
- **Event provenance:** each record occurrence or deletion is an event (`source_file`, `ordinal`
  within the file, `event_type` in {`add_or_replace`, `delete`}, `pmid`, `revision_id` or null).
  - Final state = the last event per PMID in (file sequence, ordinal) order.
  - A delete removes the PMID from the final state, but its history is retained.
  - Identical repeated content keeps the same `revision_id`; the event is still logged.
- **Replay:** the final state is always computed from the ordered event log, never by in-place
  mutation, so an interrupted application can be replayed deterministically.

## Parsed PubMed store

- **Location:** `prowl_artifacts/literature/parsed/<parser-version>/<snapshot-id>/`.
- **Authority:** **derived**, regenerable from the raw files plus the parser version. It is never the
  canonical source, and it is never a vector index.
- **Format (proposed):** one compressed JSON Lines partition per source file (events plus parsed
  fields), a partition manifest with SHA-256 hashes, and a final-state index keyed by PMID.
  Chosen for inspectability and zero new dependencies; revisited only if measured parse or query
  time requires it.
- **Lifecycle:**
  - retained while its raw inputs and parser version are current;
  - a new parser version produces a new store alongside the old one;
  - old stores are deleted only on approval.
- **Tier 2:** turning any part of this store into embeddings requires X1 approval.

## Capacity model (measured where possible, capped where not)

The download is authorized on **measured samples plus explicit conservative projections and
caps**. It does not wait for P6/P8 artifacts that cannot exist yet. Capacity is **rechecked before
each phase** (P5, P6, P8) against actual usage, and a phase stops if its cap would be exceeded.

| Component | Basis | Proposed rule |
|---|---|---|
| Raw baseline + updates + MeSH | **Measured**: publisher listing sizes (run S); the MeSH file's measured size | Exact bytes x 1.05 |
| Decompression / temporary peak | **Measured**: run S sample | Measured peak per file x 2 (two concurrent transfers) |
| Parsed store | **Projected** from run S's sample parse ratios | The **largest** of the 5 sampled ratios x total raw bytes x 1.5 |
| Retry / duplicate revisions | Projected | 10% of raw bytes |
| Tier 1 canonical artifacts (representations, passages, PMC bytes, embeddings) | Not yet measurable | **Cap:** 100 GiB reserved; P6/P8 stop if exceeded |
| Database + indexes + WAL, plus a second instance during scoped recovery | Measured in P4a on synthetic scale, projected | **Cap:** 100 GiB reserved |
| Operational headroom | Plan 10 policy | max(100 GiB, 10% of usable capacity) |

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

## Run record A: PubMed baseline, updates and MeSH (UNSIGNED)

| Field | Value |
|---|---|
| Purpose / tier | Canonical snapshot for Tier 1 selection. Serves Tier 2 only after X1 approval |
| Sources | Baseline `pubmed26n0001`-`n1334` + `.md5`; update files `n1335` to the cutoff; MeSH 2026 descriptor data (filename verified at signing); terms README |
| Cutoff | Proposed: the latest update file published on the signing date, recorded by name. Later updates are not applied to this snapshot |
| Transport | NLM's documented bulk distribution, over HTTPS where offered |
| Destination | Scratch `prowl_scratch/literature/<run-id>/`, promoted to `literature_source/pubmed/2026/{baseline,updatefiles,mesh}/` |
| Expected files / bytes | Measured from the listing at signing |
| Concurrency | At most 2 simultaneous transfers (proposed); follow any current NLM guidance |
| Per-file timeout | Proposed 30 min without progress, then abort that file and retry |
| Time cap | Proposed 72 h wall-clock per attempt; resumable. Overnight only with explicit approval |
| Capacity | The capacity model above passes, with a stop at the headroom floor |
| Volume identity | UUID/mount check at start and before every promotion. Mismatch stops the run |
| Integrity | Publisher MD5 plus local SHA-256 for every file; sequence reconciled (no gaps) |
| Retry | Transient errors: bounded exponential backoff (proposed at most 5 attempts per file). Checksum mismatch: one retry, then stop |
| No-overwrite | Promoted files are immutable. A same-name difference is a stop condition |
| Interruption | Only scratch partials exist; resume re-verifies them; nothing is half-promoted |
| Stop conditions | Checksum failure after retry; sequence gap; floor reached; volume change; unexpected file type; time cap |
| Receipt | Run ID, times, host, code hash, per-file name/bytes/MD5/SHA-256/time, cutoff, failures, reconciliation |
| Rights | NLM attribution recorded; no endorsement language; abstracts local and off-Git |
| Executed by / on | Claude or Codex, on Quinton's Mac |
| Authorization | Quinton: name, date, "terms reviewed". **Not signed** |

## Run record B: PMC objects for selected Tier 1 works (UNSIGNED; P6)

| Field | Value |
|---|---|
| Purpose | Resolve full-text availability and rights for bibliographic candidates, then retrieve permitted XML text |
| Selection input | Frozen stage-1 **bibliographic candidate set** (hash recorded): every candidate with a PMCID, **including those without an abstract** |
| Source | `pmc-oa-opendata`, anonymous HTTPS/S3: per-article JSON metadata first, then XML text objects for eligible works only |
| Rights gate | JSON licence (OAI-PMH as corroboration). Unknown or conflicting means no full text |
| Licence allowlist | *(the licence values that count as "permitted full text"; fixed and approved by Quinton at signing)* |
| Excluded | PDFs, media, supplements |
| Destination | Scratch, promoted to `literature_source/pmc/<snapshot-id>/` |
| Expected objects / bytes | Measured from selection plus inventory at signing |
| Concurrency | At most 4 simultaneous requests (proposed) |
| Per-object timeout | Proposed 5 min |
| Time cap | Proposed 24 h per attempt; resumable |
| Capacity | Checked against the measured expected bytes plus headroom |
| Volume identity | Checked at start and before promotion |
| Integrity / freeze | Per object: key, inventory date/ETag, SHA-256 of bytes, retrieval time, licence text/ID. PMCID + version is **not** a content hash |
| Retry | Transient errors: bounded backoff (at most 5 attempts). Persistent 404/missing: recorded as `missing`, not retried endlessly |
| No-overwrite | A re-fetch with different bytes becomes a **new** object version, never an overwrite; recorded as a change |
| Interruption | Only scratch partials; resume by manifest |
| Reconciliation | Requested / retrieved / eligible / missing / changed, by reason |
| Stop conditions | Error rate above 5% of requests (proposed); floor reached; volume change; time cap |
| Receipt | As run A, per object |
| Authorization | Quinton signs. **Not signed** |

## Run record P: PANORAMA study protocol PDF, one file, for reference-list reading (UNSIGNED)

Quinton approved this **in principle** on 2026-09-28 (decision-sheet item 10). It runs only after he
signs this record. It is lower priority, and it does not block imaging work.

| Field | Value |
|---|---|
| Purpose | Read the protocol's **reference list** for citation chaining (SEED-SET rule 1). Nothing else |
| Source | Zenodo record 10599559 ("The PANORAMA Study Protocol: Pancreatic Cancer Diagnosis - Radiologists Meet AI", v1). The literal file URL is written at signing |
| File | Exactly one: `PANORAMA Study Protocol.pdf` (listed at 6.3 MB). No other file, page asset or version |
| Integrity | The published MD5 (`3c89347570dc4bb327924abfd7f001c0`, per Codex's reading of the landing page; re-confirmed and written literally at signing) plus a local SHA-256. A mismatch stops the run, and the file is not used |
| Caps | One target file; at most two attempts; aggregate received bytes at most 10 MiB (retries and partials included). A retry happens **only when** the remaining allowance covers the full listed file size; otherwise the run stops (`stopped_cap`). 10 minutes wall-clock. Partial bytes and wall time are recorded in the receipt |
| Terms | The Zenodo record's licence is recorded at signing. Quinton accepts the terms at signing. No redistribution, and no copy in Git |
| Destination | `prowl_scratch/literature/panorama-protocol-<run-id>/`. **Not promoted, not ingested, not indexed, not embedded.** Kept until the reference list has been read; deleting it needs Quinton's approval |
| Use | Only the reference-list section is read. Reading it is literature inspection: the pages read and the candidates proposed are logged in `RUNNING-LOG.md`, and any seed candidates go to Quinton for review as usual |
| Executor | Quinton's Mac, by Codex or Quinton. Not from the Cowork VM (it has no network) |
| Receipt | Run ID; who ran it; time; URL; bytes; MD5; SHA-256; licence; final status (`completed` / `stopped_<reason>`). Stored at the **receipt path written literally in the signed copy**: `prowl_artifacts/literature/receipts/run-P-<run-id>.json` if that directory exists at signing, otherwise a named internal-disk path outside Git and scratch |
| Prerequisites | The receipt path is fixed in the signed copy and exists; the executor is named; Quinton signs |
| Authorization | Quinton signs (block below). **Not signed** |

**Signing run P:**
1. Copy this record to `RUN-P-SIGNED-<date>.md`.
2. Fill in literal values:
   - the file URL;
   - the MD5 re-confirmed from the Zenodo record;
   - the licence;
   - the executor;
   - the receipt path;
   - the date.
3. Quinton signs the copy.
4. The copy's SHA-256 is recorded in `RUNNING-LOG.md`.

The copy is never edited afterwards.

| Field | Value |
|---|---|
| Signed by | *(Quinton Evans)* |
| Date | |
| File URL / MD5 / licence | *(literal)* |
| Executor | *(Codex or Quinton, named)* |
| Receipt path | *(literal)* |
| Signed copy | `RUN-P-SIGNED-<date>.md`, SHA-256 *(recorded in RUNNING-LOG)* |

## Not planned

- Full PMC mirroring.
- Downloading via article web pages.
- API keys in documents or logs.
- A full-PubMed vector index (that is X1 only).
