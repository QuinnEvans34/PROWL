"""CT-only localizer plus physical-window segmenter; no reference inputs."""
import numpy as np
import torch
from monai.inferers import sliding_window_inference
from src.data import localizer_preprocessing_v4 as local_geometry
from src.data.segmenter_native_windows_v1 import tiles, orient
from src.data.segmenter_physical_windows_v1 import physical_geometry, sample_window, PhysicalReconstructor
from src.inference.predicted_physical_region_v1 import prepare


def hard_codes(probabilities):
    if (probabilities.ndim != 4 or probabilities.shape[0] != 3 or
            not np.isfinite(probabilities).all() or probabilities.min() < 0 or
            probabilities.max() > 1 or not np.allclose(probabilities.sum(0), 1, atol=2e-5, rtol=0)):
        raise ValueError('Invalid normalized three-class probabilities')
    codes = np.zeros(probabilities.shape[1:], np.uint8)
    best = probabilities[0].copy()
    for k in (1, 2):
        take = probabilities[k] > best
        codes[take] = k
        best[take] = probabilities[k][take]
    return codes


def embed(local, region):
    parent = region['parent_geometry']
    low, high = region['region_low'], region['region_high']
    if any(l < 0 or h <= l or h > n for l, h, n in zip(low, high, parent['shape'])):
        raise ValueError('Invalid region bounds')
    if local.shape != tuple(h-l for l, h in zip(low, high)):
        raise ValueError('Region shape mismatch')
    full = np.zeros(parent['shape'], local.dtype)
    full[tuple(slice(l, h) for l, h in zip(low, high))] = local
    return orient(full, parent, inverse=True)


@torch.inference_mode()
def segment(model, region, *, device, max_tiles, progress=lambda *args: None):
    """Matches existing physical executor's float32 softmax/native-center blend."""
    grid = physical_geometry(region['geometry'])
    origins = tiles(grid['shape'])
    if len(origins) > max_tiles:
        raise ValueError('Physical tile budget exceeded')
    recon = PhysicalReconstructor(grid)
    model.to(device).eval()
    for i, origin in enumerate(origins):
        progress('segmenter', i, len(origins))
        patch, _ = sample_window(region['image'], grid, origin, order=1)
        logits = model(torch.from_numpy(patch[None, None]).to(device))
        if tuple(logits.shape) != (1, 3, 144, 144, 144) or not torch.isfinite(logits).all():
            raise ValueError('Invalid segmenter logits')
        recon.add(origin, torch.softmax(logits, dim=1)[0].cpu().numpy())
    probabilities = recon.finish(origins)
    codes = hard_codes(probabilities)
    progress('segmenter', len(origins), len(origins))
    return embed(codes, region), probabilities, dict(tiles=len(origins),
        gap_voxels=int((recon.weight == 0).sum()), minimum_blend_weight=float(recon.weight.min()),
        physical_grid=grid, output_decision='native_center_probability_blend_then_argmax')


@torch.inference_mode()
def predict(image, affine, *, localizer, segmenter, localizer_recipe, device,
            max_region_voxels, max_tiles, progress=lambda *args: None):
    prepared = local_geometry.preprocess(image, affine, localizer_recipe)
    x = prepared['image'].as_tensor()
    transform = prepared['transform_record']
    localizer.to(device).eval()
    def forward(batch):
        progress('localizer', 0, 0)
        value = localizer(batch)
        if value.shape[1] != 2 or not torch.isfinite(value).all():
            raise ValueError('Invalid localizer logits')
        return value
    logits = sliding_window_inference(x[None], (144,)*3, 1, forward, overlap=.25,
        mode='constant', padding_mode='constant', sw_device=device, device='cpu')
    if tuple(logits.shape) != (1, 2, *x.shape[1:]):
        raise ValueError('Localizer shape changed')
    processed = logits[0].argmax(0, keepdim=True)
    mask = local_geometry.restore_to_source(processed, transform, discrete=True).as_tensor()[0].numpy().astype(np.uint8)
    del logits, processed, x, prepared
    # All predicted support; never select a component using reference labels.
    region = prepare(image, mask, affine, base_margin_mm=10., extra_margin_mm=[81.,43.,71.],
                     max_region_voxels=max_region_voxels)
    codes, probabilities, reconstruction = segment(segmenter, region, device=device,
        max_tiles=max_tiles, progress=progress)
    info = {k: v for k, v in region.items() if k != 'image'}
    info.update(localizer_transform=transform, reconstruction=reconstruction,
        localizer_policy='all_support', reference_inputs_used=False,
        probability_representation='float32_three_channels_on_closest_RAS_native_ROI',
        probability_outside_region=[1.,0.,0.])
    return codes, mask, probabilities, info
