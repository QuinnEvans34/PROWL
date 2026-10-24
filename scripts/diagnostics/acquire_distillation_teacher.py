"""Acquire one pinned public teacher and unmodified source; no model execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

BASE = Path('E:/PROWL/teachers/medformer-pants-b854c824')
STORAGE_ROOT = Path('E:/')
HF_REV = 'b854c8248af1e21f729dc2dfd489bd400472cf65'
CODE_REV = '45fea075a805797e78e002e9880330f4241afb1a'
WEIGHT = 'pants_pancreas_release/fold_0_latest.pth'
SIZE = 606931502
SHA = 'ff0f0868db15f99285e218e0468a2717c1a79a421357eb37171ecd5f3bb75d1f'


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def fetch(url, path, *, maximum, sha256=None, git_blob=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    if path.exists() or temporary.exists():
        raise ValueError('Existing acquisition artifact; do not overwrite or automatically retry')
    digest = hashlib.sha256(); count = 0; start = time.monotonic()
    request = urllib.request.Request(url, headers={'User-Agent': 'PROWL-teacher-preparation/1'})
    with urllib.request.urlopen(request, timeout=30) as response, temporary.open('xb') as stream:
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if count > maximum or time.monotonic() - start > 900:
                raise RuntimeError('Bounded acquisition limit exceeded')
            if shutil.disk_usage(STORAGE_ROOT).free < 100 * 1024**3:
                raise RuntimeError('Free-space floor')
            stream.write(chunk); digest.update(chunk)
    if sha256 and (digest.hexdigest() != sha256 or count != maximum):
        raise ValueError('Release checkpoint bytes/checksum mismatch')
    if git_blob:
        contents = temporary.read_bytes()
        observed = hashlib.sha1(b'blob ' + str(len(contents)).encode() + b'\0' + contents).hexdigest()
        if observed != git_blob: raise ValueError('Pinned Git object mismatch')
    temporary.rename(path)
    print(f'Acquired {path.name}: {count} bytes', flush=True)
    return dict(url=url, path=str(path), bytes=count, sha256=digest.hexdigest())


def main():
    if BASE.exists(): raise ValueError('Acquisition already started; inspect it, no rerun')
    if shutil.disk_usage(STORAGE_ROOT).free - SIZE < 100 * 1024**3: raise RuntimeError('Storage floor')
    BASE.mkdir(parents=True, exist_ok=False)
    write(BASE/'request.json', dict(hf_revision=HF_REV, code_revision=CODE_REV,
        checkpoint_sha256=SHA, checkpoint_bytes=SIZE, total_download_cap_bytes=SIZE+8*1024**2,
        purpose='Private capstone teacher inspection; no inference or training',
        authority='User: Work autonomously until distillation is set up.'))
    start = time.monotonic(); files = []
    try:
        files.append(fetch(f'https://huggingface.co/AbdomenAtlas/MedFormerPanTS/resolve/{HF_REV}/{WEIGHT}',
            BASE/'release'/WEIGHT, maximum=SIZE, sha256=SHA))
        for name in ('README.md', 'labels_pants.yaml', 'pants_pancreas_release/config.txt'):
            files.append(fetch(f'https://huggingface.co/AbdomenAtlas/MedFormerPanTS/resolve/{HF_REV}/{name}',
                BASE/'release'/name, maximum=128*1024))
        url = f'https://api.github.com/repos/MrGiovanni/R-Super/git/trees/{CODE_REV}?recursive=1'
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'PROWL'}), timeout=30) as stream:
            tree = json.load(stream)
        if tree.get('truncated'): raise ValueError('Truncated upstream tree')
        selected = [v for v in tree['tree'] if v['type'] == 'blob' and
            (v['path'] == 'LICENSE' or v['path'].startswith('rsuper_train/model/dim3/') and v['path'].endswith('.py') or
             v['path'] in ('rsuper_train/model/utils.py', 'rsuper_train/inference/inference3d.py',
                'rsuper_train/inference/utils.py', 'rsuper_train/predict_abdomenatlas.py',
                'rsuper_train/dataset_conversion/utils.py', 'rsuper_train/train_ddp.py',
                'rsuper_train/training/dataset/dataset_abdomenatlas_UFO.py',
                'rsuper_train/config/abdomenatlas/medformer_3d.yaml'))]
        if sum(v['size'] for v in selected) > 7*1024**2: raise ValueError('Unexpected source size')
        for item in selected:
            name = item['path']
            files.append(fetch(f'https://raw.githubusercontent.com/MrGiovanni/R-Super/{CODE_REV}/{name}',
                BASE/'source'/name, maximum=item['size'], git_blob=item['sha']))
        write(BASE/'acquisition.json', dict(success=True, seconds=time.monotonic()-start,
            hf_revision=HF_REV, code_revision=CODE_REV, files=files, ct_reads=0,
            model_execution=False, scientific_updates=0, files_unmodified=True,
            license_note='Model card MIT; source LICENSE CC BY-NC-ND 4.0. Kept private and unmodified.'))
    except Exception as exc:
        write(BASE/'failure.json', dict(error=f'{type(exc).__name__}: {exc}',
            completed=files, seconds=time.monotonic()-start, retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--storage-root', type=Path, default=STORAGE_ROOT)
    args = parser.parse_args()
    BASE, STORAGE_ROOT = args.base, args.storage_root
    if not STORAGE_ROOT.is_dir(): raise ValueError('Storage root must already be mounted')
    if not BASE.resolve().is_relative_to(STORAGE_ROOT.resolve()): raise ValueError('Destination outside storage root')
    main()
