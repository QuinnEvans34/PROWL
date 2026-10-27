"""Publish admitted full targets separately; never mutate the producer directory."""
import json
import os
from pathlib import Path

from src.data.manifest_records import canonical, digest
from src.data.segmenter_generated_target_admission_v1 import admit
from src.data.segmenter_teacher_cache_v1 import sha


def read_bound(path, expected):
    path = Path(path)
    if path.stat().st_size > 64 * 1024**2:
        raise ValueError('Admission record exceeds 64 MiB')
    payload = path.read_bytes()
    if digest(payload) != expected:
        raise ValueError(f'Admission record changed: {path.name}')
    return json.loads(payload)


def publish(root, output, provider, *, request_sha256, result_sha256, resources_sha256,
            provider_sha256):
    root = Path(root).resolve(strict=True)
    output = Path(output).absolute()
    parent = output.parent.resolve(strict=True)
    output = parent / output.name
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('Publication must be separate from producer directory')
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if provider.pin != provider_sha256:
        raise ValueError('Prepared provider changed')
    pins = {'request.json': request_sha256, 'result.json': result_sha256,
            'resources.json': resources_sha256}
    records = {name: read_bound(root / name, pin) for name, pin in pins.items()}
    manifest, common = admit(root, records['request.json'], records['result.json'],
                             records['resources.json'], provider, qualification_only=False)
    # Recheck the small terminal records after payload verification.
    for name, pin in pins.items():
        read_bound(root / name, pin)
    output.mkdir()  # Exclusive claim; failed directories remain for inspection.
    def write(name, value):
        with (output / name).open('xb') as stream:
            stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
    # References avoid duplicating the cache or modifying frozen producer artifacts.
    for name, row in manifest['members'].items():
        source = root / (name + '.npz')
        if sha(source) != row['payload_sha256']:
            raise ValueError('Target changed before publication')
        (output / source.name).symlink_to(source)
    write('common-identity.json', common)
    write('provider-control.json', provider.control)
    write('admission.json', dict(version='full-teacher-admission-1',
          producer_root=str(root), source_record_hashes=pins,
          provider_sha256=provider.pin, manifest_sha256=digest(canonical(manifest)),
          members=len(manifest['members']), scientific_ready=False,
          payload_storage='references_to_verified_producer_files'))
    write('manifest.pending', manifest)
    fd = os.open(output, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    # A manifest is the publication boundary. link is atomic and cannot overwrite.
    os.link(output / 'manifest.pending', output / 'manifest.json')
    (output / 'manifest.pending').unlink()
    fd = os.open(output, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return dict(output=str(output), manifest_sha256=sha(output / 'manifest.json'),
                members=len(manifest['members']), scientific_ready=False)
