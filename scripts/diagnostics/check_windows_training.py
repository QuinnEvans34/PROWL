"""Inspect environment readiness without patient reads, models, or optimizer updates.

Exit 0 means the Python/CUDA environment is available, not that training is qualified.
"""
import importlib
import importlib.metadata
import argparse
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def inspect():
    report = {
        'scope': 'environment_only_no_patient_or_weight_reads',
        'python': platform.python_version(),
        'executable': sys.executable,
        'platform': platform.platform(),
        'environment_ready': False,
        'training_qualified': False,
        'packages': {},
        'errors': [],
        'local_inputs': {name: (ROOT / name).exists() for name in (
            'configs/local/roots.yaml', 'outputs/splits/train.txt',
            'outputs/splits/val.txt', 'outputs/splits/test.txt',
            'pretrained_weights/supervised_suprem_segresnet_2100.pth')},
        'workspace_disk_free_bytes': shutil.disk_usage(ROOT).free,
    }
    if sys.version_info[:2] != (3, 12):
        report['errors'].append('Python 3.12 required by Windows machine specification')
    for name in ('torch', 'torchvision', 'monai', 'nibabel', 'SimpleITK', 'numpy',
                 'pandas', 'scipy', 'yaml', 'mlflow', 'pytest', 'psutil', 'jsonschema', 'httpx'):
        try:
            module = importlib.import_module(name)
            report['packages'][name] = (importlib.metadata.version(name) if name == 'jsonschema'
                else str(getattr(module, '__version__', 'imported')))
        except Exception as exc:
            report['packages'][name] = {'error': f'{type(exc).__name__}: {exc}'}
            report['errors'].append(f'{name} unavailable')
    torch = sys.modules.get('torch')
    if torch is not None:
        try:
            available = torch.cuda.is_available()
            report['cuda'] = {'available': available, 'wheel_runtime': torch.version.cuda}
            if not available:
                report['errors'].append('CUDA unavailable to PyTorch')
            else:
                # A small allocation and kernel prove more than driver enumeration alone.
                value = torch.arange(16, device='cuda', dtype=torch.float32).sum().item()
                assert value == 120.0
                info = torch.cuda.get_device_properties(0)
                report['cuda'].update(name=info.name, vram_bytes=info.total_memory,
                    capability=list(torch.cuda.get_device_capability(0)),
                    bf16_supported=torch.cuda.is_bf16_supported(), small_kernel_passed=True)
        except Exception as exc:
            report['errors'].append(f'CUDA check failed: {type(exc).__name__}: {exc}')
    try:
        report['nvidia_smi'] = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,temperature.gpu,driver_version',
             '--format=csv,noheader'], capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        report['nvidia_smi'] = {'error': str(exc)}
    report['entrypoints'] = {}
    for name in ('scripts.train_full_segmenter', 'scripts.prepare_full_segmenter_cache',
                 'src.training.segmenter_full_session_v1'):
        try:
            importlib.import_module(name)
            report['entrypoints'][name] = 'imported'
        except Exception as exc:
            report['entrypoints'][name] = f'{type(exc).__name__}: {exc}'
            report['errors'].append(f'{name} unavailable')
    report['environment_ready'] = not report['errors']
    report['real_run_requirements'] = [
        'Connected external storage, verified protected cohort/source metadata and portable paths',
        'Retained GPU fit/resume evidence, followed by representative real-data and independent backup checks',
        'Selected experiment with fixed config, duration, metrics and storage allocation',
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Save environment inventory in a fresh directory')
    args = parser.parse_args()
    report = inspect()
    if args.output:
        destination = Path(args.output).resolve()
        destination.mkdir(parents=True, exist_ok=False)
        report['installed_inventory'] = sorted(
            ({'name': d.metadata['Name'], 'version': d.version} for d in importlib.metadata.distributions()),
            key=lambda value: value['name'].lower())
        (destination/'environment.json').write_text(json.dumps(report, indent=2)+'\n')
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], check=True,
            capture_output=True, text=True).stdout
        (destination/'installed-freeze.txt').write_text(freeze)
    print(json.dumps(report, indent=2))
    return 0 if report['environment_ready'] else 2


if __name__ == '__main__':
    sys.exit(main())
