# Minimal same-recipe reference request

Dependency for the four-case CUDA evaluation, not permission to interrupt Mac KD.
No suitable current-control prediction is present in the received packet or local
Week5 evidence. Historical resized predictions and scalar Dice reports do not meet
this requirement. The new Windows single-case diagnostic may proceed before parity,
but cannot qualify or unlock the batch by itself.

## Inputs and one-case scope

- Case: PanTS_00001070; CT SHA256
  `90bf329d4a959144dfc453c5f1adce83ac18b1d5493984cb8aaa3911a1f1000f`.
- Original native shape426x301x157; exact header affine and millimeter units must
  be bound to the request, not inferred from a mask.
- Localizer inference export SHA256
  `46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5`.
- Control20k inference export SHA256
  `8b2a104f9830776da7011a759f5dfddbc9750725380bf244f7d292f02aadcd63`;
  original checkpoint919ebd4c18e72aece8b47299b3a1ccc8a1f392be53e229d0921a04f74e6651ad.
- Use the packet's exact localizer-recipe.json (SHA256
  61d0be900c1ca802efd5602db9aa848b0b0c70eddeaeca5054f4744f58f3ee95),
  all_support,144cube/25%overlap/constant logits blend/argmax then native nearest.
- Segmenter: physical144/72, source-index10mm base then81/43/71mm expansion,
  HU[-100,250], three-channel float32 softmax, native-center probability blend,
  no AMP/TTA/threshold search; CUDA TF32 disabled. Outside ROI background.

## Runnable implementation interface

Fetch the laptop readiness branch without overwriting active producing files.
Use `src.inference.physical_cascade_v1.predict` from that reviewed commit, and
`src.inference.cascade_models_v1.load_weights` with the exact export hashes above:

```python
codes, mask, probabilities, evidence = predict(
    ct_array, native_affine, localizer=localizer, segmenter=segmenter,
    localizer_recipe=packet_localizer_recipe, device='mps',
    max_region_voxels=96_000_000, max_tiles=512,
    progress=owned_supervisor_resource_tick,
)
```

This is the exact prediction interface, not an unsupervised shell-launch command.
The Mac must bind its own paths/runtime/hash receipt and existing owned MPS
supervision before a runnable dispatch command is valid. Only after KD releases
the GPU and the Mac authorizes the bounded reference should it run this once.
No labels or optimizer are inputs. Do not automatically retry a failure.

Proposed Mac ceiling:600seconds,12GiB owned RSS,6GiB device allocation,2GiB output
and2GiB independent backup,100GiB free-space floor,AC and exclusive ownership.
The Mac must confirm these fit its applicable resource policy; they are not a
resource-policy override. Preserve failure and worker-cleanup evidence.

## Minimum private return packet

1. Native localizer uint8 mask and final uint8 codes (NIfTI, original shape/affine).
2. `region-probabilities.npy`: all3 float32 channels on closest-RAS native ROI,
   before argmax; not uint16, logits, resized tensors or a single lesion channel.
3. Evidence returned by predict: localizer transform, parent/local geometry,
   region_low/high, physical grid, blend minimum and zero-gap count.
4. Bound request: CT/model/recipe/source/runtime hashes, backend/precision, limits;
   file manifest; independent backup comparisons; timing/peak resources/exit/reaped.

If an already retained current-control provided-region probability reference exists,
send its exact identity/region/representation first. It can validate the segmenter
substage only after matching that assisted region in a separately labeled diagnostic;
it cannot alone validate autonomous localizer bounds. No replacement from old weights.

## Pre-result numerical rule proposed for review

Inherited laptop proposal, still awaiting explicit rule review: exact source/model/
recipe/native shape and ROI bounds; native affine absolute tolerance1e-5, zero
relative tolerance; all3 probabilities absolute tolerance1e-5 and relative1e-4;
hard-code disagreement fraction<=0.001. Require finite probabilities in[0,1],
sum-to-one within2e-5, valid0/1/2codes and zero reconstruction gaps. Compare probabilities
only on an identical ROI/grid; mismatched bounds fail admission rather than being
silently intersected. Record maxima and disagreement counts even on failure.
No tolerances are to be chosen or relaxed after seeing outputs. The four-case batch
remains blocked until this rule is reviewed and a valid reference passes it.
