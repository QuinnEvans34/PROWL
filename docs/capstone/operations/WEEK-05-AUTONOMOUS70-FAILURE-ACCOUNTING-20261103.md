# Runnable CPU-qualified successor; launch approval remains pending

The original proposal/request and all producing pins remain intact. Additive executor v2 and preparer v3 implement the recommended resource-failure policy without raising the localizer cap or removing a patient.

Successor request: `E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a02/request.json`

SHA256: `7db98398be4da35bf775976ef81ec73e848e0258e56e760307817a4e5ec48364`

Parent SHA256: `853faa584b3abc87e5b16b25c186af9cdbd5e1bbe69b08de208d5ecabe083cbc`

Exactly 70 patients remain: five reused predictions, up to 64 new predictions, and one declared preflight resource failure (5592). The latter gets a failure record with null Dice, no CT restoration/read, no model forward and no scoring. Its failure record receives an independent backup. Completion reports 69/70 maximum execution coverage and the failed ID; subsequent unexpected failures preserve completed, failed and pending lists. The existing 16-million-voxel cap remains unchanged.

Eight CPU tests passed in 6.45 seconds, covering parent admission/reuse guards and successor denominator/cap tampering, non-authorizing admission template, direct failed-case worker/scorer rejection, and a mocked full controller execution with exactly five reuses, 64 inference calls and 69 scoring calls. These tests do not claim real GPU or source qualification.

The revised request retains the parent conservative 65-case time/storage projection. Proposed limits remain 32 GiB outputs, 32 GiB new independent backups, 64 GiB combined backups, 12 GiB inference RSS, 6 GiB GPU and 100 GiB C:/E: free-space floors. Restore only 64 required CTs under 7,200 seconds/2 GiB RSS/3 GiB output. Evaluation is bounded to 42,000 seconds, with 600 seconds per worker. Estimated total remains 2.6–5.1 hours plus checks. The larger scope and allowances are not yet approved.

## Prepared commands

Read-only verification may run now:

```powershell
$py = 'C:/Users/quinn/.cache/prowl-week05-matched-20261102-a01/venv/Scripts/python.exe'
$pin = '7db98398be4da35bf775976ef81ec73e848e0258e56e760307817a4e5ec48364'
& $py scripts/diagnostics/prepare_autonomous_baseline_v3_20261103.py --inspect-sha256 $pin
```

Only after explicit human approval of the exact revised scope, numerical exception, failure policy and limits, record that decision and materialize the existing template as admission.json. The template alone never authorizes execution. The following is a future sequence, not an instruction to launch now:

```powershell
$prepared = 'E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a02'
if (Test-Path "$prepared/admission.json") { throw 'Admission already exists; inspect instead of overwriting' }
Copy-Item -LiteralPath "$prepared/admission-template.json" -Destination "$prepared/admission.json"
& $py scripts/diagnostics/execute_autonomous_baseline_v2_20261103.py --restore-sha256 $pin
# Inspect successful/reaped restore.resources.json and exact restoration receipt before continuing.
& $py scripts/diagnostics/execute_autonomous_baseline_v2_20261103.py --admit-sources-sha256 $pin
# Inspect successful/reaped source-admission.resources.json and ready.json before continuing.
$readyHash = (Get-FileHash "$prepared/ready.json" -Algorithm SHA256).Hash.ToLower()
& $py scripts/diagnostics/execute_autonomous_baseline_v2_20261103.py --launch-ready-sha256 $readyHash
```

Inspect files/processes before each stage; never rerun a started or failed stage. Source admission verifies exact CT/reference hashes, original native geometry and units for executable cases. Inference retains reference-byte separation; scoring remains a separate CPU process. Existing outputs are reused under original model/recipe/runtime/source/artifact checks. No admission.json, restored source directory, ready.json, scientific output or GPU dispatch was created during this preparation. Mac KD remains separate.
