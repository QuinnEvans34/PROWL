from copy import deepcopy
from pathlib import Path
import unittest

from scripts.diagnostics.compare_stunet_checkpoints import bundle_arm
from src.training.stunet_checkpoint_review import RAW, FIXED_5MM, compare_checkpoints


ARCHIVE = (Path(__file__).resolve().parents[1] / 'docs/capstone/coordination'
           / 'LENOVO-STUNET-CORRECTED-COMPLETE-NATIVE-METADATA-20261110.json')


class CheckpointReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline, cls.identities, _ = bundle_arm(ARCHIVE, 18000, RAW)
        cls.candidate, _, _ = bundle_arm(ARCHIVE, 24000, RAW)

    def compare(self, baseline=None, candidate=None, identities=None):
        return compare_checkpoints(baseline or self.baseline, candidate or self.candidate,
                                   self.identities, identities or self.identities, policy=RAW)

    def test_legacy_counts_without_component_identities(self):
        result = self.compare()
        self.assertAlmostEqual(result['baseline']['positive_macro_dice'], .43051696723124094)
        self.assertAlmostEqual(result['candidate']['positive_macro_dice'], .41197206677087506)
        self.assertEqual(sum(result['overlap_transitions'].values()), 36)
        self.assertEqual(result['component_changes']['status'], 'unavailable_missing_reference_hit_ids')

    def test_same_hit_count_can_hide_a_swap(self):
        baseline = deepcopy(self.baseline)
        for row in baseline['cases']:
            m = row['metrics']
            m['hit_ids'] = list(range(1, m['detected_components'] + 1))
            row['small_ids'] = []
        swap = next(row for row in baseline['cases']
                    if 0 < row['metrics']['detected_components'] < row['metrics']['reference_components'])
        swap['small_ids'] = [1]
        candidate = deepcopy(baseline)
        changed = next(row for row in candidate['cases'] if row['case_id'] == swap['case_id'])
        added = changed['metrics']['reference_components']
        changed['metrics']['hit_ids'][0] = added
        result = self.compare(baseline, candidate)['component_changes']
        self.assertEqual(result['lost'], [dict(case_id=swap['case_id'], component_id=1, under_1mL=True)])
        self.assertEqual(result['gained'], [dict(case_id=swap['case_id'], component_id=added, under_1mL=False)])

    def test_rejects_mismatched_identity_and_coverage(self):
        for field in ('native_affine', 'source_sha256', 'native_shape'):
            with self.subTest(field=field):
                identities = deepcopy(self.identities)
                row = identities[0]
                if field == 'native_affine':
                    row[field][0][3] += 1
                elif field == 'native_shape':
                    row[field][0] += 1
                else:
                    row[field]['lesion'] = 'a' * 64
                with self.assertRaisesRegex(ValueError, 'geometry'):
                    self.compare(identities=identities)
        for case_error in ('missing', 'duplicate', 'gap'):
            with self.subTest(case_error=case_error):
                candidate = deepcopy(self.candidate)
                if case_error == 'missing':
                    candidate['cases'].pop()
                elif case_error == 'duplicate':
                    candidate['cases'][0] = candidate['cases'][1]
                else:
                    candidate['cases'][0]['gaps'] = 1
                with self.assertRaises(ValueError):
                    self.compare(candidate=candidate)

    def test_rejects_policy_and_step_mismatch(self):
        candidate = deepcopy(self.candidate)
        candidate['policy'] = FIXED_5MM
        with self.assertRaisesRegex(ValueError, 'policy'):
            self.compare(candidate=candidate)
        with self.assertRaisesRegex(ValueError, 'chronological'):
            self.compare(self.candidate, self.baseline)


if __name__ == '__main__':
    unittest.main()
