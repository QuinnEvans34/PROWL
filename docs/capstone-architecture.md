# Capstone Architecture — storage tiers, formats, and the contracts between them

**Drafted 2026-08-02.** Design doc for the 10-week capstone. Every contract below maps to a bug this
project has already hit — that is the point. The architecture is not decoration; it is the set of
mistakes we are structurally preventing from recurring.

---

## 1. Should CT scans live in a database? No. But the instinct is right.

The feeling that *"there must be a better way to load this"* is correct. The answer is not a document
database — it is a **purpose-built array format**. Here is the honest comparison.

| option | what it actually is | verdict for us |
|---|---|---|
| **Postgres BYTEA / large objects** | binary column in a relational DB | **No.** 1 GB field cap (largest scans exceed it), backups balloon to ~800 GB, no memory-mapping, image bytes pollute the buffer pool. |
| **MongoDB / GridFS** | files chunked into 255 KB documents | **No.** All the overhead of a database, none of the benefit. GridFS is built to serve files over HTTP, not to feed a training loop. No partial-volume reads, serialization cost on every access. |
| **Object storage (S3 / R2 / MinIO)** | blob store with an HTTP API | **Yes, at scale** — this is the cloud answer, and it is not a database. |
| **Zarr / HDF5 / N5** | chunked, compressed N-dimensional arrays with random access | **The scientifically correct answer.** Read a sub-volume without decompressing the whole thing; Zarr works natively over S3. Cost: many small chunk files behave badly on network filesystems unless sharded. |
| **WebDataset (tar shards)** | sequential tar archives streamed by the loader | **Yes for cloud training.** Dead simple, streams over HTTP/S3, the ML-standard answer. |
| **LMDB** | memory-mapped key-value store, single file | **Fast locally**, but does not stream from object storage. |
| **plain `.npy` per case** | one array file per case on disk | **Correct for local dev.** Trivially debuggable, zero dependencies, fast enough at our scale. |

**Conclusion: no single format wins. The access pattern differs by tier, so the tier defines the
format.**

---

## 2. Three tiers

### Cold — the archive
Original `.nii.gz`, exactly as published. **Never read during training.**
- PanTS Mini 382 GB + PANORAMA ~200 GB = **~582 GB**
- Lives on the external drive (and optionally object storage for the cloud path)
- Immutable. Checksummed. This is the provenance record — if anything downstream is questioned, this
  is what we re-derive from.

### Warm — the training cache
The whole-box preprocessed array: crop to pancreas → resample 1.5 mm → 128³.
**This is the only thing the trainer ever reads.**
- **10.0 MiB per case** (128³ float32 image + uint8 label)
- Lives on the **internal SSD** (or a cloud persistent volume)

| cohort | cases | warm size |
|---|---:|---:|
| `scaledmax_clean` (current) | 1,412 | **13.8 GiB** |
| `panorama_mix` (EXP-27) | 2,568 | **25.1 GiB** |
| all PanTS Mini | 9,901 | 96.7 GiB |
| all PanTS + PANORAMA usable | 11,865 | ~116 GiB |

**Format: `.npy` per case locally; WebDataset tar shards (~256 cases ≈ 2.5 GiB per shard) for cloud.**

**This tier is the whole answer to the cloud question.** We upload 25 GiB, not 582 GB. At 50 Mbps
that is roughly 70 minutes, once — after which every cloud run mounts the same volume.

### Index — Postgres
Metadata, cohorts, provenance, predictions, review decisions. **~50–100 MB.** No voxels, ever.

---

## 3. The contracts

Each contract is a promise between two components, and each one is an enforcement point. **Every
single one corresponds to a bug already hit in Weeks 1–5.**

### C1 · Ingest → Index
`build_manifest` writes one row per scan: `case_id`, `source_dataset`, `storage_root_id`,
`relative_path`, `sha256`, `bytes`, `shape`, `spacing`, `phase`, `site`, `has_lesion`.
- **Idempotent** — re-running updates, never duplicates.
- **Never an absolute path.** `storage_root_id` + relative path; the root comes from config.
- *Prevents:* hardcoded `/Volumes/...` paths breaking on every machine that isn't the laptop.

### C2 · Index → Cohort ★ the important one
**A cohort is a query result materialized into a table, not a text file.**
```sql
cohort(id, name, definition_sql, created_at, frozen_at)
cohort_member(cohort_id, scan_id)   -- PK (cohort_id, scan_id)
```
- **Disjointness is a database constraint, not a convention.** A derived cohort declares its parent
  fold; an assertion (or trigger) rejects any member that appears in a sibling eval cohort.
- Frozen cohorts get `frozen_at` set and become append-forbidden.
- *Prevents:* **the `make_scaled_split.py` validation leak** — sampling from the manifest's `split`
  column instead of the carved `train.txt`, which contaminated `scaledmax` by 266 cases and inflated
  the headline from 0.415 to 0.528. That bug is impossible if cohort membership is a constrained
  relation.
- *Also prevents:* the **cohort-definition contamination** we found in the reports work — 122 of 750
  "tumor-free" test cases carry a report-described lesion, because the cohort was defined on mask
  presence alone. A cohort defined by an explicit join across **mask AND report evidence** makes that
  visible at definition time.

### C3 · Cohort + Preprocessing config → Cache builder
Cache directory name = `hash(preprocessing config)`, where the config includes **spacing, HU window,
orientation, ROI source, crop margin, target size, and mask-resolution policy**.
- A changed preprocessing parameter produces a different cache key. Stale caches cannot be silently
  reused.
- *Prevents:* the open Codex finding — *"cache tag omits HU/orientation/mask-policy → stale-cache
  risk after the mask/resize changes."*

### C4 · Cache → Trainer
The trainer reads **only** the warm tier and refuses to start if the cache's config hash does not
match the run config.
- **Safety requirement for building this:** a test asserting cached and uncached paths produce
  **bit-identical arrays** for a sample of cases. The cache goes in *behind* the existing transforms
  interface, not as a rewrite.
- *Prevents:* **EXP-11**, lost to a train/eval preprocessing mismatch that produced a plausible-looking
  but meaningless 0.217 pancreas Dice.

### C5 · Trainer → Registry
A checkpoint is invalid without embedded: preprocessing config hash, cohort id + hash, git sha, seed,
step, and the metrics it was selected on.
- *Prevents:* the EXP-12 checkpoint loss, and the recurring *"which cohort was this trained on?"*
  question. Already partly solved by the per-run archive + `run_ledger.csv`; this makes it structural.

### C6 · Registry → Inference ★
**Inference must call the same preprocessing code path as training.** Not a reimplementation — the
same function, keyed by the checkpoint's embedded config hash.
- *Prevents:* the **train/serve double-processing bug** found in Week 5 deployment review.

### C7 · Inference → Index
Predictions written back as rows: `(model_version, scan_id)` unique, with predicted lesion volume,
patient-level score, and the mask's storage path (mask files go to disk, like every other volume).
- Enables the volume gate, the AUC analysis, and per-cohort reporting to be **queries** rather than
  ad-hoc scripts over CSVs.

### C8 · Index → UI
The UI reads predictions and writes reviewer decisions (`accept` / `edit` / `reject`) back to
Postgres. Reviewer decisions are the human-in-the-loop record and never overwrite the model output —
they are a separate table joined on `(scan_id, model_version)`.

---

## 4. Cloud compute — the actual data path

**What gets uploaded:** the warm tier for one cohort. **25 GiB, once.**

```
local:  cold archive (582 GB, external drive)
             |  cache builder  (runs locally, supervised, one time)
             v
        warm cache (25 GiB, internal SSD)
             |  pack into WebDataset shards + upload
             v
cloud:  persistent volume / object storage (25 GiB)
             |  training container mounts it
             v
        checkpoints + metrics  --sync-->  MLflow (local or Neon-backed)
```

**What never goes to the cloud:** the 582 GB cold archive. There is no reason to send it — the model
cannot consume it directly anyway.

**Cost sketch:** RTX 4090 at $0.34–0.69/hr; a 24k-step run plausibly 1–3 hours → **$1–3 per run**.
Persistent volume for 25 GiB ≈ $2–3/month. A disciplined 60-run capstone lands around **$60–180**.

**Traps, pre-registered:**
1. **Keep fp32.** Enabling AMP on CUDA changes a variable and silently breaks comparability with every
   MPS result to date.
2. **Re-run the baseline on the new hardware.** Seed 42 does not reproduce across architectures.
   EXP-08 already taught this lesson at n=20 vs n=40; hardware is part of "matched."
3. **Avoid spot instances until `--resume` is verified end-to-end.** Preemption plus an unproven
   resume path is how EXP-12 was lost the first time.
4. **Check the Windows/CUDA laptop first** — free, unpreemptable, no upload.

---

## 5. At scale — what changes and what does not

| dimension | today | capstone target | breaks at |
|---|---|---|---|
| cold archive | 382 GB | ~582 GB | fine on a 2 TB drive |
| warm cache | 13.8 GiB | 25–116 GiB | fine on internal SSD |
| Postgres rows | — | ~12k scans, ~250k prediction rows | **nowhere near** any tier limit |
| training cohort | 1,412 | 2,568 (EXP-27) | compute-bound, not storage-bound |
| runs per day | 1 (overnight) | 2–3 (cloud) | budget, not technology |

**The honest observation: nothing in this architecture is stressed by our scale.** 12,000 scans and
250,000 prediction rows is a small database. The design is not there to survive volume — it is there
to make a specific class of error impossible. Every contract above exists because we already made
that mistake once and caught it in an audit rather than in a result.

That is the argument to make at defense: **not "this scales," but "this is auditable."**

---

## 6. Sequencing — do not rewrite storage first

The existing pipeline works and produced every result we have. The storage layer goes in **behind
the current interfaces**, one contract at a time, each with a regression test:

1. **C1 + C2** (index + cohorts in Postgres) — highest value, lowest risk, prevents the leak class.
   Splits become queries; keep exporting `.txt` files so nothing downstream changes.
2. **C3 + C4** (cache with config-hash key) — gated on the bit-identical test. Unlocks cloud + speed.
3. **C5 + C6** (config embedded in checkpoint, shared preprocessing path) — small, high value.
4. **C7 + C8** (predictions and review decisions in the DB) — enables the UI and the gate analysis.

**Profile before optimizing:** nobody has measured whether the ~0.3 it/s on MPS is compute-bound or
I/O-bound. If it is I/O — gunzip + resample on every sample — the local warm cache alone may deliver
a large multiple with no cloud at all. That measurement decides the order of items 2 and 3, and it is
half a day of work.
