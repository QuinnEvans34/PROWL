# Prepared CP02 metadata request

Recipient: Codex chat **Plan capstone experiment workflow**, on Quinns-Laptop.
Status: Quinton explicitly authorized “Yes, request the development metadata” on October20.
The metadata-only request was sent to the named training chat. Response pending; no training
changes or remote inference requested.

## Request text

Quinton has authorized the DAG/RAG chat to compare measurement errors and lesion false positives
on a fixed exposed development subset. Please provide a metadata-only handoff for the fixed
step6000 checkpoint already transferred to the Mac. Do not launch inference, open CT/annotation
arrays, change the running experiment, or choose cases based on quality metrics.

Run: `pants_pancreas_region_24k_20261019`. Checkpoint SHA-256:
`ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`.
Known current70 development-list hash:
`6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf`.
Known input-control hash:
`bda7d9c58536c618936232628630996d793b331eb29fd6062630fb05a3888ae2`.

Verify those metadata identities, exact development/validation agreement and disjointness from
training. Using admitted preparation metadata only, select the first three sorted lesion-positive
and first three sorted annotation-empty development IDs. Retain the preselected denominator if
a later size/geometry problem occurs; do not replace cases after inspecting quality. Provide:

1. Current development IDs or a pinned metadata selection receipt that proves the sorted selection,
   stratum counts, six selected IDs and explicit current-training exclusion.
2. For each selected ID: admitted annotation state, source CT/pancreas/lesion SHA-256 hashes,
   source relative names, and retained shape/affine/units/size metadata if already available.
3. The metadata/control/review hashes and producer identities used for those checks, and whether
   each selected case was exposed in the completed step6000 development evaluation. Do not return
   quality scores for case selection.

The Mac will match its existing source files, freeze its private selection, reuse the retained
case00000029 output if selected, and run separate bounded local inference for other cases. The
same CP01 largest-union rule is only a comparison; no alternate cleanup or UI promotion follows.
Return the compact metadata in this chat or a local handoff file; the requesting chat can read your
response. No new network listener, cloud upload or public data publication is needed.
