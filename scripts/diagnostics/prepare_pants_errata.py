"""Materialize a versioned local errata overlay; no CT/model/training reads."""
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import ARCHIVE_SHA,sha
from src.data.pants_errata_v1 import VERSION,SOURCE,EXPECTED,corrected_mask
OUT=BASE/'annotation-errata-02'


def worker():
    if os.environ.get('PROWL_ERRATA')!='1':raise ValueError('Supervisor required')
    import numpy as np
    import nibabel as nib
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_physical_windows_v1 import coverage_bank
    from src.data.segmenter_varied_region_v1 import components,planned_visits,choose
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(Path(p))==h,p
    archive=BASE/'mac-kd-metadata-20261023-a01.zip';assert sha(archive)==ARCHIVE_SHA
    with zipfile.ZipFile(archive) as z:
        handoff=json.loads(z.read('HANDOFF.json'))
        def read(name):
            import hashlib
            value=z.read(name);assert hashlib.sha256(value).hexdigest()==handoff['files'][name]['sha256']
            return value
        train=read('membership/train.txt').decode().splitlines();dev=read('membership/development.txt').decode().splitlines()
        assert len(train)==1333 and len(dev)==70 and not set(train)&set(dev)
        assert set(EXPECTED)<=set(train) and not set(EXPECTED)&set(dev)
        members={n:json.loads(read(f'native-region/members/{n}.json')) for n in train}
        manifest={r['case_id']:r for r in json.loads(read('source/manifest-selected.json'))}
        assert set(manifest)==set(train+dev)
        focused,exposure=planned_visits(train)
        source=Path('/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922')
        rows=[]
        for name,count in sorted(EXPECTED.items()):
            meta=members[name];assert meta['positive'] and meta['lesion_voxels']==count
            paths={r:source/'PanTSMini_Label'/name/'segmentations'/f'{f}.nii.gz' for r,f in [('lesion','pancreatic_lesion'),('pancreas','pancreas')]}
            decoded={}
            for role,p in paths.items():
                assert sha(p)==meta['source_sha256'][role]
                obj=nib.load(p);assert list(obj.shape)==meta['parent_geometry']['source_shape'] and np.prod(obj.shape)<=256000000
                assert np.allclose(obj.affine,meta['parent_geometry']['source_affine'],rtol=0,atol=1e-4)
                decoded[role],_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
            original=nib.load(paths['lesion'])
            fixed=corrected_mask(name,decoded['lesion'],role='train',original_sha256=sha(paths['lesion']),expected_sha256=meta['source_sha256']['lesion'])
            folder=OUT/'masks'/name;folder.mkdir(parents=True)
            dest=folder/'pancreatic_lesion.nii.gz'
            header=original.header.copy();header.set_data_dtype(np.uint8);header.set_slope_inter(1,0)
            new=nib.Nifti1Image(fixed,original.affine,header)
            for form in ('qform','sform'):
                affine,code=getattr(original,'get_'+form)(coded=True)
                getattr(new,'set_'+form)(affine,int(code))
            nib.save(new,dest);reopened=nib.load(dest)
            assert reopened.shape==original.shape and np.array_equal(reopened.affine,original.affine)
            assert not np.asarray(reopened.dataobj).any()
            for form in ('qform','sform'):
                a,c=getattr(original,'get_'+form)(coded=True);b,d=getattr(reopened,'get_'+form)(coded=True)
                assert c==d and (a is None and b is None or np.array_equal(a,b))
            sl=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
            # Rebuild from the pancreas mask, never turn combined class2 into0:
            # an erroneous lesion could have overwritten legitimate pancreas voxels.
            target=np.ascontiguousarray(orient(decoded['pancreas'],meta['parent_geometry'])[sl])
            cover=coverage_bank(target>0,meta['record']);parts,positive=components(target,meta['record'])
            assert not positive and len(cover)<=focused[name] and int(target.sum())==meta['pancreas_source_voxels']
            for visit in range(focused[name]):
                origin,trace=choose(meta['record'],cover,parts,step=0,focused_visit=visit,total=focused[name],seed=42,name=name)
                if trace['kind']=='component_jitter':
                    anchor=tuple(np.asarray(trace['anchor'])//np.asarray(meta['record']['factors']))
                    assert target[anchor]==1
            row=dict(case_id=name,role='train',action='replace_lesion_with_zero_keep_case_and_pancreas',
                original_path=str(paths['lesion']),original_sha256=meta['source_sha256']['lesion'],corrected_path=str(dest),corrected_sha256=sha(dest),
                original_voxels=count,corrected_voxels=0,pancreas_sha256=meta['source_sha256']['pancreas'],
                old_coverage_windows=len(meta['cover']),new_coverage_windows=len(cover),
                old_focus_components=len(meta['parts']),new_focus_components=len(parts),
                focused_visits=focused[name],total_visits=exposure[name],source_geometry_preserved=True)
            write(folder/'sampling.json',dict(record=meta['record'],cover=cover,parts=parts,positive=False,lesion_voxels=0,
                region_low=meta['region_low'],region_high=meta['region_high'],scope='corrected label-only metadata, not admitted training cache'))
            for role,p in paths.items():assert sha(p)==meta['source_sha256'][role]
            rows.append(row);print(name,'corrected, reopened, geometry and sampling checks passed',flush=True)
        counts=dict(train_total=len(train),train_positive_before=sum(members[n]['positive'] for n in train),
                    train_positive_after=sum(members[n]['positive'] for n in train)-len(rows),
                    development_total=len(dev),development_positive_unchanged=sum(manifest[n]['target_state']=='positive' for n in dev))
        write(OUT/'overlay.json',dict(version=VERSION,source=SOURCE,provenance='local_derivative_from_maintainer_erratum_not_new_upstream_release',
            cases=rows,counts=counts,membership_unchanged=True,originals_preserved=True,
            old_caches_valid_for_corrected_training=False,scientific_launch_authorized=False,
            integration='explicit future loader/cache binding required; no frozen loader changed'))
    # Reassess fixed pilot without rerunning models or removing the corrected case.
    pilot=json.loads((BASE/'patient-pilot-02/result.json').read_text())
    print('pilot keys',list(pilot['cases'][0]),flush=True)
    write(OUT/'pilot-reassessment-input.json',dict(pilot_result_sha256=sha(BASE/'patient-pilot-02/result.json'),
        corrected_case='PanTS_00003059',case_remains_in_pilot=True,new_status='annotation_negative',
        original_scores_preserved=True,teacher_accepted=False))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();OUT.mkdir(exist_ok=False)
        original=json.loads((BASE/'patient-pilot-02/request.json').read_text());pins=dict(original['pins'])
        for p in [Path(__file__).resolve(),ROOT/'src/data/pants_errata_v1.py']:pins[str(p)]=sha(p)
        write(OUT/'request.json',dict(pins=pins,version=VERSION,seconds=600,rss_bytes=12*1024**3,
            ct_reads=0,model_runs=0,training_updates=0))
        ok=run([sys.executable,__file__,'--worker'],OUT,seconds=600,rss_bytes=12*1024**3,
            env={**os.environ,'PROWL_ERRATA':'1','OMP_NUM_THREADS':'2'})
        raise SystemExit(0 if ok else 1)
