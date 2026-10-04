"""D-321 metadata scope, synthetic resource qualification and one exact CPU fidelity job."""
import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import signal
import shutil
import sys
import time
import nibabel as nib
import numpy as np
from scripts.diagnostics import segmenter_source_verification as source
from scripts.diagnostics import segmenter_content_pilot as prior
from src.data import segmenter_geometry_v1 as geometry
from src.data import segmenter_geometry_loader_v1 as loader
from src.data.segmenter_native_views_v2 import render_native
from src.data.source_inventory_records import content_hash,require

REPO=source.REPO
SCOPE=REPO/'outputs/prowl/SEGMENTER-GEOMETRY-SCOPE-attempt02-20261001'
PROFILE=REPO/'outputs/prowl/SEGMENTER-GEOMETRY-REHEARSAL-attempt02-20261001'
DEST=REPO/'outputs/prowl/SEGMENTER-GEOMETRY-FIDELITY-attempt02-20261001'
BOX='outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-REVIEW-20261001/retained-box-check.json'
BOX_PIN='00d6222a92896d0dbfffc3b40a84966bd61551ce6424ac3362281e0e96431092'
RECIPE=geometry.recipe()
SCREEN=dict(minimum_lesion_native_recall=.90,minimum_component_native_recall=.90,
    minimum_union_native_recall=.95,landmark_error_mm=1e-5,all_components_survive=True)
CODE=['src/data/segmenter_geometry_v1.py','src/data/segmenter_geometry_loader_v1.py',
    'scripts/diagnostics/segmenter_geometry_qualification.py','src/data/segmenter_native_views_v2.py',
    'tests/test_segmenter_geometry.py','tests/test_segmenter_geometry_loader.py',
    'tests/test_segmenter_geometry_qualification.py']


def pins():return loader.frozen.code_pins()|{n:source.sha((REPO/n).read_bytes()) for n in CODE}
def runtime():return prior.runtime()


def scope_from_records(records):
    require(content_hash(records)==loader.DESCRIPTORS,'Independent descriptor pin differs')
    full=json.loads(source.safe_local(prior.PROPOSAL,prior.PROPOSAL_PIN))
    m2=source.verify_package(prior.M2,prior.M2_PIN)
    boxes=json.loads(source.safe_local(BOX,BOX_PIN));boxes={b['study_id']:b for b in boxes['cases']}
    rows=[];projections=[];cases=[]
    verified={r['uri']:r for r in m2['files']}
    for operation in ('optimizer','evaluator'):
        for d in records[operation]:
            sid=d['study_id'];loader.checked_descriptor(records,loader.DESCRIPTORS,sid,operation)
            selected=[r for r in full['files'] if r['study_id']==sid];group=[]
            for r in selected:
                old=verified[r['uri']]
                require(old['state']=='verified' and all(r[k]==old[k] for k in ('study_id','protected_role','kind','uri','sha256','observation')),'M2/source proposal differs')
                group.append(r|dict(geometry=old['retained_ct_geometry']))
            loader.check_rows(d,group);rows.extend(group);cases.append(sid)
            b=boxes[sid];require(b['pancreas_source_sha256']==d['pancreas']['content_sha256'] and b['protected_role']==d['protected_role'],'Retained pancreas bounds differ')
            a=np.asarray(d['geometry']['affine_ras']).reshape(4,4)
            _,_,shape,_,_,spacing=geometry.canonical_geometry(d['geometry']['shape_xyz'],a,RECIPE)
            lower=np.asarray([v[0] for v in b['canonical_pancreas_bounds']]);upper=np.asarray([v[1]+1 for v in b['canonical_pancreas_bounds']])
            pad=np.ceil(RECIPE['margin_mm']/spacing).astype(int)
            box=[np.maximum(0,lower-pad).tolist(),np.minimum(shape,upper+pad).tolist()]
            record=geometry.plan_geometry(d['geometry']['shape_xyz'],a,box,RECIPE,
                source_identity=dict(study_id=sid,ct_sha256=d['image']['content_sha256']),roi_origin='provided_pancreas_reference')
            projections.append(dict(study_id=sid,operation=operation,pancreas_bounds=b['canonical_pancreas_bounds'],transform=record,
                transform_sha256=content_hash(record),projection_only=True))
    require(len(cases)==7 and len(set(cases))==7 and len(rows)==21,'Seven-case fixed scope differs')
    capability=json.loads((prior.M2/'request.json').read_bytes())['capability']|dict(
        operations=['full_compressed_hash','full_gzip_decode_native_arrays'])
    return dict(state='metadata_scope_verified',component='segmenter-geometry-scope-v1',decision='D-321',
        cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,records=records,
        cases=cases,files=rows,projections=projections,capability=capability,recipe=RECIPE,recipe_sha256=content_hash(RECIPE),
        screen=SCREEN,m2_sha256=prior.M2_PIN,proposal_sha256=prior.PROPOSAL_PIN,box_sha256=BOX_PIN,
        code_pins=pins(),runtime=runtime(),source_arrays_read=0,model_updates=0,
        largest_native_voxels=max(math.prod(p['transform']['source_shape']) for p in projections),
        largest_sampling_voxels=max(math.prod(p['transform']['sampling_shape']) for p in projections))


def capture_scope():
    start=time.monotonic();signal.alarm(1800);initial=pins();env=runtime()
    session=loader.resolve_registered();result=scope_from_records(session.records)
    require(pins()==initial and runtime()==env,'Metadata source/runtime changed')
    require(prior.rss()<=2*1024**3,'Metadata RSS limit')
    SCOPE.mkdir();source.put(SCOPE/'result.json',result)
    print(json.dumps(dict(scope_receipt_sha256=prior.package(SCOPE),cases=result['cases'],files=len(result['files']),
        largest_native_voxels=result['largest_native_voxels'],largest_sampling_voxels=result['largest_sampling_voxels'],
        seconds=time.monotonic()-start,peak_rss_bytes=prior.rss())));signal.alarm(0)


def checked_scope(pin):
    r=source.verify_package(SCOPE,pin)
    require(r==scope_from_records(r['records']),'Metadata scope changed');return r


def probability_check(out,tick):
    onehot=np.stack([out['target']==c for c in range(3)]).astype(np.float32)
    p=geometry.restore_probabilities(onehot,out['transform'],trusted_record_sha256=out['transform_sha256'],tick=tick)
    mask=p.argmax(axis=0).astype(np.uint8)
    result=dict(shape=list(p.shape),dtype=p.dtype.str,source_affine=out['transform']['source_affine'],
        probability_sha256=hashlib.sha256(memoryview(p).cast('B')).hexdigest(),
        argmax_sha256=hashlib.sha256(memoryview(mask).cast('B')).hexdigest(),
        source_grid_exact=True,classes=[0,1,2],sum_tolerance=1e-4,scope='one_hot_reference_inverse_probe_no_model')
    del p,onehot;gc.collect();return mask,result


def landmark_check(record):
    # Analytic world relation, independent of the forward/inverse interpolation implementation.
    a=np.asarray(record['source_affine']);ta=np.asarray(record['tensor_affine']);lo=np.asarray(record['pad_low']);step=record['effective_spacing_mm'][0]
    edge=np.asarray(record['roi_world_low_edge_mm']);error=0.
    for point in ([0,0,0],np.array(record['source_shape'])-1,(np.array(record['source_shape'])-1)/2):
        world=(a@np.r_[point,1])[:3];tensor=(world-edge)/step-.5+lo
        restored=(ta@np.r_[tensor,1])[:3];error=max(error,float(np.max(np.abs(restored-world))))
    require(error<=SCREEN['landmark_error_mm'],'Analytic landmark mismatch');return error


def screen(fidelity,probability_mask,pan,les,landmark_error):
    n=int(les.sum());tp=int(((probability_mask==2)&(les==1)).sum());prob_recall=tp/n if n else None
    passed=(fidelity['mechanical_survival_pass'] and fidelity['metrics']['lesion']['recall'] is not None and
        fidelity['metrics']['lesion']['recall']>=SCREEN['minimum_lesion_native_recall'] and
        all(c['roundtrip_recall']>=SCREEN['minimum_component_native_recall'] for c in fidelity['components']) and
        fidelity['metrics']['pancreas_lesion_union']['recall']>=SCREEN['minimum_union_native_recall'] and
        prob_recall is not None and prob_recall>=SCREEN['minimum_lesion_native_recall'] and landmark_error<=SCREEN['landmark_error_mm'])
    return dict(passed=bool(passed),reference_probability_argmax_lesion_recall=prob_recall,
        thresholds=SCREEN,decision_scope='recipe_screen_not_member_eligibility_or_model_performance')


def synthetic_arrays(projection,pattern):
    t=projection['transform'];shape=t['canonical_shape'];p=np.zeros(shape,np.uint8);bounds=projection['pancreas_bounds']
    slices=tuple(slice(lo,hi+1) for lo,hi in bounds);p[slices]=1;l=np.zeros(shape,np.uint8)
    if pattern=='dense':l[slices]=1
    elif pattern=='fragmented':l[::64,::64,::32]=1
    elif pattern=='boundary':l[:,0,:]=1
    elif pattern=='tiny':
        center=[(lo+hi)//2 for lo,hi in bounds];l[center[0]:center[0]+2,center[1]:center[1]+3,center[2]]=1
    inverse=np.asarray(t['orientation_inverse'])
    p=nib.orientations.apply_orientation(p,inverse);l=nib.orientations.apply_orientation(l,inverse)
    return np.zeros(p.shape,np.float32),p,l,np.asarray(t['source_affine'])


def profile_worker(scope_pin):
    scope=checked_scope(scope_pin);start=time.monotonic();initial=pins();env=runtime();results=[]
    def tick():
        if time.monotonic()-start>900 or prior.rss()>8*1024**3:raise prior.core.BudgetError('Synthetic time/RSS ceiling')
    signal.alarm(900)
    # Each actual source/header/crop projection is exercised on invented voxels; largest also covers special patterns.
    largest=max(scope['projections'],key=lambda p:math.prod(p['transform']['source_shape']))
    jobs=[(p,'tiny') for p in scope['projections']]+[(largest,k) for k in ('dense','empty','fragmented','boundary')]
    for index,(projection,pattern) in enumerate(jobs):
        ct,pan,les,a=synthetic_arrays(projection,pattern);tick()
        out=geometry.preprocess(ct,pan,les,a,RECIPE,source_identity=projection['transform']['source_identity'],
            lesion_target_state='verified_negative' if pattern=='empty' else 'positive',tick=tick)
        require(out['transform']==projection['transform'],'Synthetic header/crop replay differs')
        mask,probe=probability_check(out,tick);error=landmark_check(out['transform'])
        require(sum(c['native_voxels'] for c in out['fidelity']['components'])==int(les.sum()),'Synthetic component accounting lost members')
        result=dict(index=index,projection_study_id=projection['study_id'],pattern=pattern,fidelity=out['fidelity'],
            evidence_domain='synthetic',source_data='invented_arrays_on_retained_header_projection',real_qualifications_granted=False,
            transform_sha256=out['transform_sha256'],probability_probe=probe,landmark_error_mm=error)
        source.put(PROFILE/(f'fixture-{index:02}.json'),result);results.append(result)
        if pattern in ('dense','boundary'):
            comps=prior.core.component_content(les,pan,a,tick)
            png,views=render_native(ct,pan,les,a,'Invented geometry '+pattern,comps['components'],tick)
            prior.check_output(PROFILE,64*1024**2,len(png));prior.write_bytes(PROFILE/(f'fixture-{index:02}.png'),png)
            source.put(PROFILE/(f'fixture-{index:02}-views.json'),views)
        del ct,pan,les,out,mask;gc.collect();tick()
    require(initial==pins() and env==runtime(),'Synthetic code/runtime changed')
    source.put(PROFILE/'result.json',dict(state='passed',component='segmenter-geometry-profile-v1',scope_receipt_sha256=scope_pin,
        code_pins=initial,runtime=env,recipe=RECIPE,results=results,geometry_recipe_accepted=False,
        seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_arrays_read=0,model_updates=0));signal.alarm(0)


def profile(scope_pin):
    checked_scope(scope_pin);PROFILE.mkdir();source.put(PROFILE/'started.json',dict(decision='D-321',scope_receipt_sha256=scope_pin,code_pins=pins(),runtime=runtime()))
    try:
        report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_geometry_qualification','--profile-worker','--scope-sha256',scope_pin],900,8*1024**3,PROFILE/'worker.log')
        source.put(PROFILE/'supervision.json',report);prior.check_output(PROFILE,64*1024**2,4096)
        print(json.dumps(dict(profile_receipt_sha256=prior.package(PROFILE),supervision=report,result=json.loads((PROFILE/'result.json').read_bytes()))))
    except BaseException as e:source.put(PROFILE/'failure.json',dict(state='incomplete',error=str(e)));raise


def build_request(scope_pin,profile_pin):
    scope=checked_scope(scope_pin);profile=source.verify_package(PROFILE,profile_pin)
    require(profile['state']=='passed' and profile['scope_receipt_sha256']==scope_pin and profile['code_pins']==pins() and profile['runtime']==runtime(),
        'Synthetic profile/input/code/runtime changed')
    require(len(profile['results'])==11 and profile['source_arrays_read']==profile['model_updates']==0,'Synthetic coverage differs')
    files=scope['files'];compressed=sum(r['compressed_bytes'] for r in files);expanded=sum(r['expanded_bytes'] for r in files)
    return dict(component='segmenter-geometry-request-v1',stage='segmenter_geometry_fidelity',decision='D-321',
        scope_receipt_sha256=scope_pin,profile_receipt_sha256=profile_pin,cohort_completion_sha256=loader.COMPLETION,
        descriptor_sha256=loader.DESCRIPTORS,cases=scope['cases'],files=files,projections=scope['projections'],
        capability=scope['capability'],recipe=RECIPE,recipe_sha256=content_hash(RECIPE),screen=SCREEN,
        limits=dict(hash_bytes=compressed,decode_bytes=compressed,expanded_bytes=expanded,seconds=1800,rss_bytes=8*1024**3,output_bytes=64*1024**2),
        code_pins=pins(),runtime=runtime(),output=str(DEST),workers=0,serial=True,model_updates_allowed=False,
        qualifications_granted=False,geometry_recipe_accepted=False,candidate_substitution=False,
        reference_reads='same_native_arrays_in_memory_no_additional_source_pass',validation_scope='one_positive_engineering_reference_no_performance_claim')


def checked_request(pin):
    require(DEST.resolve(strict=True)==DEST,'Unsafe output root')
    raw=(DEST/'request.json').read_bytes();require(source.sha(raw)==pin,'Independent exact request pin differs')
    r=json.loads(raw);require(r==build_request(r['scope_receipt_sha256'],r['profile_receipt_sha256']),'Request source/runtime/scope changed');return r


def prepare(scope_pin,profile_pin):
    request=build_request(scope_pin,profile_pin);DEST.mkdir();source.put(DEST/'request.json',request)
    print(json.dumps(dict(request_sha256=source.sha((DEST/'request.json').read_bytes()),cases=request['cases'],limits=request['limits'],code_sha256=content_hash(request['code_pins']))))


def worker(pin):
    req=checked_request(pin);start=time.monotonic();counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);results=[]
    def tick():
        if time.monotonic()-start>req['limits']['seconds'] or prior.rss()>req['limits']['rss_bytes']:raise prior.core.BudgetError('Real geometry time/RSS ceiling')
        prior.check_output(DEST,req['limits']['output_bytes'])
    signal.alarm(req['limits']['seconds']);session=loader.resolve_registered();tick()
    before=source.mount_guard(req['capability'])
    try:
        with source.directory(req['capability']['source_root']) as rootfd:
            for projection in req['projections']:
                sid=projection['study_id'];stem=sid.split(':')[-1];op=projection['operation'];d=session.select(sid,op)
                source.put(DEST/(stem+'-read-reservation.json'),dict(request_sha256=pin,study_id=sid,counts_before=counts.copy(),
                    possible_remaining_reads={k:req['limits'][k]-counts[k] for k in counts}))
                ct,pan,les,a,decoded=loader.read_case(session,req,trusted_request_sha256=pin,approved_request_sha256=pin,
                    study_id=sid,operation=op,rootfd=rootfd,counts=counts,tick=tick)
                out=geometry.preprocess(ct,pan,les,a,RECIPE,source_identity=dict(study_id=sid,ct_sha256=d['image']['content_sha256']),
                    lesion_target_state=d['lesion_target_state'],tick=tick)
                require(out['transform']==projection['transform'],'Real native box/geometry differs from pinned projection')
                mask,probability=probability_check(out,tick);error=landmark_check(out['transform'])
                verdict=screen(out['fidelity'],mask,pan,les,error)
                native_components=prior.core.component_content(les,pan,a,tick)
                png,views=render_native(ct,pan & (les==0),les,a,stem+' native class1/2 reference',native_components['components'],tick)
                prior.check_output(DEST,req['limits']['output_bytes'],len(png));prior.write_bytes(DEST/(stem+'-native.png'),png)
                back=out['reference_roundtrip'];back_components=prior.core.component_content(back==2,back==1,a,tick)
                png2,views2=render_native(ct,(back==1).astype(np.uint8),(back==2).astype(np.uint8),a,stem+' nearest reference round-trip',back_components['components'],tick)
                prior.check_output(DEST,req['limits']['output_bytes'],len(png2));prior.write_bytes(DEST/(stem+'-roundtrip.png'),png2)
                result=dict(study_id=sid,operation=op,protected_role=d['protected_role'],transform=out['transform'],
                    transform_sha256=out['transform_sha256'],fidelity=out['fidelity'],probability_probe=probability,
                    analytic_landmark_error_mm=error,screen=verdict,decoding=decoded,views=dict(native=views,roundtrip=views2),
                    source_counts_after=counts.copy(),source_arrays_changed=False,model_updates=0)
                source.put(DEST/(stem+'.json'),result);results.append(result)
                print(json.dumps(dict(case=stem,screen=verdict,lesion=out['fidelity']['metrics']['lesion'])),flush=True)
                del ct,pan,les,out,mask,png,png2,back;gc.collect();tick()
        after=source.mount_guard(req['capability']);require(before==after,'Source root/mount changed')
        require(counts=={k:req['limits'][k] for k in counts} and len(results)==7,'Incomplete exact source/geometry accounting')
        source.put(DEST/'result.json',dict(state='geometry_evidence_complete_not_recipe_acceptance',request_sha256=pin,cases=results,
            counts=counts,mount_before=before,mount_after=after,screen_pass_count=sum(r['screen']['passed'] for r in results),
            all_requested_accounted=True,source_arrays_read=21,model_updates=0,qualifications_granted=False,
            seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),visual_review='pending'))
    except BaseException as e:source.put(DEST/'worker-failure.json',dict(state='incomplete_consumed',error=str(e),counts=counts,completed_cases=len(results)));raise
    finally:signal.alarm(0)


def run(pin):
    req=checked_request(pin);source.put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry',decision='D-321'))
    try:
        report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_geometry_qualification','--worker','--request-sha256',pin],
            req['limits']['seconds'],req['limits']['rss_bytes'],DEST/'worker.log')
        result=json.loads((DEST/'result.json').read_bytes());require(result['request_sha256']==pin and len(result['cases'])==7,'Incomplete geometry ledger')
        checked_request(pin);source.put(DEST/'supervision.json',report);prior.check_output(DEST,req['limits']['output_bytes'],4096)
        print(json.dumps(dict(receipt_sha256=prior.package(DEST),counts=result['counts'],screen_pass_count=result['screen_pass_count'],
            seconds=result['seconds'],peak_rss_bytes=result['peak_rss_bytes'],supervision=report)))
    except BaseException as e:source.put(DEST/'failure.json',dict(state='incomplete_consumed',error=str(e),partial_counts='See per-case reservations and worker records; killed reads have upper bounds'));raise


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for name in ('scope','profile','profile-worker','prepare','worker','run','verify'):g.add_argument('--'+name,action='store_true')
    p.add_argument('--scope-sha256');p.add_argument('--profile-sha256');p.add_argument('--request-sha256');p.add_argument('--receipt-sha256');args=p.parse_args()
    require(shutil.disk_usage(REPO).free>=100*1024**3,'Internal disk reserve')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Geometry diagnostic deadline')))
    if args.scope:capture_scope()
    elif args.profile:profile(args.scope_sha256)
    elif args.profile_worker:profile_worker(args.scope_sha256)
    elif args.prepare:prepare(args.scope_sha256,args.profile_sha256)
    elif args.worker:
        require((DEST/'consumed.json').is_file() and json.loads((DEST/'consumed.json').read_bytes())['request_sha256']==args.request_sha256,'Worker requires exact consumed launch record')
        worker(args.request_sha256)
    elif args.run:run(args.request_sha256)
    else:
        result=source.verify_package(DEST,args.receipt_sha256);checked_request(args.request_sha256)
        require(result['request_sha256']==args.request_sha256 and len(result['cases'])==7,'Fresh verification scope differs')
        print(json.dumps(dict(state='verified',counts=result['counts'],cases=7,model_updates=0)))


if __name__=='__main__':main()
