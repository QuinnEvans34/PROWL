# Independent evaluation: next steps for Quinton

**Latest result:** The once-only frozen run is complete. See [October22 results](FROZEN-ANSWER-EVALUATION-2026-10-22.md): 0/20 complete answers, with source integrity preserved. Inputs and results have verified independent encrypted backups. Do not rerun the preparation/capture instructions below for this attempt; they are history. Scoring review and a repair decision remain separate from completing the run.

> **Current October 22 decision:** Quinton authorized the development assistant to access the
> reviewed questions and administer one evaluation of the frozen candidate. Follow the
> [approved amendment](QUESTION-SET-AND-EVALUATION.md#october-22-amendment-frozen-evaluation-administered-by-the-development-assistant).
> The user only needs to unlock encrypted storage; running the validator by hand is no longer
> required. Earlier agent-exclusion/manual-only instructions below are superseded. Existing
> evidence criteria, original drafts, backups and first-pass failures remain preserved.

## Encrypted workspace setup (October22)

Quinton requested help setting up the required private workspace and independent backup. Use
`scripts/retrieval/setup-private-storage.command` in the ordinary macOS Terminal. This small helper
uses native AES-256 disk-image tooling; passwords go directly to macOS prompts, never Python,
command arguments, this chat or a logfile. Expect password creation followed by unlock prompts for
the new primary and the backup verification. Save the password in your password manager.

The helper checks the registered external/internal UUIDs, different device roles, the shared26GiB
backup cap and100GiB free-space floors. It reserves128MiB per encrypted image (conservative256MiB
headroom per root), creates unique owner-only directories, copies the reviewed original into the
primary image, closes it, copies/checksums the encrypted image to the independent internal device,
reopens that backup read-only and verifies the original bytes. Only after both images are detached
and verified does it relocate the unchanged original out of the repository. Changed originals,
tracked files, failures and partial images are preserved; no overwrite, automatic retry or forced
detach. A lock prevents duplicate setup processes.

Actual image locations are shown only in the private Terminal. The public `outputs/prowl/independent-preparation-20261022/storage-*/status.json`
receipt contains state/booleans/hashes, never questions, paths or passwords. Its success state is
`workspace_ready_not_evaluation_freeze`. Later transcription/results require a fresh verified
backup before the final evaluation freeze. Do not mistake an initial-draft backup for the frozen
complete test set. Mounted images are accessible to other processes under your macOS account;
keep development agents away from them and eject them after the private session.

Verification:8 storage tests plus one completed native invented-only128MiB AES-256 rehearsal on the actual
registered external/internal roots. The rehearsal passed encrypted-image identity, read-only backup
reopen, original-byte equality and source relocation, then removed only its own invented images.
A preliminary metadata check caught diskutil's requirement for the mounted-volume path rather than
a nested artifact directory. An initial external-mountpoint rehearsal and a focused reproduction
failed with Permission denied; using an owner-only internal mountpoint passed the complete rehearsal.
These failures were corrected before any real draft handling. No real storage
completion is inferred from this rehearsal; rely on the separate actual setup receipt.


## October22 reviewed draft: assisted preparation implemented

Quinton confirmed individual questions/answers/evidence review and separately confirmed whole-set
consistency, duplicate-intent and prior-exposure review. The exact statements are retained in
`configs/evidence/evaluation/assisted-review-attestation-20261022.json`; a private operator must bind
them to the original reviewed draft bytes. This development agent has not opened the questions.

The existing CLI now checks exposure v5 (771 origins/396 wordings). A v2 schema records AI author and
label preparer separately from Quinton's semantic review, consistency review and operator roles.
`--prepare-assisted` is a **manual private mechanical-preparation command**, not execution admission.
It takes an assistant-produced transcription with exact passage quotations, derives offsets, verifies
original-draft hashes, and applies the existing evidence/balance/overlap checks. Quinton does not enter
technical labels. The legacy `--prepare` path remains closed. No candidate requests are made.

Use the conversion handoff at the end of [the Claude prompt](CLAUDE-EVALUATION-PROMPT-2026-10-22.md).
Public bindings are available with `.venv-retrieval/bin/python -m src.retrieval.private_evaluation --assisted-bindings`.
After the private workspace is ready, the operator runs the same module with `--prepare-assisted` in
an ordinary private terminal. It prompts for the transcription and original reviewed draft paths
without echo, accepts only bounded nonsymlink files outside the repository, and saves a new owner-only
`.validated` directory. It does not overwrite inputs or fabricate review decisions. Do not run that
mode in an agent-connected terminal or supply the protected paths/content to this development chat.

Storage/independent encrypted backup and once-only execution admission are still pending. This step
must not be reported as an independent score or a completed protected freeze. Git ignoring a file
inside the repository is not isolation. Preserve the original draft/history when relocating it.

Verification:80 focused checks passed in the final combined run (28 new,52 existing); the first
attempt had42 passes/17 setup errors due to a missing invented-fixture import, corrected before those
17 tests executed. Added operator-flow checks verify exact original binding, owner-only output and
no content echo. Actual public preflight/bindings verified against14 papers/1179 passages. No actual
protected data, live questions, model calls or candidate changes were used in these checks.


## October22: Claude drafting selected; evaluation admission still pending

Use the [copyable Claude prompt](CLAUDE-EVALUATION-PROMPT-2026-10-22.md) with its two public attachments.
Quinton selected a separate Claude chat to draft questions; record AI authorship and human review
honestly. Keep proposed questions/evidence outside this development chat and do not enter them in
the fictional-source rehearsal app. Candidate commit74782f7 is pinned. Public exposure v5 now
reconciles771 origins/396 wordings; the existing CLI still checks v4 and remains closed. This is
public preparation, not private admission or an independent result. Role/schema adaptation, v5
admission binding, private storage/backup, semantic review and the once-only evaluator remain
pending. See the prompt document for the current limits and operator handoff.


## October20 preparation update

Use the [change-only review packet](../../../outputs/prowl/evaluation-preparation-20261020/changes-to-review.md)
and [independent workflow](INDEPENDENT-LABELING-WORKFLOW-2026-10-20.md). Prior v4/v5 acceptance is
verified and preserved; Quinton has accepted the two replacements and changed evidence/consistency.
The public CLI now verifies exposure v4 preparation:346 origins/182 distinct wordings, including
the source-record and Week3 matrices. It remains unable to admit protected authoring. The current
demo's narrower coverage is documented in [preparation results](EVALUATION-PREPARATION-2026-10-20.md).
Do not write protected questions here or use historical v1 private templates. The separate human-operated
assistant is selected; revised role schema/tool qualification and storage/admission remain required. No source search,
offset entry or JSON authoring is assigned to Quinton.

## Historical October17 status — superseded by the acceptance above

The [disease-source review](DEVELOPMENT-DISEASE-REVIEW-2026-10-17.md) supersedes the execution
instructions below. Proposed development v6 and exposure v3 are now prepared (292 entries/33 known intents). The public inventory now includes 136 distinct normalized wordings and the
current target is 14 sources / 1,179 passages. Human review of the proposed revised development set and the independent
labeling arrangement are pending; engineering source review is complete. **Do not start private authoring or use the old templates yet.**
Quinton supplies natural questions; he is not being assigned article search, JSON or offset work.

The only current command is public and reads no protected content:

```sh
.venv-retrieval/bin/python -m src.retrieval.private_evaluation --public-preflight
```

Normal validation/`--prepare` now stop before requesting any private path. The lower-level validator
is retained for invented tests; a future admission/schema version must match the actual frozen scope
and reviewer roles. Earlier approvals remain valid for their ten-source scope.

## Historical ten-source instructions — not current execution steps

> **October17 workflow revision:** Quinton will supply natural questions but will not search papers,
> choose evidence spans or enter technical labels. The instructions below describe the earlier
> authoring arrangement and are retained as a technical reference. Do not ask him to execute them.
> First reconcile the scan-centered capability contract and an independent engineering-supported
> labeling process against the [disease-reference update](DISEASE-REFERENCE-CORPUS-2026-10-17.md).
> Existing private tooling may be reused by that process; it does not establish completed review.

The 30 development questions are accepted, including evidence and the full consistency pass.
You do not need to review them again. Step 5 now needs the separate **30-question private test set**.
This measures performance on questions the development agent has not helped write or seen.

## 1. Prepare private storage

Follow [protected authoring](PROTECTED-EVALUATION-AUTHORING.md) before writing questions. Confirm
the current shared storage allocation and independent encrypted-backup capacity; this checkpoint
creates neither an encrypted image nor a storage allocation. Do not assume an older capacity limit
in a historical document is the current approval. Keep private content outside the repository,
agent-connected folders, cloud documents, chat and Trello. Work with agents idle and unmount the
image afterward. A mounted image is accessible to processes running as your OS user.

## 2. Read sources and author independently

The local [source-reading pack](../../../outputs/prowl/evaluation-private-preparation-20261017/source-reading/README.md)
contains all 947 frozen passages from the ten-source corpus, with article attribution, representation
identities and normalized character offsets. It contains no suggested test questions or gold labels.
Overlapping passages are not independent evidence. Full source text remains local, outside Git.

Copy these public blank templates into your private workspace:

- [Suite template](../../../configs/evidence/evaluation/private-authoring-template-v1.json): fill the authorship/review description and add 30 cases to `cases`.
- [Case template](../../../configs/evidence/evaluation/private-case-template-v1.json): copy once per question, use distinct `q:heldout-01` through `q:heldout-30` identities and matching label question IDs.
- [Closed format reference](../contracts/retrieval/private-evaluation-v1.schema.json): allowed fields and values.

These templates deliberately fail validation until completed. The template status names a validation
stage, not acceptance. Keep their public corpus/development hashes unchanged. Leave content hashes
blank during drafting; the explicit `--prepare` command below computes them in a separate copy.

Write **20 answerable questions and 10 unsupported/refused questions**. Cover all five answerable
families (`appearance`, `measurement`, `anatomy`, `ai_limits`, `review`) and all four difficulty
categories (`easy`, `paraphrase`, `multi_passage`, `limiting`). Choose actual frozen information needs
from [needs v2](planning/INFORMATION-NEEDS-V2.md) and its inherited base. Do not manufacture supported
answers to meet the counts. Avoid one paper being the sole gold support for more than 10 of the
20 answerable questions; multiple genuinely supporting papers are allowed.

For each answerable case, record required concepts, exact direct/partial/limiting spans and a judgment
for every retained source. Use normalized Unicode character offsets `[start, end)`, not HTML byte
offsets. Each direct span must fit completely inside a frozen passage. Representation ID/hash and
offset fields follow the [span contract](../contracts/retrieval/span-label.schema.json). Every required
concept must have direct support. Unsupported/refused cases have no gold spans, concepts or source
judgments; record the reason and boundary in their expected behavior and review notes.

## 3. Complete your semantic review and second pass

Check whether the evidence actually supports the expected meaning, including population, modality,
units and limitations. Then separately check consistency across the set. Record the actual reviewer,
ISO date/time, reasoning and both completed review stages. Set the three suite-level review flags
only after doing those reviews.

Compare intended facts and paraphrases with all exposed development versions, the old regression
and demo questions listed in [public exposure inventory](../../../configs/evidence/evaluation/public-exposure-v1.json).
The inventory has 142 records / 64 distinct wordings / 31 intent groups. It is a known repository
inventory, not proof that all past conversation exposure has been captured. Review that history too.
Different wording alone does not make a question independent. If a development revision is needed,
tell this chat only what public development material needs changing; keep the protected question private.

## 4. Run the checker privately

Use Terminal.app outside an agent-connected terminal, while agents are idle. From the repository:

```sh
.venv-retrieval/bin/python -m src.retrieval.private_evaluation --prepare
```

Confirm the private session and enter your private JSON path at the hidden prompt. Do not put it in
the command line or send it to this chat. The input must be an ordinary, non-symlink JSON file outside
the repository, at most 2 MiB. The tool cannot establish whether the location is encrypted or whether
other agents can access it; those remain your responsibility. A terminal check is not a security sandbox.

The checker verifies the closed format, corpus versions, exact evidence offsets, concept coverage,
counts, family/difficulty coverage and exact exposed wording/intent reuse. It does not judge entailment
or detect all paraphrases. Review assertions remain human attestations.

Successful output goes beside your input into a new `<input-stem>.validated` directory containing
`validated-set.json` and `validation.json`, with owner-only permissions. The input is unchanged and
existing outputs are never overwritten. For revisions, keep prior evidence and use a new draft name.
A failed write can leave an incomplete output directory; no atomic or power-loss guarantee is claimed.
Without `--prepare`, existing content hashes are checked instead of recalculated. Do not paste private
files, paths or content-bearing diagnostics here. The tool's fixed failure message can be shared.

## 5. Finish the protected freeze

Mechanical success is not the final freeze. Preserve authoring history, build the private content
manifest, freeze the encrypted image, verify the independent encrypted backup and unmount it as
described in the authoring worksheet. These storage/freeze operations are not automated by this checker.
Only then complete the closed, content-free public receipt with genuine hashes, counts and attestations.
The validation report's suite hash is not a substitute for the separately required content-manifest hash.

Current state: the public protected receipt remains `not_created`, and retrieval comparisons remain
gated. No actual protected questions or labels have been authored, opened or validated by this task.
Once the real protected freeze receipt is complete, the next engineering step is the development
retrieval comparison, followed by readable cited summaries and viewer integration.

## Delivered checks

28 invented-input private-validator tests and 36 public-checkpoint tests pass. Public corpus loading
verifies ten sources / 947 passages and the exposure inventory. Tests are engineering checks, not
held-out performance results. The prior development validator still refuses private-set records.
