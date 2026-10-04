# Next bounded slice: lesion content and native alignment

**Status October1 D-317:** four-case pilot completed and reviewed; [results](SEGMENTER-CONTENT-PILOT-RESULTS-2026-10-01.md).
Pilot request consumed; [remaining-eight packet](SEGMENTER-CONTENT-CONTINUATION-PACKET-2026-10-01.md) proposed, not frozen/launched.
Earlier prospective definitions below are retained. No real Stage2 permissions or training.

October 1, 2026, after D-316's M1/M2 source verification. Implementation proposal, not a frozen source-array request, qualification, cohort or training authorization.

## Evidence and fixed candidates

All36 proposed files exist and pass compressed identity verification. All12 lesion headers match retained positively qualified mm CT geometry. Five lesion files have signed-byte scaling; six declare unknown spatial units, supported only through their exact matching qualified mm CT grid. Headers do not establish foreground or negative status.

Exact machine-readable proposal: `outputs/prowl/SEGMENTER-SOURCE-REVIEW-20261001/m3-content-scope-proposal.json`, SHA-256 `33853ca3eb106f55858a63e1d24ab57aa7c746b57bcf48b61b2613167f0000cb`. It binds M1/M2 receipts, every path/role/hash/observation, measured lesion headers and hash-bound retained companion content metadata. All24 companion dtype/expanded-size records were recovered from D-294 evidence with record hashes and exact source-byte matches. No extra source headers or arrays were read to size this proposal.

Keep all12 candidates and original roles. Start with a four-case engineering pilot: train3/26/2973 and validation5641. This exercises previously audited labels, scaled encoding, the 124-voxel legacy hint and the largest native grid. The remaining eight are train6110/2232/6238/5821/4965 and validation2514/2727/7265. Review the four pilot sheets before separately freezing the continuation. No substitution or qualification from the selection.

## Bounded reads and resource qualification

|Stage|Cases/files|Full compressed hash pass|Full compressed decode pass|Expanded NIfTI bytes|
|---|---:|---:|---:|---:|
|Pilot|4/12|92,711,337|92,711,337|317,547,616|
|Continuation|8/24|183,291,323|183,291,323|635,508,776|
|Total proposal|12/36|276,002,660|276,002,660|953,056,392|

Each selected CT/pancreas/lesion is opened for a fresh hash pass, then one complete bounded gzip decode pass; account both. Maximum aggregate compressed allowance across both jobs is 552,005,320 bytes. No hidden nibabel proxy rereads or separate display reads; views use arrays already loaded in the serial case worker. Offsets are352 in measured lesion/retained companion records. CTs are int16; both targets are int8. Do not assume these beyond the frozen bytes; validate actual streamed headers before allocation.

Largest case5641 is46,219,264 voxels with184,878,112 total expanded bytes across its three files; this is storage payload, not a peak-memory estimate. Before the pilot, profile a synthetic case of this exact shape using dense, empty, fragmented and boundary-contact targets plus scaled signed-byte decoding. Measure the actual checker, connected-component path, overlap/bounds and plotting. Proposed ceilings per source batch:900seconds,8GiB CPU RSS,64MiB outputs, serial cases. No GPU/model or retained tensor cache. If the synthetic path does not fit, revise the implementation/budget and preserve the failed profile before freezing a source request.

## Owned implementation and failure rules

Add a new versioned reader/runner and tests. Reuse pure strict binary policy and secure descriptor utilities where appropriate; leave old consumers/schemas unchanged. Verify registered source mount and root identities before/after each job. Freeze code/runtime, capability and predecessor receipt pins; source files remain read-only. Require exact source observations before/after each open and compressed hashes matching M2. Enforce read caps before reads and expanded caps before allocation. Validate complete gzip EOF/CRC, exact expected expanded size and streamed header identity; hashing alone is not a gzip integrity check.

Use an exclusive consumption marker and one-shot fixed output identity. Failed attempts remain consumed with partial-case/read counters; no fallback path, source repair, retry of consumed request or omitted failure. Complete the request's case ledger even for held outcomes when safe; stop globally on volume identity/resource/request failure. Completion and receipt are written last. Test missing/replaced/symlinked files, hash mismatch, partial reads, invalid gzip CRC/trailing data, oversized expansion, changed headers, wrong role, omitted/duplicate inputs, timeout/memory/output failure and interruption.

## Content rules

Decode semantic values after NIfTI scaling using `pants-semantic-binary-atol1e-6-v1`, absolute1e-6 and relative0. Never generic `>0`, raw signed-byte threshold, clipping, inferred rounding or mask rewriting. Record stored value/count pairs, effective scaling and semantic endpoint residuals. Require finite CT/target values and the exact three-way native grid. Apply the same approved binary rule to both targets.

For each lesion record foreground counts, all26-connected components and sizes, source-index/world bounds, source-boundary contacts, pancreas overlap and lesion-outside-pancreas counts. Preserve all components. Outside-pancreas pixels are an observation requiring review, not automatic deletion or a reason to enlarge a pancreas-only ROI. Record empty masks as unknown lesion-reference status; do not infer verified negatives from a file, compressed size, legacy hint or empty array. Compare legacy counts only as discrepancies, not as truth or acceptance criteria.

No lesion-derived training box, class-assembly promotion or model input is produced here. Subsequent shared geometry fixes the pancreas-only box first and records excluded lesion components afterward. Tiny lesions need native fidelity checks; 2mm localizer displays are insufficient by themselves.

## Native alignment and review

Use source-grid CT and both decoded targets already in memory. Generate physical-aspect axial/coronal/sagittal overlays with orientation/coordinates/spacing and separate pancreas/lesion contours. Include lesion first/middle/last occupied slices, maximum lesion-area views and the planes needed to show disconnected components; deduplicate and cap panels explicitly. For empty lesion outcomes, show pancreas/FOV context and prominently record unknown target status. Preserve tiny targets with a labeled native-detail inset alongside full-FOV context; display magnification does not alter masks. Bound CT display window and panel sizes in the recipe.

Reviewer records are technical geometry/alignment observations, not diagnoses, expert lesion adjudication or annotation-completeness certification. Inspect every requested pilot case and record any uncertainty. No model performance filtering, deleting difficult cases or silently replenishing the list.

## Exit and subsequent work

Publish immutable diagnostic content/alignment evidence only, with fresh-process receipt replay and unchanged source/code pins. Reconcile all12 candidates after the separately frozen continuation. Then propose paired lesion-inventory records, explicit new purpose dispositions/qualification or holds, preserved historical annotation transitions, and a frozen consumed subset. Permission/cohort publication is its own bounded slice. Follow with shared physical ROI geometry/fidelity, fresh three-class synthetic learning/recovery, zero-update resource qualification and an exact short training request. Positive-only diagnostics cannot establish negative specificity or formal autonomous/generalization performance.
