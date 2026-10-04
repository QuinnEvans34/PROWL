# CAP-EXP-006 probability audit — D-290 results

**The fixed thresholds do not rescue validation localization.** Lowering the foreground threshold
from0.50 to0.01 increases mean processed validation recall from46.1% to60.5%, while Dice decreases
and false foreground/crop extent increase. This supports prioritizing more varied training exposure
before another sustained run. It does not prove data breadth is the sole cause or guarantee expansion
will fix it. No threshold or production ROI policy is selected.

## Verified execution

All27 cases reproduced the saved terminal processed confusion counts and boxes exactly, and all27
restored native binary masks were exactly equal to the saved exports. Model parameter hashes match
before/after; step remains2400, optimizer updates0. Existing16 train/11 validation only;54 qualified
source files,512MiB cache cap (actual191.5MiB). No new candidates, lesion labels or final-test data
were consumed. No source rewriting, dependency changes or Git publication.

The supervised audit completed in241.37seconds, peakRSS8.11GiB, within20minutes/16GiB. Full native
suite before freeze: **1,220 passed**, two existing upstream warnings,31.74seconds. Nine new tests
cover invalid probabilities, ties, empty masks/subsets, role binding and strict metric parity; existing
source-geometry/checkpoint/role tests remain passing. Original inference dependencies were unchanged;
only the prior additive executor reporting change required the recorded compatibility check.

## All fixed development-validation probes

Recall/Dice and reference coverage below are measured on the processed grid. Crop size uses the
same processed box mapped to acquired source volume, not the padded tensor denominator.
The combined screen requires processed-reference coverage≥99.5% and source crop≤25%; it is a
mixed-grid engineering diagnostic, **not a native-reference or production ROI acceptance result**.
The native-reference audit from D-288 remains separately preserved.

| Operating point | Mean Dice | Mean recall | Minimum recall | Mean predicted/reference volume | Coverage count | Source-size count | Combined screen |
|---|---:|---:|---:|---:|---:|---:|---:|
|argmax|0.4529|46.1%|25.7%|1.07×|4/11|8/11|2/11|
|0.5|0.4529|46.1%|25.7%|1.07×|4/11|8/11|2/11|
|0.25|0.4528|49.0%|28.2%|1.22×|4/11|8/11|2/11|
|0.1|0.4509|52.2%|31.8%|1.40×|4/11|8/11|2/11|
|0.05|0.4466|54.6%|34.0%|1.55×|6/11|8/11|4/11|
|0.01|0.4275|60.5%|40.5%|2.03×|6/11|7/11|3/11|

The0.05 probe gives4/11 combined screens versus2/11 at baseline;0.01 falls to3/11. Those partial
improvements are reported, not promoted. The largest0.01 validation crop occupies58.0% of its source
scan. Training remains much stronger: mean recall96.97% at baseline and99.91% at0.01, consistent with
the earlier train/development gap. This audit cannot attribute that gap to a particular cause.

## Every development-validation case

The median is calculated only over reference voxels missed by baseline argmax. Each case's median
is below0.006, so a modest change near0.50 cannot recover much of that missed region. These scores
are model probabilities, not established calibrated probabilities. Quantiles for reference/background/
missed reference and all five fixed operating points are retained per case; no adaptive sweep followed.

| Case | Missed-reference median probability | Baseline recall | Recall at0.01 | Source crop at0.01 |
|---|---:|---:|---:|---:|
|00001004|0.001344|56.9%|71.4%|5.9%|
|00002942|0.003462|58.9%|73.5%|9.8%|
|00003104|0.000246|25.7%|40.5%|6.2%|
|00004995|0.005820|56.4%|75.7%|42.9%|
|00005747|0.000505|35.1%|46.4%|16.2%|
|00007265|0.001999|38.7%|58.4%|9.6%|
|00007482|0.000419|44.4%|56.8%|58.0%|
|00007484|0.000642|33.8%|43.3%|5.9%|
|00007687|0.001949|48.5%|65.3%|42.3%|
|00007839|0.000413|41.3%|52.6%|49.5%|
|00008855|0.005457|66.8%|81.2%|6.4%|

## Evidence and next work

Frozen request: `outputs/prowl/probability-audit-request-8a0e68ba-6b10-4007-b91c-1939ea016d1d`;
SHA-256 `bed1fc8504c485274bb632b686b63b3df79760d66d465ab99057711a59e543ee`.
Consumed audit: `outputs/prowl/probability-audit-ce515b71-cd9b-449e-ae84-d0685febf433`;
receipt SHA-256 `6a187b3b12b69dc2b80c1cdae503e00abd984252c38217d210e4081a8a5821b0`.
Derived summaries and test log: `outputs/prowl/probability-audit-review-20260929`.
All receipt file hashes were independently rechecked before summarizing. Do not rerun the consumed
request or extend CAP-EXP-006.

The [new-candidate header job](../data/LOCALIZER-EXPANSION-V2-HEADER-JOB-2026-09-29.md) is prepared,
not executed:148 new candidates,296 unique CT/pancreas paths, matching protected roles. Its JSON
SHA-256 is `2e30e9e10e0b6b9a12ada52e1fab56f693eaf944ddbc76c840caab433a516511`.
The new inputs total4,817,659,594 compressed bytes in retained inventory; worst-case bounded header
reads are19,398,656bytes, below20MiB. No current payload identity or decompressed sizes are asserted.

**Next:** implement/test that exact header-job consumer and run its frozen request, then use measured
headers to bound positive qualification batches. Preserve difficult cases and all holds, freeze new
qualified roles, and profile a versioned consumer before selecting the next training budget. Keep the
training intervention focused on data breadth; any changes to thresholds, loss, augmentation or
margins require their own explicit experimental rationale. No new training launch is pending.
