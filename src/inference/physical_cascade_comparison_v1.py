"""CPU-only saved-output comparison; never loads models, CTs or reference labels."""
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib

WINDOWS_REQUEST = 'dc37f20affd1e071c46208ebbd8b34052aa09a704718df235de4385a48a726b3'
MAC_REQUEST = '2a0c7bfb09eb53807967ac6efee8d78554fd4b36cf726528a27bad370b75510e'
RULE = dict(affine_atol=1e-5, probability_atol=1e-5, probability_rtol=1e-4,
    maximum_argmax_disagreement=.001, normalization_atol=2e-5,
    exact_region_bounds=True, reference='Mac MPS', tolerance_review_commit='c35cd2b',
    scope='engineering_consistency_not_model_quality')
CORE = ('src/inference/physical_cascade_v1.py','src/inference/predicted_physical_region_v1.py',
    'src/inference/cascade_models_v1.py','src/data/localizer_preprocessing_v4.py',
    'src/data/segmenter_geometry_v2.py','src/data/segmenter_native_windows_v1.py',
    'src/data/segmenter_physical_windows_v1.py','src/models/segresnet.py')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def read(path):
    with Path(path).open(encoding='utf-8') as f:return json.load(f)


def same_sources(a,b,source_root):
    result=[]
    for relative in CORE:
        pins=[]
        for request in (a,b):
            values=[v for k,v in request['pins'].items() if k.replace('\\','/').endswith('/'+relative)]
            if len(values)!=1:raise ValueError('Missing/ambiguous source pin: '+relative)
            pins.append(values[0])
        content=(Path(source_root)/relative).read_bytes().replace(b'\r\n',b'\n')
        variants={hashlib.sha256(v).hexdigest() for v in (content,content.replace(b'\n',b'\r\n'))}
        if any(pin not in variants for pin in pins):raise ValueError('Inference source mismatch: '+relative)
        result.append(dict(path=relative,windows_sha256=pins[0],mac_sha256=pins[1],
            normalized_sha256=hashlib.sha256(content).hexdigest()))
    return result


def load_run(root,expected_request):
    root=Path(root)
    if digest(root/'request.json')!=expected_request:raise ValueError('Request identity mismatch')
    request=read(root/'request.json');result=read(root/'output/result.json')
    resources_path=root/('worker.resources.json' if expected_request==WINDOWS_REQUEST else 'resources.json')
    resources=read(resources_path)
    if not resources.get('success') or not resources.get('workers_reaped') or resources.get('exit_code')!=0:
        raise ValueError('Worker completion/cleanup gate failed')
    if (result['request_sha256']!=expected_request or
        result['status']!='LOCAL_DIAGNOSTIC_COMPLETE_REFERENCE_PENDING' or
        result['reference_inputs_used'] is not False or result['optimizer_updates']!=0):
        raise ValueError('Incomplete or assisted diagnostic')
    if read(root/'output/input-access.json')['reference_paths_allowed'] is not False:
        raise ValueError('Reference access boundary missing')
    files={}
    for name in ('prediction.nii.gz','localizer.nii.gz','region-probabilities.npy'):
        p=root/'output'/name;expected=result['artifacts'][name]
        if p.stat().st_size!=expected['bytes'] or digest(p)!=expected['sha256']:
            raise ValueError('Output integrity mismatch: '+name)
        files[name]=p
    return request,result,files


def compare_arrays(win,mac,win_codes,mac_codes,win_localizer,mac_localizer):
    if win.shape!=mac.shape or win.ndim!=4 or win.shape[0]!=3 or win.dtype!=np.float32 or mac.dtype!=np.float32:
        raise ValueError('Probability representation mismatch')
    count=0;maximum=0.;normalization_max=[0.,0.]
    # Slab comparison bounds temporary memory and uses Mac as the predeclared reference.
    for start in range(0,win.shape[1],8):
        x=win[:,start:start+8];y=mac[:,start:start+8]
        for k,values in enumerate((x,y)):
            if not np.isfinite(values).all() or values.min()<0 or values.max()>1:
                raise ValueError('Nonfinite/out-of-range probability')
            error=float(np.max(np.abs(values.sum(0)-1)))
            normalization_max[k]=max(normalization_max[k],error)
            if error>RULE['normalization_atol']:raise ValueError('Unnormalized probabilities')
        difference=np.abs(x-y)
        maximum=max(maximum,float(difference.max()))
        count+=int(np.count_nonzero(difference>RULE['probability_atol']+RULE['probability_rtol']*np.abs(y)))
    if win_codes.shape!=mac_codes.shape or win_localizer.shape!=win_codes.shape or mac_localizer.shape!=win_codes.shape:
        raise ValueError('Native code/mask grids differ')
    if not all(np.isin(v,[0,1,2]).all() for v in (win_codes,mac_codes)) or not all(np.isin(v,[0,1]).all() for v in (win_localizer,mac_localizer)):
        raise ValueError('Invalid class codes')
    hard=int(np.count_nonzero(win_codes!=mac_codes));frac=hard/win_codes.size
    local=int(np.count_nonzero(win_localizer!=mac_localizer))
    return dict(passed=count==0 and frac<=RULE['maximum_argmax_disagreement'] and local/win_codes.size<=RULE['maximum_argmax_disagreement'],
        probability_values=int(win.size),probability_values_outside_tolerance=count,
        max_probability_absolute_difference=maximum,normalization_max_error=normalization_max,
        native_voxels=int(win_codes.size),hard_code_disagreements=hard,hard_code_disagreement_fraction=frac,
        localizer_mask_disagreements=local,localizer_mask_disagreement_fraction=local/win_codes.size)


def compare(windows,mac,*,source_root):
    a,x,af=load_run(windows,WINDOWS_REQUEST);b,y,bf=load_run(mac,MAC_REQUEST)
    for key in ('case_id','ct_sha256','source_shape','units','localizer_recipe','policy'):
        if a[key]!=b[key]:raise ValueError('Request scientific identity differs: '+key)
    if {k:v['sha256'] for k,v in a['models'].items()}!={k:v['sha256'] for k,v in b['models'].items()}:
        raise ValueError('Model identities differ')
    source_check=same_sources(a,b,source_root)
    for result,request in ((x,a),(y,b)):
        if result['source_shape']!=request['source_shape'] or result['units']!='mm':raise ValueError('Reported source differs')
        if not np.allclose(result['source_affine'],request['source_affine'],atol=RULE['affine_atol'],rtol=0):raise ValueError('Reported affine differs')
        if result['evidence']['reference_inputs_used'] is not False:raise ValueError('Assisted region')
        if result['evidence']['reconstruction']['gap_voxels']!=0 or result['evidence']['reconstruction']['minimum_blend_weight']<=0:
            raise ValueError('Reconstruction gaps')
    if not np.allclose(a['source_affine'],b['source_affine'],atol=RULE['affine_atol'],rtol=0):raise ValueError('Source affine mismatch')
    ex,ey=x['evidence'],y['evidence']
    for key in ('region_low','region_high','geometry','parent_geometry','localizer_policy',
                'localizer_transform','probability_representation','probability_outside_region'):
        if ex[key]!=ey[key]:raise ValueError('Exact transform/region mismatch: '+key)
    if ex['reconstruction']['physical_grid']!=ey['reconstruction']['physical_grid']:raise ValueError('Physical grid differs')
    arrays=[]
    for files,request in ((af,a),(bf,b)):
        row=[]
        for name in ('prediction.nii.gz','localizer.nii.gz'):
            n=nib.load(files[name])
            if list(n.shape)!=request['source_shape'] or n.header.get_xyzt_units()[0]!='mm' or not np.allclose(n.affine,request['source_affine'],atol=RULE['affine_atol'],rtol=0):
                raise ValueError('Saved native grid mismatch')
            row.append(np.asarray(n.dataobj))
        probabilities=np.load(files['region-probabilities.npy'],mmap_mode='r',allow_pickle=False)
        if probabilities.shape[1:]!=tuple(ex['geometry']['shape']):raise ValueError('ROI probability shape mismatch')
        arrays.append((probabilities,*row))
    result=compare_arrays(arrays[0][0],arrays[1][0],arrays[0][1],arrays[1][1],arrays[0][2],arrays[1][2])
    # Reconcile each hard output against its OWN probabilities, independently of parity.
    from src.inference.physical_cascade_v1 import hard_codes,embed
    for probs,codes,_ in arrays:
        if not np.array_equal(embed(hard_codes(probs),ex),codes):raise ValueError('Codes do not match stored probabilities')
    return dict(status='PASS_ENGINEERING_COMPARISON' if result['passed'] else 'FAIL_ENGINEERING_COMPARISON',
        rule=RULE,comparison=result,source_check=source_check,
        windows_request_sha256=WINDOWS_REQUEST,mac_request_sha256=MAC_REQUEST,
        runtime_windows=a['environment'],runtime_mac=b['environment'],
        case_id=a['case_id'],model_quality_tested=False,labels_read=False,batch_authorized_by_comparison_alone=False)
