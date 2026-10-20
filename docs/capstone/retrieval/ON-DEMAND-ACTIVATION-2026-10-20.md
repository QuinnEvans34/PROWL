# Current-model activation intake — October 20

**Closeout requirement:** Quinton explicitly requested merging the branch into `main` after this
work. Complete the verified transfer and bounded local inference walkthrough first, then refresh
remote refs, review the complete integration diff (including the shared UI redesign), resolve any
conflicts without losing either lane's work, run relevant checks and merge/publish to `main`.
The current integration branch is `claude/prowl-ui-implementation`; earlier scoped retrieval
publications must be reconciled without duplicating or discarding changes. This authorizes the
eventual merge. Quinton subsequently explicitly approved the temporary encrypted transfer.

**State:** checkpoint transferred and verified; one real MPS prediction completed and displayed.
The output touches the inference-region boundary, so the UI correctly withholds volume.
AI-05 remains In Progress; pipeline integration passed, reliable measurement/accuracy acceptance did not.

Quinton authorized obtaining the current checkpoint and one development scan for a bounded Mac
walkthrough, then explicitly authorized the checkpoint-transfer request to **Plan capstone
experiment workflow**. The owner verified the immutable raw step6000 checkpoint and its independent
backup without loading the model. Training was not interrupted or changed.

## Frozen inputs

Run: `pants_pancreas_region_24k_20261019`. Checkpoint: `execution/step-006000.pt`,
56,576,803 bytes, SHA-256
`ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`.
Do not replace it with a mutable last/best checkpoint or choose a different step by outcome.

`PanTS_00000029` was selected as the first sorted member of the current admitted 70-case development
list before reviewing its quality. The owner confirmed exact agreement with input-control membership
and presence in the completed step6000 native evaluation. Provenance:

| Record | SHA-256 |
|---|---|
| Run development IDs | `6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf` |
| Run input-control | `bda7d9c58536c618936232628630996d793b331eb29fd6062630fb05a3888ae2` |
| Admitted manifest | `46b436edeba2995c942d53b9c2849760a4802cbbf04c95ba9664182874fb31bc` |
| CT, 18,733,837 bytes | `dfafa585d7ad71f09303960d8aa7f325f5848d39db35ec76e6f8e1b860b95c12` |
| Supplied pancreas, 76,330 bytes | `1a556c01eb7d3a0b5e8a451ff4c906dae28b98223941030cb719c7c004f6add0` |

Both original inputs already exist on the Mac's mounted PROWL-Data source snapshot. Local hashes
exactly match the owner's admitted identities; no second scan transfer or copy is necessary.
Native shape is419×340×109 (15,528,140 voxels), spacing0.8496090174×0.8496090174×2.5mm,
with identical CT/mask affine and explicit mm units. These fit existing compressed/decoded/native
limits. Local decoding confirms finite CT and a nonempty binary supplied-pancreas mask.

Our region calculation produces low[7,102,5], high[384,285,99] and30 physical windows, exactly
matching the retained producer record. This verifies preprocessing configuration for this case;
it does not verify model predictions or CUDA/MPS numerical equivalence. No lesion reference was
opened. The supplied pancreas is region assistance, never the prediction being measured.
The UI measures output pancreas extent as labels1+2 and suspected-lesion volume as label2,
as documented in the implementation report; the evaluator's class1-only metric is different.

## Initial transfer attempt (historical)

The existing Windows SMB share is reachable on the same local subnet. Finder was opened on the
existing E$ share; sign-in did not complete using the prefilled account. Quinton was asked to
enter credentials directly in the OS dialog, not in chat. He does not know the password and
requested Guest access; one Guest attempt was explicitly denied by Windows. Quinton then corrected
the account name and entered credentials directly in the OS dialog. Windows again denied access.
The dialog does not distinguish a password error from administrative-share permission; neither
cause is established. The refusal is
retained in private `guest-denied.png`. Do not enable Guest or change Windows authentication. No new share/server, firewall change,
cloud upload, saved credential or training-drive disconnection was performed. The checkpoint
is not yet on the Mac. The exact remote path and network address remain in the private intake.

After authentication, copy only the pinned checkpoint into a new private external artifact folder,
verify its byte count and SHA-256, and retain a transfer receipt. Recheck AC, idle inference resources
and free storage. Build the private configuration with the existing helper, restart only the owned
unconfigured 8017 service, and run one case through `/predict` with the current600s / 8GiB limits.
Record success or failure, elapsed time and available resource evidence. Inspect the native outline
and same-mask measurement identity; any boundary refusal remains visible. Do not promote accuracy
or anatomical completeness from one development example. No automatic retry or case substitution.

At intake the Mac is on AC, no local trainer is running, and free space is approximately107GiB
internal/1.9TiB external. Service8017 still reports `configured:false`. These observations are
time-specific and must be refreshed before execution.

Private evidence: `outputs/prowl/on-demand-activation-20261020/remote-intake.md`,
`local-input-intake.json`, `geometry-preflight.json`. No model deserialization or forward pass
has occurred in this activation block. Existing implementation checks were not repeated.

## Approved password-free transfer design

Use a temporary HTTPS receiver on the Mac's current LAN address, with one fixed checkpoint upload
route. Restrict accepted requests to the training laptop's current LAN address and a newly generated
single-use bearer token. Give the sender the exact generated certificate through the existing
private chat handoff and require certificate verification; never use insecure TLS bypass. Do not
put the token in URLs, public docs, Git, Trello or user-facing output.

Accept only56,576,803 bytes with SHA-256
`ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f` into one new private checkpoint
file on PROWL-Data. No directory listing, arbitrary filename, overwrite, download or command route.
Bound the receiver to5 minutes and one successful upload, then close it. Reject wrong source/token,
length or digest; preserve a failed-transfer receipt without activation. No firewall change,
public tunnel, guest enabling, reusable credentials, training change or scan upload is included.
A separate removable-drive copy remains the alternative.

Quinton explicitly approved this listener. Five artificial TLS checks passed before activation:
wrong token/path/length rejection, peer restriction, digest rejection, no overwrite, one-success
shutdown and deadline enforcement including a stalled TLS handshake. The implementation is
`scripts/receive_checkpoint_once.py`; configuration and credentials stay private.

## Actual transfer and real prediction

The sender returned HTTP201 with normal TLS certificate/hostname verification. Exactly 56,576,803
bytes arrived and the Mac independently rehashed the checkpoint to the frozen digest. Sender
transfer time 22.062s; receiver lifetime 69.828s including coordination. The source checkpoint was
unchanged, the sender's one-use token was removed after acknowledgment, the receiver's generated
private key was removed, and a fresh connection confirmed its listener closed. No firewall or
Guest changes, public endpoint, training interruption or scan transfer occurred.

Local original CT and assistance were reused. AC/free-space/no-local-trainer checks were refreshed.
Private configuration pins the current code closure, checkpoint, recipe and inputs; device is MPS,
600s / 8GiB sampled-RSS limits unchanged. Only the owned unconfigured 8017 server was replaced;
configured server is owned session 63294. The independent loader does not restore an optimizer.

One user-interface request created job `d8f8cca5d508413c9ba5f96114857c19`:

| Observation | Result |
|---|---|
| Worker | ready, exit0, reaped;19.1039s elapsed |
| Sampled peak worker process-group RSS |1,207,795,712 bytes, about1.12GiB; not a total GPU-allocation measurement |
| Physical reconstruction |30 windows, zero uncovered region voxels; minimum blend weight0.0010000000475 |
| Predicted native mask SHA-256 |`75fcf8e07d9a8c2650ce842004ad160e4879912debfcd8df944c778416e2ca49` |
| Label1 / label2 counts |44,548 /6,547; diagnostic counts, not accepted whole-organ volumes |
| Boundary contact |52 label1 voxels on low-z source plane5;15 on high-z plane98 |
| Other contacts |No lesion voxels on region faces; no foreground on CT exterior faces |
| UI question |“how big is this pancreas?” correctly returns Measurement unavailable with crop-boundary reason |

The real native CT, green pancreas prediction and red lesion prediction display together. The
verified viewer and measurement code consume the same mask identity. Independent Python face
counts agree with the browser's rejection. The provided pancreas selected the search region and
was not substituted for the model output. No lesion reference was opened and no second inference
or cleanup/postprocessing was used to obtain a more favorable result.

**Interpretation:** region coverage and transport work, but boundary contact can reflect stray
predictions or truncated segmentation; its cause is unproven. This development example cannot
support a reliable whole-pancreas size answer. Preserve it for model/native-boundary investigation;
do not suppress the guard, silently remove components, select a better case or claim CUDA/MPS
parity. Per-target measurement qualification and reference-reviewed accuracy remain open.

The supervisor now retains private `worker.log` (sampled 1MiB cap) and `execution.json` with elapsed
seconds, sampled peak RSS, return code, failure category and reaping status. Neither is exposed
through the HTTP artifact allowlist. Failure causes can be inspected without leaking paths in UI.

## Integration validation and merge scope

- 5 transfer tests; 22 inference/geometry/lifecycle tests; 155 affected retrieval/lifecycle/saved-viewer
checks: 182 Python checks pass. Two existing Torch deprecation warnings remain.
- 212 UI unit/library tests pass; the optional retained-volume replay was then run with its evidence
directory and passed separately, for 213 distinct UI checks total, with zero new literature-model calls.
- Production build passes with the existing bundle-size warning.
- Real browser prediction, native overlay and measurement rejection inspected; real NIfTI hashes,
labels, face contacts and request identity independently retained. Broader historical Playwright
suites were not rerun in this block; earlier redesign handback and current unit checks remain their evidence.

Before merge, refreshed main is `5a86f27`; it is an ancestor of the integration branch. Of 87 files
changed on the portable retrieval publication, only the newer handoff/activation docs and the
shared-shell LiteratureSearchPanel differ in integration HEAD; reviewed differences preserve the
panel context/measurement wiring. Merge includes the existing UI redesign and all completed
retrieval/measurement changes, not raw inputs/checkpoints/private configurations or result images.
The merge is engineering integration, not an AI-05 or clinical quality acceptance.

Private evidence under `outputs/prowl/on-demand-activation-20261020/`: transfer receipt,
private configuration, actual-job(request/log/execution/package and independent-mask-audit),
UI screenshot, test/build logs. One frozen validation package is retained for this review;
production prediction retention remains session-only. The initial live result is preserved in the evidence package and screenshot.

## Merge closeout

[PR1](https://github.com/QuinnEvans34/PROWL/pull/1) merged into main at20:24:14UTC on October20,
merge commit`3d53c55129a47a17663142633e85f7eb307079b6`, reviewed head`050b7b7`.
GitHub reported clean/mergeable and no configured status checks; local validation above supplies
check evidence. The merge tree exactly matches the tested integration head. Local main was
fast-forwarded to the merge; original integration and portable publication branches are retained.

Switching through the older local main briefly triggered Vite restarts and the browser's connection
error page. The existing Vite process recovered; a fresh in-app tab verifies the merged `/predict`
page, connected service and admitted case with Run enabled. The original server job remains ready;
its private frozen evidence is preserved. No second inference was performed to restore the page.
Do not describe the new tab as retaining the earlier in-memory answer. Service8017/config remain
unchanged; next substantive work is the boundary/measurement qualification issue, not another merge.
