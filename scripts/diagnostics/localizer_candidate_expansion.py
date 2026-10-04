"""D-289 metadata-only publication/replay; never opens source CT or target files."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from uuid import uuid4
from src.data.localizer_candidates_v2 import select_candidates

REPO = Path(__file__).resolve().parents[2]
OLD = REPO/'outputs/prowl/localizer-candidates-f1f88917-7aa0-4cd5-a4e7-e8a84897421c'
OLD_PIN = '3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1'
INVENTORY = REPO/'outputs/prowl/localizer-metadata-4c93efaa-f102-4bef-bae6-8966b3446d91'


def sha(b): return hashlib.sha256(b).hexdigest()
def encoded(x): return (json.dumps(x, sort_keys=True, indent=2) + '\n').encode()


def pinned(path, pin):
    if path.resolve(strict=True) != path or not path.is_file() or path.stat().st_size > 32*1024**2:
        raise ValueError('Unsafe or oversized metadata')
    raw = path.read_bytes()
    if sha(raw) != pin: raise ValueError('Metadata pin changed: ' + path.name)
    return raw


def build():
    receipt = json.loads(pinned(OLD/'receipt.json', OLD_PIN))
    for name, ref in receipt['files'].items():
        if Path(name).name != name: raise ValueError('Unsafe package member')
        raw = pinned(OLD/name, ref['sha256'])
        if len(raw) != ref['bytes']: raise ValueError('Package size changed')
    old = json.loads((OLD/'selection.json').read_bytes())
    pins = old['input_pins']
    raw = pinned(REPO/'outputs/manifest.csv', pins['manifest_sha256'])
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    roles = {}
    for role, name in [('train','train.txt'), ('validation','val.txt'), ('test','test.txt')]:
        members = pinned(REPO/'outputs/splits'/name, pins['membership'][role]).decode().splitlines()
        for sid in members:
            if not sid or sid in roles: raise ValueError('Duplicate or empty protected member')
            roles[sid] = role
    pinned(INVENTORY/'verification.json', pins['inventory_receipt_sha256'])
    inventory = json.loads(pinned(INVENTORY/'files.json', pins['inventory_files_sha256']))
    by_case = {}
    for item in inventory:
        key = (item['study_id'], item['kind'])
        if key in by_case: raise ValueError('Duplicate inventory input')
        by_case[key] = item
    retained = {role:[c['study_id'].split(':')[-1] for c in old['candidates'][role]] for role in ('train','validation')}
    selection = select_candidates(rows, roles, counts={'train':128,'validation':48}, retained=retained,
                                  floors={'train':4,'validation':3}, seed='prowl-sept29-hybrid-v2')
    totals = {}
    for role, group in selection['candidates'].items():
        for c in group:
            refs = [by_case[(c['study_id'], kind)] for kind in ('ct','pancreas')]
            if any(r['protected_role'] != role for r in refs): raise ValueError('Inventory role mismatch')
            c['inventory_inputs'] = refs
            c['retained_hold'] = 'unknown_spatial_units; not resolved or replaced' if c['study_id'] == 'pants:study:PanTS_00006350' else None
        totals[role] = dict(candidates=len(group), files=2*len(group),
            observed_compressed_bytes=sum(r['bytes'] for c in group for r in c['inventory_inputs']),
            new_candidates=sum(c['selection_reason'] != 'retained' for c in group),
            inventory_states=sorted({r['state'] for c in group for r in c['inventory_inputs']}))
    selection.update(input_pins=pins, parent_candidate_receipt_sha256=OLD_PIN,
        accounting=totals, decompressed_memory_projection=None,
        projection_limit='Retained stat evidence only; no current payload or header verification.',
        source_payload_reads=0, original_membership_changed=False)
    return selection


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--check', type=Path);args=parser.parse_args()
    payload = encoded(build())
    if args.check:
        receipt = json.loads((args.check/'receipt.json').read_bytes())
        for name, pin in receipt['files'].items():
            if Path(name).name != name: raise ValueError('Unsafe package member')
            pinned(args.check.resolve()/name, pin)
        if (args.check/'selection.json').read_bytes() != payload: raise ValueError('Replay differs')
        print('Exact metadata replay passed');return
    dest = REPO/'outputs/prowl'/('localizer-candidates-v2-'+str(uuid4()));dest.mkdir()
    files = {'selection.json':payload}
    for name in ('src/data/localizer_candidates_v2.py','src/data/localizer_candidates.py',
                 'scripts/diagnostics/localizer_candidate_expansion.py'):
        files[name.replace('/','__')] = (REPO/name).read_bytes()
    for name, raw in files.items():
        with (dest/name).open('xb') as stream: stream.write(raw)
    receipt = encoded(dict(decision='D-289',state='candidate_selection_complete_not_qualification',
                           files={name:sha(raw) for name,raw in files.items()}))
    with (dest/'receipt.json').open('xb') as stream: stream.write(receipt)
    print(dest);print('receipt_sha256='+sha(receipt));print(json.dumps(build()['accounting']))


if __name__ == '__main__': main()
