# Expanded content continuation — D-293 results

**All nine standard batches and five larger singleton batches completed.** Exactly132 additional
candidates/264 files were processed. With the16-case pilot, all148 new candidates now have content
evidence; with the retained28, all176 selected identities are reconciled without replacement.
**Training eligibility and the existing16/11 runtime are unchanged.**

## Findings and accounting

Every consumed CT is finite, and all CT/target native grids match their pinned header evidence.
All files passed identity checks, gzip EOF/CRC and content-hash recording. New nonempty targets
have semantic values exactly0 and1; eight are entirely zero. No unresolved binary encoding occurred.
No exact compressed-CT hash duplicates were found across all176 candidates. This does not establish
biological patient uniqueness or exclude identical voxels encoded in different files.

| Protected role | Candidates preserved | No automated content hold | Unknown CT units | Empty pancreas reference |
|---|---:|---:|---:|---:|
|Training|128|113|9|6|
|Development validation|48|40|6|2|
|Total|176|153|15|8|

These hold categories do not overlap. **153 is a content-screen count, not a positively qualified
or executable cohort count.** Source-use scope, review findings, explicit purpose decisions, issue
preservation and immutable publication remain required. Old6350 accounts for one validation unit
hold; all earlier evidence/holds remain preserved. No inference from typical spacing or visual
appearance resolved units, and no source header or label was rewritten.

Empty references, all retained:
- Training:1783,2488,2691,2694,4025,7082.
- Development validation:7612,8940.

New CT unit questions, all retained:
- Training:2048,4640,5117,5507,6154,6712,7509,8812,8831.
- Development validation:754,3179,5663,6479,8477; plus old6350.

Empty references are unresolved use cases, not established corrupt masks or trusted negatives.
They need scan-coverage/source evidence before a purpose decision. No candidate was replaced to
restore a desired training count. The five larger cases remain in evidence and were not excluded.

## Visual review and limitations

All124 available continuation alignment sheets were reviewed as paired plain/overlay overviews,
with up to five distinct target-related planes (the three axial slots can repeat). The eight empty
references have no target-centered sheet and remain explicitly unreviewed for coverage. The previous
pilot's16 and original28 reviews are retained separately. This is limited engineering review, not
all-slice inspection, contour certification, independent expert acceptance or diagnosis.

Overviews retain every panel at half sheet width; cases5190,5507,2727,8988 and all five larger cases
were additionally inspected at full sheet resolution. No gross image/target displacement was flagged
on reviewed planes. Noise, sparse references, nonaxial/coarse reformats and restricted scan coverage
are not reasons for silent exclusion. The review records explicit questions where evidence is limited:

- **2727:** reference lies on the first axial slice at the inferior boundary; whole-organ coverage
  is unsupported. Three axial views are the same slice.
- **5190:** sparse reference on noisy CT; fuller reference-coverage review is needed before treating
  it as a complete pancreas target.
- **8988:** severe noise and limited upper-abdominal coverage; preserve visible-reference scope.
- **4359/6110:** short or limited scan coverage; preserve that observation.
- **5663:** lateral coverage limitation/boundary contact, with CT units already unresolved.
- **5507:** unusual positioning/projection and streaks; the existing unit hold remains.

Retained mask bounds/header orientations identify source-face contact in32/148 new candidates,
including27 in this continuation, and34/176 overall. These are coverage observations, not new blanket
exclusions. Exact per-case faces, hashes, notes and review status are in the reconciliation record.

## Resource verification

The96M-voxel synthetic allocation/decode rehearsal passed in1.91seconds at3.48GiB RSS. It exercised
gzip decoding, float CT/target materialization, binary decoding and foreground coordinate work with
zero source reads. It is not a worst-case anatomy/compression benchmark. Each larger request pins
that receipt and the exact executing source; model input/preprocessing limits remain64M.

Rehearsal: `outputs/prowl/large-content-rehearsal-d9951cff-2645-49a5-99c0-6b9c2f319bd2.json`;
SHA-256 `50212a896ee2145ab2f440737d2515e778ddea3fe11c1ebfd3cad51633a11bd8`.

All14 real jobs stayed within20minutes/16GiB/1GiB compressed/4GiB expanded/256MiB evidence each.
Their measured runtime sums to246.59seconds (excluding preparation/review); highest RSS5.20GiB.
Total continuation reads:4,247,297,049compressed and10,800,227,238expanded bytes.

| Batch | Role | Cases | Seconds | Peak GiB | Receipt SHA-256 |
|---|---|---:|---:|---:|---|
|batch-02|train|16|29.38|3.74|`d4baf94797e2113b7ccb180cf2a3c1358633420f2ada7d32cedf4dfd45e76732`|
|batch-03|train|16|30.64|4.26|`9f0939349f2643aef5ed3b8a02a5b2e60c391308a27a071bf25bb50b7aeba020`|
|batch-04|train|16|22.02|4.61|`e7b3eea9a2284cedabe7df8cbd51b64e044ebd4c19469439c4eed2169fb64068`|
|batch-05|train|16|26.68|4.37|`980a55ba44489ce0d11df9c7e2cd779042e5d3dd10153719d483dda990f11440`|
|batch-06|train|16|33.78|5.20|`f4f7d1c6b255ed9c363215bb16f8e1c47045afbee3ecddcc68b7c74e1327ac44`|
|batch-07|train|12|18.36|3.61|`4be7bff916138241147667fda5b0472c80c4115c7914ed273cc285481110b826`|
|batch-08|train|1|11.78|3.01|`46905a9dcc00c0209019df132d644939e02c3ab726653c1fa8a87153add1f2ee`|
|batch-09|train|1|7.02|3.09|`e8ed76f813b8bdac0e440679e547d5416c1845887bed00dc6c644eb8caefe310`|
|batch-10|train|1|5.19|3.92|`0240fe6eecdd113e0d250e70052f0664b56aa49d9786a8b0bf2f66d7af61eafe`|
|batch-11|train|1|9.77|4.00|`90383679cc2e48a5f8fa3ecee699e514c8ed66af0fd056c69c93cf1f3cd31cd6`|
|batch-12|validation|16|16.51|3.13|`fdd32d5bb8a78907ee31c55a9ba513626b8b9961b8af3968595f107907bc9431`|
|batch-13|validation|16|24.94|3.22|`86b373a2bdc7b7cdee4f4a7bd8d3d6946d94d4f0080866b046dc7ccfca6c12e0`|
|batch-14|validation|3|3.83|2.02|`1d24dd17ec28bdc78226cbfe6cdc8f632a54d4fbf4e132325f46efe63bbb9f25`|
|batch-15|validation|1|6.70|2.85|`ce85e6c8c29b2ff55aded0df15ea39546bb923e27392aa2b8968307917e08a79`|

There were no failed jobs or automatic retries. Every request is consumed; do not rerun it.
The large cases1935,3206,6822,8937 and6186 all completed within the unchanged memory/byte/time
budgets; their96M cap applies to this diagnostic, not the existing model consumer.

## Verification and evidence

Twenty-two new tests validate all14 scopes, reject the consumed pilot/unknown batches, candidate/
header/role substitutions and changed limits, and require the large-case receipt. Existing decoding,
gzip, source identity and resource tests remain passing. **1,264 native tests passed**, two existing
upstream warnings,31.97seconds, before freezing requests. Source/environment were unchanged during
execution. No model inference, training, new dependency, source mutation or Git publication occurred.

Queue indices retain each request path/hash and result path/receipt:
- `outputs/prowl/content-continuation-queue-dedaf4c9-3d3a-44e3-b7b3-26fb56f96633/complete.json`
- `outputs/prowl/content-continuation-queue-06c1f8bc-4838-40be-ae57-4d2a7c1466c7/complete.json`

Derived review and reconciliation: `outputs/prowl/content-continuation-review-20260929`.
All15 new-candidate content receipts plus the prior28-case receipt were verified member-by-member.
Candidate IDs exactly equal the frozen128/48 selection and retain protected roles. The reconciliation
record covers all176 identities, all holds, review/image hashes, boundary observations and duplicate
checking. Original packages retain their historical `visual_review: pending`; the separate review
record completes this overview step without rewriting them.

## Next implementation

1. Record purpose-specific qualifications for candidates supported by content and scoped review
   evidence; preserve all23 unresolved cases and every historical issue. Address flagged visible-
   reference questions explicitly rather than treating153 as a promised cohort size.
2. Publish/replay new immutable train/development-validation cohorts and keep candidate-versus-
   executable accounting visible. Unresolved cases remain available for later justified experiments.
3. Implement/profile a separately versioned consumer, including the five larger cases if qualified.
   Revalidate preprocessing/geometry and cache/streaming costs before freezing a new training run.

Unit and empty-reference investigations can proceed separately; they need not prevent supported
cases from advancing. No new training request is prepared, and no eligibility changed in D-293.
