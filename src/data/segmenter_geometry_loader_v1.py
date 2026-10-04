"""Registered D-320 resolution and exact bounded triple reads; no global source activation."""
import json
import os
import numpy as np
from scripts.diagnostics import freeze_segmenter_cohort as frozen
from scripts.diagnostics import segmenter_source_verification as source
from src.data import segmenter_content_v1 as content
from src.data.manifest_records_v3 import manifest_validation_session
from src.data.manifest_records import digest
from src.data.source_inventory_records import content_hash,require
from src.data.segmenter_cohort_bundle_v1 import resolve
from src.operations.segmenter_cohort_storage import segmenter_store

COMPLETION='73e7e034f16c4a42e9f08e8318eb834bd654a400377274fba13521a1bd2587ed'
CODES='03f0d1e4e91039c5315b77f8486facfa0d5790a858bc686ef432aaa4ecaaaab3'
CAPABILITY='0b89b9a97aaa5faf22687be716c27c90e7e799ddea57bab331a2a42a43d713b2'
DESCRIPTORS='cd52c55577c93b08b67ecfbb2ed6a76288b35d31d26004b8bf31bb8e1cf49481'
_TOKEN=object()


class ResolvedInputs:
    def __init__(self,records,token):
        require(token is _TOKEN,'A replayed registered cohort is required')
        self.records=records

    def select(self,study_id,operation):
        return checked_descriptor(self.records,DESCRIPTORS,study_id,operation)


def resolve_registered():
    cap=frozen.CAP.read_bytes()
    store=segmenter_store(frozen.REPO/'configs/local/roots.yaml',cap,
        trusted_capability_sha256=CAPABILITY,artifact_id=frozen.BUNDLE_ID,
        provider_capability=frozen.PROVIDER.read_bytes(),trusted_provider_sha256=frozen.PROVIDER_PIN)
    with manifest_validation_session():
        files,receipt=store.resolve(frozen.BUNDLE_ID,receipt_sha256=COMPLETION,
            validate=lambda f:frozen.validate(f,CODES,CAPABILITY))
        d=json.loads(files['purpose-derived.json']);bases={k:v.encode() for k,v in json.loads(files['purpose-inputs.json'])['membership'].items()}
        _,rows=resolve(d,bases,json.loads(files['cohorts.json']),frozen.EXPECTED)
        require(content_hash(rows)==DESCRIPTORS==receipt['validation']['descriptor_sha256'],'Independent resolved descriptor pin differs')
    return ResolvedInputs(rows,_TOKEN)


def checked_descriptor(records,descriptor_pin,study_id,operation):
    require(content_hash(records)==descriptor_pin,'Descriptor records changed')
    require(operation in ('optimizer','evaluator'),'Explicit optimizer/evaluator operation required')
    selected=[r for r in records[operation] if r['study_id']==study_id]
    require(len(selected)==1,'Member absent from qualified matching-role cohort')
    d=selected[0];role={'optimizer':'train','evaluator':'validation'}[operation]
    require(d['operation']==operation and d['protected_role']==role and d['lesion_target_state'] in ('positive','verified_negative') and
        d['purpose']=='pancreas_lesion_segmenter_'+('training' if role=='train' else 'validation') and
        d['roi_source']=='pancreas_only' and d['class_precedence']=='lesion_over_pancreas','Descriptor role/target contract differs')
    return d


def check_rows(descriptor,rows):
    require(len(rows)==3 and {r['kind'] for r in rows}=={'ct','pancreas','lesion'} and
        len({r['uri'] for r in rows})==3,'Exact three-input scope required')
    for r in rows:
        ref=descriptor['image' if r['kind']=='ct' else r['kind']]
        source.member_name(r['uri'])
        require(r['study_id']==descriptor['study_id'] and r['protected_role']==descriptor['protected_role'] and
            ref['root_alias']=='followup_source' and ref['uri']==r['uri'] and ref['bytes']==r['compressed_bytes']==r['observation']['bytes'] and
            ref['content_sha256']==r['sha256'] and r['geometry']==descriptor['geometry'],'Source triple differs from qualified descriptors')


def read_triple(rootfd,descriptor,rows,counts,limits,tick=lambda:None):
    """Low-level verified-file primitive; production entry is read_case below."""
    check_rows(descriptor,rows);arrays={};headers={}
    for key,field in [('hash_bytes','compressed_bytes'),('decode_bytes','compressed_bytes'),('expanded_bytes','expanded_bytes')]:
        content.reserve(counts,key,sum(r[field] for r in rows),limits)
    for row in rows:
        tick()
        with source.source_stream(rootfd,row) as stream:
            content.hash_exact(stream,row,counts,limits,tick)
            stream.seek(0);array,header,_=content.decode_exact(stream,row,counts,limits,tick)
        arrays[row['kind']]=array;headers[row['kind']]=header
    g=descriptor['geometry'];a=np.asarray(g['affine_ras']).reshape(4,4)
    require(all(list(v.shape)==g['shape_xyz'] for v in arrays.values()) and
        all(np.allclose(h['affine'],a,rtol=0,atol=1e-5) for h in headers.values()),'Native triple geometry differs')
    ct=arrays['ct'].astype(np.float32)*headers['ct']['slope']+headers['ct']['intercept'];require(np.isfinite(ct).all(),'Nonfinite semantic CT')
    pancreas,pdecode=content.target_content(arrays['pancreas'],headers['pancreas'],tick)
    lesion,ldecode=content.target_content(arrays['lesion'],headers['lesion'],tick)
    require(pancreas.any(),'Qualified pancreas reference became empty')
    require(bool(lesion.any())==(descriptor['lesion_target_state']=='positive'),'Qualified lesion semantics changed')
    return ct,pancreas,lesion,a,dict(pancreas_decode=pdecode,lesion_decode=ldecode,headers=headers)


def read_case(session,request,*,trusted_request_sha256,study_id,operation,rootfd,counts,
              approved_request_sha256=None,tick=lambda:None):
    require(type(session) is ResolvedInputs,'Bare manifest/descriptors cannot authorize source reads')
    require(digest(source.encoded(request))==trusted_request_sha256 and request['cohort_completion_sha256']==COMPLETION and
        request['descriptor_sha256']==DESCRIPTORS,'Independent read request/lineage differs')
    require(approved_request_sha256==trusted_request_sha256 and request['stage']=='segmenter_geometry_fidelity' and
        request['capability']['operations']==['full_compressed_hash','full_gzip_decode_native_arrays'] and
        request['capability']['source_writes'] is False and request['capability']['global_activation'] is False,
        'Prepared or wrong-stage capability lacks exact read approval')
    descriptor=session.select(study_id,operation)
    cases=request['cases'];require(len(cases)==7 and len(set(cases))==7 and study_id in cases,'Exact seven-case requested membership required')
    expected={sid for v in frozen.EXPECTED.values() for sid in v}
    require(set(cases)==expected and len(request['files'])==21 and
        {(r['study_id'],r['kind']) for r in request['files']}=={(sid,k) for sid in expected for k in ('ct','pancreas','lesion')},
        'Missing/extra requested triples')
    rows=[r for r in request['files'] if r['study_id']==study_id]
    # Verify the held/open directory really corresponds to the approved source mount/root.
    mount=source.mount_guard(request['capability']);s=os.fstat(rootfd)
    require((s.st_dev,s.st_ino)==(mount['root_device'],mount['root_inode']),'Source descriptor does not name approved root')
    return read_triple(rootfd,descriptor,rows,counts,request['limits'],tick)
