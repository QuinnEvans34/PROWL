# Stage 2 contracts and candidate proposal results

October 1, 2026 — D-315 complete. Separate dual-target purpose/cohort records work on invented
evidence; the retained-metadata proposal selects 8 train and 4 development-validation candidates.
**Real Stage 2 qualifications: zero.** No source files were inspected, no arrays read, no real cohort
frozen, no model executed and no training run prepared or launched.

## What is now implemented

New `segmenter_qualification_v1.py` and `segmenter_cohort_v1.py` bind both pancreas/lesion annotations,
CT and target identities, reviewed check receipts, exact purposes, permanent original roles and all
applicable issues. A pure resolver rechecks those dependencies before returning three-input
descriptors. Negative supervision needs an explicit case-bound reviewed reference standard; empty
or missing masks alone cannot supply it. Difficult cases remain supported and held cases cannot
silently enter a consumed cohort.

The old source snapshot schema covers CT/pancreas only. It remains unchanged; a new pinned lesion-
inventory sidecar supplies the third input's evidence. Three new schemas cover this sidecar and
the new qualification/cohort records. No shared manifest migration, source activation or global
consumer change. [Contract details](../data/STAGE2-PURPOSE-CONTRACTS-2026-10-01.md).

## Retained evidence and limits

The D-294 staging plan pins the same manifest and 113/40 localizer cohorts. D-289's candidate receipt
pins the 128/48 proposal and original role split bytes. The legacy manifest CSV is independently
pinned and read only for an allowlist of case ID, lesion-presence hint and lesion-count hint; its
old absolute paths, reports and patient identifiers are neither copied nor resolved.

The retained manifest contains five old quarantined lesion records: 3/26/31 have nonempty audited
masks, 78/266 have empty masks. None has allowed uses. Current source-snapshot inventory does not
establish per-case lesion availability across the broader cohort. The expected sibling filename is
therefore an **unobserved path proposal**, not a present/qualified file or a byte/read budget.

All 176 broad candidates remain in the new metadata ledger: 153 localizer-qualified, 23 held
(15 CT units / 8 empty pancreas references). All remain pending Stage 2 qualification. The historical
31/78/266 contexts outside that broad candidate selection are identified separately, not erased.
Original protection accounting remains 7,200 train / 1,800 validation / 901 publisher-test. Publisher-
test images/labels were not opened. Biological study-as-subject uniqueness remains unverified.

Among the currently qualified localizer members, legacy hints indicate 16 train and only 2
validation lesion positives. These are unverified target hints, not newly established positives or
negatives. The small slice can support engineering/learning diagnostics after qualification, but
two validation hints cannot support a stable lesion-performance estimate or final baseline. Broader
lesion-positive validation must be separately proposed from permanent original roles later.

## Exact 8/4 candidate proposal

Selection preceded new source observations. Training proposes six nonempty legacy hints and two
other candidates; validation includes both positive hints plus two other candidates. The deterministic
selection retains known challenges, protocol variation and larger grids. No case is filtered on model
performance, noise, coverage quality or expected ease. A held result stays visible; no automatic refill.

|Role|PanTS case|Descriptive protocol / slice stratum|Legacy lesion count hint|Reason|
|---|---:|---|---:|---|
|Train|3|Venous / >5 mm|1,055|Retained nonempty lesion audit, currently quarantined|
|Train|26|Non-contrast / >2–5 mm|7,244|Retained scaled-binary lesion audit, currently quarantined|
|Train|6110|Arterial / ≤2 mm|0|Short coverage and tiny pancreas reference; zero is not verified negative|
|Train|2973|Non-contrast / >5 mm|124|Smallest remaining positive count hint; fidelity challenge|
|Train|2232|Arterial / >2–5 mm|3,867|Positive-hint protocol variation|
|Train|6238|Venous / ≤2 mm|7,412|Positive-hint thin-slice variation; 40.55M native voxels|
|Train|5821|Arterial / >2–5 mm|3,399|Largest remaining positive-hint grid, 38.29M voxels|
|Train|4965|Delayed / ≤2 mm|0|Protocol and retained coverage variation; zero is unverified|
|Validation|2514|Venous / >2–5 mm|1,880|One of both current positive hints|
|Validation|5641|Non-contrast / ≤2 mm|47,190|Other positive hint; 46.22M native voxels|
|Validation|2727|Arterial / ≤2 mm|0|Single-boundary-slice tiny pancreas challenge; zero is unverified|
|Validation|7265|Delayed / ≤2 mm|0|Delayed/thin protocol variation; zero is unverified|

The two largest selected training grids are 6238 and 5821; the rule for 5821 is largest *remaining*
positive hint after earlier diversity selections. Protocol/slice strata are descriptive retained
metadata, not new header measurements. Counts in this table are legacy hints, not current audited
lesion sizes. Zero-hint cases may remain held after investigation; the first qualified subset might
be positive-only. It must then be labeled accordingly and cannot report negative specificity.

## Verification and resources

47 new targeted tests pass; full native suite **1,836 passes**, two existing torch.jit warnings.
Checks cover independent expected outcomes, adversarial evidence/identity/policy substitutions,
missing annotation/permission, unknown units, wrong mapping, false negative claims, malformed geometry,
holds/exclusion/difficulty, wrong role, shortage/refill refusal and deterministic candidate selection.
No dependency changes. The native suite uses the established process-inspection permission needed
by existing supervisor tests; elapsed 62.61 seconds.

The metadata job read 31,571,267 bytes of pinned retained metadata, took 1.307 seconds and peaked
at 349,749,248 bytes / 0.326 GiB RSS. Limits 300 s / 2 GiB / 64 MiB input / 10 MiB output passed.
Its process blocks source-array/model/external-root opens. Original-source stat calls and array reads
are zero. An independent fresh process regenerated byte-identical candidate/hold accounting and
the exact proposal. Final input and implementation hashes match. Four shared data modules and two
old schemas match their retained D-294 hashes, proving this slice did not widen localizer behavior.

Early test attempts are retained. The first exposed the two-kind source inventory restriction;
the second exposed two fixture probes that needed to target the sidecar and missing annotation
through the production API. Fixes preserved the old contract and strengthened the probes. No
failed preparation created real permissions or a published cohort.

## Evidence

New local directory: `outputs/prowl/STAGE2-METADATA-20261001`. Includes metadata ledger/proposal,
input pins, new/shared implementation pins, targeted attempts, full native log, fresh replay and
final checks. This is local retained evidence, not a new backup or Git-publication claim.

|Record|SHA-256|
|---|---|
|Inventory / candidate proposal|`2f38464f4fd6efe8235b5471bf2f46466ab7ce13d17e1c7ccff2c7876997aab4`|
|Metadata receipt|`e83c27e10c9ba245b55d2c741b0d120fe3acbb2915da2c5c09eea0fb5fc3a28b`|
|Review receipt, 15 files / 483,620 bytes|`b25f3e204b4dec4c149b3f2e26e856a7cb104e30acb8226d814dbbe685e5a0a8`|

## Next bounded step

Prepare/test/freeze M1 in the [source-verification proposal](SEGMENTER-SOURCE-VERIFICATION-PROPOSAL-2026-10-01.md):
observe the exact 12 expected lesion files and 24 companions under registered roots, with no payload
reads. That establishes actual availability/sizes for a fresh header/content request. Then qualify
the reviewed targets, preserve any holds, freeze the consumed subset and build shared ROI geometry.
The larger [Stage 2 packet](STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md) remains the path through
synthetic learning, recovery, real zero-update profiling and one concrete smoke request.

The component-reference diagnostic remains a separate proposal; no original reference reads were
issued here. No new training, promotion, source rewrites, real eligibility changes, retrieval edits,
Git publication or Claude dispatch. Existing 153 members/23 holds and all prior experiments remain.
