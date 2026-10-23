# Full lesion coverage and detail: early stop, October 19

User explicitly requested stopping the run and discussing a pancreas-focused,
coverage-preserving successor. Owned session 95776 was interrupted; all four
identified supervisor/worker processes were absent on the subsequent check.
No graceful-final-save claim: last journal update is 6,270 / 78,830.906 seconds;
latest scheduled checkpoint is 6,000. Original journals, reports, configuration,
receipt pins and checkpoints are retained unchanged. No restart is authorized.

| Full native 70-case development result | 2k | 4k | 6k |
| --- | --- | --- | --- |
| Positive lesion macro Dice | .028697 | .053757 | .061095 |
| Pancreas Dice | .137881 | .200327 | .364512 |
| Positive cases detected | 33/36 | 31/36 | 32/36 |
| Empty cases with any predicted lesion | 34/34 | 34/34 | 34/34 |
| Empty-case predicted lesion voxels | 8,370,282 | 2,334,489 | 2,556,346 |

All three native passes completed 70 cases with zero reconstruction gaps.
The complete 6k endpoint improved pancreas outlining but only modestly improved
lesion Dice; false-positive voxel burden rose about 9.5% versus 4k.
Planned 24k hypothesis remains unresolved after early termination; this is not a
statistical rejection of coverage preservation or proof of futility at 24k.

The input intervention bundled geometry, sampling and full-CT inference. The old
pancreas-focused .423761 result is not an equivalent autonomous full-CT task.
Sampler inspection found every fourth *patient visit* selected a uniform CT
window. Cohort permutations synchronized those visits: first 3,999 updates were
focused, followed by a broad-window block. This is a scheduling concern, not a
proven sole cause. Coverage checks did not establish effective optimization.

Discussion proposal only: retain complete anatomy in a pancreas-centered region
with surrounding context; never use ground-truth lesion masks to choose ordinary
development/inference crops. Any oracle-provided-pancreas experiment must be
labeled separately from predicted-localizer evaluation. Training masks may guide
focused sampling; held-out lesions may only audit crop coverage, not repair crops.
Resolve physical field of view versus detail and interleave sample types, with
independent per-patient coverage counters and exact restoration tests, before a
new specification. No new training or dataset audit is authorized by this note.

Evidence: E:/PROWL/artifacts/pants_full_coverage_physical_24k_20261018/execution/
history.jsonl and native-{002000,004000,006000}.json. Operator action recorded in
the separate operator-stop.json; original execution journal was not rewritten.
