"""Bounded Phase C diagnostic, with a separate process/RSS/time supervisor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

REPO=Path(__file__).resolve().parents[2]
CAP=REPO/'docs/capstone/data/LOCALIZER-PREPROCESSING-CAPABILITY-2026-09-28.json'
RECIPE=REPO/'configs/capstone/localizer-preprocessing-v1.json'
CAP_PIN='0e0a05279dead8c365a3359f35da260aacdcca20c98400ddb820242a1ed80473'
RECIPE_PIN='3bdc8ae7f60039b6a3e4e8a3ae2629255af4f3519ff83814145f7988d2242f94'


def sha(data):return hashlib.sha256(data).hexdigest()


def worker(dest):
    import io
    import numpy as np
    import torch
    import monai
    import nibabel
    from src.data.localizer_inputs import open_localizer_dataset
    from src.data.localizer_preprocessing import preprocess,restore_to_source
    from scripts.diagnostics.localizer_alignment_review import render
    from src.data.source_inventory_records import require
    require(dest.parent==REPO/'outputs/prowl' and dest.resolve(strict=True)==dest,'Unexpected evidence destination')
    torch.set_num_threads(2)
    started=time.monotonic();hashes={};used=0
    def save(name,data):
        nonlocal used
        require(Path(name).name==name and used+len(data)<=64*1024**2,'Output scope/budget')
        require(shutil.disk_usage(dest).free>=100*1024**3+len(data),'Internal free-space floor')
        with (dest/name).open('xb') as f:f.write(data)
        used+=len(data);hashes[name]=sha(data)
    dataset=open_localizer_dataset(repo=REPO,capability_path=CAP,trusted_capability_sha256=CAP_PIN,
                                   recipe_path=RECIPE,trusted_recipe_sha256=RECIPE_PIN)
    require(len(dataset)==2,'Unexpected cohort count')
    reports=[]
    for index in range(len(dataset)):
        load_start=time.monotonic();image,target,affine,decode=dataset.load_native(index)
        load_seconds=time.monotonic()-load_start
        transform_start=time.monotonic();train=preprocess(image,affine,dataset.recipe,target=target)
        transform_seconds=time.monotonic()-transform_start
        infer=preprocess(image,affine,dataset.recipe)
        require(torch.equal(train['image'],infer['image']),'Train/inference input differs')
        require(train['image'].shape[0]==1 and train['image'].min()>=0 and train['image'].max()<=1,'Image channel/range')
        restored=restore_to_source(train['label'],train['transform_record'],discrete=True)[0].as_tensor().numpy().astype(np.uint8)
        require(np.isin(restored,[0,1]).all() and restored.any(),'Restoration lost binary positive target')
        label=train['label'][0].as_tensor().numpy().astype(np.uint8)
        processed=train['image'][0].as_tensor().numpy()*400-100
        spacing=np.linalg.norm(np.asarray(train['transform_record']['processed_affine'])[:3,:3],axis=0)
        raw=dataset.descriptors[index]['study_id'].split(':')[-1]
        for suffix,ct,mask,sp,second in [('preprocessed',processed,label,spacing,None),
                                       ('roundtrip',image,target,np.linalg.norm(affine[:3,:3],axis=0),restored)]:
            coords=np.where(mask);mid=[int(np.median(c)) for c in coords];views=[(2,mid[2]),(1,mid[1]),(0,mid[0])]
            if second is None:
                panels=[(a,i,False) for a,i in views]+[(a,i,True) for a,i in views]
                sheet=render(ct,mask,sp,panels,raw+' '+suffix)
            else:
                # Two separately labeled sheets stacked: original target and restored target.
                from PIL import Image
                top=render(ct,mask,sp,[(a,i,True) for a,i in views],raw+' original target')
                bottom=render(ct,second,sp,[(a,i,True) for a,i in views],raw+' restored target')
                sheet=Image.new('RGB',(top.width,top.height+bottom.height));sheet.paste(top,(0,0));sheet.paste(bottom,(0,top.height))
            b=io.BytesIO();sheet.save(b,format='PNG');save(raw+'-'+suffix+'.png',b.getvalue())
        report=dict(study_id=dataset.descriptors[index]['study_id'],source_shape=list(image.shape),
            processed_shape=list(label.shape),source_foreground=int(target.sum()),processed_foreground=int(label.sum()),
            restored_foreground=int(restored.sum()),roundtrip_dice=float(2*np.logical_and(target,restored).sum()/(target.sum()+restored.sum())),
            train_inference_equal=True,load_seconds=load_seconds,transform_seconds=transform_seconds,
            source=dataset.descriptors[index],decode=decode,transform_record=train['transform_record'])
        reports.append(report);save(raw+'.json',json.dumps(report,sort_keys=True).encode())
        del image,target,train,infer,label,processed,restored
    save('results.json',json.dumps(dict(status='numerical_checks_passed_visual_review_pending',cases=reports,
        elapsed_seconds=time.monotonic()-started,environment=dict(python=sys.version,torch=torch.__version__,
        monai=monai.__version__,numpy=np.__version__,nibabel=nibabel.__version__),source_files=4,
        source_bytes=23331170,training_started=False),sort_keys=True).encode())
    save('worker-files.json',json.dumps(hashes,sort_keys=True).encode())


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path);p.add_argument('--run',action='store_true');a=p.parse_args()
    if a.worker:worker(a.worker);return
    if not a.run:p.error('--run required')
    if shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Internal free-space floor')
    dest=REPO/'outputs/prowl'/('localizer-preprocessing-'+str(uuid4()));dest.mkdir()
    request=dict(capability_sha256=CAP_PIN,recipe_sha256=RECIPE_PIN,maximum_worker_rss=4*1024**3,maximum_seconds=600,
        code={n:(REPO/n).read_text() for n in ['src/data/localizer_inputs.py','src/data/localizer_preprocessing.py',
        'scripts/diagnostics/localizer_preprocessing_check.py']},
        plan=(REPO/'docs/capstone/data/LOCALIZER-PREPROCESSING-JOB-2026-09-28.md').read_text())
    with (dest/'request.json').open('x') as f:json.dump(request,f,sort_keys=True)
    print(dest,flush=True);start=time.monotonic();peak=0;reason=None
    with (dest/'worker.log').open('xb') as log:
        proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.localizer_preprocessing_check','--worker',str(dest)],
                              cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                if time.monotonic()-start>600:reason='time_cap';raise RuntimeError(reason)
                rss=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if rss.returncode==0 and rss.stdout.strip():
                    peak=max(peak,int(rss.stdout.strip())*1024)
                    if peak>4*1024**3:reason='memory_cap';raise RuntimeError(reason)
                elif proc.poll() is None:reason='memory_monitor_failed';raise RuntimeError(reason)
                time.sleep(.25)
            if proc.returncode:reason='worker_failed';raise RuntimeError(reason)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
            (dest/'supervisor.json').write_text(json.dumps(dict(exit_code=proc.returncode,stop_reason=reason,
                peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start),sort_keys=True))
    refs=json.loads((dest/'worker-files.json').read_bytes())
    for name,pin in refs.items():
        if Path(name).name!=name or sha((dest/name).read_bytes())!=pin:raise ValueError('Saved evidence changed')
    refs.update({name:sha((dest/name).read_bytes()) for name in ['request.json','worker.log','worker-files.json','supervisor.json']})
    payload=json.dumps(dict(status='preprocessing_checks_complete_visual_review_pending',files=refs,training_started=False),sort_keys=True).encode()
    with (dest/'verification.json').open('xb') as f:f.write(payload)
    print('receipt_sha256='+sha(payload),flush=True)


if __name__=='__main__':main()
