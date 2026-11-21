import unittest
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scripts.stunet_audit.align_candidate_samples_v2 import align


class SparseAlignmentTests(unittest.TestCase):
    def test_fractional_translation_with_intensity_change(self):
        r = gaussian_filter(np.random.default_rng(42).normal(100, 90, (56, 56, 56)), 1).astype(np.float32)
        coords = np.indices((48, 48, 48), dtype=float)
        offset = np.array([2.3, 3.6, 4.1])
        q = map_coordinates(r,coords+offset[:,None,None,None],order=1,prefilter=False)*1.2+7
        out = align(q, r, [2, 4, 4])
        np.testing.assert_allclose(out['fitted_offset_voxels'], offset, atol=.05)
        self.assertGreater(out['fitted_tissue_correlation'], .999)
        self.assertFalse(out['patient_identity_confirmed'])
        self.assertFalse(out['physical_units_assigned'])

    def test_unrelated_signal_does_not_become_identity(self):
        rng = np.random.default_rng(4)
        out = align(rng.normal(100, 50, (32, 32, 32)),rng.normal(100,50,(40,40,40)),[4,4,4])
        self.assertLess(out['fitted_tissue_correlation'], .1)
        self.assertFalse(out['image_identity_confirmed'])

    def test_constant_and_nonfinite_refused(self):
        for q in (np.full((8,8,8),np.nan),np.ones((8,8,8))):
            with self.assertRaises(ValueError):
                align(q,np.ones((16,16,16)),[4,4,4])
