# Four-case segmenter content/alignment pilot — D-317

October 1, 2026. **All four cases passed technical content checks; all four native sheets reviewed.** The reader, largest-case resource rehearsal and exact source execution are complete. No real Stage2 qualifications, frozen segmenter cohort or training.

## What the data showed

|Case|Role|Lesion voxels|26-connected components|Outside pancreas mask|Within retained pancreas-only box|
|---|---|---:|---:|---:|---|
|3|train|1,055|1|0 (0%)|Entire extent|
|26|train|7,244|1|431 (5.95%)|Entire extent|
|2973|train|124|1|3 (2.42%)|Entire extent|
|5641|validation|47,190|1|47,190 (100%)|Entire extent|

All counts match the retained legacy hints, now independently measured from current bytes under the approved semantic binary rule. All twelve files pass fresh hashes, complete gzip EOF/CRC, exact expanded lengths, header/data identity and native geometry. CT/targets are finite; both masks are supported binary values after NIfTI scaling. No lesion touches the acquired source boundary in this pilot. All components and outside-pancreas pixels are retained unchanged.

Case2973 has a124-voxel lesion occupying one7.5mm native slice. Its native detail panel shows the small mask alongside the pancreas boundary. This is a target-fidelity challenge to carry into the shared geometry/resampling tests, not a filter criterion.

**Case5641 has disjoint pancreas/lesion masks.** Selected native views show adjacent/complementary-looking contours; this is a technical visual observation, not expert annotation adjudication or a confirmed publisher convention. The retained pancreas-only bounds and freshly verified lesion bounds establish complete bounding-box containment, despite zero voxel overlap. Do not confuse mask overlap with containment in a localization region; do not automatically reject this candidate, clip the lesion, merge the targets or enlarge the ROI using the lesion. Source annotation relationship still needs a recorded interpretation before purpose qualification.

The containment check used only hash-bound retained pancreas content evidence and the new pilot's coordinate records. It read no additional source arrays. In canonical RAS, case5641 pancreas bounds are [120..301,241..318,0..121] and lesion bounds [252..299,264..308,5..72]. This is existing bounding-box evidence, not adoption of a new training ROI recipe or a tensor round-trip result.

## Native sheet review

All generated panels on all four sheets were inspected: axial/orthogonal full-FOV views and native-detail insets, with physical aspect, RAS axes, CT display window and separate pancreas/lesion outlines. No gross display translation or axis mismatch was observed. Case26 and2973 boundary differences remain explicit observations. Case5641's source annotation relationship remains open. Reviews do not certify lesion diagnosis, complete annotation, reader agreement or clinical acceptability.

The immutable source execution retains `visual_review=pending`; the separate append-only review links its receipt and each sheet hash. Review SHA `328b501b2c0e627f9cde2ae47b65e4be0f8833bbda24159a5fca507266e4701e`. Retained-box check SHA `dcd1ee85b9886edf83595cd3cd7315b80443b518b5fd86a4ca2ff47d18eefec1`.

Sheets are at `outputs/prowl/SEGMENTER-CONTENT-PILOT-20261001/PanTS_########.png`. The single-slice2973 and disjoint-mask5641 sheets are useful next-phase fixtures. Original files remain read-only; no diagnostic array cache or model inputs were published.

## Implementation, tests and resource qualification

New pure diagnostic helper `src/data/segmenter_content_v1.py` and supervised runner `scripts/diagnostics/segmenter_content_pilot.py`; new `tests/test_segmenter_content.py`. Old source/localizer/segmenter qualification consumers and schemas remain unchanged. The reader checks byte/allocation caps before operations, validates the header before allocating, enforces one gzip member/exact payload, hashes both passes and never invokes a nibabel array proxy. Labels use `pants-semantic-binary-atol1e-6-v1` after scaling, with stored/semantic counts and endpoint residuals.

Native-coordinate components use26-connectivity and preserve every component. More than4,096 component records produces an explicit resource hold; records are never silently truncated. Native display reorientation has independent world-coordinate tests for flipped/permuted axes, and detail magnification does not alter targets. Display planes cap at18; any components needing further planes are reported. None were unshown in these four cases.

**41 new checks;1,910 native tests pass**, two existing torch.jit warnings,65.16seconds. Fault checks include gzip corruption/truncation/trailing members, source/hash/header mismatch, budgets rejected before reads, scaled/nonfinite/unsupported values, memory layouts, components/empty semantics, source roles/omissions/duplicates, orientation and supervised timeout/memory/interruption. First targeted run had one synthetic-header-factory spacing inconsistency (sform2mm vs default pixdim1mm); fixed before any profiling/source request. All attempts preserved.

The actual512×434×208 synthetic reader/analyzer/render path passed dense, empty,392-component fragmented and boundary-contact targets in15.4059seconds,890,830,848bytes peakRSS (0.830GiB). It decoded184,878,112expanded bytes per synthetic case, including scaled signed-byte labels, without source reads or model work. Rehearsal receipt `14eaa7e08cea3c0f624d58e9d0b67a012472ba5a5a3ab6f9aa031fa68bd31ae6`.

## Exact source execution

Request `outputs/prowl/SEGMENTER-CONTENT-PILOT-20261001/request.json`, SHA `b27b26ab73f3c2fd2015604de2884f70dbec2e9c6e9decd0e686c5a039e38fe8`, consumed once. Explicit fresh source-array capability; no M1/M2 request reused. Native volume UUID/root and pre/post file identities verified. Child process supervised during native allocations and computation; interruption/failure records retain read reservations and actual completed counts.

Actual worker6.7766seconds,1,034,420,224bytes peakRSS (0.963GiB). Read92,711,337compressed hash bytes plus92,711,337compressed decode bytes,317,547,616expanded bytes, exactly the frozen allowances. Limits900seconds/8GiB/64MiB output; all twelve original arrays decoded once, overlays use those in-memory arrays. No further source reads for review or metadata box checks.

Complete source receipt `2f972c5c8136c60630ba3559b7435b84c79af0cec7689c190ebfd6b28ce26d7f`. Fresh-process receipt/member/source/runtime/request verification and append-only technical review are preserved separately in `outputs/prowl/SEGMENTER-CONTENT-PILOT-REVIEW-20261001`. No pending pilot run or permission to rerun its consumed request.

## Next bounded work

[Eight-case continuation packet](SEGMENTER-CONTENT-CONTINUATION-PACKET-2026-10-01.md): keep the pilot consumer's exact scope, implement/test a separate24-file consumer/request, then apply the same content/views checks to the remaining five train/three validation cases. Proposed full hash+decode366,582,646compressed bytes,635,508,776expanded bytes. No continuation source request is frozen or launched in D-317.

Then reconcile all twelve candidates and propose explicit new lesion-purpose qualifications/holds and preserved annotation transitions. Positive-only use requires clear labeling; empty masks stay unknown without an explicit negative-reference standard. Real permissions/cohort publication remain a separate slice. Shared pancreas-only ROI geometry must retain the2973 single-slice challenge and5641 annotation distinction, followed by fresh three-class synthetic learning/recovery, zero-update MPS profile and an exact short training request. Current153 localizer members/23holds,176 candidates and original7200/1800/901 membership remain unchanged.

Final sealed review receipt `b4cc90d56a5ecef5c47353d77726b136cf17776b5e4b3b3ef525e492db58999d`:19members/91,382bytes, including code snapshots, every test attempt, qualification/execution logs, append-only technical review and independently replayed retained-box check. Source package38members/2,851,981bytes; synthetic profile13members/244,293bytes. All source/code/runtime/request/member pins verified in a fresh process. No source arrays reopened for final checks.
