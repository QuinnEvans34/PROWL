import unittest

from scripts.diagnostics.review_error_oracles_20261108 import positive_case, summarize, bound_json


class ErrorOracleTests(unittest.TestCase):
    def test_known_confusion_counts(self):
        r = positive_case('case', 10, 20, 5, 1/3)
        self.assertEqual(r['false_positive'], 15)
        self.assertEqual(r['false_negative'], 5)
        self.assertAlmostEqual(r['perfect_fp_removal_dice'], 2/3)
        self.assertAlmostEqual(r['perfect_fn_recovery_dice'], 20/35)

    def test_removal_cannot_recover_complete_miss(self):
        for p in (0, 100):
            r = positive_case('case', 10, p, 0, 0)
            self.assertEqual(r['perfect_fp_removal_dice'], 0)

    def test_perfect_prediction_is_unchanged(self):
        r = positive_case('case', 10, 10, 10, 1)
        self.assertEqual(r['fp_removal_gain'], 0)
        self.assertEqual(r['fn_recovery_gain'], 0)

    def test_impossible_or_noninteger_counts_rejected(self):
        for counts in ((10, 2, 3), (0, 0, 0), (-1, 2, 0), (True, 2, 1), (10., 2, 1)):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                positive_case('case', *counts, 0)

    def test_saved_dice_must_reproduce(self):
        for dice in (.2, float('nan'), float('inf')):
            with self.subTest(dice=dice), self.assertRaises(ValueError):
                positive_case('case', 10, 20, 5, dice)

    def cohort(self):
        # Half the positives have zero recall, half perfect recall: nonlinear macro check.
        return [dict(case_id=str(i), target_voxels=10, predicted_voxels=20,
                     true_positive=0 if i < 18 else 10, dice=0 if i < 18 else 2/3,
                     size_band=('small', 'medium', 'large')[i % 3]) for i in range(36)] + [
            dict(case_id=str(i), target_voxels=0, predicted_voxels=100,
                 true_positive=0, dice=0, size_band='empty') for i in range(36, 70)]

    def test_macro_is_mean_of_per_case_oracles(self):
        r = summarize(self.cohort(), 1/3)['summary']
        self.assertEqual(r['perfect_fp_removal_dice'], .5)
        self.assertNotAlmostEqual(r['perfect_fp_removal_dice'], 2*.5/(1+.5))
        self.assertEqual(r['removing_only_empty_case_alarms_positive_macro_dice'], 1/3)
        self.assertEqual(r['empty_false_positive_voxels'], 3400)

    def test_cohort_identity_and_class_denominators_required(self):
        rows = self.cohort()
        rows[1]['case_id'] = rows[0]['case_id']
        with self.assertRaises(ValueError):
            summarize(rows, 1/3)
        with self.assertRaises(ValueError):
            summarize(self.cohort()[:-1], 1/3)

    def test_input_tampering_rejected(self):
        with self.assertRaises(ValueError):
            bound_json(b'{}', '0'*64)


if __name__ == '__main__':
    unittest.main()
