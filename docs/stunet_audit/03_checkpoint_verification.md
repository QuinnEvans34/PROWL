# Checkpoint acquisition and verification

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

The original author-linked Google Drive artifact was downloaded to:

`/Volumes/PROWL-Data/PROWL/teachers/stunet-b-base-20261106/base_ep4k.model`

- Author README file ID: `1BHCp1Ort-OaVFwaZmvsG4qHiKiPeNb4h`.
- Bytes: **466,715,133**.
- SHA256: **7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a**.
- Transfer time: 27.336 seconds, recorded by the acquisition helper.
- Publisher checksum/signature: **not found**. Author-linked HTTPS provenance and local integrity are recorded; cryptographic authenticity is **not independently verified**.

No mirror or downstream-fine-tuned checkpoint was substituted. Large weights and the unmodified external source checkout are outside Git. `checkpoint_manifest.json` binds the source revision, URL, artifact, tensor inventory and successful probe report.

## Restricted loading, including refused attempts

The probe used CPU-only `torch.load(..., weights_only=True)`. Two earlier attempts safely refused NumPy metadata globals; their reports and resource receipts remain preserved under `outputs/prowl/stunet-audit-20261106/checkpoint-cpu-01` and `-02`. A successful wrapper exit in those attempts means a handled refusal, not a successful checkpoint load.

After static pickle-global inspection, the third attempt explicitly allowed only NumPy scalar/dtype metadata (`numpy.core.multiarray.scalar`, `numpy.dtype`, `Float64DType`, `Float32DType`) in addition to PyTorch's restricted loader. There was **no unrestricted-pickle fallback**. The small upstream plan was read separately using a restricted unpickler; arbitrary classes and persistent references were refused.

For model construction, the audit compiled only the four actual upstream `nn.Module` class definitions from the pinned v2 trainer's AST. It did not import the training launcher, install nnU-Net into the live environment or run a trainer. This is an isolated minimal CPU feasibility harness, not production integration. PyTorch version: 2.13.0.

## Actual successful synthetic check

Third attempt: **3.249 supervised seconds**, **5,132,632,064-byte peak owned RSS**, exit 0, workers reaped. One 64³ synthetic forward/backward, zero optimizer updates, zero clinical model forwards. Output shapes were three classes at 64³, 32³, 16³, 8³ and 4³. Mean synthetic multiscale cross-entropy was 2.8847744465; gradients were finite and nonzero. Exact loaded-body and unchanged-new-head checks passed.

This does not establish patient accuracy, 128³ GPU memory, throughput, preprocessing correctness, scientific repeatability, checkpoint recovery or deployment readiness. Those require separate bounded qualification before a scientific launch. The first two refusals are retained; they were not overwritten by the pass.
