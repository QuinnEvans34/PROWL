# SuPreM preparation handback — October6,2026

## Phone handback

1. **Finished:** the approved repository-text/control review and
   [concrete qualification packet](SUPREM-INITIALIZATION-QUALIFICATION-PACKET-2026-10-06.md).
   Current scratch and historical SuPreM-compatible backbone configurations match. Actual source
   qualification is still open; no weight payload or model computation was used.
2. **Changed/checks:** two new review/packet documents and this chat's queue/AGENTS/notebook
   pointers. Static architecture trace, retained203-file inventory JSON, source pins, local links,
   scoped whitespace/diff and historical-tail preservation are checked. No new unit/full-suite
   claim; successful prior suites were not repeated. W01-08 tracks this drafting task on Trello.
3. **Decision needed:** whether to implement SUP-01's exact four-file in-memory auditor with
   invented CPU tensors. Actual candidate rights, protected-evaluation relationship and payload
   compatibility are not accepted by approving that coding slice.
4. **Restart:** begin at the packet's SUP-01 allowlist/interface/tests after that implementation
   scope is approved. Stop after its handback; real source audit and pretrained consumer follow later.

## Findings and limits

The v5 scratch factory routes through `segmenter_session_v1.ARCH` and the existing SegResNet builder:
1input/3output channels,16initial filters,GroupNorm8,down[1,2,2,4]/up[1,1,1],zero dropout.
The historical definition matches. An initial commentary about a width/block mismatch was corrected
after tracing this factory; it is not a project finding. Actual source tensor equality was not tested.

The historical loader permits shape-matching partial imports and ignores source-only tensors. The
head-only variant mutates before assertions. The proposed auditor checks complete inventories and
controls before returning cloned replacement state, preserves precisely the fresh three-class head,
and exposes no file reader or real-session switch. The current v5 import-denial and scratch checkpoint
identity remain unchanged.

The retained D-326 JSON records the SuPreM candidate at56,500,623bytes with SHA-256
`2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3` and
`weight_import_allowed=false`. Reading that record establishes the recorded identity, not current
file presence, licensed origin or architecture/source acceptance. The current source release,
checkpoint/data terms, retrieval linkage, protected-evaluation relationship and serializer remain
unverified. No upstream page was accessed. Prior fine-tuned checkpoints remain prohibited.

## Reviewed input pins

| Input read | SHA-256 |
|---|---|
| `src/models/segresnet.py` | `d3fff9db229c3641aab2456a54cce64d7ebf08494a9fe1abef241cef7d8b722d` |
| `src/training/segmenter_session_v1.py` | `0dbc18456a238c0a4dff30e6ec201bdb28e44b37c50bd2f7efa4e44c3b291a6d` |
| `src/training/segmenter_v5_training_session_v1.py` | `d6f9059c16c1f8b34261a63203bde5da7ec056d1dc782a2675b3f838366b5d36` |
| `src/training/segmenter_v5_executor_v1.py` | `007e711991b305d117afaaaa03401a50e7818c44319157dbb349b4f9baf36444` |
| `configs/level45.yaml` | `a76321cf44464a89582511cf1111009d72063627ad6ef2f146281177a0b22df6` |
| `scripts/train.py` | `7daafae7acbe3e2d1cd115604587c3fe53e8688cc41800df0b5cd963b4f817d5` |
| `scripts/legacy/inspect_checkpoint.py` | `bd7393a3c4b4b92281c8ddbcf9d891eaa85b51ec644ee446f5707281821b923e` |
| `scripts/diagnostics/segmenter_checkpoint_inventory.py` | `8ed669b46198bd7f2466840542ecc3cdaab2b844432394c06b407d224a04b3cf` |
| `tests/test_segmenter_v5_transaction.py` | `a6af9d08834ffce2a540e9e4f30345420c95a326db950754ee7e990c27ee4dea` |
| `tests/test_segmenter_training_transaction.py` | `e05d6f50bb067ac75a2ff473ecfb94ee0352c54a227857ce5520883a3027b4f7` |
| `docs/capstone/imaging/MODEL-LINEAGE-AND-TRAINING.md` | `46750c72235490c8a4c370a25db1d8ca57b2a9490954ff97b5b996c5264b9523` |
| Retained checkpoint-inventory `result.json` | `994e2a13b99e04c8b1f3d8dee176ef04f7146db77fa5fe6254f851aac4b3fe3d` |

These are current read pins, not replacement D-335 producer pins. No reviewed source/test changed.
The protected experiment marker-to-end SHA-256 stays
`df37ba7cdec1ae1fb941feb5e60a87ef599f28118d5415a50032397bbe96b997`.
Exact verification results and Trello completion/readback are recorded below after final checking.

**Final static verification:**12reviewed input pins match, including the retained inventory JSON;
203recorded inventory members and the exact candidate entry reconcile. Eight architecture fields
match between current source and historical configuration.159local Markdown link occurrences
resolve across the five edited documents. New documents have no trailing whitespace and all edited
files end with newlines. Scoped `git diff --check` passes. The protected historical tail is unchanged.
The three named future code/test/contract paths are absent, confirming this remains a draft.
No prior targeted tests or full suite were rerun. Missing historical inspector paths were resolved
through the file inventory to `scripts/legacy/inspect_checkpoint.py`; no replacement was created.

Trello [W01-08](https://trello.com/c/fB1rBcPM/30-w01-08-prepare-suprem-initialization-qualification-packet)
was created at drafting start, updated with the findings/next scope, moved to Done and marked
complete. Final readback verified its exact description, Done list and completion flag. This is
completion of the drafting task; SUP-01 implementation and source qualification remain open.

## Boundaries and remaining work

No new source/test implementation, weight read/deserialization/import, model instantiation/forward/
update, accelerator work, download, source stat/header/array job, install, external write, deletion,
Git commit/push or experiment registration occurred. No new directory was created. D-335 remains
the complete/consumed experiment checkpoint. Cohorts/holds/failures and the fixed backup ceiling
remain unchanged. Retrieval and N4 remain with their existing owners. Human hours are unknown;
agent runtime is excluded and the hours log is not credited with an estimate.

The recommended order is SUP-01 invented audit, bounded public-source and actual-checkpoint
qualification, then separately versioned pretrained consumer/recovery integration. The varied-data
candidate/negative-standard scope stays visible. The192-update duration policy is delivered but
does not authorize an executor or training. Follow-ups wait quietly after this drafting handback.
