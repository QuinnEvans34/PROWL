import unittest
import numpy as np
from src.inference.saved_postprocess_screen_v1 import physical_ball,recover,predictions,POLICIES


class SavedScreenTests(unittest.TestCase):
    def test_enclosed_background_hole_filled_pancreas_protected(self):
        p=np.zeros((7,7,7),np.uint8);p[1:6,1:6,1:6]=2;p[3,3,3]=0
        self.assertEqual(recover(p,np.eye(4),kind='holes')[3,3,3],2)
        p[3,3,3]=1;self.assertEqual(recover(p,np.eye(4),kind='holes')[3,3,3],1)
        p[2,3,3]=0;self.assertEqual(recover(p,np.eye(4),kind='holes')[2,3,3],0)

    def test_open_notch_is_not_enclosed_hole(self):
        p=np.zeros((7,7,7),np.uint8);p[1:6,1:6,1:6]=2;p[:4,3,3]=0
        np.testing.assert_array_equal(recover(p,np.eye(4),kind='holes'),p)

    def test_hole_volume_uses_physical_units(self):
        p=np.full((5,5,5),2,np.uint8);p[2,2,2]=0
        a=np.diag([5.,5.,5.,1.]);self.assertEqual(recover(p,a,kind='holes')[2,2,2],0)

    def test_closing_is_additive_and_protects_pancreas(self):
        p=np.zeros((9,9,9),np.uint8);p[2:7,2:7,2:7]=2;p[4,4,4]=0;p[4,4,5]=1
        out=recover(p,np.eye(4),kind='closing')
        self.assertTrue(np.all(out[p==2]==2));self.assertEqual(out[4,4,5],1)

    def test_ball_accounts_for_anisotropy(self):
        a=np.diag([1.,1.,5.,1.]);b=physical_ball(a)
        self.assertEqual(int(b.sum()),5)

    def test_fixed_grid_and_threshold_fallback(self):
        code=np.zeros((12,4,4),np.uint8);code[0,0,0]=1;code[1,1,1]=3;code[10,1,1]=8
        records=[dict(component_id=1,min_predicted_pancreas_center_distance_mm=1.),dict(component_id=2,min_predicted_pancreas_center_distance_mm=15.)]
        result={k:v.copy() for k,v in predictions(code,np.eye(4),records)}
        self.assertEqual(tuple(result),POLICIES)
        self.assertEqual(result['near10'][10,1,1],0)
        self.assertEqual(result['near10_conf04'][1,1,1],1)
        self.assertEqual(result['raw'][1,1,1],2)


if __name__=='__main__':unittest.main()
