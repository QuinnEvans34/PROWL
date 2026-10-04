# Expanded content qualification — exact batch proposal after D-291

**Planning only. No content requests are frozen or launched.** The accompanying
`LOCALIZER-EXPANSION-V2-CONTENT-BATCHES-2026-09-29.json` assigns all148 new candidates to15 exact
batches and preserves their selected role, inventory observations and measured header evidence.
SHA-256: `52eee153491981d57a3820536c7ea5c90c1f1fa8fdf6bda50ff12d1e7b837483`.

## Scope and resource accounting

Ten standard batches contain up to16 cases each (143 cases total). Five cases above the existing
64M-voxel cap each get a separate proposed diagnostic batch:1935,3206,6822,8937 (train),6186
(validation). This separates resource testing, not scientific eligibility. All candidates remain in
accounting; no replacements. Original28 candidates/evidence and held6350 remain unchanged.

Each standard batch preserves the old evidence-job limits:20minutes,16GiB RSS,1GiB cumulative
compressed/4GiB decompressed,128MiB compressed and512MiB decompressed per file,64M voxels,
256MiB evidence,100GiB internal free floor. Process one pair at a time; no all-batch RAM cache.
Largest proposed batch estimate:574.0MB compressed and1.55GB expanded with1MiB/file offset
allowance. Actual gzip EOF/CRC reads remain capped; header estimates do not prove those sizes or RSS.

Large singletons propose an explicit96M-voxel **diagnostic-only** cap, enough for the observed92.89M
maximum. This scope is not active. Test declared-size refusal, bounded decoding and measured memory
before consuming them. Keep all other budgets unchanged; stop if these cannot safely fit. Do not
raise the current16/11 model-input or preprocessing limits by modifying their constants.

## Implementation and evidence gates

1. Add a separate versioned batch consumer. Validate selected candidate identity, header receipt,
   batch-plan digest, exact roles/pairs and registered source mount. Recheck inode/stat identity and
   pin source/environment/plan in single-use requests. Changing a request creates a new record.
2. Test duplicate/substituted/held/wrong-role input refusal, every resource limit, malformed gzip,
   declared array size, semantic scaling and shape/affine mismatch. Retain failures and partial work.
3. Execute the first standard batch as a pilot. Measure actual compressed/decompressed bytes,
   elapsed time, peak memory and evidence size before continuing the remaining standard batches.
   Any continuation has its own frozen request; no automatic retry after a failure.
4. For every pair, preserve hashes and gzip CRC/EOF evidence, CT finiteness, geometry, units,
   strict-binary decoding evidence and visible-target properties. Generate bounded CT/reference
   alignment sheets. Review every consumed case; record noise, partial coverage and boundary contact
   without treating difficulty as automatic exclusion or promising whole-organ coverage.
5. Fourteen new CTs lack declared units. They remain candidates and can receive diagnostic evidence,
   but have no positive physical-geometry qualification until supported units evidence is recorded.
   Do not infer mm from typical spacing, visual plausibility, metadata stratum or model behavior.
   The141 masks lacking units need case-specific matching-grid evidence under the established
   CT-grounded interpretation; a mm CT header alone is insufficient without content/alignment checks.
6. Reconcile all15 batch outcomes with retained28 candidates. Preserve every old issue and each
   new hold. Only positively supported purpose decisions can enter new immutable training/evaluation
   cohorts. Independently resolve/replay them before building a versioned model consumer.

No candidate is trained on by this plan. Release terms/publisher correspondence, biological patient
uniqueness and final-test boundaries retain their existing limitations. No lesion targets, PANORAMA,
retrieval edits, new dependencies or Git publication are part of these jobs.
