"""Two bound training cases; real input replay, never optimizer qualification."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha,ARCHIVE_SHA
from src.data.manifest_records import canonical,digest
OUT=BASE/'annotation-errata-inputs-01'
NAMES=['PanTS_00003059','PanTS_00000691']
CACHE_SHA='77811d7b62a188d5644887b3ed52f7082ab95a6f576042ef87baac485e187c63'
OVERLAY_SHA='033f8f5cb7533031412a04f8daff62e5f95786123d0a21fc3c32c711ef5b06bc'


def prepare():
    archive=BASE/'mac-kd-metadata-20261023-a01.zip'; assert sha(archive)==ARCHIVE_SHA
    bindings=json.loads((BASE/'pilot-local-bindings-01.json').read_text())
    pilot={r['case_id']:r for r in bindings['pilot']}
    meta_root=OUT/'metadata'; meta_root.mkdir()
    with zipfile.ZipFile(archive) as z:
        handoff=json.loads(z.read('HANDOFF.json'))
        def read(n):
            b=z.read(n); assert hashlib.sha256(b).hexdigest()==handoff['files'][n]['sha256']; return b
        train=read('membership/train.txt'); dev=read('membership/development.txt')
        (OUT/'train.txt').write_bytes(train);(OUT/'development.txt').write_bytes(dev)
        rows=json.loads(read('source/manifest-selected.json'))
        old=json.loads(read('source/original-control-selected.json'))
        review=json.loads(read('membership/cohort-review.json'))
        for row in rows:
            name=row['case_id']
            if name not in NAMES: continue
            files=pilot[name]['files']; observations={}
            for kind,f in files.items():
                p=Path(f['path']);s=p.stat()
                assert f['status']=='match' and sha(p)==f['expected_sha256']==f['sha256']
                assert (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)==(f['bytes'],f['mtime_ns'],f['inode'],f['device'])
                row[kind+'_path']=str(p)
                observations[kind]=dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
            old['observations'][name]=observations
            raw=read(f'source/cached-metadata/{name}.json')
            (meta_root/(name+'.json')).write_bytes(raw)
            assert hashlib.sha256(raw).hexdigest()==review['prepared_cache']['members'][name]['metadata_sha256']
        with (OUT/'manifest.csv').open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        old['manifest_sha256']=sha(OUT/'manifest.csv')
        # Unvisited rows retain remote paths; this is NOT a full Mac source admission.
        write(meta_root/'control.json',old)
        review['prepared_cache']['root']=str(meta_root)
        write(OUT/'review.json',review)


def worker(stage):
    if os.environ.get('PROWL_ERRATA_INPUTS')!='1': raise ValueError('Supervisor required')
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from src.data.pants_errata_inputs_v1 import ErrataInputs
    from src.data.segmenter_varied_region_v1 import planned_visits
    from src.training.segmenter_augmentation_v1 import augment
    from src.data.segmenter_full_batch_v1 import array_hash
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items(): assert sha(Path(p))==h,p
    train=(OUT/'train.txt').read_text().splitlines(); counts,_=planned_visits(train)
    p=ErrataInputs(correction_root=BASE/'annotation-errata-cache-01',
        correction_manifest_sha256=CACHE_SHA,overlay_sha256=OVERLAY_SHA,
        manifest=OUT/'manifest.csv',review=OUT/'review.json',train_file=OUT/'train.txt',
        dev_file=OUT/'development.txt',planned_counts=counts)
    rows=[]
    for name in NAMES:
        case=p.load(name,role='train',operation='optimizer')
        assert not case['positive'] and not (case['target']==2).any()
        assert case['image'].shape==case['target'].shape and case['image'].dtype==np.float32
        # Exercise actual from_case path with three addresses, loading each CT only once.
        for step,visit in [(0,0),(1,1),(3,1)]:
            x,y,t,trace=p.from_case(case,step=step,focused_visit=visit,seed=42)
            a,b,aug=augment(x,y,t,seed=42,update=step+1,case_id=name)
            assert not (b==2).any()
            rows.append(dict(case_id=name,step=step,visit=visit,image_sha256=array_hash(x),
                target_sha256=array_hash(y),augmented_image_sha256=array_hash(a),
                augmented_target_sha256=array_hash(b),sampling=trace,augmentation=aug))
        print(stage,name,'real CT/target and three sampled/augmented views passed',flush=True)
    result=dict(provider_sha256=p.pin,rows=rows,ct_reads=2,training_updates=0,
                scope='two_case_real_input_replay_not_optimizer_cold_restore',full_cohort_admitted=False)
    if stage=='cold':
        prior=json.loads((OUT/'producer/result.json').read_text())
        assert canonical(prior)==canonical(result),'Fresh-process input replay differs'
    for path,h in request['pins'].items(): assert sha(Path(path))==h,path
    write(OUT/stage/'result.json',result)


if __name__=='__main__':
    if '--worker' in sys.argv: worker(sys.argv[-1])
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();OUT.mkdir(exist_ok=False);prepare()
        pins=dict(json.loads((BASE/'annotation-errata-cache-01/request.json').read_text())['pins'])
        for path in [Path(__file__).resolve(),ROOT/'src/data/pants_errata_inputs_v1.py',ROOT/'tests/test_pants_errata_inputs_v1.py']+list(OUT.glob('*.json'))+list(OUT.glob('*.txt'))+list(OUT.glob('*.csv'))+list((OUT/'metadata').glob('*.json')):
            pins[str(path)]=sha(path)
        write(OUT/'request.json',dict(pins=pins,cases=NAMES,seconds_per_stage=600,rss_bytes=12*1024**3,
            no_model_or_optimizer=True,full_cohort_admitted=False))
        for stage in ['producer','cold']:
            dest=OUT/stage;dest.mkdir()
            ok=run([sys.executable,__file__,'--worker',stage],dest,seconds=600,rss_bytes=12*1024**3,
                env={**os.environ,'PROWL_ERRATA_INPUTS':'1','OMP_NUM_THREADS':'2'})
            if not ok: raise SystemExit(1)
        write(OUT/'result.json',dict(success=True,stages=['producer','cold'],cases=2,views_per_stage=6,
            full_cohort_admitted=False,optimizer_cold_restore=False,scientific_launch_authorized=False))
