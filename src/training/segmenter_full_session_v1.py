"""Scalable successor to the capstone pretrained session, independent of scripts/train.py.

Retains the capstone model, normalized loss, role-checked batches, isolated RNG and dirty-state
rule. Cohort size and horizon are configuration, and update accounting is O(1), not a replay
of the entire history on every update. The executor journals history outside checkpoints.
"""
from copy import deepcopy
import hashlib
import math
import os

import numpy as np
import torch

from src.data.manifest_records import canonical, digest
from src.data.segmenter_training_inputs_v1 import Batch
from src.data.source_inventory_records import require
from src.models.segresnet import build_model
from src.training import segmenter_session_v1 as numerical
from src.training import segmenter_normalized_loss_v1 as loss
from src.training.segmenter_pretrained_session_v1 import Session as PretrainedSession
from src.training.experiment_config import load_suprem_checked

POLICY = 'full_cohort_seeded_permutation_v1'


def identity_for(config, control, device, initialization):
    return deepcopy(dict(version='segmenter-full-session-1', config=config,
        control=control, device=device, initialization=initialization,
        architecture=numerical.ARCH, loss=loss.LOSS, sampling=POLICY))


def validate_config(c):
    require(set(c) == {'max_steps', 'tensor_shape', 'seed', 'learning_rate', 'weight_decay',
                       'warmup_steps', 'lr_schedule'}, 'Full session configuration fields')
    require(type(c['max_steps']) is int and c['max_steps'] > 0, 'Positive training horizon required')
    require(type(c['seed']) is int and 0 <= c['seed'] < 2**32, 'Invalid seed')
    require(len(c['tensor_shape']) == 3 and all(type(v) is int and 16 <= v <= 192 and v % 8 == 0
            for v in c['tensor_shape']), 'Unsupported tensor dimensions')
    require(all(type(c[k]) in (int, float) and math.isfinite(c[k]) and c[k] >= 0
            for k in ('learning_rate', 'weight_decay')) and c['learning_rate'] > 0, 'Invalid optimizer')
    require(type(c['warmup_steps']) is int and 0 <= c['warmup_steps'] < c['max_steps']
            and c['lr_schedule'] in ('constant', 'warmup_cosine'), 'Invalid schedule')


class Session:
    rng_scope = PretrainedSession.rng_scope

    def __init__(self, config, control, *, device, initialization, initialize=True):
        validate_config(config)
        train, dev = control['train'], control['validation']
        require(train and dev and len(set(train + dev)) == len(train + dev), 'Distinct nonempty roles required')
        require(device in ('cpu', 'mps'), 'Explicit supported device required')
        if device == 'mps':
            require(torch.backends.mps.is_available() and os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '0',
                    'Native MPS with fallback disabled required')
        self.identity = identity_for(config, control, device, initialization)
        self.config, self.control = self.identity['config'], self.identity['control']
        self.identity_pin = digest(canonical(self.identity))
        self.control_pin = digest(canonical(control))
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(config['seed'])
            self.model = build_model({'model': numerical.ARCH})
        if initialize and initialization['kind'] == 'suprem':
            load_suprem_checked(self.model, initialization)
        else:
            require(initialization['kind'] in ('scratch', 'suprem'), 'Unknown initialization')
        self.device = device
        self.model.to(device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=config['learning_rate'],
                                          weight_decay=config['weight_decay'])
        self.cpu_rng = torch.Generator().manual_seed(config['seed']).get_state()
        self.mps_rng = None
        if device == 'mps':
            old = torch.mps.get_rng_state()
            try:
                torch.mps.manual_seed(config['seed']); self.mps_rng = torch.mps.get_rng_state().cpu().clone()
            finally: torch.mps.set_rng_state(old)
        self.step, self.dirty = 0, False
        self.exposure = {name: 0 for name in train}
        self._epoch, self._order = None, None

    def next_member(self):
        require(0 <= self.step < self.config['max_steps'], 'Training horizon exhausted')
        epoch, cursor = divmod(self.step, len(self.control['train']))
        if self._epoch != epoch:
            seed = int.from_bytes(hashlib.sha256(f"{self.config['seed']}:{epoch}:{POLICY}".encode()).digest()[:8], 'little')
            self._order = torch.randperm(len(self.control['train']), generator=torch.Generator().manual_seed(seed)).tolist()
            self._epoch = epoch
        return self.control['train'][self._order[cursor]]

    def _clean(self):
        require(not self.dirty and digest(canonical(self.identity)) == self.identity_pin,
                'Dirty or changed session cannot advance')

    def _batch(self, provider, name, role, operation):
        require(digest(canonical(provider.control)) == self.control_pin, 'Input cohort changed')
        require(name in self.control['train' if role == 'train' else 'validation'], 'Wrong input role')
        b = provider.get(name, role=role, operation=operation)
        require(type(b) is Batch and b.role == role, 'Checked matching-role batch required')
        x, y = b.checked(self.control_pin, operation, name)
        require(x.shape == (1, *self.config['tensor_shape']) and y.shape == tuple(self.config['tensor_shape'])
            and x.dtype == np.float32 and np.isfinite(x).all() and x.min() >= 0 and x.max() <= 1
            and np.isin(y, [0, 1, 2]).all(), 'Invalid optimizer/evaluator arrays')
        return b, torch.as_tensor(x), torch.as_tensor(y, dtype=torch.long)

    def update(self, provider):
        self._clean(); name = self.next_member()
        b, x, y = self._batch(provider, name, 'train', 'optimizer')
        c = self.config
        if c['lr_schedule'] == 'constant': factor = 1.
        elif self.step < c['warmup_steps']: factor = (self.step + 1) / max(1, c['warmup_steps'])
        else: factor = .5 * (1 + math.cos(math.pi * (self.step-c['warmup_steps']) / (c['max_steps']-c['warmup_steps'])))
        for group in self.optimizer.param_groups: group['lr'] = c['learning_rate'] * factor
        self.dirty = True
        with self.rng_scope():
            self.model.train(); self.optimizer.zero_grad(set_to_none=True)
            value = loss.objective(self.model(x[None].to(self.device)), y[None].to(self.device))
            require(torch.isfinite(value).item(), 'Nonfinite loss')
            value.backward()
            require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in self.model.parameters()),
                    'Nonfinite/missing gradient')
            self.optimizer.step()
            require(numerical.finite(self.model.state_dict()) and numerical.finite(self.optimizer.state_dict()),
                    'Nonfinite optimizer state')
        self.step += 1; self.exposure[name] += 1; self.dirty = False
        return dict(step=self.step, member_id=name, loss=float(value.detach().cpu()),
                    learning_rate=self.optimizer.param_groups[0]['lr'], batch_sha256=b.hashes())

    @torch.no_grad()
    def evaluate_case(self, provider, name):
        self._clean(); _, x, y = self._batch(provider, name, 'validation', 'evaluator')
        with self.rng_scope():
            self.model.eval(); logits = self.model(x[None].to(self.device))
            require(torch.isfinite(logits).all().item(), 'Nonfinite validation prediction')
            predicted = logits.argmax(1)[0].cpu()
        # Tensor-grid development metrics; never label these as native/published benchmark Dice.
        values = {}
        for label, code in [('pancreas', 1), ('lesion', 2)]:
            target = y == code; guess = predicted == code
            tp, total, found = int((target & guess).sum()), int(target.sum()), int(guess.sum())
            values[label] = dict(target_voxels=total, predicted_voxels=found, true_positive=tp,
                                 dice=2*tp/(total+found) if total+found else None)
        return dict(case_id=name, step=self.step, scope='tensor_grid_development', metrics=values)

    def state(self):
        self._clean()
        return numerical.cpu_tree(dict(version=1, identity=self.identity, identity_sha256=self.identity_pin,
            step=self.step, exposure=self.exposure, model=self.model.state_dict(),
            optimizer=self.optimizer.state_dict(), cpu_rng=self.cpu_rng, mps_rng=self.mps_rng))

    @classmethod
    def restore(cls, state, expected_identity):
        require(state['version'] == 1 and state['identity'] == expected_identity and
            state['identity_sha256'] == digest(canonical(expected_identity)) and numerical.finite(state),
            'Checkpoint identity/state mismatch')
        i = expected_identity
        s = cls(i['config'], i['control'], device=i['device'], initialization=i['initialization'], initialize=False)
        require(type(state['step']) is int and 0 <= state['step'] <= s.config['max_steps'] and
            set(state['exposure']) == set(s.exposure) and all(type(v) is int and v >= 0 for v in state['exposure'].values())
            and sum(state['exposure'].values()) == state['step'], 'Checkpoint progress mismatch')
        expected = s.model.state_dict()
        require(set(state['model']) == set(expected) and all(type(state['model'][k]) is torch.Tensor and
            state['model'][k].shape == v.shape and state['model'][k].dtype == v.dtype for k, v in expected.items()),
            'Checkpoint model signature mismatch')
        opt = state['optimizer']; standard = s.optimizer.state_dict()
        require(set(opt) == set(standard) and len(opt['param_groups']) == 1 and
            set(opt['param_groups'][0]) == set(standard['param_groups'][0]) and
            all(opt['param_groups'][0][k] == v for k, v in standard['param_groups'][0].items() if k != 'lr'),
            'Checkpoint optimizer recipe mismatch')
        indices = standard['param_groups'][0]['params']
        require(set(opt['state']) == (set(indices) if state['step'] else set()), 'Incomplete optimizer state')
        for index, param in zip(indices, s.model.parameters()):
            if state['step']:
                moment = opt['state'][index]
                require(set(moment) == {'step', 'exp_avg', 'exp_avg_sq'} and
                    moment['step'].numel() == 1 and moment['step'].item() == state['step'] and
                    all(moment[k].shape == param.shape and moment[k].dtype == param.dtype
                        for k in ('exp_avg', 'exp_avg_sq')) and (moment['exp_avg_sq'] >= 0).all().item(),
                    'Invalid optimizer moments/step')
        require((i['device'] == 'cpu' and state['mps_rng'] is None) or
            (i['device'] == 'mps' and type(state['mps_rng']) is torch.Tensor and
             state['mps_rng'].dtype == torch.uint8 and state['mps_rng'].shape == s.mps_rng.shape),
            'Checkpoint native RNG mismatch')
        s.model.load_state_dict(state['model'], strict=True); s.optimizer.load_state_dict(state['optimizer'])
        s.step, s.exposure = state['step'], deepcopy(state['exposure'])
        s.cpu_rng, s.mps_rng = state['cpu_rng'].clone(), state['mps_rng']
        torch.Generator().set_state(s.cpu_rng)
        return s
