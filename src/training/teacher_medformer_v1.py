"""Pinned, frozen MedFormer runtime; unmodified external source, tensor-only weights."""
from copy import deepcopy
import hashlib
import importlib
import importlib.machinery
import json
from pathlib import Path
import sys
import types

import torch
import yaml

from src.data.manifest_records import canonical, digest

MODULES = ('medformer.py', 'medformer_utils.py', 'utils.py', 'conv_layers.py', 'trans_layers.py')


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def bundle_identity(base, conversion, *, variant='ema'):
    """Build admission metadata, not a launch receipt. Caller must freeze its hash."""
    base, conversion = Path(base).resolve(), Path(conversion).resolve()
    if variant not in ('ema', 'raw'): raise ValueError('Explicit teacher weight variant required')
    report = json.loads(conversion.read_text())
    acquisition = json.loads((base/'acquisition.json').read_text())
    if not report['success'] or not report['restricted_weights_only'] or not acquisition['success']:
        raise ValueError('Teacher acquisition/conversion incomplete')
    # Check external source against its original acquisition, not just current bytes.
    for row in acquisition['files']:
        if sha(row['path']) != row['sha256']: raise ValueError('Acquired teacher bytes changed')
    model_dir = base/'source/rsuper_train/model/dim3'
    dependencies = base/'dependencies'
    files = [model_dir/name for name in MODULES]
    files += [base/'source/LICENSE', base/'release/labels_pants.yaml',
              base/'release/pants_pancreas_release/config.txt']
    files += sorted(dependencies.rglob('*.py')) + sorted(dependencies.rglob('METADATA'))
    if not (dependencies/'einops/__init__.py').exists(): raise ValueError('Isolated einops required')
    selected = report['states'][variant]
    if sha(selected['path']) != selected['sha256']: raise ValueError('Converted weights changed')
    labels = sorted(yaml.safe_load((base/'release/labels_pants.yaml').read_text()))
    if labels != report['labels'] or len(labels) != 26 or labels[19] != 'pancreatic_lesion':
        raise ValueError('Release labels changed')
    return dict(version='frozen-medformer-pants-1', variant=variant, labels=labels,
        lesion_channel=19, activation='sigmoid', weights=deepcopy(selected),
        source_checkpoint_sha256=report['source_sha256'], conversion_sha256=sha(conversion),
        acquisition_sha256=sha(base/'acquisition.json'), code_revision=acquisition['code_revision'],
        model_directory=str(model_dir), dependency_directory=str(dependencies),
        config=str(base/'release/pants_pancreas_release/config.txt'),
        files={str(p):sha(p) for p in files},
        scope='teacher-assisted exploratory until membership qualification',
        source_license='CC BY-NC-ND 4.0; private unmodified external code', model_card_license='MIT')


def _model_class(identity):
    folder = Path(identity['model_directory']).resolve()
    namespace = '_prowl_medformer_' + digest(canonical(identity))[:16]
    if namespace not in sys.modules:
        # A private package loads only the five reviewed files; do not execute
        # upstream dim3/__init__.py, which imports unrelated optional architectures.
        package = types.ModuleType(namespace)
        package.__path__ = [str(folder)]
        package.__spec__ = importlib.machinery.ModuleSpec(namespace, loader=None, is_package=True)
        sys.modules[namespace] = package
    dependency = str(Path(identity['dependency_directory']).resolve())
    if 'einops' in sys.modules:
        if not Path(sys.modules['einops'].__file__).resolve().is_relative_to(dependency):
            raise ValueError('Conflicting unpinned einops already loaded')
    sys.path.insert(0, dependency)
    try: return importlib.import_module(namespace + '.medformer').MedFormer
    finally: sys.path.remove(dependency)


class FrozenTeacher:
    def __init__(self, identity, identity_sha256, *, device='cpu'):
        if digest(canonical(identity)) != identity_sha256 or identity['version'] != 'frozen-medformer-pants-1':
            raise ValueError('Teacher identity pin')
        if device not in ('cpu', 'cuda', 'mps'): raise ValueError('Explicit teacher device')
        for path, pin in identity['files'].items():
            if sha(path) != pin: raise ValueError('Teacher source/config/dependency changed: ' + path)
        if sha(identity['weights']['path']) != identity['weights']['sha256']:
            raise ValueError('Teacher weights changed')
        self.identity, self.pin, self.device = deepcopy(identity), identity_sha256, device
        config = yaml.safe_load(Path(identity['config']).read_text())
        kwargs = {k:config[k] for k in ('base_chan','map_size','conv_block','conv_num','trans_num',
            'num_heads','fusion_depth','fusion_dim','fusion_heads','expansion','attn_drop','proj_drop',
            'proj_type','norm','act','kernel_size','aux_loss')}
        kwargs.update(scale=config['down_scale'], class_list_seg=identity['labels'],
            class_list_cls=['pancreatic_lesion'], classification_branch=False, clip_branch=False)
        if identity['labels'][identity['lesion_channel']] != 'pancreatic_lesion' or identity['activation'] != 'sigmoid':
            raise ValueError('Semantic output mapping changed')
        with torch.random.fork_rng(devices=[]):
            self.model = _model_class(identity)(config['in_chan'], len(identity['labels']), **kwargs)
        state = torch.load(identity['weights']['path'], weights_only=True, map_location='cpu', mmap=True)
        # Unlike upstream strict=False, any missing/random head is a hard failure.
        self.model.load_state_dict(state, strict=True)
        self.model.requires_grad_(False).eval().to(device)

    @torch.inference_mode()
    def lesion_probability(self, window):
        if digest(canonical(self.identity)) != self.pin: raise ValueError('Teacher identity changed')
        if (window.ndim != 5 or window.shape[:2] != (1,1) or window.dtype != torch.float32 or
                any(n < 32 or n % 16 for n in window.shape[2:]) or not torch.isfinite(window).all().item()):
            raise ValueError('Finite B1C1 float32 teacher window; dimensions multiples of 16 >=32')
        if self.model.training or any(p.requires_grad for p in self.model.parameters()):
            raise ValueError('Teacher is not frozen/eval')
        result = self.model(window.to(self.device))
        if not isinstance(result, dict) or set(result) != {'segmentation'}:
            raise ValueError('Unexpected teacher output contract')
        logits = result['segmentation']
        if isinstance(logits, (list, tuple)): logits = logits[0]
        if logits.shape != (1, len(self.identity['labels']), *window.shape[2:]):
            raise ValueError('Teacher output dimensions')
        if not torch.isfinite(logits).all().item(): raise ValueError('Nonfinite teacher logits')
        return logits[:, self.identity['lesion_channel']].sigmoid().cpu()
