# Seven-case saved-output visual review

Quinton explicitly requested the missed-lesion and false-positive visual review
now. Lenovo owns the complete autonomous70 saved outputs and will do this CPU-only
work while the qualified Mac KD continuation keeps its GPU. No inference,
training, scoring rerun, threshold change or scientific recipe change is requested.

## Fixed inspection targets

The [hash-bound selection manifest](WEEK-05-VISUAL-ERROR-REVIEW-20261104.json)
binds Lenovo closeout `d290d43`, export SHA256
`3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6`,
original request/ready/completion and per-case score/result/access hashes.

- All five missed reference components: cases4681,8769,6755,2889 and2235.
- Additional high-FP positive case8711 and largest raw-FP reference-empty case6880.
- Up to three largest zero-overlap predicted components per case, selected by
  voxel count with component ID breaking ties. Seven cases, five missed targets
  and21FP targets total. These are representative selections, not exhaustive
  clinical review or physical-volume severity rankings.

Verify saved source CT/reference/prediction bytes, native grids and geometry before
rendering. Keep original outputs immutable. Preserve unknown reference-unit flags;
do not repair header units, crop away errors, change sampling or rescore. Use native
CT context and enlarged targeted views, clear reference/prediction legends,
orientation, slice indices and world coordinates. Verify transforms before naming
anatomical planes; unsupported geometry is a reported limitation, not an invitation
to silently resample. Bind image hashes, selected component, plane selection and
all source identities in a fresh manifest. Reuse qualified overlay tools where safe.

One CPU thread,12GiB RSS,2GiB fresh-output ceiling,100GiB free-space floor, AC,
initial20-minute budget for all seven cases. Stop/report any safety or integrity
failure; no unbounded retries. No model or GPU job is authorized by this handoff.

## Actual review and return

Open every rendered contact sheet with image tools. Record what is visible about
annotation/prediction relationships separately from causal hypotheses. Compare
with the previous four-case inspection; do not claim medical diagnosis, independent
generalization or qualification of the failed numerical-equivalence comparison.
The exposed-development/UNQUALIFIED exception remains explicit.

Commit/push additive renderer tests if needed and sanitized manifest/report/status;
update Trello with evidence. Keep CTs, masks and medical-image PNGs private. Return
resource/cleanup evidence and precise image paths/hashes. For Mac inspection,
prepare a private archive up to100MiB with `prowl-review-transfer-v1` exact inventory,
safe regular relative members and independent archive hash. Use the existing
encrypted transfer workflow; keep one-time codes out of Git and documentation.
No source checkout merge or public imaging upload is needed.

The Mac will verify returned publication/transport, inspect images available here
and reconcile findings into the Week5 error analysis. This is visual review, not
production reviewer acceptance, a new annotation, or an automatic training change.
