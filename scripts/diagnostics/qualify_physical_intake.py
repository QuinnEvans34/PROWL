"""Physical-detail qualification, reusing the completed native CT-content audit."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from itertools import product
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import nibabel as nib
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import SETUP,TRAIN,MANIFEST,read_journal
from src.data.segmenter_native_inputs_v1 import anchors
from src.data.segmenter_physical_inputs_v1 import PhysicalInputs
from src.data.segmenter_native_windows_v1 import orient,tiles,starts,sample_origin
from src.data.segmenter_physical_windows_v1 import POLICY,physical_geometry,sample_window,native_destination,PhysicalReconstructor
from src.data.segmenter_content_v1 import target_content
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import training_guard,watch_windows,require_ac
BASE=Path('E:/PROWL/readiness/native-intake-20261018-a02')
OUT=Path('E:/PROWL/readiness/physical-intake-20261018-a01')
SPEC=ROOT/'docs/capstone/operations/PANTS-PHYSICAL-DETAIL-INTAKE-20261018.json'
_P=None;_SOURCE=None


def provider():
    return PhysicalInputs(manifest=MANIFEST,review=SETUP/'cohort-review.json',train_file=TRAIN,dev_file=SETUP/'development.txt')


def verify():
    r=json.loads((OUT/'request.json').read_text())
    if any(sha256(p)!=h for p,h in r['pins'].items()):raise ValueError('Physical producing/evidence pin changed')
    if provider().pin!=r['control_sha256']:raise ValueError('Physical input control changed')
    return r


def prepare():
    from scripts.diagnostics.qualify_native_intake import verify as native_verify
    native_verify();p=provider()
    source=read_journal(BASE/'cohort-complete/cases.jsonl')
    if len(source)!=1403 or not json.loads((BASE/'cohort-complete/results.json').read_text())['completed']:
        raise ValueError('Native source audit incomplete')
    resources=json.loads((BASE/'cohort-complete/resources.json').read_text())
    if not resources['workers_reaped']:raise ValueError('Native audit workers still active')
    pilot=json.loads((BASE/'request.json').read_text())['pilot']
    files=list((ROOT/'src').rglob('*.py'))+[Path(__file__),SPEC,BASE/'cohort-complete/cases.jsonl',
        BASE/'cohort-complete/results.json',BASE/'cohort-complete/resources.json',BASE/'pilot/visual-review.json']
    OUT.mkdir(exist_ok=False)
    request=dict(pins={str(x):sha256(x) for x in files},control=p.control,control_sha256=p.pin,policy=POLICY,
        pilot=pilot,source_audit=str(BASE/'cohort-complete/cases.jsonl'),
        cohort_seconds=21600-resources['seconds'],pilot_seconds=3200,rss_bytes=12*1024**3,
        source_ct_content='All 1403 native CTs already read/checked; unchanged observations bind reuse. New cohort stage reads labels only.',
        scientific_training=False,test_reads=0)
    with (OUT/'request.json').open('xb') as f:f.write(canonical(request))


def load_labels(p,source):
    name=source['case_id'];role=source['role'];p.check_role(name,role,'audit')
    metadata=p.root/(name+'.json')
    if sha256(metadata)!=source['metadata_sha256']:raise ValueError('Source metadata changed')
    masks={}
    for kind in ('ct','pancreas','lesion'):
        path=Path(p.rows[name][kind+'_path']);s=path.stat()
        if dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)!=p.observations[name][kind]:
            raise ValueError('Source observation changed')
        if kind=='ct':continue  # Reuse completed finite/content audit, not a new CT payload pass.
        if sha256(path)!=source['source_sha256'][kind]:raise ValueError('Label changed')
        obj=nib.load(path);g=source['geometry']
        if obj.shape!=tuple(g['source_shape']) or not np.allclose(obj.affine,g['source_affine'],atol=1e-5,rtol=0):raise ValueError('Label alignment')
        proxy=obj.dataobj;mask,_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
        masks[kind]=orient(mask,g)
    target=masks['pancreas'].astype(np.uint8);target[masks['lesion']!=0]=2
    positive=bool(masks['lesion'].any())
    if positive!=source['positive'] or int(masks['lesion'].sum())!=source['lesion_voxels']:raise ValueError('Changed native target')
    centers=anchors(masks['lesion'] if positive else masks['pancreas'])
    if positive and len(centers)!=source['components']:raise ValueError('Component count changed')
    if not positive:centers=centers[:1]
    return dict(name=name,target=target,geometry=source['geometry'],positive=positive,centers=centers)


def check_geometry(record):
    native=record['native'];a=np.array(native['affine']);b=np.array(record['affine']);f=np.array(record['factors'])
    if min(f)<1 or max(record['spacing_mm'])>1.00001:raise ValueError('Downsampling or spacing failure')
    for corner in product(*[(-.5,n-.5) for n in record['native_shape']]):
        fine=(np.array(corner)+.5)*f-.5
        if not np.allclose(a @ [*corner,1],b @ [*fine,1],rtol=0,atol=1e-5):raise ValueError('Physical field edge changed')
    for n,factor,fine_n in zip(record['native_shape'],f,record['shape']):
        original=np.arange(n);centers=factor*(original+.5)-.5
        for neighbors in (np.floor(centers),np.ceil(centers)):
            if not np.array_equal(np.floor((neighbors+.5)/factor).astype(int),original):raise ValueError('Native target index round trip')
        covered=np.zeros(n,bool)
        for start in starts(fine_n):covered|=(centers>=start)&(centers<=min(start+143,fine_n-1))
        if not covered.all():raise ValueError('Native-center inference gap')


def case_check(p,source,pilot=False):
    began=time.monotonic();name=source['case_id'];case=load_labels(p,source)
    if pilot:
        actual=p.load(name,role='train')
        if not np.array_equal(actual['target'],case['target']):raise ValueError('Label-only audit differs from production loader')
        case=actual
    record,centers,bank=p.describe(case);check_geometry(record)
    seen_cover=set();seen_anchors=set()
    for visit in range(18):
        origin,kind=sample_origin(record['shape'],centers,visit=visit,seed=42,case_id=name,coverage=bank)
        if kind.startswith('coverage_'):seen_cover.add(int(kind.split('_')[1]))
        if kind.startswith('anchor_'):seen_anchors.add(int(kind.split('_')[1]))
    if seen_cover!=set(range(len(bank))) or seen_anchors!=set(range(len(centers))):raise ValueError('Incomplete scheduled field/component exposure')
    support=case['target']==2 if case['positive'] else case['target']>0
    # The bank is Cartesian and covers the entire expanded annotation bounding field,
    # including voxel-cell edges, not only selected native centers.
    axes=[sorted({origin[d] for origin in bank}) for d in range(3)]
    if set(bank)!=set(product(*axes)):raise ValueError('Non-Cartesian cover bank')
    for axis,(factor,n) in enumerate(zip(record['factors'],record['shape'])):
        indices=np.flatnonzero(support.any(axis=tuple(d for d in range(3) if d!=axis)))
        low,high=int(indices[0])*factor,(int(indices[-1])+1)*factor
        covered=np.zeros(high-low,bool)
        for start in axes[axis]:covered[max(0,start-low):min(high-low,start+144-low)]=True
        if not covered.all():raise ValueError('Annotation field clipped')
    # Exercise actual production target sampling and inverse interpolation on EVERY
    # guaranteed annotation window. Full tiled oracle reconstruction is additionally
    # exercised on the real twelve-case pilot; the full-field axis proof is per-case.
    for origin in bank:
        patch,_=sample_window(case['target'],record,origin,order=0)
        destination,coords=native_destination(record,origin)
        restored=ndimage.map_coordinates(patch.astype(np.float32),coords,order=1,mode='nearest',prefilter=False)
        if not np.array_equal(restored,case['target'][destination]):raise ValueError('Actual window target round trip lost detail')
    ts=tiles(record['shape']);oracle=None
    if pilot:
        recon=PhysicalReconstructor(record)
        for origin in ts:
            patch,_=sample_window(case['target'],record,origin,order=0)
            recon.add(origin,np.stack([patch==k for k in range(3)]).astype(np.float32))
        oracle=bool(np.array_equal(recon.finish(ts).argmax(0),case['target']))
        if not oracle:raise ValueError('Full native oracle reconstruction failed')
        del recon
        render(case,record,bank,name)
    return dict(case_id=name,role=source['role'],positive=source['positive'],native_shape=record['native_shape'],
        fine_shape=record['shape'],spacing_mm=record['spacing_mm'],factors=record['factors'],
        source_shape=source['source_shape'],source_sha256=source['source_sha256'],metadata_sha256=source['metadata_sha256'],
        old_coverage=source['old_coverage'],new_field_coverage=1.,lesion_voxels=source['lesion_voxels'],components=source['components'],
        exact_target_roundtrip=True,boundary_voxels_unchanged=True,all_anchors_exposed=True,
        annotated_field_exposure_18_visits=1.,guaranteed_cover_windows=len(bank),full_field_tile_count=len(ts),
        roundtrip_dice=1. if source['positive'] else None,roundtrip_recall=1. if source['positive'] else None,
        oracle_reconstruction_exact=oracle,geometry=record,elapsed_seconds=time.monotonic()-began,
        roundtrip_evidence='all native-center index mappings plus actual annotation-window sampling/inverse; full tiled oracle on pilot',
        ct_payload_read=pilot)


def render(case,record,bank,name):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    origin=bank[0];x,_=sample_window(case['image'],record,origin,order=1);y,_=sample_window(case['target'],record,origin,order=0)
    foreground=y==2 if case['positive'] else y>0
    center=np.rint(np.argwhere(foreground).mean(0)).astype(int)
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for axis,ax in enumerate(axes):
        sl=[slice(None)]*3;sl[axis]=int(center[axis]);other=[d for d in range(3) if d!=axis]
        ax.imshow(x[tuple(sl)].T,origin='lower',cmap='gray',vmin=0,vmax=1,interpolation='nearest',
                  aspect=record['spacing_mm'][other[1]]/record['spacing_mm'][other[0]])
        for label,color in ((1,'cyan'),(2,'red')):
            m=y[tuple(sl)]==label
            if m.any() and not m.all():ax.contour(m.T,levels=[.5],colors=[color],linewidths=.7)
        ax.set_title(f'Actual 144³ input, axis {axis}');ax.set_axis_off()
    fig.suptitle(name+' | first of '+str(len(bank))+' coverage windows\nSpacing '+str(np.round(record['spacing_mm'],3).tolist())+' mm; coarse axes upsampled, no downsampling. Masks are targets.',fontsize=10)
    fig.tight_layout(rect=(0,0,1,.88));fig.savefig(OUT/'pilot'/(name+'.png'),dpi=110);plt.close(fig)


def init_worker():
    global _P,_SOURCE
    _P=provider();_SOURCE={r['case_id']:r for r in read_journal(BASE/'cohort-complete/cases.jsonl')}


def task(name):return case_check(_P,_SOURCE[name],False)


def worker(stage):
    request=verify();p=provider();source={r['case_id']:r for r in read_journal(BASE/'cohort-complete/cases.jsonl')}
    names=p.control['train']+p.control['validation'];records={};began=time.monotonic();directory=OUT/stage
    def save(r):
        if r['case_id'] in records:raise ValueError('Duplicate case')
        records[r['case_id']]=r
        with (directory/'cases.jsonl').open('ab') as f:f.write(canonical(r));f.flush();os.fsync(f.fileno())
        print(json.dumps(dict(completed=len(records),total=12 if stage=='pilot' else 1403,seconds=time.monotonic()-began)),flush=True)
    if stage=='pilot':
        for name in request['pilot']:save(case_check(p,source[name],True))
    else:
        for r in read_journal(OUT/'pilot/cases.jsonl'):save(dict(r,reused_pilot=True))
        pool=ProcessPoolExecutor(max_workers=2,initializer=init_worker)
        try:
            futures=[pool.submit(task,n) for n in names if n not in records]
            for future in as_completed(futures):save(future.result())
        except BaseException as exc:
            (directory/'failure.json').write_bytes(canonical(dict(error=str(exc),completed=len(records))))
            # Fail immediately; the owning Windows job supervisor reaps descendants.
            print('Physical intake failed: '+str(exc),file=sys.stderr,flush=True);os._exit(1)
        else:pool.shutdown(wait=True)
    verify()
    expected=set(request['pilot'] if stage=='pilot' else names)
    if set(records)!=expected:raise ValueError('Missing member')
    (directory/'results.json').write_bytes(canonical(dict(completed=True,cases=len(records),
        train=sum(r['role']=='train' for r in records.values()),development=sum(r['role']=='validation' for r in records.values()),
        seconds=time.monotonic()-began,ct_payload_reads=12 if stage=='pilot' else 0,
        exact_native_target_roundtrip=True,full_annotation_field_coverage=1.,test_reads=0,scientific_updates=0)))


def run(stage):
    request=verify()
    if stage=='cohort' and not (OUT/'pilot/visual-review.json').is_file():raise ValueError('Pilot visual review required')
    directory=OUT/stage;directory.mkdir(exist_ok=False)
    def tick():
        require_ac()
        if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Free space floor')
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        tick()
        with (directory/'worker.log').open('x') as log:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',stage],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:watch_windows(process,seconds=request[stage+'_seconds'],rss_bytes=request['rss_bytes'],tick=tick)
            finally:(directory/'resources.json').write_bytes(canonical(getattr(process,'duration_resources',{})))
    print(stage+' physical qualification complete; workers reaped',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--run',choices=['pilot','cohort']);ap.add_argument('--worker',choices=['pilot','cohort']);a=ap.parse_args()
    if a.prepare:prepare()
    elif a.run:run(a.run)
    elif a.worker:worker(a.worker)
