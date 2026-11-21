import unittest
import numpy as np
from scripts.stunet_audit.review_candidate_translations import review


class TranslationReviewTests(unittest.TestCase):
    def test_crop_and_intensity_transform_rank_correct_translation_without_identity_claim(self):
        r = np.random.default_rng(15).normal(20, 80, (32, 34, 36)).astype(np.float32)
        q = r[3:27, 5:29, 7:31] * 1.2 + 7
        out = review(q, r)
        self.assertEqual(out['offset_voxels'], [3, 5, 7])
        self.assertGreater(out['whole_query_correlation'], .99999)
        self.assertLess(out['fitted_residual_rmse'], .0001)
        self.assertFalse(out['identity_confirmed'])

    def test_unrelated_signal_does_not_look_like_transformed_crop(self):
        rng = np.random.default_rng(22)
        out = review(rng.normal(size=(24, 24, 24)), rng.normal(size=(32, 32, 32)))
        self.assertLess(out['whole_query_correlation'], .1)

    def test_invalid_distributions_refused(self):
        for q in (np.ones((4, 4, 4)), np.full((4, 4, 4), np.nan)):
            with self.assertRaises(ValueError):
                review(q, np.ones((8, 8, 8)))
