import tempfile
from pathlib import Path
import unittest
import math
import torch
from src.training.stunet_transfer_20261106 import architecture, transfer_state, deep_supervision_loss


class TransferTests(unittest.TestCase):
    def states(self):
        return ({'body':torch.ones(2), 'seg_outputs.0.weight':torch.ones(5,2,1,1,1)},
                {'body':torch.zeros(2), 'seg_outputs.0.weight':torch.zeros(3,2,1,1,1)})

    def test_strict_body_fresh_heads(self):
        src,dst=self.states(); result=transfer_state(src,dst)
        self.assertTrue(torch.equal(result['body'],src['body']))
        self.assertTrue(torch.equal(result['seg_outputs.0.weight'],dst['seg_outputs.0.weight']))

    def test_missing_unexpected_and_prefix_rejected(self):
        src,dst=self.states()
        for bad in ({},dict(src,extra=torch.ones(1)),{'module.'+k:v for k,v in src.items()}):
            with self.assertRaises(ValueError):transfer_state(bad,dst)

    def test_bad_body_dtype_shape_finite(self):
        for t in (torch.ones(3),torch.ones(2).double(),torch.tensor([float('nan'),1])):
            src,dst=self.states(); src['body']=t
            with self.assertRaises(ValueError):transfer_state(src,dst)

    def test_source_pin_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.py';p.write_text('raise RuntimeError("executed")')
            with self.assertRaisesRegex(ValueError,'pin'):architecture(p)

    def test_loss_finite_and_all_scale_gradients(self):
        target=torch.zeros(1,16,16,16,dtype=torch.long);target[:,4:12,4:12,4:12]=1;target[:,7:9,7:9,7:9]=2
        outs=[torch.zeros(1,3,n,n,n,requires_grad=True) for n in (16,8,4,2,1)]
        loss=deep_supervision_loss(outs,target);loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(all(o.grad is not None and torch.isfinite(o.grad).all() and o.grad.abs().sum()>0 for o in outs))

    def test_bad_targets_and_scales(self):
        target=torch.zeros(1,16,16,16,dtype=torch.long)
        outs=[torch.zeros(1,3,n,n,n) for n in (16,8,4,2,1)]
        for bad in (target.float(),target+3):
            with self.assertRaises(ValueError):deep_supervision_loss(outs,bad)
        with self.assertRaises(ValueError):deep_supervision_loss(outs[:4],target)
        with self.assertRaises(ValueError):deep_supervision_loss(outs[::-1],target)

    def test_uniform_logits_empty_target_exact_reduction(self):
        sizes=(16,8,4,2,1)
        outs=[torch.zeros(1,3,n,n,n) for n in sizes]
        target=torch.zeros(1,16,16,16,dtype=torch.long)
        expected=sum(w*(math.log(3)+1-1e-5/(n**3/3+1e-5))
                     for w,n in zip((16/31,8/31,4/31,2/31,1/31),sizes))
        self.assertAlmostEqual(deep_supervision_loss(outs,target).item(),expected,places=5)


if __name__=='__main__': unittest.main()
