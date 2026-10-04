"""D-326 bounded byte-only checkpoint inventory; tensor-cache payloads excluded."""
import argparse,json,os,resource,signal,time
from pathlib import Path
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from scripts.diagnostics import segmenter_source_verification as source,segmenter_content_pilot as prior
REPO=source.REPO;DEST=REPO/'outputs/prowl/SEGMENTER-CHECKPOINT-INVENTORY-20261002'
LIMITS=dict(seconds=600,rss_bytes=256*1024**2,hash_bytes=9*1024**3,output_bytes=8*1024**2,max_files=256)


def category(name):
    p=source.member_name(name);require(p.suffix in ('.pt','.pth','.ckpt'),'Not a model-like filename')
    if name.startswith('outputs/cache/'):return 'excluded_tensor_cache_payload'
    if name.startswith('outputs/checkpoints/'):return 'prior_project_checkpoint_import_denied'
    if name.startswith('outputs/prowl/'):return 'capstone_diagnostic_checkpoint_import_denied'
    if name in ('pretrained_weights/supervised_suprem_segresnet_2100.pth','MedFormerPanTS/pants_pancreas_release/fold_0_latest.pth'):return 'third_party_weights_not_approved_for_this_run'
    raise ValueError('Unknown checkpoint scope')


def validate_request(r):
    require(set(r)=={'decision','stage','limits','files','excluded_cache_count','code_sha256'} and r['decision']=='D-326' and r['stage']=='checkpoint_byte_inventory' and r['limits']==LIMITS,'Wrong inventory request')
    require(0<len(r['files'])<=LIMITS['max_files'] and len({v['uri'] for v in r['files']})==len(r['files']),'Checkpoint inventory duplicates/cap')
    require(sum(v['observation']['bytes'] for v in r['files'])<=LIMITS['hash_bytes'],'Inventory read cap')
    for v in r['files']:require(v['category']==category(v['uri']) and v['category']!='excluded_tensor_cache_payload','Tensor cache payload forbidden')


def prepare(stats):
    allrows=json.loads(Path(stats).read_bytes());rows=[]
    with source.directory(REPO) as fd:
        for x in sorted(allrows,key=lambda x:x['path']):
            cat=category(x['path'])
            if cat=='excluded_tensor_cache_payload':continue
            obs=source.observe(fd,dict(uri=x['path'],expected_bytes=x['bytes']));require(obs['state']=='observed','Checkpoint stat hold')
            rows.append(dict(uri=x['path'],category=cat,observation=obs['observation']))
    r=dict(decision='D-326',stage='checkpoint_byte_inventory',limits=LIMITS,files=rows,excluded_cache_count=sum(category(x['path'])=='excluded_tensor_cache_payload' for x in allrows),code_sha256=digest(Path(__file__).read_bytes()));validate_request(r)
    DEST.mkdir();(DEST/'request.json').open('xb').write(canonical(r));print(digest(canonical(r)))


def run(pin):
    raw=(DEST/'request.json').read_bytes();require(digest(raw)==pin,'Inventory request changed');r=json.loads(raw);validate_request(r);require(r['code_sha256']==digest(Path(__file__).read_bytes()),'Inventory producer changed');source.put(DEST/'consumed.json',dict(request_sha256=pin));start=time.monotonic();signal.alarm(LIMITS['seconds']);counts={'hash_bytes':0};records=[]
    def tick():require(time.monotonic()-start<LIMITS['seconds'] and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=LIMITS['rss_bytes'],'Inventory resources');prior.check_output(DEST,LIMITS['output_bytes'])
    try:
        with source.directory(REPO) as fd:
            for row in r['files']:
                tick()
                with source.source_stream(fd,row) as stream:
                    h=source.hash_stream(stream,row['observation']['bytes'],counts,tick);require(stream.read(1)==b'','Checkpoint trailing bytes')
                records.append(dict(**row,sha256=h,bytes=row['observation']['bytes'],weight_import_allowed=False))
        require(counts['hash_bytes']==sum(v['bytes'] for v in records),'Incomplete inventory accounting')
        result=dict(state='complete_byte_inventory_no_model_decode',decision='D-326',request_sha256=pin,files=records,counts=counts,excluded_cache_count=r['excluded_cache_count'],coverage='Known repository outputs/checkpoints, outputs/prowl and exact two retained third-party weight paths; no whole-computer completeness claim',model_deserializations=0,source_arrays_read=0,model_forwards=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        source.put(DEST/'result.json',result);print(prior.package(DEST))
    except BaseException as e:source.put(DEST/'failure.json',dict(state='consumed_incomplete',error=str(e),counts=counts,completed_files=records));raise
    finally:signal.alarm(0)

if __name__=='__main__':
    a=argparse.ArgumentParser();g=a.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');a.add_argument('--stats');a.add_argument('--request-sha256');v=a.parse_args()
    if v.prepare:prepare(v.stats)
    else:run(v.request_sha256)
