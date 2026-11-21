import unittest
import numpy as np
from scripts.stunet_audit.confirm_cropped_images import exact_crop

class ExactCropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=np.random.default_rng(7).uniform(-200,700,(64,64,64)).astype(np.float32)
        cls.q=cls.r[7:55,9:57,5:53].copy()
    def test_entire_translated_crop_is_verified(self):
        result=exact_crop(self.q,self.r)
        self.assertEqual(result['status'],'EXACT_CROPPED_IMAGE_IDENTITY')
        self.assertEqual(result['offset_voxels'],[7,9,5])
        self.assertEqual(result['matching_query_voxels'],48**3)
        self.assertFalse(result['geometry_qualified'])
    def test_one_changed_voxel_cannot_pass(self):
        q=self.q.copy();q[0,0,0]+=0.01
        self.assertNotEqual(exact_crop(q,self.r,suggested_offsets=[[7,9,5]])['status'],'EXACT_CROPPED_IMAGE_IDENTITY')
    def test_unrelated_and_rescaled_not_exact(self):
        other=np.random.default_rng(9).uniform(-200,700,self.q.shape).astype(np.float32)
        for q in (other,self.q*1.01):self.assertNotEqual(exact_crop(q,self.r)['status'],'EXACT_CROPPED_IMAGE_IDENTITY')

if __name__=='__main__':unittest.main()
