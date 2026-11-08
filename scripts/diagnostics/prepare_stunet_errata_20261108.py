"""One receipt-bound CPU correction; no CT/model reads or scientific dispatcher."""
import argparse, copy, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(4*1024**2), b''): h.update(block)
    return h.hexdigest()


def write(p, value):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())


def worker(r):
    import numpy as np
    import nibabel as nib
    from src.data.stunet_errata_20261108 import EXPECTED, POLICY, corrected_target, new_schedule
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_physical_windows_v1 import coverage_bank
    from src.data.segmenter_varied_region_v1 import components
    from scripts.diagnostics.plan_stunet_coverage_20261106 import check_cover
    out = Path(r['output']); out.mkdir(exist_ok=False)
    parent = json.loads(Path(r['parent_plan']).read_text()); members = copy.deepcopy(parent['members'])
    if set(r['cases']) != set(EXPECTED): raise ValueError('Exact seven cases required')
    proofs = {}; before = {}
    for cid, case in r['cases'].items():
        metadata = Path(case['metadata']); m = json.loads(metadata.read_text())
        if sha(metadata) != parent['members'][cid]['cache']['metadata_sha256']: raise ValueError('Stale metadata')
        masks = {}
        for kind in ('pancreas', 'lesion'):
            path = Path(case[kind]); h = sha(path); before[str(path)] = h
            if h != m['source_sha256'][kind]: raise ValueError('Source identity')
            obj = nib.load(path)
            if obj.shape != tuple(m['parent_geometry']['source_shape']) or not np.allclose(obj.affine, m['parent_geometry']['source_affine'], atol=1e-5, rtol=0): raise ValueError('Source alignment')
            masks[kind], _ = target_content(obj.dataobj.get_unscaled(), dict(slope=float(obj.dataobj.slope), intercept=float(obj.dataobj.inter)))
        original = corrected_target(cid, masks['pancreas'], masks['lesion'], role='train', lesion_sha256=m['source_sha256']['lesion'])
        target = orient(original, m['parent_geometry'])[tuple(slice(l,h) for l,h in zip(m['region_low'],m['region_high']))].copy()
        if target.shape != tuple(m['record']['native_shape']) or int(target.sum()) != int(original.sum()): raise ValueError('Pancreas field lost')
        cover = coverage_bank(target > 0, m['record'], window=128); check_cover(target, m['record'], cover)
        parts, positive = components(target, m['record'])
        if positive or (target == 2).any(): raise ValueError('Correction retains lesion')
        updated = copy.deepcopy(m)
        updated.update(cover=cover, parts=parts, positive=False, lesion_voxels=0,
                       annotation_policy=POLICY, original_lesion_voxels=m['lesion_voxels'],
                       original_metadata_sha256=sha(metadata), target_semantics='original pancreas plus empty corrected lesion')
        npz = out/(cid+'.npz'); mp = out/(cid+'.json')
        with npz.open('xb') as f: np.savez_compressed(f,target=target); f.flush(); os.fsync(f.fileno())
        write(mp, updated)
        with np.load(npz, allow_pickle=False) as f:
            if f.files != ['target'] or not np.array_equal(f['target'],target): raise ValueError('Target roundtrip')
        members[cid].update(cover=cover,positive=False,lesion_voxels=0,
                           cache=dict(bytes=npz.stat().st_size, metadata_sha256=sha(mp), target_sha256=sha(npz)))
        proofs[cid] = dict(original_source_sha256=m['source_sha256'],original_lesion_voxels=m['lesion_voxels'],
            corrected_lesion_voxels=0,pancreas_voxels=int(target.sum()),full_pancreas_retained=True,
            cache=members[cid]['cache'],coverage_windows=len(cover),components=len(parts))
        print(json.dumps(dict(case=cid,status='CORRECTED_CPU_ONLY')),flush=True)
        del original,target,masks
    for path,h in before.items():
        if sha(path) != h: raise ValueError('Original changed')
    ordinary = sorted(set(members)-set(EXPECTED))
    if any(members[c] != parent['members'][c] for c in ordinary): raise ValueError('Ordinary binding changed')
    schedule = new_schedule(members)
    overlay = dict(version=POLICY,complete=False,corrected_cases=proofs,parent_plan_sha256=sha(r['parent_plan']),
        ordinary_binding_count=len(ordinary),ordinary_bindings_exact=True,
        ordinary_array_rehash_performed=False,original_source_files_unchanged=True,
        status='CPU_CORRECTION_ONLY_NOT_TRAINING_READY')
    write(out/'overlay.json',overlay)
    write(out/'plan-proposal.json',dict(version='stunet-corrected-continuation-1',members=members,schedule=schedule,
        overlay_sha256=sha(out/'overlay.json'),parent_plan_sha256=sha(r['parent_plan']),
        corrected_cache=str(out),original_cache=r['original_cache'],training_positive=664,training_empty=669,
        complete_annotated_field_coverage=True,coverage_windows=sum(len(m['cover']) for m in members.values()),
        qualification='CPU_ONLY_PROVIDER_AND_RESTORE_PENDING'))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if sha(a.request)!=a.sha256: raise ValueError('Receipt hash')
    r=json.loads(Path(a.request).read_text())
    for path,h in r['pins'].items():
        if sha(path)!=h: raise ValueError('Pin changed: '+path)
    if a.worker: return worker(r)
    from src.operations.full_training_platform import require_ac,watch_windows
    from src.operations.stunet_continuation_storage_20261108 import check_storage,size
    require_ac();check_storage()
    if r['seconds']!=600 or r['rss_bytes']!=4*1024**3 or r['output_cap_bytes']!=32*1024**2: raise ValueError('CPU budget')
    if size('C:/Users/quinn/PROWL-Backups')+r['output_cap_bytes']>88*1024**3: raise RuntimeError('Qualification backup admission')
    root=Path(r['stage_root']);root.mkdir(exist_ok=False);back=Path(r['backup']);back.mkdir(exist_ok=False)
    if Path(r['output']).exists():raise FileExistsError('Prior attempt output')
    write(root/'dispatch.json',dict(supervisor=os.getpid(),request_sha256=a.sha256))
    child=None
    try:
        with (root/'worker.log').open('x') as log:
            child=subprocess.Popen([sys.executable,__file__,'--request',a.request,'--sha256',a.sha256,'--worker'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            write(root/'owner.json',dict(supervisor=os.getpid(),worker=child.pid))
            last=[0.]
            def tick():
                import psutil
                require_ac()
                if time.monotonic()-last[0]>60:check_storage();last[0]=time.monotonic()
                if size(r['output'])>r['output_cap_bytes']:raise RuntimeError('Output cap')
                rss=psutil.Process().memory_info().rss
                try: owned=[psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True)
                except psutil.NoSuchProcess: owned=[]
                for process in owned:
                    try:rss+=process.memory_info().rss
                    except psutil.NoSuchProcess:pass
                if rss>r['rss_bytes']:raise RuntimeError('Combined CPU RSS')
            resource=watch_windows(child,seconds=r['seconds'],rss_bytes=r['rss_bytes'],tick=tick)
        proof=[]
        for source in sorted(Path(r['output']).iterdir()):
            dest=back/source.name
            with source.open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
            h=sha(source)
            if h!=sha(dest):raise ValueError('CPU output backup mismatch')
            proof.append(dict(name=source.name,sha256=h,bytes=source.stat().st_size))
        write(root/'resources.json',dict(resource,success=True,exit_code=child.returncode,backups=proof))
    except BaseException as e:
        if child is not None and child.poll() is None:
            import psutil
            parent=psutil.Process(child.pid);children=parent.children(recursive=True)
            for process in children+[parent]:
                try:process.kill()
                except psutil.NoSuchProcess:pass
            child.wait(timeout=10);psutil.wait_procs(children,timeout=10)
        write(root/'failure.json',dict(error=repr(e),resources=getattr(child,'duration_resources',{})))
        raise


if __name__=='__main__':main()
