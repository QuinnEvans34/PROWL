# Native metadata volume diagnostic — continuing record

October6,2026. Quinton's “continue on … iterate through each step until we are ready to train
right now” approves this slice and bounded readiness continuation. Contract written before code:
[diagnostic contract](../imaging/SUPREM-METADATA-VOLUME-PROBE-CONTRACT-V1.md).
Diagnostic complete:19native invented checks pass;0.419581s/55,803,904B aggregate peak,6samples,
workers reaped. Initial18pass0.428712s/55,623,680B; added an invalid-UTF8 error-byte cap test/fix,
then qualified the final19. No failed tests. Logs `/tmp/prowl-vdiag-attempt-01.log` and `-02.log`.
Actual two parent-directory commands finished, zero source leaf access. No source acceptance/
training authority. The prior B01 refusal remains retained/retired.

Native command: `.venv-prowl/bin/python scripts/diagnostics/probe_suprem_metadata_volume_v1.py
--approved-directory-diagnostic`. Each literal approved directory used once:

| Directory | Return | Reason | stdout/stderr bytes | Wall | Aggregate sampled peak |
|---|---:|---|---:|---:|---:|
| repo/pretrained_weights |1|command_nonzero|402/0|0.050447s|20,824,064B|
| repo/outputs/prowl |1|command_nonzero|397/0|0.047922s|21,168,128B|

Both have domainvolume_diagnostic_only,scopeauthoritynone,trainingfalse,sourcepayload0,
volumenull,errornull,3samples/50ms,ownedchildreapedtrue. Normal native tool review accepted scope.
The probe retains stderr errors and volume fields only; it discarded these nonzero stdout
responses. Exact failure messages therefore remain unknown. This limitation is retained, not
repaired by repeating either consumed diagnostic. Directory locators failed to yield volume fields.

## Next bounded repair under Quinton's iteration instruction

Use a new source-reader version with a descriptor-based Darwin fstatfs observer, mapping the
opened directory to its physical mount, then bounded diskutil info on that mount. Bind filesystem
device/fsid as well as APFS UUID/mount, retaining no-follow ownership/identity checks. Reject
unknown ABI/platform, mount mismatch, malformed/nonzero/bounded-output/resource failures.
This addresses the observed directory-locator failure without assuming its exact missing message.
Keep R01/A and dispatcher1 byte-identical. Write explicit v2 contracts before code and qualify
the new native observer on invented temporary directories, then one new B02 preflight/metadata
attempt with the same single named source, read/output/CPU budgets and a fresh authorization.
Never replay B01, either directory diagnostic, or switch source/namespace on failure.

No source rights/separation acceptance or real values/training is bundled into the repair.
