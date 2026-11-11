"""Import exactly the authorized three-file 32k replay packet."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.diagnostics.reconstruct_mac_stunet_32k_masks_20261111 import packet, sha, write

LIMITS = {
    'model-only.pt': 300 * 1024**2,
    'native-32000.json': 4 * 1024**2,
    'manifest.json': 64 * 1024,
}


def import_packet(archive, destination, expected):
    if not re.fullmatch('[a-f0-9]{64}', expected):
        raise ValueError('Expected transport SHA-256 is required')
    if (archive.is_symlink() or not archive.is_file()
            or archive.stat().st_size > sum(LIMITS.values()) + 1024**2
            or sha(archive) != expected):
        raise ValueError('Transport identity or size differs')
    if destination.exists() or destination.is_symlink() or destination.parent.resolve() != destination.parent.absolute():
        raise ValueError('Expected a fresh private destination')
    with tarfile.open(archive, 'r:*') as tar:
        members = {}
        for member in tar:
            if (member.name not in LIMITS or member.name in members
                    or not member.isfile() or not 0 < member.size <= LIMITS[member.name]):
                raise ValueError('Unexpected transfer member')
            members[member.name] = member
        if set(members) != set(LIMITS):
            raise ValueError('Incomplete transfer')
        with tar.extractfile(members['manifest.json']) as stream:
            manifest = json.load(stream)
        from scripts.diagnostics import evaluate_native_small_lesion_outliner_20261111 as replay
        if (manifest['step'] != replay.STEP or manifest['source_checkpoint_sha256'] != replay.CHECKPOINT_SHA
                or manifest['independent_checkpoint_sha256'] != replay.CHECKPOINT_SHA
                or manifest['tensor_equality'] is not True
                or manifest['report_sha256'] != replay.REPORT_SHA
                or not re.fullmatch('[a-f0-9]{64}',manifest['model_sha256'])):
            raise ValueError('Unexpected 32k provenance')
        hashes = {'model-only.pt':manifest['model_sha256'],'native-32000.json':replay.REPORT_SHA}
        for key, digest in hashes.items():
            with tar.extractfile(members[key]) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                    raise ValueError('Packet member SHA-256 differs')
        destination.mkdir(mode=0o700)
        for key, member in members.items():
            with tar.extractfile(member) as source, (destination/key).open('xb') as target:
                for block in iter(lambda:source.read(1024**2),b''):
                    target.write(block)
    if sha(archive)!=expected:
        raise ValueError('Archive changed during import')
    packet(destination)
    receipt = dict(archive_sha256=expected,
                   member_sha256={key:sha(destination/key) for key in LIMITS},
                   model_source_checkpoint_sha256=manifest['source_checkpoint_sha256'])
    write(destination/'import-receipt.json',receipt)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path)
    p.add_argument('destination',type=Path)
    p.add_argument('--sha256',required=True)
    a = p.parse_args()
    print(json.dumps(import_packet(a.archive,a.destination,a.sha256)))
