# Current-model activation intake — October 20

**Closeout requirement:** Quinton explicitly requested merging the branch into `main` after this
work. Complete the verified transfer and bounded local inference walkthrough first, then refresh
remote refs, review the complete integration diff (including the shared UI redesign), resolve any
conflicts without losing either lane's work, run relevant checks and merge/publish to `main`.
The current integration branch is `claude/prowl-ui-implementation`; earlier scoped retrieval
publications must be reconciled without duplicating or discarding changes. This authorizes the
eventual merge; it does not approve the pending temporary network listener or waive verification.

**State:** input and geometry preflight passed; existing SMB login unavailable and Guest explicitly denied.
AI-05 remains In Progress. This is not a successful inference or accuracy review.

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

## Transfer and next execution

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
unconfigured8017 service, and run one case through `/predict` with the current600s/8GiB limits.
Record success or failure, elapsed time and available resource evidence. Inspect the native outline
and same-mask measurement identity; any boundary refusal remains visible. Do not promote accuracy
or anatomical completeness from one development example. No automatic retry or case substitution.

At intake the Mac is on AC, no local trainer is running, and free space is approximately107GiB
internal/1.9TiB external. Service8017 still reports `configured:false`. These observations are
time-specific and must be refreshed before execution.

Private evidence: `outputs/prowl/on-demand-activation-20261020/remote-intake.md`,
`local-input-intake.json`, `geometry-preflight.json`. No model deserialization or forward pass
has occurred in this activation block. Existing implementation checks were not repeated.

## Proposed password-free transfer (not activated)

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

This would create a new network listener; Quinton's choice/approval is pending. No listener,
certificate, token or remote upload request has been created. Once approved, implement and verify
these controls with artificial small fixtures before moving the actual checkpoint.
