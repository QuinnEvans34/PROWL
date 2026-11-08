import json
from pathlib import Path
import unittest
import numpy as np
from src.inference.standard_segmentation_postprocess_v1 import postprocess,POLICY_ID,MAXIMUM_DISTANCE_MM


class StandardPolicyTests(unittest.TestCase):
    def test_five_mm_default_and_raw_retained(self):
        p=np.zeros((12,3,3),np.uint8);p[0,1,1]=1;p[4,1,1]=2;p[7,1,1]=2
        before=p.copy();out,details=postprocess(p,np.eye(4))
        self.assertEqual(out[4,1,1],2);self.assertEqual(out[7,1,1],0)
        np.testing.assert_array_equal(p,before);self.assertTrue(details['applied'])
        self.assertEqual(details['policy_id'],POLICY_ID)

    def test_missing_pancreas_is_recorded_not_silently_deleted(self):
        p=np.full((3,3,3),2,np.uint8);out,details=postprocess(p,np.eye(4))
        np.testing.assert_array_equal(out,p);self.assertFalse(details['applied'])
        self.assertEqual(details['reason'],'predicted_pancreas_missing')

    def test_shared_config_matches_executable_policy(self):
        p=Path(__file__).resolve().parents[1]/'configs/inference/segmentation-postprocessing-v1.json'
        config=json.loads(p.read_text())
        self.assertEqual(config['policy_id'],POLICY_ID)
        self.assertEqual(config['maximum_distance_mm'],MAXIMUM_DISTANCE_MM)
        self.assertTrue(config['retain_raw_outputs'])
        self.assertFalse(config['apply_to_existing_frozen_runs'])


if __name__=='__main__':unittest.main()
