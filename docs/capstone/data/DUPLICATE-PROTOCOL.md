# PANORAMA–PanTS duplicate-control protocol

> **Current experiment exception, October 12, 2026:** CAP-EXP-017 uses the user-approved
> [exploratory admission amendment](../operations/PANORAMA-EXPLORATORY-ADMISSION-20261012.md):
> retain the 274 declared exclusions and existing holds; exclude the five provenance-uncertain
> current development cases; no new broad duplicate scan. The protocol below remains the
> stronger benchmark-control design, not a pending requirement to repeat preparation for
> this exploratory run. Neither metadata reconciliation nor this exception certifies zero overlap.

**Status:** Approved Plan 03 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/03-panorama-integration.md`](../implementation/03-panorama-integration.md)

## Purpose

Prevent the same or materially identical CT examination from contributing both training evidence and
protected evaluation evidence. The protocol combines source-declared imports with image-level checks
because neither method is sufficient alone.

This is a candidate-detection and adjudication system, not a patient-identification system. It does
not claim two similar scans belong to the same person without evidence.

## Threat model

The same CT may differ across collections because of:

- filename, patient/study ID, or archive path changes;
- gzip recompression or NIfTI header differences;
- axis order/orientation changes;
- integer versus floating representation or minor intensity rounding;
- resampling, small crops, or padding;
- derived provenance that names only a pooled institution.

Conversely, two different abdominal CTs can look similar after aggressive downsampling. Therefore
exact matches can support exclusion, while approximate scores only support review.

## Ordered layers

### Layer 1 — source-declared overlap

- Exclude every PANORAMA row with `level` equal to `MSD_dataset` or `NIH_dataset`.
- Assert 194 MSD plus 80 NIH equals 274 excluded studies.
- Assert the import-clean remainder is 1,964 studies with 578 PDAC-positive studies.
- Attach the source-field evidence to each exclusion issue.
- Never re-enable one of these studies because a later image detector fails to match it.

### Layer 2 — exact source-byte identity

Compare SHA-256 hashes of available CT source files. Equal hashes are conclusive byte identity.
Compression and container differences mean unequal hashes are not evidence of different imaging.

### Layer 3 — exact decoded-volume identity

For each CT:

1. decode through the pinned imaging reader;
2. convert to canonical RAS axis order without interpolation;
3. normalize the decoded HU representation through a versioned rule, initially finite rounded
   integer HU values;
4. hash the canonical voxel buffer and shape;
5. record physical geometry separately so an array match with conflicting spacing/origin is visible.

An exact decoded match across PANORAMA and PanTS is treated as a duplicate even when archive bytes or
headers differ. The PANORAMA copy is excluded because PanTS supplies the protected evaluation design.

### Layer 4 — approximate CT fingerprint

The initial fingerprint spike uses a reproducible transformation such as:

1. canonical RAS orientation;
2. HU clipping to a versioned broad CT window, initially `[-1000, 1000]`;
3. a deterministic body/foreground crop with the rule and failure behavior recorded;
4. physical resampling to a coarse grid, initially 3 mm isotropic;
5. deterministic pad/crop and resize to a fixed low-resolution tensor, initially `64³`;
6. fixed quantization/normalization;
7. a compact signature used for nearest-neighbor retrieval, with the similarity measure and library
   versions recorded.

These are spike defaults, not timeless constants. The selected fingerprint version is frozen only
after the calibration below. Candidate search is cross-source; no clinical label or protected role
may influence the similarity threshold.

## Calibration before eligibility scanning

Create at least 20 planted positive controls from known source CTs. Preserve the original ID and make
one or more deterministic variants covering the threat model: recompression/header edits,
orientation changes, numeric rounding, minor resampling, and small crop/pad changes.

Also include a named set of known non-matching controls from both sources to characterize candidate
volume. Freeze the transform seed, fingerprint parameters, retrieval depth, and threshold before
running against the full eligible pool.

The fingerprint is acceptable when:

- at least 19 of 20 planted variants retrieve their source as candidates;
- no positive control is hidden by preprocessing failure;
- false candidates remain reviewable within the Week 3 schedule;
- every result is reproducible from the recorded snapshot/config/code identity.

If a method cannot meet both recall and a reviewable queue, it is rejected or revised as a new
version. The planted set and earlier result remain unchanged.

## Candidate review

Every approximate candidate record includes:

- both source-scoped study IDs and protected roles;
- source snapshot and CT hashes;
- exact/decoded match flags;
- fingerprint version, score, rank, and threshold;
- shape, spacing, orientation, and coarse intensity summaries;
- a local contact sheet or synchronized slice comparison where license permits;
- reviewer, timestamp, decision, rationale, and evidence references.

Permitted dispositions:

- `confirmed_duplicate` — exclude the PANORAMA record and link both studies through one protection
  group;
- `cleared_distinct` — retain both studies and preserve the adjudication;
- `unresolved` — quarantine the PANORAMA record; it cannot enter a training cohort;
- `invalid_input` — quarantine and correct/reacquire through a new artifact.

An approximate score alone can never produce `confirmed_duplicate` or merge source IDs.

## Protection behavior

- A confirmed duplicate of any PanTS record is removed from the PANORAMA training-eligible pool; it
  is not useful independent data even if both copies would otherwise be train-role.
- Any unresolved candidate involving PanTS validation or test is blocking and quarantined.
- Every member of a confirmed/suspected group shares a `protection_group_id` used by cohort guards.
- Source records remain separate and immutable. Exclusion is a cohort/issue disposition, not deletion.
- Changing the fingerprint or an adjudication creates new issue/manifest/cohort versions and
  invalidates descendants that depended on the earlier result.

## Required tests

| Scenario | Expected result |
|---|---|
| Declared MSD/NIH import | Excluded even if no file is available for fingerprinting |
| Same compressed bytes under two names | Layer 2 match |
| Same decoded voxels with different gzip/header | Layer 3 match |
| Orientation/resampling planted variant | Layer 4 candidate retrieval |
| Similar but unrelated abdominal CT | Candidate may be raised but is never auto-excluded |
| Fingerprint preprocessing failure | Study quarantined; not interpreted as “no match” |
| Candidate crosses training and validation/test | PANORAMA study blocked until adjudicated |
| Same snapshots/config run twice | Same exact hashes, signatures, neighbors, and candidate order |
| Threshold/config changes | New fingerprint version and downstream derivation identity |

## Report

The duplicate report publishes:

- population and snapshot IDs scanned;
- counts from every layer;
- planted-control composition, recovery count, recall, and misses;
- known-nonmatch candidate rate and full review-queue size;
- confirmed, cleared, unresolved, and invalid dispositions;
- protection-role matrix for all candidates;
- algorithm/config/code/environment identities;
- residual limitations, including pooled provenance that cannot independently prove identity.

The correct conclusion is “no unresolved duplicate candidates under version X and stated controls,”
not “the datasets have zero overlap.”

## Fallback

If acceptable recall requires an unreviewable queue, PANORAMA is not mixed into the protected PanTS
experiment. The sources remain separate, declared imports remain excluded, and the residual risk is
reported. Evaluation protection outranks the expected gain from additional training data.
