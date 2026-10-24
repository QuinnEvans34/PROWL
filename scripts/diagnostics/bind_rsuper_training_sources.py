"""Bind frozen full cohort to Mac bytes; no voxel decoding or training."""
import csv,json,os,sys,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha,ARCHIVE_SHA
OUT=BASE/'rsuper-training-sources-01'
def worker():
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(Path(p))==h
    source=Path(request['source']);meta_root=OUT/'metadata';meta_root.mkdir()
    with zipfile.ZipFile(BASE/'mac-kd-metadata-20261023-a01.zip') as z:
        handoff=json.loads(z.read('HANDOFF.json'))
        def read(n):
            b=z.read(n);assert hashlib.sha256(b).hexdigest()==handoff['files'][n]['sha256'];return b
        train=read('membership/train.txt');dev=read('membership/development.txt')
        (OUT/'train.txt').write_bytes(train);(OUT/'development.txt').write_bytes(dev)
        rows=json.loads(read('source/manifest-selected.json'));old=json.loads(read('source/original-control-selected.json'));review=json.loads(read('membership/cohort-review.json'))
        assert {r['case_id'] for r in rows}==set(train.decode().split()+dev.decode().split()) and len(rows)==1403
        for i,row in enumerate(rows):
            name=row['case_id'];n=int(name.removeprefix('PanTS_'));lo=((n-1)//1000)*1000+1
            paths={'ct':source/f'PanTSMini_ImageTr_{lo:08d}_{lo+999:08d}'/name/'ct.nii.gz','pancreas':source/'PanTSMini_Label'/name/'segmentations/pancreas.nii.gz','lesion':source/'PanTSMini_Label'/name/'segmentations/pancreatic_lesion.nii.gz'}
            raw=read(f'source/cached-metadata/{name}.json');meta=json.loads(raw);observations={}
            for kind,p in paths.items():
                before=p.stat();h=sha(p);after=p.stat()
                assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
                assert h==meta['source_sha256'][kind],(name,kind,'source hash mismatch')
                row[kind+'_path']=str(p);observations[kind]=dict(bytes=after.st_size,modified_ns=after.st_mtime_ns,inode=after.st_ino,device=after.st_dev)
            old['observations'][name]=observations;(meta_root/(name+'.json')).write_bytes(raw)
            assert sha(meta_root/(name+'.json'))==review['prepared_cache']['members'][name]['metadata_sha256']
            with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(index=i+1,case_id=name,matched=True))+'\n')
            if (i+1)%50==0:print(i+1,'/1403 source byte identities verified',flush=True)
        with (OUT/'manifest.csv').open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        old['manifest_sha256']=sha(OUT/'manifest.csv');write(meta_root/'control.json',old)
        review['prepared_cache']['root']=str(meta_root);write(OUT/'review.json',review)
        write(OUT/'result.json',dict(success=True,cases=1403,train=1333,development=70,decoded_voxel_reads=0,scientific_updates=0,source_bytes_only=True))
if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();archive=BASE/'mac-kd-metadata-20261023-a01.zip';assert sha(archive)==ARCHIVE_SHA
        p=json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot'][0]['files']['ct']['path']
        OUT.mkdir(exist_ok=False);write(OUT/'request.json',dict(source=str(Path(p).parents[2]),seconds=7200,rss_bytes=2*1024**3,pins={str(Path(__file__).resolve()):sha(Path(__file__)),str(archive):sha(archive)}))
        ok=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=7200,rss_bytes=2*1024**3,env=os.environ.copy())
        if not ok:raise SystemExit(1)
