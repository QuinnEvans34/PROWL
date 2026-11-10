import unittest
from copy import deepcopy

import numpy as np

from src.inference import stunet_margin_screen_20261110 as screen
from src.inference.component_proximity_filter_v1 import filter_prediction
from src.training.pants_native_evaluation import native_metrics


class MarginScreenTests(unittest.TestCase):
    def test_all_policy_counts_match_independent_native_voxel_scoring(self):
        rng = np.random.default_rng(17)
        p = rng.random((3, 9, 8, 7), dtype=np.float32)
        p /= p.sum(0)
        code = screen.encode(p)
        pancreas = (rng.random(code.shape) > .6).astype(np.uint8)
        lesion = (rng.random(code.shape) > .96).astype(np.uint8)
        affine = np.array([[.7, .2, 0, 10], [0, 1.2, .1, -4], [0, 0, 2.5, 9], [0, 0, 0, 1]])
        results = screen.score_case(code, pancreas, lesion, affine)
        self.assertEqual(len(results), 54)
        for key, policy in screen.policies().items():
            with self.subTest(policy=key):
                pred = screen.apply(code, affine, policy)
                direct = native_metrics(pred, pancreas, lesion, affine)
                self.assertEqual({k:v for k,v in results[key].items() if k != 'hit_component_ids'}, direct)
        raw = screen.decode(code, 0.)
        standard, _ = filter_prediction(raw, affine, maximum_distance_mm=5.)
        np.testing.assert_array_equal(standard, screen.apply(code, affine, screen.policies()['bias0_near5_min0']))

    def test_lossless_all_bias_replay_and_ties(self):
        p = np.array([[.4, .1, 1/3, 0], [.2, .8, 1/3, 0], [.4, .1, 1/3, 1]], dtype=np.float32).reshape(3, 1, 1, 4)
        code = screen.encode(p)
        for b in screen.BIASES:
            adjusted = p.astype(np.float64).copy()
            adjusted[2] *= np.exp(b)
            np.testing.assert_array_equal(screen.decode(code, b), adjusted.argmax(0))
        np.testing.assert_array_equal(screen.decode(code, 0.), p.argmax(0))
        np.testing.assert_array_equal(screen.unpack(screen.pack(code), list(code.shape)), code)
        odd = np.array([0, 1, 11], dtype=np.uint8).reshape(1, 1, 3)
        np.testing.assert_array_equal(screen.unpack(screen.pack(odd), [1, 1, 3]), odd)

    def test_growing_candidate_recovers_tissue_but_rejects_unseeded_blob(self):
        p = np.zeros((3, 9, 3, 3), dtype=np.float32)
        p[0] = .8; p[1] = .1; p[2] = .1
        p[:, 1, 1, 1] = [.1, .8, .1]  # raw pancreas context
        p[:, 2, 1, 1] = [.1, .1, .8]  # confident lesion seed
        p[:, 3, 1, 1] = [.5, .1, .4]  # weak attached extension
        p[:, 6, 1, 1] = [.5, .1, .4]  # weak detached blob
        code = screen.encode(p)
        policy = screen.policies()['grow0.5_seed-0.5_near5']
        result = screen.apply(code, np.eye(4), policy)
        self.assertEqual(result[3, 1, 1], 2)
        self.assertEqual(result[6, 1, 1], 0)
        self.assertEqual(result[1, 1, 1], 1)

    def test_full_affine_distance_and_missing_pancreas_fail_open(self):
        pred = np.zeros((7, 2, 2), dtype=np.uint8)
        pred[0, 0, 0] = 1; pred[3, 0, 0] = 2
        p = np.eye(3, dtype=np.float32)[pred].transpose(3, 0, 1, 2)
        code = screen.encode(p)
        affine = np.diag([2., 1., 1., 1.])
        settings = screen.policies()['bias0_near5_min0']
        self.assertEqual(screen.apply(code, affine, settings)[3, 0, 0], 0)
        code[0, 0, 0] = 0
        self.assertEqual(screen.apply(code, affine, settings)[3, 0, 0], 2)

    def test_empty_reference_and_replay_reject_corruption(self):
        p = np.zeros((3, 2, 2, 3), dtype=np.float32); p[0] = 1
        code = screen.encode(p)
        result = screen.score_case(code, np.zeros(code.shape, np.uint8), np.zeros(code.shape, np.uint8), np.eye(4))
        self.assertTrue(all(m['lesion']['dice'] is None for m in result.values()))
        for corrupt in (np.array([15], np.uint8), np.array([240], np.uint8)):
            with self.assertRaises(ValueError):
                screen.unpack(corrupt, [1, 1, 1])
        with self.assertRaises(ValueError):
            screen.encode(p*np.nan)
        with self.assertRaises(ValueError):
            screen.components(code, 0., np.zeros((4, 4)))

    def test_higher_dice_with_a_lost_component_remains_ineligible(self):
        base = dict(lesion=dict(target_voxels=10, predicted_voxels=100, true_positive=5, dice=10/110),
            pancreas=dict(dice=.8), reference_positive=True, target_volume_mm3=100.,
            voxel_mm3=10., reference_components=2, detected_components=2,
            hit_component_ids=[1, 2], case_detected=True, false_alarm_any=False)
        metrics = {k:deepcopy(base) for k in screen.policies()}
        name = 'bias0_near5_min0'
        candidate = metrics[name]
        candidate['lesion'].update(predicted_voxels=5, dice=10/15)
        candidate.update(hit_component_ids=[1], detected_components=1)
        rows = [dict(case_id='synthetic-positive', policies=metrics)]
        result = screen.summarize(rows, require_full=False)
        self.assertTrue(result['guards'][name]['checks']['dice_gain_at_least_02'])
        self.assertFalse(result['guards'][name]['passes'])
        self.assertEqual(result['selected_exploratory_policy'], 'raw')
        self.assertEqual(result['guards'][name]['lost_components'], [dict(case_id='synthetic-positive', component_id=2)])
        candidate['target_volume_mm3'] += 1
        with self.assertRaisesRegex(ValueError, 'Matched reference'):
            screen.summarize(rows, require_full=False)

    def test_complete_cohort_is_required_for_final_selection(self):
        p = np.zeros((3, 2, 2, 3), dtype=np.float32); p[0] = 1
        code = screen.encode(p)
        metrics = screen.score_case(code, np.zeros(code.shape, np.uint8), np.zeros(code.shape, np.uint8), np.eye(4))
        with self.assertRaisesRegex(ValueError, 'denominators'):
            screen.summarize([dict(case_id='synthetic', policies=metrics)])


if __name__ == '__main__':
    unittest.main()
