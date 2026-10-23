"""Lossless training-target cache and one-window lookahead; unchanged inference.

Only deterministic targets/metadata are cached, never a resized CT or a random
training view. The cache is built from bound train labels, with no CT data reads.
The original RegionInputs reader remains the validation implementation.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib

from src.data.manifest_records import canonical,digest
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.data.segmenter_pancreas_region_v1 import crop_case,bank,POLICY as REGION_POLICY
from src.data.segmenter_varied_region_v1 import VariedInputs,components
from src.training.experiment_config import sha256

POLICY=dict(version='equivalent-varied-target-cache-prefetch-1',
    cache='lossless_native_region_uint8_targets_and_source_bound_metadata',
    image='original_float32_CT_then_lossless_region_then_identical_HU_window',
    lookahead=1,inference='unchanged_region_v1',sampling='unchanged_varied_region_v1')


def source_info(provider,name,role,operation,*,objects=False):
    provider.check_role(name,role,operation)
    meta_path=provider.root/(name+'.json')
    pin=provider.review['prepared_cache']['members'][name]['metadata_sha256']
    if sha256(meta_path)!=pin:raise ValueError('Original metadata changed')
    meta=json.loads(meta_path.read_text());result={}
    for kind in ('ct','pancreas','lesion'):
        path=Path(provider.rows[name][kind+'_path']);s=path.stat()
        observed=dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
        if observed!=provider.observations[name][kind]:raise ValueError('Source observation changed')
        if kind!='ct' and sha256(path)!=meta['source_sha256'][kind]:raise ValueError('Label identity changed')
        if objects:result[kind]=nib.load(path)
    return meta,pin,result


def label_case(provider,name):
    """One derived-target conversion; CT header only, no CT voxel access."""
    meta,pin,objects=source_info(provider,name,'train','optimizer',objects=True)
    ct=objects['ct'];r=geometry(ct.shape,ct.affine)
    if np.prod(ct.shape,dtype=np.int64)>256000000:raise ValueError('Source voxel cap')
    if ct.shape!=tuple(meta['transform']['source_shape']) or not np.allclose(
        ct.affine,meta['transform']['source_affine'],atol=1e-5,rtol=0):raise ValueError('Original geometry changed')
    masks={}
    for kind in ('pancreas','lesion'):
        obj=objects[kind]
        if obj.shape!=ct.shape or not np.allclose(obj.affine,ct.affine,atol=1e-5,rtol=0):
            raise ValueError('Label geometry changed')
        proxy=obj.dataobj
        masks[kind],_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
    positive=provider.review['target_states'][name]=='positive'
    if bool(masks['lesion'].any())!=positive or not masks['pancreas'].any():raise ValueError('Target state changed')
    target=orient(masks['pancreas'],r).astype(np.uint8)
    target[orient(masks['lesion'],r)!=0]=2
    case=crop_case(dict(name=name,target=target,geometry=r,positive=positive,
        original_pancreas=masks['pancreas'],source_sha256=meta['source_sha256'],metadata_sha256=pin))
    record,cover=bank(case);parts,part_positive=components(case['target'],record)
    if part_positive!=positive:raise ValueError('Component state changed')
    small={k:case[k] for k in ('name','geometry','positive','region_low','region_high','parent_geometry',
        'source_sha256','metadata_sha256')}
    small.update(record=record,cover=[list(o) for o in cover],parts=parts,
        lesion_voxels=int((case['target']==2).sum()),pancreas_source_voxels=int(masks['pancreas'].sum()))
    return np.ascontiguousarray(case['target']),small


def save_target(root,name,target,metadata):
    root=Path(root)
    if target.dtype!=np.uint8 or target.shape!=tuple(metadata['geometry']['shape']) or not np.isin(target,[0,1,2]).all():
        raise ValueError('Invalid target cache')
    # Exclusive creation. A partial/failed member is retained and never reused as complete.
    array=root/(name+'.npz');meta=root/(name+'.json')
    with array.open('xb') as f:np.savez_compressed(f,target=target)
    with meta.open('xb') as f:f.write(canonical(metadata))
    return dict(target_sha256=sha256(array),metadata_sha256=sha256(meta),bytes=array.stat().st_size+meta.stat().st_size)


def normalize_region(full_image,parent,low,high):
    if full_image.dtype!=np.float32 or not np.isfinite(full_image).all():raise ValueError('Nonfinite or wrong CT')
    image=orient(full_image,parent)
    image=np.ascontiguousarray(image[tuple(slice(l,h) for l,h in zip(low,high))]).copy()
    np.clip(image,-100,250,out=image);image+=100;image/=350
    return image


class FastVariedInputs(VariedInputs):
    def __init__(self,*,target_cache,cache_manifest_sha256,prefetch=True,manifest_name='manifest.json',qualification_only=False,**kwargs):
        super().__init__(**kwargs)
        # Match the frozen varied provider's explicit source-vs-final policy names.
        self.control['source_loader_policy']=self.control.pop('policy')
        self.control['policy']=deepcopy(REGION_POLICY)
        self.pin=digest(canonical(self.control))
        if manifest_name not in ('manifest.json','pilot-manifest.json'):raise ValueError('Unsupported cache manifest')
        self.target_cache=Path(target_cache);manifest=self.target_cache/manifest_name
        if sha256(manifest)!=cache_manifest_sha256:raise ValueError('Target cache manifest changed')
        self.cache_manifest=json.loads(manifest.read_text())
        members=set(self.cache_manifest['members']);train=set(self.control['train'])
        if not members or not members<=train:raise ValueError('Target cache train roles changed')
        if not qualification_only and (members!=train or not self.cache_manifest['complete']):
            raise ValueError('Complete target cache required for science')
        if self.cache_manifest['source_control_sha256']!=self.pin:raise ValueError('Cache source control changed')
        self.control=deepcopy(self.control)
        self.control['throughput']=dict(POLICY,manifest_sha256=cache_manifest_sha256)
        if qualification_only:self.control['qualification_only']=True
        self.pin=digest(canonical(self.control))
        self._executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='prowl-input') if prefetch else None
        self._future=None;self._future_key=None;self._next=None;self._closed=False

    def cache_member(self,name):
        member=self.cache_manifest['members'][name]
        array=self.target_cache/(name+'.npz');meta=self.target_cache/(name+'.json')
        if sha256(array)!=member['target_sha256'] or sha256(meta)!=member['metadata_sha256']:
            raise ValueError('Target cache member changed')
        return array,json.loads(meta.read_text())

    def load(self,name,*,role,operation='audit'):
        if role!='train':
            self.wait_pending()
            return super().load(name,role=role,operation=operation)
        meta,pin,_=source_info(self,name,role,operation)
        array,small=self.cache_member(name)
        if small['metadata_sha256']!=pin or small['source_sha256']!=meta['source_sha256']:
            raise ValueError('Target cache provenance changed')
        with np.load(array,allow_pickle=False) as data:
            if data.files!=['target']:raise ValueError('Unexpected cache payload')
            target=np.ascontiguousarray(data['target'])
        if target.dtype!=np.uint8 or target.shape!=tuple(small['geometry']['shape']) or not np.isin(target,[0,1,2]).all():
            raise ValueError('Invalid cached target')
        ct=nib.load(self.rows[name]['ct_path']);parent=small['parent_geometry']
        if ct.shape!=tuple(parent['source_shape']) or not np.allclose(ct.affine,parent['source_affine'],atol=1e-5,rtol=0):
            raise ValueError('Cached source geometry changed')
        image=normalize_region(ct.get_fdata(dtype=np.float32,caching='unchanged'),parent,small['region_low'],small['region_high'])
        case={k:v for k,v in small.items() if k not in ('record','cover','parts')}
        case.update(image=image,target=target)
        key=digest(canonical(dict(source=case['source_sha256'],low=case['region_low'],high=case['region_high'],record=small['record'])))
        self.component_cache[name]=(key,small['parts'],small['positive'])
        return case

    @staticmethod
    def key(name,step,focused_visit,seed):return (name,step,focused_visit,seed)

    def plan_next(self,request):
        if self._closed:raise ValueError('Input provider closed')
        self._next=request

    def _produce(self,key):
        name,step,visit,seed=key
        return super().training_window(name,step=step,focused_visit=visit,seed=seed)

    def training_window(self,name,*,step,focused_visit,seed):
        if self._closed:raise ValueError('Input provider closed')
        key=self.key(name,step,focused_visit,seed)
        if self._future is not None:
            if key!=self._future_key:raise ValueError('Prefetch order/counters changed')
            value=self._future.result();self._future=None;self._future_key=None
            source_info(self,name,'train','optimizer');self.cache_member(name)
        else:value=self._produce(key)
        request=self._next;self._next=None
        if request is not None and self._executor is not None:
            self._future_key=request;self._future=self._executor.submit(self._produce,request)
        return value

    def wait_pending(self):
        if self._future is not None:self._future.result()

    def close(self):
        if not self._closed:
            try:self.wait_pending()
            finally:
                if self._executor:self._executor.shutdown(wait=True,cancel_futures=True)
                self._future=None;self._future_key=None;self._next=None;self._closed=True
