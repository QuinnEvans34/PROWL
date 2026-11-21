import copy
import unittest
import torch
from src.training.stunet_activation_checkpointing_v1 import enable


class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_blocks_context = torch.nn.ModuleList([
            torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.ReLU(), torch.nn.Dropout(.25))])
        self.conv_blocks_localization = torch.nn.ModuleList([torch.nn.Linear(8, 3)])

    def forward(self, x):
        for block in (*self.conv_blocks_context, *self.conv_blocks_localization):
            x = block(x)
        return x


class CheckpointTests(unittest.TestCase):
    def test_outputs_gradients_rng_and_keys_match_without_input_gradients(self):
        torch.manual_seed(42)
        original = Toy()
        candidate = copy.deepcopy(original)
        keys = list(candidate.state_dict())
        parameters = [id(p) for p in candidate.parameters()]
        enable(candidate)
        self.assertEqual(keys, list(candidate.state_dict()))
        self.assertEqual(parameters, [id(p) for p in candidate.parameters()])
        x = torch.randn(2, 4)
        rng = torch.get_rng_state()
        a = original(x)
        a.square().sum().backward()
        after_original = torch.get_rng_state()
        torch.set_rng_state(rng)
        b = candidate(x)
        b.square().sum().backward()
        self.assertTrue(torch.equal(a, b))
        self.assertTrue(torch.equal(after_original, torch.get_rng_state()))
        for p, q in zip(original.parameters(), candidate.parameters()):
            self.assertIsNotNone(q.grad)
            self.assertTrue(torch.equal(p.grad, q.grad))

    def test_eval_is_unchanged_and_reenable_refused(self):
        a = Toy().eval()
        b = copy.deepcopy(a)
        enable(b)
        with torch.no_grad():
            x = torch.randn(2, 4)
            self.assertTrue(torch.equal(a(x), b(x)))
        with self.assertRaisesRegex(ValueError, 'already'):
            enable(b)
