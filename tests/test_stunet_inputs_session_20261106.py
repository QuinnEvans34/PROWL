import unittest
import numpy as np
import torch
from src.data.stunet_inputs_20261106 import select_origin
from src.training.stunet_session_20261106 import lr_at,compare,cpu_tree,rng_state,restore_rng
from scripts.diagnostics.plan_stunet_coverage_20261106 import check_cover
from src.data.segmenter_physical_windows_v1 import coverage_bank,sample_window,PhysicalReconstructor
from src.data.segmenter_native_windows_v1 import tiles


class InputTests(unittest.TestCase):
    def test_schedule_lr(self):
        self.assertAlmostEqual(lr_at(0),2e-7,places=18);self.assertEqual(lr_at(499),1e-4);self.assertEqual(lr_at(11999),0)
        with self.assertRaises(ValueError):lr_at(12000)

    def test_complete_bank_and_gap_rejection(self):
        t=np.ones((150,20,12),np.uint8);r={'native_shape':list(t.shape),'shape':list(t.shape),'factors':[1,1,1]}
        bank=coverage_bank(t>0,r,window=128);check_cover(t,r,bank)
        with self.assertRaises(ValueError):check_cover(t,r,[bank[0]])

    def test_component_anchor_and_determinism(self):
        m={'record':{'shape':[300,200,180]},'parts':[{'low':[4,6,8],'high':[240,110,130],'anchor':[110,50,60]}]}
        e={'case_id':'train','kind':'component_jitter'}
        a,trace=select_origin(e,m,13);b,_=select_origin(e,m,13);self.assertEqual(a,b)
        self.assertTrue(all(0<=x-o<128 for x,o in zip(trace['anchor'],a)))

    def test_boundary_padding_and_reconstruction(self):
        shape=(140,5,3);a=np.ones(shape,np.float32);r={'native_shape':list(shape),'shape':list(shape),'factors':[1,1,1]}
        recon=PhysicalReconstructor(r,window=128);windows=tiles(shape,window=128,stride=64)
        for origin in windows:
            x,transform=sample_window(a,r,origin,order=1,window=128)
            self.assertEqual(x.shape,(128,128,128));self.assertEqual(transform['normalized_shape'][1:],[5,3])
            prob=np.zeros((3,128,128,128),np.float32);prob[1]=1;recon.add(origin,prob)
        result=recon.finish(windows);self.assertTrue(np.all(result[1]==1))

    def test_full_state_comparison_and_rng(self):
        a={'tensor':torch.tensor([1.]),'tuple':(3,'x')};b=cpu_tree(a);compare(a,b)
        b['tensor']+=.01
        with self.assertRaises(ValueError):compare(a,b)
        state=rng_state(torch.device('cpu'));x=torch.rand(3);restore_rng(state,torch.device('cpu'));self.assertTrue(torch.equal(x,torch.rand(3)))


if __name__=='__main__':unittest.main()
