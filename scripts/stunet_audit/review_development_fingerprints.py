"""Reuse the 75 frozen fingerprints for within-development image-duplicate review."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import time
from scripts.stunet_audit.overlap import FingerprintIndex

ROOT=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-audit-20261106')

def main():
    start=time.monotonic();manifest=ROOT/'query-manifest.json'
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!='95a2a0137f5427b7f437ddd413d3d67f5b086f1cbed088a3ba2c2fa1d64bc710':raise ValueError('Development manifest changed')
    rows=json.loads(manifest.read_text())['queries']
    if len(rows)!=75 or any(r['role']!='development' for r in rows):raise ValueError('Scope differs')
    destination=ROOT/'within-development-01';destination.mkdir(exist_ok=False)
    refs=[];pins={};file_groups=defaultdict(list);voxel_groups=defaultdict(list)
    for row in rows:
        path=ROOT/'query-fingerprints-01'/(hashlib.sha256(row['case_id'].encode()).hexdigest()+'.json')
        raw=path.read_bytes()
        if len(raw)>2*1024**2:raise ValueError('Fingerprint file bound')
        pins[str(path)]=hashlib.sha256(raw).hexdigest();f=json.loads(raw)
        if f['file_sha256']!=row['sha256']:raise ValueError('Source binding differs')
        if not f.get('normalized_voxel_sha256'):raise ValueError('Full native fingerprint required')
        refs.append(dict(case_id=row['case_id'],fingerprint=f))
        file_groups[f['file_sha256']].append(row['case_id']);voxel_groups[f['normalized_voxel_sha256']].append(row['case_id'])
    (destination/'input-pins.json').write_text(json.dumps(pins,indent=2))
    index=FingerprintIndex(refs);ranked=[]
    for row in refs:
        candidates=[r for r in index.rank(row['fingerprint'],top_k=6) if r['reference_id']!=row['case_id']][:5]
        ranked.append(dict(case_id=row['case_id'],candidates=candidates))
    lookup={r['case_id']:r['fingerprint'] for r in refs}
    a,b=(lookup[k] for k in ('PanTS_00006755','PanTS_00002889'))
    result=dict(scope='75 permitted development fingerprints only; no new CT/mask/model reads',
        exact_file_groups=[v for v in file_groups.values() if len(v)>1],
        exact_scaled_float32_voxel_groups=[v for v in voxel_groups.values() if len(v)>1],
        known_pair_6755_2889=dict(file_equal=a['file_sha256']==b['file_sha256'],
            voxel_equal=a['normalized_voxel_sha256']==b['normalized_voxel_sha256'],patient_identity='NOT_ESTABLISHED'),
        training_development_patient_separation_verified=False,clearance_issued=False,seconds=time.monotonic()-start)
    (destination/'ranked-candidates.json').write_text(json.dumps(ranked,indent=2))
    (destination/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
