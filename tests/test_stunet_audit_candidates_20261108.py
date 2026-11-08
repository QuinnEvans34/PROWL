import unittest
import numpy as np
from src.inference.component_proximity_filter_v1 import filter_prediction


class FilterTests(unittest.TestCase):
    def test_reference_free_removal_preserves_pancreas_and_near_tissue(self):
        p=np.zeros((32,4,4),np.uint8);p[1,1,1]=1;p[2,1,1]=2;p[25,1,1]=2
        out,info=filter_prediction(p,np.eye(4))
        self.assertEqual(out[2,1,1],2);self.assertEqual(out[25,1,1],0)
        np.testing.assert_array_equal(out==1,p==1)
        self.assertEqual(p[25,1,1],2);self.assertEqual(len(info['removed_components']),1)

    def test_missing_context_fails_open(self):
        p=np.full((2,2,2),2,np.uint8)
        out,info=filter_prediction(p,np.eye(4));np.testing.assert_array_equal(out,p)
        self.assertFalse(info['context_available'])

    def test_physical_distance_not_voxel_count(self):
        p=np.zeros((4,2,2),np.uint8);p[0,0,0]=1;p[3,0,0]=2
        a=np.eye(4);a[0,0]=5
        self.assertEqual(filter_prediction(p,a)[0][3,0,0],0)


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        import torch
        torch.set_num_threads(1);torch.manual_seed(42)
        self.torch=torch
        self.outputs=[torch.randn(1,3,s,s,s,requires_grad=True) for s in (16,8,4,2,1)]
        self.target=torch.zeros((1,16,16,16),dtype=torch.long);self.target[0,1,1,1]=2

    def test_only_coarsest_logit_changes_ignored_by_candidate(self):
        from src.training.stunet_supervision_candidate_v1 import deep_supervision_loss as loss
        changed=list(self.outputs);changed[-1]=changed[-1]+self.torch.tensor([0.,2.,4.]).reshape(1,3,1,1,1)
        self.assertEqual(float(loss(changed,self.target,policy='omit_coarsest').detach()),float(loss(self.outputs,self.target,policy='omit_coarsest').detach()))
        self.assertNotEqual(float(loss(changed,self.target,policy='baseline').detach()),float(loss(self.outputs,self.target,policy='baseline').detach()))

    def test_zero_coarsest_gradient_not_missing(self):
        from src.training.stunet_supervision_candidate_v1 import deep_supervision_loss
        deep_supervision_loss(self.outputs,self.target,policy='omit_coarsest').backward()
        self.assertTrue(all(x.grad is not None and self.torch.isfinite(x.grad).all() for x in self.outputs))
        self.assertEqual(float(self.outputs[-1].grad.abs().sum()),0.)
        self.assertGreater(float(self.outputs[0].grad.abs().sum()),0.)

    def test_explicit_policy_required(self):
        from src.training.stunet_supervision_candidate_v1 import deep_supervision_loss
        with self.assertRaises(ValueError):deep_supervision_loss(self.outputs,self.target,policy='automatic')


if __name__=='__main__':unittest.main()
