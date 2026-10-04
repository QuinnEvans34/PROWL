"""144-cube readiness session. Real cache inputs have an inference-only interface."""
from copy import deepcopy
from io import BytesIO
import math
import os
import time
import torch
from monai.inferers import sliding_window_inference
from src.models.segresnet import build_model
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.training.twomm_adapter import validate_config, pad_image, remove_padding, patch_batch
from src.training.localizer import configured_loss
from src.training.localizer_checkpoint import finite_tree
from src.training.localizer_run import cpu_tree

POLICY = 'processed_grid_pancreas_background_equal_v2'
CONTROLS = {'inputs.json': 'inputs_sha256', 'source.json': 'source_sha256',
            'environment.json': 'environment_sha256'}


def validate_identity(identity):
    require(set(identity) == {'schema_version', 'run_id', 'purpose', 'device', 'config',
        'sampling_policy', 'inputs_sha256', 'source_sha256', 'environment_sha256',
        'cache_receipt_sha256'}, 'Incomplete twomm identity')
    require(identity['schema_version'] == 'twomm-session-1' and
        identity['purpose'] in ('synthetic-recovery', 'qualified-cache-inference') and
        identity['device'] in ('cpu', 'mps') and identity['sampling_policy'] == POLICY,
        'Unsupported twomm execution')
    require(isinstance(identity['run_id'], str) and identity['run_id'].startswith('twomm-session-')
        and len(identity['run_id']) <= 100, 'Invalid run identity')
    for key in (k for k in identity if k.endswith('_sha256')):
        value = identity[key]
        require(isinstance(value, str) and len(value) == 64 and
                all(c in '0123456789abcdef' for c in value), 'Invalid identity pin')
    validate_config(identity['config'])
    require(identity['config']['schema_version']=='twomm-adapter-1', 'Readiness requires original adapter version')


def synthetic_item():
    """Internal generated fixture: synthetic_update cannot accept caller-supplied CTs."""
    y = torch.zeros((1, 96, 96, 96), dtype=torch.uint8)
    y[:, 24:72, 30:66, 32:64] = 1
    return dict(study_id='synthetic-recovery', operation='optimizer',
        descriptor=dict(study_id='synthetic-recovery', operation='optimizer', protected_role='train'),
        image=y.float() * .8 + .1, label=y)


def initialize_model(self, identity, *, restoring_on_cpu=False):
    """Shared mechanics only; each caller validates its own execution identity."""
    self.config = deepcopy(identity['config'])
    self.device = 'cpu' if restoring_on_cpu else identity['device']
    if self.device == 'mps':
        require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '0' and
                torch.backends.mps.is_available(), 'Native MPS without fallback required')
    self.step = 0
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(self.config['seed'])
        self.model = build_model({'model': dict(in_channels=1, out_channels=2, init_filters=16,
            norm='group', num_groups=8, blocks_down=(1, 2, 2, 4), blocks_up=(1, 1, 1), dropout_prob=0)})
    self.model.to(self.device)
    self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config['learning_rate'],
                                      weight_decay=self.config['weight_decay'])
    if self.config.get('schema_version') in ('twomm-adapter-4','twomm-adapter-5','twomm-adapter-6'):
        self.scheduler=torch.optim.lr_scheduler.ConstantLR(self.optimizer,factor=1.0,total_iters=self.config['max_steps'])
    elif self.config.get('schema_version')=='twomm-adapter-3':
        from src.training.twomm_tail_schedule import CosineThenConstantLR
        self.scheduler=CosineThenConstantLR(self.optimizer,**{k:v for k,v in self.config['schedule'].items() if k!='schema_version'})
    else:
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer,
                                             T_max=self.config['max_steps'], eta_min=0)


class Session:
    def __init__(self, identity, *, restoring_on_cpu=False):
        validate_identity(identity)
        self.identity = deepcopy(identity)
        initialize_model(self, identity, restoring_on_cpu=restoring_on_cpu)

    def update(self, *args, **kwargs):
        raise ValueError('Readiness session cannot perform real optimizer updates')

    def synthetic_update(self):
        require(self.identity['purpose'] == 'synthetic-recovery', 'Real session cannot update')
        x, y, trace = patch_batch(synthetic_item(), self.config, step=self.step)
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        loss = configured_loss(self.model(x.to(self.device)), y.to(self.device), self.config)
        require(torch.isfinite(loss).item(), 'Nonfinite loss')
        loss.backward()
        require(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                    for p in self.model.parameters()), 'Invalid gradients')
        self.optimizer.step()
        self.scheduler.step()
        self.step += 1
        require(finite_tree(self.model.state_dict()), 'Nonfinite updated model')
        return dict(completed_step=self.step, loss=loss.item(), sampling=trace)

    @torch.no_grad()
    def predict(self, image):
        x, trace = pad_image(image, self.config)
        self.model.eval()
        result = sliding_window_inference(x[None], self.config['patch_size'], 1, self.model,
            overlap=.25, mode='constant', padding_mode='constant', sw_device=self.device, device='cpu')
        require(result.shape == (1, 2, *x.shape[1:]) and torch.isfinite(result).all().item(),
                'Invalid full-volume prediction')
        return remove_padding(result[0].softmax(0), trace), trace

    def predict_cache(self, cache, role, index, *, timings=None):
        require(self.identity['purpose'] == 'qualified-cache-inference', 'Wrong cache session purpose')
        # Independently expected pins must match the verified cache, not just an arbitrary item.
        from src.training.twomm_cache import DiskRoleCache
        require(type(cache) is DiskRoleCache, 'Verified persisted cache required')
        cache.members(role)  # Verify the in-memory manifest before inspecting its binding.
        require(digest(canonical(cache._manifest['binding'])) == self.identity['inputs_sha256'], 'Cache binding differs')
        require(digest((cache.path / 'complete.json').read_bytes()) == self.identity['cache_receipt_sha256'],
                'Cache completion differs')
        started = time.monotonic()
        item = cache.get(role, index)
        loaded = time.monotonic()
        probability, trace = self.predict(item['image'])
        if timings is not None:
            timings.update(cache_load_seconds=loaded-started, inference_seconds=time.monotonic()-loaded)
        return probability, trace, item


def weight_digest(session):
    import hashlib
    h = hashlib.sha256()
    for name, value in session.model.state_dict().items():
        h.update(name.encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def decode(files, identity):
    validate_identity(identity)
    require(set(files) == {'identity.json', 'state.pt'} | set(CONTROLS), 'Wrong checkpoint members')
    require(files['identity.json'] == canonical(identity), 'Checkpoint identity differs')
    for name, key in CONTROLS.items():
        require(digest(files[name]) == identity[key], 'Checkpoint control differs')
    state = torch.load(BytesIO(files['state.pt']), map_location='cpu', weights_only=True)
    require(set(state) == {'schema_version', 'identity_sha256', 'step', 'model', 'optimizer',
                          'scheduler', 'cpu_rng'}, 'Incomplete checkpoint state')
    require(state['schema_version'] == 'twomm-state-1' and
            state['identity_sha256'] == digest(canonical(identity)), 'State identity differs')
    step = state['step']
    require(type(step) is int and 0 <= step <= identity['config']['max_steps'], 'Invalid step')
    require(identity['purpose'] == 'synthetic-recovery' or step == 0, 'Real readiness checkpoint has updates')
    require(finite_tree(state), 'Nonfinite checkpoint')
    rng = state['cpu_rng']
    require(isinstance(rng, torch.Tensor) and rng.dtype == torch.uint8 and
            rng.shape == torch.get_rng_state().shape, 'Invalid CPU RNG')
    restored = Session(identity, restoring_on_cpu=True)
    load_model_state(restored, state, identity['config'], step)
    return restored, rng


def load_model_state(restored, state, config, step):
    """Strict model/optimizer/scheduler validation shared by versioned codecs."""
    # Restrict inventories before PyTorch can silently accept extra optimizer/scheduler settings.
    expected_scheduler = restored.scheduler.state_dict()
    require(set(state['scheduler']) == set(expected_scheduler), 'Scheduler inventory differs')
    sch = state['scheduler']
    parented=config.get('schema_version') in ('twomm-adapter-4','twomm-adapter-5','twomm-adapter-6')
    if parented:lr=config['learning_rate']
    elif config.get('schema_version')=='twomm-adapter-3':
        from src.training.twomm_tail_schedule import next_rate
        lr=next_rate(config,step)
    else:
        lr = config['learning_rate'] * (1 + math.cos(math.pi * step / config['max_steps'])) / 2
    require(len(sch['_last_lr']) == 1 and abs(sch['_last_lr'][0] - lr) < 1e-12 and
            sch == dict(expected_scheduler, last_epoch=step, _step_count=step + 1, _last_lr=sch['_last_lr']),
            'Scheduler position or policy differs')
    opt = state['optimizer']; expected = restored.optimizer.state_dict()
    require(set(opt) == set(expected) and len(opt['param_groups']) == 1, 'Optimizer inventory differs')
    actual_lr = opt['param_groups'][0]['lr']
    if parented:expected['param_groups'][0]['initial_lr']=restored.parent_reference['identity']['config']['learning_rate']
    require(abs(actual_lr - lr) < 1e-12 and sch['_last_lr'] == [actual_lr] and
            opt['param_groups'] == [dict(expected['param_groups'][0], lr=actual_lr)], 'Optimizer policy differs')
    ids = expected['param_groups'][0]['params']
    optimizer_step=step+config['parent_steps'] if parented else step
    require(set(opt['state']) == (set(ids) if optimizer_step else set()), 'Optimizer state inventory differs')
    for index, param in zip(ids, restored.model.parameters()):
        if optimizer_step:
            entry = opt['state'][index]
            require(set(entry) == {'step', 'exp_avg', 'exp_avg_sq'} and
                isinstance(entry['step'], torch.Tensor) and entry['step'].numel() == 1 and
                entry['step'].item() == optimizer_step and all(entry[k].shape == param.shape and
                entry[k].dtype == param.dtype for k in ('exp_avg', 'exp_avg_sq')) and
                (entry['exp_avg_sq'] >= 0).all().item(), 'Invalid optimizer history')
    expected_model = restored.model.state_dict()
    require(set(state['model']) == set(expected_model) and all(
        state['model'][k].shape == v.shape and state['model'][k].dtype == v.dtype
        for k, v in expected_model.items()), 'Model tensor inventory differs')
    restored.model.load_state_dict(state['model'], strict=True)
    restored.optimizer.load_state_dict(opt)
    restored.scheduler.load_state_dict(sch)
    restored.step = step


def validate_payload(files, identity):
    session, _ = decode(files, identity)
    return dict(step=session.step, identity_sha256=digest(canonical(identity)))


def payload(session, identity, controls):
    require(session.identity == identity and session.config == identity['config'], 'Session identity differs')
    state = cpu_tree(dict(schema_version='twomm-state-1', identity_sha256=digest(canonical(identity)),
        step=session.step, model=session.model.state_dict(), optimizer=session.optimizer.state_dict(),
        scheduler=session.scheduler.state_dict(), cpu_rng=torch.get_rng_state()))
    stream = BytesIO(); torch.save(state, stream)
    files = dict(controls, **{'identity.json': canonical(identity), 'state.pt': stream.getvalue()})
    validate_payload(files, identity)
    return files


def restore_payload(files, identity):
    base, rng = decode(files, identity)
    if identity['device'] == 'cpu':
        torch.set_rng_state(rng)
        return base
    restored = Session(identity)
    restored.model.load_state_dict(base.model.state_dict())
    restored.optimizer.load_state_dict(base.optimizer.state_dict())
    restored.scheduler.load_state_dict(base.scheduler.state_dict())
    restored.step = base.step
    torch.set_rng_state(rng)
    return restored


def publish_checkpoint(store, files, identity):
    check = validate_payload(files, identity)
    artifact_id = f"{identity['run_id']}:step:{check['step']}"
    derivation = digest(canonical(dict(identity=identity, step=check['step'])))
    metadata = dict(artifact_type='localizer-checkpoint', schema_version='twomm-session-1',
        component='twomm-readiness-session', code_sha256=identity['source_sha256'],
        parents=[identity['inputs_sha256'], identity['cache_receipt_sha256']],
        retention='recovery-verification-keeper', sensitivity='private-research',
        run_id=identity['run_id'], stage_id='checkpoint')
    pin, status = store.publish(artifact_id, derivation_sha256=derivation, files=files,
                               metadata=metadata, validate=lambda f: validate_payload(f, identity))
    return dict(artifact_id=artifact_id, receipt_sha256=pin, derivation_sha256=derivation,
                step=check['step'], status=status)
