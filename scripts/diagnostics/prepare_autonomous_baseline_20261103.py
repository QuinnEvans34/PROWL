"""Metadata-only70-case request and admission inspection; no extraction/inference."""
import argparse,csv,json,math,statistics,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import evaluate_four_case_exception_20261102 as prior
from scripts.acquisition.restore_remaining_cts_20261030 import CACHE
from src.data.segmenter_native_windows_v1 import geometry,tiles
from src.data.segmenter_physical_windows_v1 import physical_geometry
from src.data.localizer_preprocessing_v4 import plan_geometry
q=prior.q
OUT=Path('E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a01')
RUN=Path('E:/PROWL/artifacts/week05-autonomous70-20261103-a01')
SOURCES=Path('E:/PROWL/sources/pants/week05-autonomous70-20261103-a01')

def prepare():
    if OUT.exists():raise FileExistsError('Preparation already exists')
    q.resource_gate();old=prior.request('f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd')
    identities=json.loads((q.BUNDLE/'development-identities.json').read_text());cp=json.loads((q.BUNDLE/'control-provenance.json').read_text());review=json.loads((q.BUNDLE/'checkpoint-review.json').read_text())
    control=cp['raw_identity']['control'];names=control['validation'];ids={c['case_id']:c for c in identities['cases']}
    if len(names)!=70 or len(set(names))!=70 or set(names)!=set(ids) or set(names)&set(control['train']):raise ValueError('Role mismatch')
    loc_train=set().union(*(set(x['train_ids']) for x in review['localizer_lineage']));loc_dev=set().union(*(set(x['development_ids']) for x in review['localizer_lineage']))
    source_control=json.loads((CACHE/'control.json').read_text());rows={}
    with prior.MANIFEST.open(newline='') as f:rows={v['case_id']:v for v in csv.DictReader(f) if v['case_id'] in names}
    available={c['case_id']:c['files']['ct'] for c in old['cases']};available['PanTS_00001070']='E:/PROWL/sources/pants/week05-diagnostic-20261102-a01/PanTS_00001070.nii.gz'
    reuse={n:dict(root=str(prior.BASE/n/'autonomous'),request_sha256='f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd',kind='four-case-autonomous') for n in prior.CASES}
    reuse['PanTS_00001070']=dict(root=str(q.BASE/'output'),request_sha256=prior.QUAL,kind='matched-diagnostic-native-output')
    for item in reuse.values():
        item['result_sha256']=q.sha(Path(item['root'])/'result.json')
        item['input_access_sha256']=q.sha(Path(item['root'])/'input-access.json')
    cases=[];pins=dict(old['pins']);unresolved=[]
    for name in names:
        p=CACHE/(name+'.json');meta=json.loads(p.read_text())
        if q.sha(p)!=ids[name]['metadata_sha256'] or meta['source_sha256']!=ids[name]['source_sha256']:raise ValueError('Retained metadata differs')
        t=meta['transform'];g=physical_geometry(geometry(t['source_shape'],t['source_affine']));count=len(tiles(g['shape']))
        plan_geometry(t['source_shape'],t['source_affine'],old['localizer_recipe'])
        if math.prod(t['source_shape'])>96000000 or count>512:unresolved.append(dict(case_id=name,reason='allocation_or_tile_cap'))
        if ids[name]['localizer_training_overlap']!=(name in loc_train) or ids[name]['localizer_development_overlap']!=(name in loc_dev):raise ValueError('Exposure audit differs')
        if name in available and not Path(available[name]).is_file():raise ValueError('Known restored source disappeared')
        audit=dict(role='exposed_development',segmenter_optimizer_overlap=name in control['train'],segmenter_checkpoint_selection_overlap=True,
            localizer_optimizer_overlap=name in loc_train,localizer_selection_overlap=name in loc_dev,
            teacher_patient_membership='unknown',suprem_pretraining_membership='unknown',biological_patient_independence='unverified',control_kd_max_weight=cp['distillation_identity']['loss']['max_weight'])
        cases.append(dict(case_id=name,files=dict(ct=available.get(name,str(SOURCES/(name+'.nii.gz'))),pancreas=rows[name]['pancreas_path'],lesion=rows[name]['lesion_path']),identity=ids[name],
            expected_native=dict(shape=t['source_shape'],affine=t['source_affine'],units_required='mm',source='retained verified metadata; fresh restored header admission still required'),
            expected_ct_bytes=source_control['observations'][name]['ct']['bytes'],full_ct_tiles=count,exposure=audit,needs_restoration=name not in available,reuse=reuse.get(name)))
        pins[str(p)]=q.sha(p)
    observed=[];score_rates=[];native_fraction=[]
    for name in prior.CASES:
        res=json.loads((prior.BASE/name/'autonomous/result.json').read_text());resources=json.loads((prior.BASE/(name+'-autonomous-score.resources.json')).read_text())
        observed.append(res['seconds']/res['evidence']['reconstruction']['tiles']);score_rates.append(resources['seconds']/math.prod(res['source_shape']))
        native_fraction.append(math.prod(res['evidence']['geometry']['shape'])/math.prod(res['source_shape']))
    new=[c for c in cases if c['reuse'] is None];new_tiles=sum(c['full_ct_tiles'] for c in new);native=sum(math.prod(c['expected_native']['shape']) for c in cases)
    inventory=json.loads((ROOT/'docs/capstone/data/acquisition-2026-09-19.json').read_text());archives=[]
    for item in inventory['pants']['files']:
        if item['kind']!='training_archive':continue
        lo,hi=map(int,item['name'].removesuffix('.tar.gz').split('_')[-2:])
        if any(c['needs_restoration'] and lo<=int(c['case_id'].split('_')[-1])<=hi for c in cases):archives.append(item)
    archive_bytes=sum(x['bytes'] for x in archives);missing=sum(c['expected_ct_bytes'] for c in cases if c['needs_restoration'])
    estimates=dict(missing_cts=sum(c['needs_restoration'] for c in cases),reuse_predictions=len(reuse),new_inference=len(new),missing_ct_bytes=missing,
        all_ct_bytes=sum(c['expected_ct_bytes'] for c in cases),archive_scan_bytes_upper=archive_bytes,archive_count=len(archives),
        restore_seconds_range=[archive_bytes/(110*1024**2),archive_bytes/(60*1024**2)],
        full_ct_tiles=sum(c['full_ct_tiles'] for c in cases),new_full_ct_tiles=new_tiles,
        inference_seconds_range=[new_tiles*statistics.mean(native_fraction)*statistics.median(observed),new_tiles*max(observed)+len(new)*15],
        scoring_seconds_range=[native*min(score_rates),native*max(score_rates)],
        backup_seconds_range=[native*14*2/(100*1024**2),native*14*3/(50*1024**2)],
        raw_full_native_probability_bytes=native*12,raw_native_prediction_and_localizer_bytes=native*2,
        measured_per_tile_seconds=observed,measured_native_region_fractions=native_fraction,
        caveat='Four-case empirical projection, not guarantee; raw full-volume output upper bound; separate phase estimates do not double count training')
    limits=dict(seconds_per_worker=600,total_evaluation_seconds=42000,rss_bytes=12*1024**3,gpu_bytes=6*1024**3,output_bytes=32*1024**3,backup_bytes=32*1024**3,
        combined_backup_bytes=64*1024**3,minimum_free_bytes=100*1024**3,source_voxels=96000000,region_voxels=96000000,max_tiles=512,
        restore_seconds=7200,restore_rss_bytes=2*1024**3,restore_output_bytes=3*1024**3)
    current=q.tree_bytes('C:/Users/quinn/PROWL-Backups')
    if native*14+128*1024**2>limits['output_bytes']:unresolved.append(dict(reason='output_projection_over_cap'))
    if current+limits['backup_bytes']>limits['combined_backup_bytes']:unresolved.append(dict(reason='proposed_aggregate_backup_cap_insufficient'))
    for d,additional in [('C:/',limits['backup_bytes']),('E:/',limits['output_bytes']+limits['restore_output_bytes'])]:
        if shutil.disk_usage(d).free-additional<limits['minimum_free_bytes']:unresolved.append(dict(reason='projected_free_floor',volume=d))
    files=[Path(__file__),ROOT/'scripts/diagnostics/execute_autonomous_baseline_20261103.py',ROOT/'tests/test_week05_baseline_preparation_20261103.py',q.BUNDLE/'development-identities.json',q.BUNDLE/'control-provenance.json',q.BUNDLE/'checkpoint-review.json',CACHE/'control.json',ROOT/'docs/capstone/data/acquisition-2026-09-19.json']
    for p in files:pins[str(p)]=q.sha(p)
    request=dict(version='autonomous70-prepared-request-1',status='PREPARED_REQUIRES_NEW_SCOPE_AND_RESOURCE_ADMISSION',cases=cases,arms=['autonomous'],
        models=old['models'],localizer_recipe=old['localizer_recipe'],environment=q.environment(),pins=pins,limits=limits,estimates=estimates,
        probability_equivalence='UNQUALIFIED',prior_exception_scope='four-case-only; NOT applicable to this request',
        existing_comparison_sha256='a37a953820a55637530d30f883394fe4717d444fdebfbfd043cd8f54f5e93ab5',
        output=str(RUN),backup='C:/Users/quinn/PROWL-Backups/week05-autonomous70-20261103-a01',
        role_counts=dict(total=70,segmenter_train_overlap=0,segmenter_selection_overlap=70,localizer_train_overlap=len(set(names)&loc_train),localizer_selection_overlap=len(set(names)&loc_dev),teacher_membership_unknown=70,suprem_membership_unknown=70),
        unresolved_preflight=unresolved,current_combined_backup_bytes=current,
        admission_required=['Explicit extend numerical exception to exactly70 exposed-development cases, autonomous only','Approve proposed32GiB output/32GiB independent backup and64GiB combined backup cap (current cap40GiB is insufficient)','Approve bounded65-CT restoration plan and full failure denominator','Complete post-restoration exact identity/header admission and freeze its receipt'],
        recovery_policy='No automatic retry/resume. Preserve failure and all completed artifacts. Any later continuation needs a new receipt, reuses exact completed artifacts, subtracts elapsed budget, never drops failed/pending cohort members.',
        score_policy='Separate CPU process; existing native metrics/26-connected any-overlap components/contour conventions; empty-reference Dice undefined; report every failure/pending case; no model-quality acceptance claim')
    OUT.mkdir();q.write(OUT/'request.json',request);print(json.dumps(dict(request_sha256=q.sha(OUT/'request.json'),role_counts=request['role_counts'],estimates=estimates,unresolved_preflight=unresolved,admission_required=request['admission_required'])))

def inspect(pin):
    if q.sha(OUT/'request.json')!=pin:raise ValueError('Prepared request hash mismatch')
    r=json.loads((OUT/'request.json').read_text())
    for p,h in r['pins'].items():
        if q.sha(p)!=h:raise ValueError('Prepared pin changed: '+p)
    print(json.dumps(dict(status=r['status'],scope=len(r['cases']),admission_required=r['admission_required'],unresolved_preflight=r['unresolved_preflight'],launch_performed=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--inspect-sha256');a=p.parse_args()
    if a.prepare:prepare()
    else:inspect(a.inspect_sha256)
