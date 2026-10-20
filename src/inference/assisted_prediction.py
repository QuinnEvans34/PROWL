"""Independent pancreas-assisted inference; no training session or lesion reference."""
from itertools import product
import math
from pathlib import Path
import shutil
import numpy as np
import nibabel as nib
from .assisted_windows import geometry, orient, physical_geometry, tiles, sample_window, PhysicalReconstructor
from .on_demand import canonical, sha

ARCH = dict(in_channels=1, out_channels=3, init_filters=16, norm='group', num_groups=8,
            blocks_down=[1,2,2,4], blocks_up=[1,1,1], dropout_prob=0)
RECIPE = dict(version='assisted-on-demand-v1', base_margin_mm=10, extra_margin_mm=[81,43,71],
              hu_window=[-100,250], window=144, stride=72, maximum_tiles=256,
              orientation='closest_RAS_lossless_not_deoblique', precision='float32_tf32_disabled',
              reconstruction='native_center_positive_triangular_blend', ties='lower_label',
              outside_region='background')


def recipe_sha():
    import hashlib
    return hashlib.sha256(canonical(RECIPE)).hexdigest()


def source_box(pancreas, affine):
    if not np.isin(pancreas,[0,1]).all() or not pancreas.any():
        raise ValueError('Nonempty binary supplied pancreas required')
    plane = 1/np.linalg.norm(np.linalg.inv(np.asarray(affine)[:3,:3]),axis=1)
    base = np.ceil(RECIPE['base_margin_mm']/plane).astype(int)
    extra = np.ceil(np.asarray(RECIPE['extra_margin_mm'])/plane).astype(int)
    lo=[];hi=[]
    for axis,n in enumerate(pancreas.shape):
        support=np.flatnonzero(pancreas.any(axis=tuple(k for k in range(3) if k!=axis)))
        lo.append(max(0,max(0,int(support[0])-int(base[axis]))-int(extra[axis])))
        hi.append(min(n,min(n,int(support[-1])+1+int(base[axis]))+int(extra[axis])))
    return np.asarray(lo),np.asarray(hi)


def predict_array(image, pancreas, affine, probabilities, *, window=144, stride=72, max_tiles=256):
    """Callback consumes normalized float32 cubes and returns three probabilities.

    Small window overrides exist only for analytic tests; the production worker
    uses the pinned 144/72 recipe. No target lesion array enters this function.
    """
    if image.dtype != np.float32 or image.shape != pancreas.shape or not np.isfinite(image).all():
        raise ValueError('Invalid aligned CT/assistance')
    native=geometry(image.shape,affine)
    lo,hi=source_box(pancreas,affine)
    inverse=nib.orientations.inv_ornt_aff(np.asarray(native['forward']),pancreas.shape)
    corners=np.asarray([list(p)+[1] for p in product(*zip(lo,hi-1))])
    points=(np.linalg.inv(inverse)@corners.T).T[:,:3]
    if not np.allclose(points,np.rint(points)):raise ValueError('Nonintegral orientation')
    points=np.rint(points).astype(int);low=points.min(0);high=points.max(0)+1
    image=orient(image,native).copy()
    np.clip(image,-100,250,out=image);image+=100;image/=350
    slices=tuple(slice(int(l),int(h)) for l,h in zip(low,high))
    local_affine=np.asarray(native['affine']).copy();local_affine[:3,3]=(local_affine@[*low,1])[:3]
    local=geometry((high-low).tolist(),local_affine)
    if local['forward'] != [[0.,1.],[1.,1.],[2.,1.]]:raise ValueError('Unexpected local orientation')
    cropped=np.ascontiguousarray(image[slices]);record=physical_geometry(local)
    # Count before materializing tile origins, avoiding a huge list on pathological spacing.
    if not 1 <= stride <= window:raise ValueError('Invalid stride')
    count=math.prod((max(0,int(n)-window)//stride+1+int(max(0,int(n)-window)%stride!=0)) for n in record['shape'])
    if count>max_tiles:raise ValueError('Inference tile budget exceeded')
    ts=tiles(record['shape'],window,stride);recon=PhysicalReconstructor(record,window=window)
    for origin in ts:
        patch,_=sample_window(cropped,record,origin,order=1,window=window)
        recon.add(origin,probabilities(patch))
    probs=recon.finish(ts)
    codes=np.zeros(cropped.shape,np.uint8);best=probs[0].copy()
    for k in (1,2):
        take=probs[k]>best;codes[take]=k;best[take]=probs[k][take]
    full=np.zeros(native['shape'],np.uint8);full[slices]=codes
    return np.ascontiguousarray(orient(full,native,inverse=True)),dict(
        native_box=[lo.tolist(),hi.tolist()], region_low=low.tolist(),region_high=high.tolist(),
        tiles=len(ts),minimum_blend_weight=float(recon.weight.min()),
        uncovered_region_voxels=int((recon.weight==0).sum()),outside_region='background')


def checked_images(ct_path, pancreas_path):
    objects=[]
    for path in (ct_path,pancreas_path):
        if Path(path).stat().st_size>64*1024**2:raise ValueError('Compressed input budget exceeded')
        obj=nib.load(path)
        if (len(obj.shape)!=3 or math.prod(obj.shape)>32000000
                or math.prod(obj.shape)*max(4,obj.header.get_data_dtype().itemsize)+352>128*1024**2
                or obj.header.get_xyzt_units()[0]!='mm'
                or not np.allclose(obj.affine[3],[0,0,0,1],atol=1e-8,rtol=0)):
            raise ValueError('Unsupported native geometry/units or input budget')
        geometry(obj.shape,obj.affine)
        objects.append(obj)
    ct,pancreas=objects
    if ct.shape!=pancreas.shape or not np.allclose(ct.affine,pancreas.affine,atol=1e-5,rtol=0):
        raise ValueError('Supplied region is not aligned with CT')
    image=ct.get_fdata(dtype=np.float32,caching='unchanged')
    mask=pancreas.get_fdata(dtype=np.float32,caching='unchanged')
    if not np.isfinite(image).all() or not np.isin(mask,[0,1]).all() or not mask.any():
        raise ValueError('Invalid CT or supplied pancreas')
    return ct,image,mask.astype(np.uint8)


def load_model(path, device):
    import torch
    from monai.networks.nets import SegResNet
    if device not in ('cpu','mps','cuda'):raise ValueError('Unsupported device')
    state=torch.load(path,map_location='cpu',weights_only=True)
    session=state['session'];raw=session['raw']
    if (session['version']!=1 or raw['version']!=2 or session['identity']['version']!='pancreas-region-session-1'
            or session['identity']['raw']['architecture']!=ARCH or raw['identity']['architecture']!=ARCH
            or session['identity']['policy']['extra_margin_mm']!=[81.,43.,71.]
            or session['identity']['policy']['base_margin_mm']!=10.):
        raise ValueError('Checkpoint architecture or region recipe differs')
    # Construction and any initial RNG consumption are isolated to this worker process.
    model=SegResNet(spatial_dims=3,in_channels=1,out_channels=3,init_filters=16,
                   norm=('GROUP',{'num_groups':8}),blocks_down=(1,2,2,4),blocks_up=(1,1,1),dropout_prob=None)
    expected=model.state_dict();weights=raw['model']
    if set(weights)!=set(expected) or any(not isinstance(weights[k],torch.Tensor)
            or weights[k].shape!=v.shape or weights[k].dtype!=v.dtype or not torch.isfinite(weights[k]).all()
            for k,v in expected.items()):raise ValueError('Invalid model state')
    model.load_state_dict(weights,strict=True)
    del state,session,raw,weights,expected
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    return model.to(device).eval()


def run(request, output):
    import torch
    root=Path(__file__).resolve().parents[2]
    required=[Path(__file__), Path(__file__).with_name('assisted_windows.py'), Path(__file__).with_name('on_demand.py'), root/'scripts/predict_assisted_on_demand.py', root/'scripts/run_on_demand_worker.py']
    pins={r['path']:r['sha256'] for r in request['code']}
    if any(pins.get(str(p.resolve()))!=sha(p) for p in required):raise ValueError('Inference code closure is not pinned')
    if request['recipe_sha256']!=recipe_sha():raise ValueError('Inference recipe differs')
    case=request['case'];out=Path(output)
    ct,image,pancreas=checked_images(case['ct']['path'],case['pancreas']['path'])
    model=load_model(request['checkpoint']['path'],request['device'])
    torch.set_num_threads(2)
    def probabilities(patch):
        with torch.no_grad():
            logits=model(torch.from_numpy(patch[None,None]).to(request['device']))
            if not torch.isfinite(logits).all():raise ValueError('Nonfinite model output')
            return torch.softmax(logits,dim=1)[0].cpu().numpy()
    prediction,reconstruction=predict_array(image,pancreas,ct.affine,probabilities)
    out.mkdir(exist_ok=False)
    shutil.copyfile(case['ct']['path'],out/'ct.nii.gz')
    nifti=nib.Nifti1Image(prediction,ct.affine);nifti.header.set_xyzt_units('mm');nib.save(nifti,out/'prediction.nii.gz')
    e=dict(component='assisted-native-inference-v1',reference_inputs_used=True,
        request_identity=request['request_identity'],prediction_id=request['job_id'],
        recipe_sha256=request['recipe_sha256'],model_sha256={'segmenter':request['checkpoint']['sha256']},
        source_identity={'study_id':case['case_id'],'ct_sha256':case['ct']['sha256']},
        assistance=dict(kind='provided_pancreas',sha256=case['pancreas']['sha256'],lesion_reference_used_for_prediction=False),
        transform=dict(source_shape=list(ct.shape),source_affine=ct.affine.tolist(),units='mm',native_box=reconstruction['native_box']),
        reconstruction=reconstruction,device=request['device'],code=request['code'])
    # Filesystem paths stay in the private request, never in transport provenance.
    e['code']=[dict(sha256=r['sha256']) for r in request['code']]
    (out/'evidence.json').write_bytes(canonical(e))
    (out/'result.json').write_bytes(canonical(dict(status='complete',case_id=case['case_id'],reference_inputs_used=True,prediction_sha256=sha(out/'prediction.nii.gz'),evidence=e)))
    files={k:dict(uri=n,bytes=(out/n).stat().st_size,content_sha256=sha(out/n)) for k,n in [('ct','ct.nii.gz'),('pred','prediction.nii.gz'),('result','result.json'),('evidence','evidence.json')]}
    m=dict(schema_version='assisted-prediction-view-v1',case_id=case['case_id'],status='completed_with_warnings',
        prediction_mode='pancreas_assisted',reference_inputs_used=True,prediction_id=request['job_id'],request_identity=request['request_identity'],
        recipe_sha256=request['recipe_sha256'],assistance_sha256=case['pancreas']['sha256'],model_sha256=e['model_sha256'],
        files=files,result_sha256=files['result']['content_sha256'],inference_evidence_sha256=files['evidence']['content_sha256'],
        geometry=dict(shape=list(ct.shape),affine=ct.affine.tolist(),units='mm'),ct_window=[-100,300],labels={'0':'background','1':'pancreas','2':'lesion'},
        warnings=['Development prediction; outline accuracy and anatomical completeness require review.',
                  'Provided pancreas outline defines the search region. Cross-device equivalence has not been established.'])
    (out/'manifest.json').write_bytes(canonical(m))
