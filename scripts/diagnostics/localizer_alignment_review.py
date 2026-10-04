"""Three fixed CT/mask pairs: bounded in-memory loading and engineering contact sheets."""
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import signal
import time
from uuid import uuid4

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw
import yaml

from scripts.diagnostics.localizer_content_verify import load_spec, open_relative, signature, check_memory, digest, REPO
from scripts.diagnostics.storage_setup import disk_info
from src.data.binary_label_policy import decode_binary, APPROVED_POLICY

IDS=['PanTS_00000003','PanTS_00000026','PanTS_00000031']


def load_image(root,row):
    fd=open_relative(root,row['uri'])
    try:
        expected=dict(row['observation'],bytes=row['bytes'])
        if signature(os.fstat(fd))!=expected:raise ValueError('Source identity changed')
        with os.fdopen(os.dup(fd),'rb') as stream:data=stream.read(row['bytes']+1)
        if len(data)!=row['bytes'] or digest(data)!=row['expected_content_sha256']:raise ValueError('Source bytes changed')
        if signature(os.fstat(fd))!=expected:raise ValueError('Source mutated')
        other=open_relative(root,row['uri'])
        try:
            if signature(os.fstat(other))!=expected:raise ValueError('Source path replaced')
        finally:os.close(other)
    finally:os.close(fd)
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:raw=stream.read(256*1024**2+1)
    if len(raw)>256*1024**2:raise ValueError('Expanded byte cap')
    img=nib.Nifti1Image.from_bytes(raw)
    if len(img.shape)!=3 or np.prod(img.shape)>20_000_000:raise ValueError('Voxel/shape cap')
    check_memory(2*1024**3)
    return img


def tile(ct,mask,spacing,axis,index,overlay):
    plane=np.take(ct,index,axis=axis).T[::-1,::-1]
    target=np.take(mask,index,axis=axis).T[::-1,::-1].astype(bool)
    grey=np.rint(np.clip((plane+160)/400,0,1)*255).astype('uint8')
    rgb=np.repeat(grey[...,None],3,axis=2)
    if overlay:rgb[target]=(.55*rgb[target]+.45*np.array([255,80,0])).astype('uint8')
    image=Image.fromarray(rgb)
    axes=[i for i in range(3) if i!=axis]
    w=plane.shape[1]*spacing[axes[0]];h=plane.shape[0]*spacing[axes[1]]
    scale=min(300/w,270/h)
    return image.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.NEAREST)


def render(ct,mask,spacing,panels,title):
    canvas=Image.new('RGB',(1600,50+310*((len(panels)+4)//5)),'#101010');draw=ImageDraw.Draw(canvas)
    draw.text((12,10),title+' | RAS; window [-160,240]; orange=pancreas',fill='white')
    labels={2:'Axial left=R top=A',1:'Coronal left=R top=S',0:'Sagittal left=A top=S'}
    for n,(axis,index,overlay) in enumerate(panels):
        x=(n%5)*320;y=50+(n//5)*310
        img=tile(ct,mask,spacing,axis,index,overlay)
        canvas.paste(img,(x+(320-img.width)//2,y+30+(270-img.height)//2))
        draw.text((x+5,y),f'{labels[axis]} {index} '+('overlay' if overlay else 'plain'),fill='white')
    return canvas


def run():
    started=time.monotonic()
    def timeout(*_):raise TimeoutError('Alignment job deadline')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
    spec=load_spec();rows=[r for r in spec['files'] if r['study_id'].split(':')[-1] in IDS]
    if len(rows)!=6 or sum(r['bytes'] for r in rows)>64*1024**2:raise ValueError('Read scope/cap')
    regbytes=(REPO/'configs/local/roots.yaml').read_bytes();reg=yaml.safe_load(regbytes)
    request=json.loads((REPO/next(r['path'] for r in spec['inputs'] if r['path'].endswith('/request.json'))).read_bytes())
    if digest(regbytes)!=request['registry_sha256']:raise ValueError('Registry changed')
    root=Path(request['diagnostic_root']);primary=reg['failure_domains']['external_primary'];mount=Path(primary['mount_path'])
    def check():
        if not mount.is_mount() or mount.resolve()!=mount:raise ValueError('Mount absent')
        info=disk_info(mount)
        if info.get('VolumeUUID')!=primary['volume_uuid'] or info.get('FilesystemType')!='apfs':raise ValueError('Wrong volume')
        check_memory(2*1024**3)
    check()
    if root.parent!=Path(reg['roots']['pants_source']['acquisition_parent']) or not root.is_relative_to(mount):raise ValueError('Root binding')
    parent=REPO/'outputs/prowl'
    if parent.resolve()!=parent or shutil.disk_usage(parent).free<100*1024**3:raise ValueError('Output root/capacity')
    dest=parent/('localizer-alignment-'+str(uuid4()));dest.mkdir()
    hashes={};used=0
    def save(name,data):
        nonlocal used
        if used+len(data)>64*1024**2:raise ValueError('Output cap')
        with (dest/name).open('xb') as f:f.write(data)
        used+=len(data);hashes[name]=digest(data)
    plan=(REPO/'docs/capstone/data/LOCALIZER-ALIGNMENT-JOB-2026-09-28.md').read_bytes()
    save('request.json',json.dumps(dict(files=rows,plan_sha256=digest(plan),plan=plan.decode(),code=Path(__file__).read_text()),sort_keys=True).encode())
    print(dest,flush=True)
    for raw in IDS:
        pair={r['kind']:r for r in rows if r['study_id'].endswith(raw)};check()
        ctimg=load_image(root,pair['ct']);maskimg=load_image(root,pair['pancreas'])
        if ctimg.shape!=maskimg.shape or not np.allclose(ctimg.affine,maskimg.affine,rtol=0,atol=1e-5):raise ValueError('Grid disagreement')
        if ctimg.header.get_xyzt_units()[0]!='mm':raise ValueError('CT physical units unresolved')
        ct=nib.as_closest_canonical(ctimg).get_fdata(dtype=np.float32)
        mimg=nib.as_closest_canonical(maskimg);mask,decoded=decode_binary(mimg.get_fdata(dtype=np.float64),policy=APPROVED_POLICY)
        if not np.isfinite(ct).all() or not mask.any():raise ValueError('Nonfinite CT/empty target')
        coords=np.where(mask);z=np.unique(coords[2])
        if len(z)>96:raise ValueError('Axial review plane cap')
        spacing=nib.affines.voxel_sizes(mimg.affine)
        mid=[int(np.median(c)) for c in coords]
        views=[(2,int(z[0])),(2,int(z[len(z)//2])),(2,int(z[-1])),(1,mid[1]),(0,mid[0])]
        overview=[(a,i,False) for a,i in views]+[(a,i,True) for a,i in views]
        sheets={'overview':overview,'axial':[(2,int(i),True) for i in z]}
        for name,panels in sheets.items():
            im=render(ct,mask,spacing,panels,raw+' '+name);b=io.BytesIO();im.save(b,format='PNG');save(raw+'-'+name+'.png',b.getvalue())
        save(raw+'.json',json.dumps(dict(study_id='pants:study:'+raw,source=pair,shape=list(ct.shape),
            canonical_affine=mimg.affine.tolist(),spacing_mm=spacing.tolist(),views=sheets,decode=decoded,
            mask_bounds=[[int(c.min()),int(c.max())] for c in coords],orientation_only=True,
            original_affine=ctimg.affine.tolist(),eligibility='not_assessed'),sort_keys=True).encode())
        check();del ct,mask,ctimg,maskimg,mimg,coords
    for name,sha in hashes.items():
        if digest((dest/name).read_bytes())!=sha:raise ValueError('Evidence readback')
    check()
    save('verification.json',json.dumps(dict(status='render_complete_not_visual_verdict',files=hashes.copy(),
        elapsed_seconds=time.monotonic()-started,source_bytes=sum(r['bytes'] for r in rows),eligibility_granted=0),sort_keys=True).encode())
    signal.alarm(0)


if __name__=='__main__':run()
