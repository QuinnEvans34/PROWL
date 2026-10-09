"""Validate an interrupted audit's complete prefix without modifying prior evidence."""
import hashlib
import json
from pathlib import Path
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require


def validate_parent(parent, provider, cfg):
    parent=Path(parent)
    require(not (parent/'summary.json').exists(), 'Completed audit cannot be continued')
    resources=json.loads((parent/'resources.json').read_text())
    require(resources.get('workers_reaped') is True, 'Parent workers must be reaped')
    request=json.loads((parent/'request.json').read_text())
    require(request['config']==cfg, 'Continuation configuration changed')
    require((parent/'input-control.json').read_bytes()==canonical(provider.control), 'Parent input control changed')
    rows=[json.loads(line) for line in (parent/'cases.jsonl').read_text().splitlines()]
    expected=[(name,role) for role,key in [('train','train'),('validation','validation')]
              for name in provider.control[key]]
    require(0<len(rows)<len(expected), 'Nonempty incomplete parent prefix required')
    require([(r['case_id'],r['role']) for r in rows]==expected[:len(rows)], 'Parent ledger not an exact ordered prefix')
    expected_files={'control.json'}
    for r in rows:
        name=r['case_id'];path=provider.cache/(name+'.npz')
        require(r['status']=='technical_pass' and r['target_state']==provider.states[name], 'Parent failure/target drift')
        require(Path(r['cache_path']).resolve()==path.resolve(), 'Parent cache path changed')
        for suffix in ('.npz','.json'):
            member=provider.cache/(name+suffix)
            require(member.is_file() and not member.is_symlink(), 'Missing/unsafe completed cache member')
            expected_files.add(member.name)
    require({p.name for p in provider.cache.iterdir()}==expected_files, 'Unexpected/orphan cache evidence; review separately')
    pins={name:hashlib.sha256((parent/name).read_bytes()).hexdigest() for name in
          ('request.json','input-control.json','cases.jsonl','resources.json')}
    return rows,dict(parent=str(parent.resolve()),parent_sha256=pins,reused_cases=len(rows),
                     remaining_cases=len(expected)-len(rows),original_payload_replay=False)
