"""Opt-in corrected VariedInputs; original providers and evaluation stay unchanged.

This on-demand provider does not claim the fast prefetch policy. A new receipt is
required: its control identity binds the original provider and correction cache.
"""
from copy import deepcopy
from pathlib import Path
import nibabel as nib
import numpy as np
from src.data.manifest_records import canonical, digest
from src.data.pants_errata_v1 import EXPECTED
from src.data.pants_errata_cache_v1 import load_target
from src.data.segmenter_varied_region_v1 import VariedInputs
from src.data.segmenter_fast_varied_v1 import source_info, normalize_region


class ErrataInputs(VariedInputs):
    def __init__(self, *, correction_root, correction_manifest_sha256,
                 overlay_sha256, **kwargs):
        super().__init__(**kwargs)
        if not set(EXPECTED) <= set(self.control['train']):
            raise ValueError('All corrected cases must retain training membership')
        self.correction_root = Path(correction_root)
        self.correction_manifest_sha256 = correction_manifest_sha256
        self.overlay_sha256 = overlay_sha256
        # Verify all derived members before declaring the new input identity.
        for name in EXPECTED:
            self.corrected_target(name)
        self.control = deepcopy(self.control)
        self.control['label_revision'] = dict(version='pants-errata-inputs-1',
            original_provider_sha256=self.pin, overlay_sha256=overlay_sha256,
            correction_manifest_sha256=correction_manifest_sha256,
            corrected_cases=sorted(EXPECTED), source='on_demand_original_CT',
            evaluation='unchanged_original_labels', prefetch=False)
        self.pin = digest(canonical(self.control))

    def corrected_target(self, name):
        return load_target(self.correction_root, name, role='train',
            manifest_sha256=self.correction_manifest_sha256,
            overlay_sha256=self.overlay_sha256)

    def load(self, name, *, role, operation='audit'):
        self.check_role(name, role, operation)
        if role != 'train' or name not in EXPECTED:
            return super().load(name, role=role, operation=operation)
        original, pin, _ = source_info(self, name, role, operation)
        target, small = self.corrected_target(name)
        if (small['metadata_sha256'] != pin
                or small['original_source_sha256'] != original['source_sha256']):
            raise ValueError('Corrected target original provenance changed')
        parent = small['parent_geometry']
        ct = nib.load(self.rows[name]['ct_path'])
        if (ct.shape != tuple(parent['source_shape']) or np.prod(ct.shape) > 256000000
                or not np.allclose(ct.affine, parent['source_affine'], atol=1e-5, rtol=0)):
            raise ValueError('Corrected target CT geometry changed')
        image = normalize_region(ct.get_fdata(dtype=np.float32, caching='unchanged'),
                                 parent, small['region_low'], small['region_high'])
        case = {k: v for k, v in small.items() if k not in ('record', 'cover', 'parts')}
        case.update(image=image, target=target)
        return case
