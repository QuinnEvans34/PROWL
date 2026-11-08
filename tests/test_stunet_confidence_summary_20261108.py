import copy
import unittest
from scripts.diagnostics.summarize_stunet_confidence_20261108 import summarize, KEYS


def cohort():
    rows=[]
    for i in range(70):
        positive=i<36; n=10 if positive else 0; tp=5 if positive else 0
        metrics=dict(reference_positive=positive,reference_components=2 if i<9 else int(positive),
                     target_volume_mm3=100 if i<5 else (2000 if positive else 0),
                     voxel_mm3=1.,case_detected=positive,detected_components=2 if i<9 else int(positive),
                     hit_component_ids=([1,2] if i<9 else [1]) if positive else [],
                     false_alarm_any=not positive,
                     lesion=dict(target_voxels=n,predicted_voxels=40,true_positive=tp,dice=2*tp/(n+40)),
                     pancreas=dict(dice=.8))
        policies={k:copy.deepcopy(metrics) for k in KEYS}
        for key in KEYS[1:]:
            m=policies[key]
            m['lesion'].update(predicted_voxels=tp,dice=2*tp/(n+tp) if positive else None)
            m['false_alarm_any']=False
        h=dict(true_positive=[0]*100,false_positive=[0]*100)
        h['true_positive'][80]=tp;h['false_positive'][40]=40-tp
        rows.append(dict(case_id=str(i),policies=policies,confidence_histogram=h))
    return rows


class SummaryTests(unittest.TestCase):
    def test_safe_dice_gain_selected_with_lower_threshold_tie(self):
        r=summarize(cohort())
        self.assertEqual(r['selected_policy'],'0.4')
        self.assertTrue(r['guards']['0.4']['passes'])
        self.assertEqual(r['policies']['0.0']['positive_macro_dice'],.2)
        self.assertEqual(r['correlation']['quantized_auc_correct_vs_incorrect_raw_lesion_winners'],1.)

    def test_lost_component_blocks_even_when_case_hit_retained(self):
        rows=cohort()
        for key in KEYS[1:]:
            rows[0]['policies'][key]['hit_component_ids']=[1]
            rows[0]['policies'][key]['detected_components']=1
        r=summarize(rows)
        self.assertEqual(r['selected_policy'],'0.0')
        self.assertFalse(r['guards']['0.4']['checks']['no_lost_components'])
        self.assertTrue(r['guards']['0.4']['checks']['no_lost_cases'])

    def test_no_complete_or_unique_cohort_no_verdict(self):
        with self.assertRaises(ValueError):summarize(cohort()[:-1])
        rows=cohort();rows[1]['case_id']=rows[0]['case_id']
        with self.assertRaises(ValueError):summarize(rows)

    def test_confidence_counts_must_match_predictions(self):
        rows=cohort();rows[0]['confidence_histogram']['false_positive'][40]+=1
        with self.assertRaises(ValueError):summarize(rows)

    def test_policy_cannot_invent_new_true_positives(self):
        rows=cohort();rows[0]['policies']['0.4']['lesion'].update(true_positive=6,predicted_voxels=6,dice=.75)
        with self.assertRaises(ValueError):summarize(rows)


if __name__=='__main__':unittest.main()
