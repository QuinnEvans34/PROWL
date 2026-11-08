import copy
import unittest
from scripts.diagnostics.screen_saved_postprocessing_20261108 import summarize
from src.inference.saved_postprocess_screen_v1 import POLICIES


def cohort():
    rows=[]
    for i in range(70):
        positive=i<36;n=100 if positive else 0;tp=50 if positive else 0
        m=dict(lesion=dict(target_voxels=n,predicted_voxels=200,true_positive=tp,dice=2*tp/(n+200)),
            pancreas=dict(dice=.8),reference_positive=positive,reference_components=2 if i<9 else int(positive),
            case_detected=positive,detected_components=int(positive),hit_component_ids=[1] if positive else [],
            false_alarm_any=not positive,voxel_mm3=1. if i<5 else 20.,target_volume_mm3=n*(1. if i<5 else 20.))
        rows.append(dict(case_id=str(i),policies={name:copy.deepcopy(m) for name in POLICIES}))
    return rows


class SummaryTests(unittest.TestCase):
    def test_gain_without_recall_loss_passes(self):
        rows=cohort()
        for r in rows:
            m=r['policies']['near5'];m['lesion']['predicted_voxels']=100
            m['lesion']['dice']=2*m['lesion']['true_positive']/(m['lesion']['target_voxels']+100)
        result=summarize(rows,POLICIES)
        self.assertTrue(result['guards']['near5']['passes_raw_guards'])
        self.assertEqual(result['development_screen_leader'],'near5')

    def test_same_component_count_does_not_hide_lost_identity(self):
        rows=cohort();rows[0]['policies']['near5']['hit_component_ids']=[2]
        result=summarize(rows,POLICIES)
        self.assertFalse(result['guards']['near5']['checks']['no_lost_components'])
        self.assertEqual(result['guards']['near5']['lost_components'],[dict(case_id='0',component_id=1)])

    def test_incomplete_or_duplicate_cohort_rejected(self):
        rows=cohort()
        with self.assertRaises(ValueError):summarize(rows[:-1],POLICIES)
        rows[-1]['case_id']=rows[0]['case_id']
        with self.assertRaises(ValueError):summarize(rows,POLICIES)


if __name__=='__main__':unittest.main()
