# Broader localizer candidates — D-289

The metadata-only expansion is published and independently replayed. **128 training and48 development-
validation candidates are selected; they are not a frozen executable cohort.** No new source payloads,
headers or model probabilities were read, and no training ran.

## Preserved evidence and selection

All16 old training and12 old validation candidates remain in their protected roles, including held
case6350. Its unknown spatial units are still unresolved; it counts toward48, not toward permission
or a promised48-case executable validation cohort. Other old holds and qualifications are untouched.

New `localizer-candidate-hybrid-v2` uses only case identity, protected role and descriptive phase/spacing.
The seed is `prowl-sept29-hybrid-v2`. After retaining old candidates, fill up to4 per train stratum and3
per validation stratum, then allocate remaining slots proportionally to remaining stratum populations.
Largest-remainder arithmetic uses integers; equal remainders use lexical stratum order. Within each
stratum use SHA-256 of policy, seed, role and case ID. The v1 selector remains unchanged.

| Accounting | Training | Development validation |
|---|---:|---:|
| Prior candidates retained |16|12|
| Coverage-floor additions |29|20|
| Proportional additions |83|16|
| Total candidates |128|48|
| CT + pancreas files in retained inventory |256|96|
| Observed compressed bytes |4,204,292,167|1,306,956,408|

There are148 new candidates. All352 files were present in the retained stat inventory; this is not
fresh payload verification. The combined compressed estimate is5,511,248,575bytes (about5.13GiB).
Header/decompressed-memory estimates are unavailable until bounded header reads are performed.
The missing-phase/thin training stratum has only1 member (shortfall3); venous/thick validation has
only2 (shortfall1). Both shortages are explicit. Arterial/thin validation now has7 candidates,
including held6350; this does not yet establish executable coverage of that stratum.

This deliberately mixed sample still overrepresents rare strata; unweighted validation scores are
not population estimates. Biological patient uniqueness remains unverified beyond the accepted
study-as-subject protection. Final-test membership and data are untouched.

## Reproducibility

Package: `outputs/prowl/localizer-candidates-v2-0d91addc-1ef8-402b-b12a-611aa78f12f9`.
Receipt SHA-256: `aa9a77cbcb3848b194a2e1bcb5515174dbf4aa4efa22c18e0d0d7746ec7ab3a7`.
The package retains the full selected IDs, selection reasons, strata accounting, inventory references,
input pins and exact selector/producer source. Pinned original manifest, all three membership lists,
previous candidate package and metadata inventory were checked before selecting.

Fresh-process replay command:

```sh
.venv-prowl/bin/python -m scripts.diagnostics.localizer_candidate_expansion --check outputs/prowl/localizer-candidates-v2-0d91addc-1ef8-402b-b12a-611aa78f12f9
```

Replay passed byte-for-byte. Eleven new synthetic tests exercise nesting/role preservation, metadata
order and score independence, shortages, missing metadata, budget refusal and integer quota/tie rules.
The full native suite passed: **1,211 tests**, two existing upstream warnings,32.36seconds.
`git diff --check` also passed. Test evidence is retained in `outputs/prowl/d289-verification/`.

## Next bounded work

1. Implement/test and freeze the [probability audit](CAP-EXP-006-PROBABILITY-AUDIT-PLAN-2026-09-29.md)
   on the existing27 qualified cases. Its plan is prepared; no inference has run.
2. Prepare a header-only job for the148 new candidates (296 files), with exact selected inventory
   identities and read/resource caps. Reuse valid prior evidence without treating it as new permission.
   Use headers to plan bounded qualification batches; retain failures/holds without silent refill.
3. Qualify every newly consumed case, freeze new role cohorts, then implement/profile a separately
   versioned consumer. Current16/11 runtime and54-file caps remain unchanged.
4. Choose a new training exposure/resource budget after those checks; do not simply extend006 or
   assume128×150 updates. Training data breadth is the leading next intervention, not yet launched.
