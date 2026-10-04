# Step 2 preparation: exact retained controls and remaining source-job scope

**Status:** retained-control checks complete; live preflight and content-job budget pending.
[Machine-readable input pins and scope](SOURCE-VERIFICATION-SCOPE-2026-09-28.json).
This is a proposed next job specification, not a completed source audit or signed training run.

## Established without source-drive access

The original train/validation/test files reproduce their accepted hashes and 7,200/1,800/901 counts.
The acquisition inventory pins nine training archives, totaling 317,707,829,738 compressed bytes.
Retained extraction receipts identify all nine destinations, 9,000 CT files and 317,614,413,856 expanded
CT bytes. The label receipt reports 287,128 files/52,020,675,883 bytes across all labels; that does not
mean a pancreas-only check must inspect every organ. The publisher-test CT archive stays unextracted.
All cited local controls/receipts now have actual file hashes in the scope JSON.

The old five-study package retains zero eligibility. Its 55 covered files match their receipt and
five v2 manifest outputs replay exactly. These checks preserve old evidence, not qualify new inputs.

## Next bounded preflight

Proposed metadata-only limits: 10 minutes, 512 MiB process memory, 64 MiB evidence output and at most
350,000 directory entries. Verify the existing registered volume/root identity first. Use the nine
receipt-named CT directories and the label directory; do not follow links or create replacement roots.
Stop on unexpected layout, a symlink/special file, permission failure, changed mount or budget limit.
No raw payload contents, publisher-test headers/voxels, new extraction or scientific alias activation.
The exact directory bindings are resolved from retained configuration, not guessed from old absolute paths.

Account for all original identities. For the pancreas-localizer payload scope, produce an explicit
expected-path inventory for the 9,000 publisher-training CTs and 9,000 pancreas files, join observed
presence/size, and record other structures as outside this purpose scope. The 1,800 PROWL validation
cases remain protected; inventory presence does not permit their use in training. Test identities are
accounted for from controls; no test payload inspection is introduced by this preflight.

The current structural inventory script cannot by itself publish this per-file evidence. A tested
bounded inventory adapter is still needed. Preflight success establishes layout/accounting and a
read budget input, not content integrity, annotation quality or G1 completion.

## Content-verification job cannot be budgeted from counts alone

After exact inventory and current source bindings are known, specify:

- Which archive/file integrity checks are mandatory source-wide under the approved assurance policy.
- Which already-pinned receipts can be reused and what current bytes still need verification.
- The exact candidate pool/selection rule and CT/pancreas files to inspect in detail.
- Required source-provenance/use and issue-resolution evidence for those candidates.
- A bounded read-throughput measurement, byte/time/memory ceilings and at least 25% contingency.
- An immutable evidence output destination, interruption behavior and no-overwrite rules.

Do not treat full-tree byte hashing as implicitly authorized by a small candidate check, or substitute
selected hashes for required source-wide assurance. If a required full read threatens the weekly
schedule, report its measured cost before execution. The approved staged approach remains unchanged.


## Completed follow-up

The [live metadata preflight](LOCALIZER-METADATA-PREFLIGHT-2026-09-28.md) completed within budget:
all 18,000 CT/pancreas files present, exact protected-role counts and CT shard size totals verified.
The original JSON scope is retained as a pinned historical run input. Content integrity, qualification
and the larger content-read budget are still open; use the new inventory for the next bounded job.
