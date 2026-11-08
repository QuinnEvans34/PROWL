import unittest
import numpy as np
from src.inference.component_error_audit_20261108 import inspect, summarize


def raw(p, y):
    n, m, t = int(y.sum()), int((p == 2).sum()), int(((p == 2) & (y != 0)).sum())
    from scipy.ndimage import label
    return dict(lesion=dict(target_voxels=n, predicted_voxels=m, true_positive=t, dice=2*t/(n+m) if n+m else None),
                pancreas=dict(dice=.8), reference_components=label(y, structure=np.ones((3,3,3)))[1])


class ComponentAuditTests(unittest.TestCase):
    def test_attached_fp_and_distant_blob(self):
        p=np.zeros((32,4,4),np.uint8);y=p.copy();p[1,1,1]=1;p[2:4,1,1]=2;y[2,1,1]=1;p[25,1,1]=2
        r=inspect(p,y,np.eye(4),raw(p,y))
        self.assertEqual([c['false_positive_voxels'] for c in r['components']],[1,1])
        self.assertEqual(r['policies']['near_predicted_pancreas_10mm']['lesion']['predicted_voxels'],2)
        self.assertEqual(r['policies']['oracle_remove_reference_disjoint_components']['lesion']['predicted_voxels'],2)
        self.assertFalse(r['policies']['at_least_100mm3']['case_detected'])

    def test_world_distance_and_shear(self):
        p=np.zeros((7,7,3),np.uint8);y=p.copy();p[0,0,0]=1;p[4,4,0]=2;y[4,4,0]=1
        a=np.eye(4);a[:2,:2]=[[2,1],[0,3]]
        r=inspect(p,y,a,raw(p,y))
        self.assertAlmostEqual(r['components'][0]['min_predicted_pancreas_center_distance_mm'],(12**2+12**2)**.5)
        self.assertFalse(r['policies']['near_predicted_pancreas_10mm']['case_detected'])

    def test_no_pancreas_fails_open(self):
        p=np.zeros((3,3,3),np.uint8);p[1,1,1]=2;y=p==2
        r=inspect(p,y,np.eye(4),raw(p,y))
        self.assertIsNone(r['components'][0]['min_predicted_pancreas_center_distance_mm'])
        self.assertTrue(r['policies']['near_predicted_pancreas_10mm']['case_detected'])

    def test_reference_drift_rejected(self):
        p=np.zeros((3,3,3),np.uint8);y=p.copy();r=raw(p,y);r['lesion']['target_voxels']=1
        with self.assertRaises(ValueError):inspect(p,y,np.eye(4),r)

    def test_components_cannot_gain_true_tissue(self):
        p=np.zeros((32,4,4),np.uint8);y=p.copy();p[1,1,1]=1;p[2,1,1]=2;y[2,1,1]=1;p[25,1,1]=2
        r=inspect(p,y,np.eye(4),raw(p,y));r['case_id']='a'
        s=summarize([r],require_full=False)
        self.assertFalse(s['guards']['at_least_100mm3']['passes'])
        self.assertEqual(s['guards']['at_least_100mm3']['lost_components'],[dict(case_id='a',component_id=1)])
        self.assertEqual(s['component_groups']['reference_disjoint/far_gt10mm']['false_positive_voxels'],1)

    def test_duplicate_or_incomplete_cohort_rejected(self):
        with self.assertRaises(ValueError):summarize([])


if __name__=='__main__':unittest.main()
