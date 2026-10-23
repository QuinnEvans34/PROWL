"""Readiness evidence aggregation. Does not launch training or alter sources."""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_native_intake import OUT,provider,verify,read_journal
from scripts.diagnostics.qualify_native_windows_cuda import checked,BACKUP
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
KIND='native'
COHORT='cohort-complete'


def configure(kind):
    global OUT,provider,verify,BACKUP,KIND,COHORT
    KIND=kind
    if kind=='physical':
        from scripts.diagnostics import qualify_physical_intake as physical
        from scripts.diagnostics import qualify_native_windows_cuda as cuda
        cuda.configure(kind)
        OUT,provider,verify=physical.OUT,physical.provider,physical.verify
        BACKUP=cuda.BACKUP;COHORT='cohort'


def main():
    verify();cuda_request=checked();p=provider()
    if KIND=='native':
        amendment=json.loads((OUT/'parser-amendment.json').read_text())
        if amendment['reused_pilot_sha256']!=sha256(OUT/'pilot/cases.jsonl'):raise ValueError('Reused pilot changed')
    parent=Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01/ready.json')
    old_pins=json.loads(parent.read_text())['file_sha256']
    if any(not Path(path).is_file() or sha256(path)!=h for path,h in old_pins.items()):
        raise ValueError('Scientific baseline producing file changed')
    if (OUT/'ready.json').exists(): raise ValueError('Immutable receipt already exists')
    cases=read_journal(OUT/COHORT/'cases.jsonl')
    if len(cases)!=1403 or len({r['case_id'] for r in cases})!=1403: raise ValueError('Incomplete/duplicate accounting')
    for role,names in [('train',p.control['train']),('validation',p.control['validation'])]:
        if {r['case_id'] for r in cases if r['role']==role}!=set(names): raise ValueError('Role/accounting mismatch')
    if sum(r['positive'] for r in cases if r['role']=='train')!=671: raise ValueError('Training positive count')
    if sum(r['positive'] for r in cases if r['role']=='validation')!=36: raise ValueError('Development positive count')
    excluded={'PanTS_00000922','PanTS_00005105','PanTS_00005370','PanTS_00007299','PanTS_00007523'}
    if excluded.intersection(p.control['train']+p.control['validation']): raise ValueError('Excluded case admitted')
    for r in cases:
        if not (r['exact_target_roundtrip'] and r['boundary_voxels_unchanged'] and r['all_anchors_exposed']
                and r['new_field_coverage']==1 and r['annotated_field_exposure_18_visits']==1):
            raise ValueError('Unresolved quality failure')
        if KIND=='physical' and (min(r['factors'])<1 or max(r['spacing_mm'])>1.00001):raise ValueError('Physical spacing/downsampling failure')
    # Recheck all source observations after the complete read pass. No CT rehash or duplicate audit.
    for name in p.control['train']+p.control['validation']:
        for kind in ('ct','pancreas','lesion'):
            s=Path(p.rows[name][kind+'_path']).stat()
            if dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)!=p.observations[name][kind]:
                raise ValueError('Source changed during qualification')
    producer=json.loads((OUT/'cuda/producer.json').read_text());cold=json.loads((OUT/'cuda/cold.json').read_text())
    if len(producer['updates'])!=4 or len(cold['updates'])!=1 or not all(cold[k] for k in ('exact_restore','next_update_close','exact_input_view')):
        raise ValueError('CUDA qualification incomplete')
    if [r['step'] for r in producer['updates']]!=[1,2,3,4] or cold['updates'][0]['step']!=4:
        raise ValueError('Wrong qualification update accounting')
    if len(producer['evaluations'])!=2 or {r['case_id'] for r in producer['evaluations']}!={r['case_id'] for r in cuda_request['native_cases']}:
        raise ValueError('Native stress cases incomplete')
    if sha256(BACKUP/'saved.pt')!=sha256(OUT/'cuda/saved.pt') or producer['backup_sha256']!=sha256(BACKUP/'saved.pt'):
        raise ValueError('Independent checkpoint changed')
    if any(e['reconstruction']['gap_voxels']!=0 or e['reconstruction']['minimum_blend_weight']<=0 for e in producer['evaluations']):
        raise ValueError('Native inference gap')
    resources={}
    for stage,path in [('pilot',OUT/'pilot/resources.json'),('cohort',OUT/COHORT/'resources.json'),
                       ('producer',OUT/'cuda/producer-resources.json'),('cold',OUT/'cuda/cold-resources.json')]:
        r=json.loads(path.read_text())
        if not r['workers_reaped'] or r['peak_owned_rss_bytes']>12*1024**3:raise ValueError('Resources or workers unresolved')
        resources[stage]=r
    for r in (producer,cold):
        if r['peak_reserved_bytes']>8*1024**3:raise ValueError('GPU memory bound')
    suites=[]
    filenames=('windows-regression-tests.xml','physical-guard-tests.xml') if KIND=='physical' else ('windows-regression-tests.xml','continuation-tests-repaired.xml')
    for filename in filenames:
        suites.extend(ET.parse(OUT/filename).getroot().findall('testsuite'))
    tests={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','errors','failures','skipped')}
    if tests['errors'] or tests['failures']:raise ValueError('Regression tests failed')
    pilot=read_journal(OUT/'pilot/cases.jsonl')
    requested_pilot=set(json.loads((OUT/'request.json').read_text())['pilot'])
    if len(pilot)!=12 or {r['case_id'] for r in pilot}!=requested_pilot:
        raise ValueError('Pilot membership incomplete')
    if KIND=='physical' and not all(r['oracle_reconstruction_exact'] is True for r in pilot):
        raise ValueError('Physical pilot full tiled oracle incomplete')
    if not json.loads((OUT/'pilot/visual-review.json').read_text())['reviewed_all_12']:
        raise ValueError('Pilot visual review incomplete')
    prior={r['case_id']:r for r in read_journal('E:/PROWL/readiness/input-fidelity-20261018-a01/cases.jsonl')}
    comparisons=[dict(case_id=r['case_id'],old_field_coverage=prior[r['case_id']]['crop_coverage'],
        old_target_roundtrip_dice=prior[r['case_id']]['lesion']['dice'],old_target_recall=prior[r['case_id']]['lesion']['recall'],
        new_field_coverage=r['new_field_coverage'],new_target_roundtrip_dice=r['roundtrip_dice'],new_target_recall=r['roundtrip_recall']) for r in pilot]
    tile_counts=np.array([r['full_field_tile_count'] for r in cases]);spacing=np.array([r['spacing_mm'] for r in cases])
    summary=dict(status='INTAKE_VERIFIED_REVIEW_REQUIRED',scientific_launch_authorized=False,input_kind=KIND,
        input_policy=p.control['policy'],
        train_cases=1333,development_cases=70,train_positive_cases=671,development_positive_cases=36,
        field_coverage_min=1.,annotated_field_training_exposure_min=1.,positive_target_roundtrip_dice_min=1.,
        all_native_targets_exact=True,clinical_annotation_adjudication=False,new_exclusions=0,test_reads=0,
        baseline_producing_files_unchanged=len(old_pins),
        annotated_lesion_voxels_preserved=sum(r['lesion_voxels'] for r in cases),
        lesion_components_preserved=sum(r['components'] for r in cases),
        maximum_guaranteed_cover_windows=max(r['guaranteed_cover_windows'] for r in cases if r['role']=='train'),
        comparisons=comparisons,tests=tests,resources=resources,
        legacy_test_collection='test_segmenter_content.py imports Unix resource; unsupported on Windows; retained in regression-tests.xml',
        native_tiles=dict(min=int(tile_counts.min()),median=float(np.median(tile_counts)),max=int(tile_counts.max()),
                          development_total=sum(r['full_field_tile_count'] for r in cases if r['role']=='validation')),
        input_spacing_mm=dict(min=spacing.min(0).tolist(),median=np.median(spacing,axis=0).tolist(),max=spacing.max(0).tolist()),
        cuda=dict(exact_restore=True,exact_input_view=True,next_update_max_absolute_difference=cold['max_absolute_difference'],
                  peak_allocated_bytes=max(producer['peak_allocated_bytes'],cold['peak_allocated_bytes']),
                  peak_reserved_bytes=max(producer['peak_reserved_bytes'],cold['peak_reserved_bytes']),
                  optimizer_updates=4,cold_updates=1,nonpromotable=True,
                  update_seconds=[r['seconds'] for r in producer['updates']],
                  inference=[dict(seconds=e['seconds'],tiles=e['reconstruction']['tiles']) for e in producer['evaluations']]),
        scientific_run_pending=['Review physical spacing, context and full-CT inference tradeoffs',
                                'Approve frozen scientific run budget and production launch integration'])
    if KIND=='physical':
        from scripts.diagnostics.qualify_physical_intake import BASE
        summary['reused_native_source_audit']=dict(path=str(BASE/'cohort-complete'),cases=1403,
            resources=json.loads((BASE/'cohort-complete/resources.json').read_text()))
        summary['cohort_verification_method']='Reused native CT-content audit with unchanged source observations; all labels and physical mappings rechecked; actual coverage-window target roundtrips for every case; full tiled oracle on 12 pilot cases'
    with (OUT/'summary.json').open('xb') as f:f.write(canonical(summary))
    evidence=[x for x in OUT.rglob('*') if x.is_file() and x.suffix in ('.json','.jsonl','.xml','.png') and x.name!='ready.json']
    producing=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    producing+=list((ROOT/'tests').glob('test_segmenter_native*.py'))+list((ROOT/'tests').glob('test_native_intake*.py'))+list((ROOT/'tests').glob('test_segmenter_physical*.py'))
    producing+=list((ROOT/'tests').glob('test_physical_intake*.py'))
    receipt=dict(status=summary['status'],scientific_launch_authorized=False,control_sha256=p.pin,
        summary_sha256=sha256(OUT/'summary.json'),file_sha256={str(x):sha256(x) for x in producing+evidence},
        checkpoint_sha256={str(x):sha256(x) for x in (OUT/'cuda/saved.pt',OUT/'cuda/expected.pt',BACKUP/'saved.pt')},
        backup_sha256=sha256(BACKUP/'saved.pt'),original_sources_unchanged_at_final_check=True)
    with (OUT/'ready.json').open('xb') as f:f.write(canonical(receipt))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['native','physical'],default='native');a=ap.parse_args()
    configure(a.kind);main()
