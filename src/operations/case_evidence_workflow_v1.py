"""Invented, CPU-only case/evidence smoke adapters. Never performs scientific inference."""
import gzip
import hashlib
import json
from pathlib import Path

from .workflow_plan_v1 import Stage, encoded, sha
from src.review.store import ReviewStore, FILES, digest
from src.retrieval.evidence_spans import catalog, resolve

NATIVE_NAMES={'manifest.json',*FILES.values()}
PASSAGE='This is an invented research passage for workflow testing, not medical guidance.'


def native_fixture():
    import nibabel as nib
    import numpy as np
    files={}
    for key,name in [('ct','ct.nii.gz'),('pred','prediction.nii.gz')]:
        values=np.zeros((4,4,4),dtype=np.uint8)
        if key=='pred': values[1:3,1:3,1:3]=1
        image=nib.Nifti1Image(values,np.eye(4));image.header.set_xyzt_units('mm')
        files[name]=gzip.compress(image.to_bytes(),mtime=0)
    files['result.json']=encoded({'status':'synthetic','scientific_result':False})
    files['evidence.json']=encoded({'scope':'invented fixture only','model_called':False})
    refs={key:dict(uri=name,bytes=len(files[name]),content_sha256=digest(files[name])) for key,name in FILES.items()}
    m=dict(schema_version='saved-prediction-view-v2',case_id='invented_workflow_case',status='completed',
           prediction_mode='autonomous',reference_inputs_used=False,
           model_sha256={'localizer':'a'*64,'segmenter':'b'*64},
           geometry={'units':'mm','shape':[4,4,4],'affine':np.eye(4).tolist()},
           ct_window=[-100,300],labels={'0':'background','1':'pancreas','2':'lesion'},
           warnings=['Invented test fixture; never a scientific prediction.'],files=refs,
           result_sha256=refs['result']['content_sha256'],inference_evidence_sha256=refs['evidence']['content_sha256'])
    files['manifest.json']=encoded(m)
    return files


class MemoryPackage(ReviewStore):
    """Use the existing review manifest validator without a store or HTTP side effects."""
    def __init__(self,files): self.files=files
    def reader(self,source):
        def read(name,cap):
            data=self.files[name]
            if not 0<len(data)<=cap:raise ValueError('Package member exceeds cap')
            return data
        return read


def validate_native(files):
    if set(files)!=NATIVE_NAMES:raise ValueError('Native member inventory differs')
    _,m,identity=MemoryPackage(files).manifest('saved')
    for key,name in FILES.items():
        ref=m['files'][key]
        if ref['bytes']!=len(files[name]) or ref['content_sha256']!=digest(files[name]):
            raise ValueError('Native file identity differs')
    # Decode only tiny invented bytes; no real scan or model access.
    import nibabel as nib
    import numpy as np
    for key in ('ct','pred'):
        image=nib.Nifti1Image.from_bytes(gzip.decompress(files[FILES[key]]))
        if list(image.shape)!=m['geometry']['shape'] or not np.array_equal(image.affine,m['geometry']['affine']):
            raise ValueError('Native geometry differs')
        if key=='pred' and not set(np.unique(image.get_fdata()))<=set((0,1,2)):
            raise ValueError('Invalid synthetic labels')
    return {'manifest_sha256':identity,'scope':'synthetic-native-package'}


def evidence_fixture():
    passages=[{'record':{'passage':{'passage_id':'invented-source'},'text':PASSAGE}}]
    _,spans=catalog(passages)
    selection={'status':'excerpts','span_ids':[next(iter(spans))]}
    return {'literature.json':encoded(dict(passages=passages,selection=selection,
                                          answer=resolve(selection,spans)))}


def validate_evidence(files):
    if set(files)!={'literature.json'}:raise ValueError('Evidence inventory differs')
    data=json.loads(files['literature.json'])
    _,spans=catalog(data['passages'])
    if data['answer']!=resolve(data['selection'],spans):
        raise ValueError('Citation/quotation differs from source')
    return {'evidence_sha256':digest(files['literature.json']),'scope':'synthetic-exact-quotation'}


def validate_bundle(files):
    if set(files)!=NATIVE_NAMES|{'literature.json','bundle.json'}:raise ValueError('Bundle inventory differs')
    native=validate_native({n:files[n] for n in NATIVE_NAMES})
    literature=validate_evidence({'literature.json':files['literature.json']})
    expected=dict(schema='synthetic-case-evidence-bundle-v1',native=native,literature=literature,
                  review_decision=None)
    if json.loads(files['bundle.json'])!=expected:raise ValueError('Bundle binding differs')
    return expected


def definition(*, evidence_version=1):
    # Own validators and persistence contracts are part of producer identity.
    repo=Path(__file__).resolve().parents[2]
    paths=[Path(__file__),repo/'src/operations/workflow_plan_v1.py',
           repo/'src/operations/workflow_execution_v1.py',repo/'src/operations/artifact_store.py',
           repo/'src/review/store.py',repo/'src/retrieval/evidence_spans.py']
    producer=sha({str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    stages=[Stage('native',producer=producer),
            Stage('evidence',('native',),inputs={'invented_passage':digest(PASSAGE.encode())},
                  config={'version':evidence_version},producer=producer),
            Stage('bundle',('native','evidence'),producer=producer)]
    def assemble(parents,config):
        files={**parents['native'],**parents['evidence']}
        files['bundle.json']=encoded(dict(schema='synthetic-case-evidence-bundle-v1',
            native=validate_native(parents['native']),literature=validate_evidence(parents['evidence']),
            review_decision=None))
        return files
    handlers={'native':lambda p,c:native_fixture(),'evidence':lambda p,c:evidence_fixture(),'bundle':assemble}
    validators={'native':validate_native,'evidence':validate_evidence,'bundle':validate_bundle}
    return stages,handlers,validators
