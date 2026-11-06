"""CT-only raw Universal inference, with two-channel CPU accumulation.

Upstream source/backbone stay external and unchanged. This adaptation uses current
MONAI preprocessing and linear probability restoration; it is not claimed to be
numerically identical to the upstream hard-mask inverse/postprocessing pipeline.
"""
import math
from pathlib import Path
import time
import numpy as np
from scipy.ndimage import affine_transform


def native_probability(probability, working_affine, native_shape, native_affine):
    if probability.ndim != 3 or not np.isfinite(probability).all():
        raise ValueError('Finite 3D probability required')
    mapping = np.linalg.inv(working_affine) @ native_affine
    out = affine_transform(probability, mapping[:3,:3], offset=mapping[:3,3],
                           output_shape=tuple(native_shape), order=1,
                           mode='grid-constant', cval=0.0, prefilter=False)
    return np.clip(out, 0, 1)


def codes_from_probabilities(pancreas, lesion):
    if pancreas.shape != lesion.shape or not np.isfinite(pancreas).all() or not np.isfinite(lesion).all():
        raise ValueError('Aligned finite probabilities required')
    codes = (pancreas > .5).astype(np.uint8)
    codes[lesion > .5] = 2
    return codes


def prepare_ct(path, expected_sha256, expected_header):
    import nibabel as nib
    import torch
    from monai.data import MetaTensor
    from monai.transforms import Orientation, Spacing
    from src.inference.universal_model_loading_20261105 import digest
    path=Path(path)
    if digest(path)!=expected_sha256: raise ValueError('CT source identity changed')
    obj=nib.load(path)
    if obj.header.get_xyzt_units()[0]!='mm' or list(obj.shape)!=expected_header['shape'] or not np.allclose(obj.affine,expected_header['affine'],rtol=0,atol=1e-5):
        raise ValueError('CT geometry/units changed')
    if math.prod(obj.shape)>96_000_000: raise ValueError('Native voxel cap')
    # Bound spacing output before allocating the resampled image.
    extent=np.linalg.norm(obj.affine[:3,:3],axis=0)*np.asarray(obj.shape)
    if math.prod(np.ceil(extent/1.5).astype(int)+4)>48_000_000: raise ValueError('Working voxel cap')
    image=np.asarray(obj.dataobj,dtype=np.float32)
    if not np.isfinite(image).all(): raise ValueError('Nonfinite CT')
    x=MetaTensor(torch.from_numpy(image[None]),affine=obj.affine)
    x=Orientation(axcodes='RAS')(x)
    x=Spacing(pixdim=(1.5,1.5,1.5),mode='bilinear',padding_mode='border',align_corners=False)(x)
    working_affine=x.affine.cpu().numpy().copy()
    scaled=np.clip((x.as_tensor().numpy()[0]+175.)/425.,0.,1.)
    # Whole CT-derived foreground only; never a pancreas or lesion reference box.
    foreground=scaled>0
    if not foreground.any(): raise ValueError('No image foreground')
    low=[]; high=[]
    for axis in range(3):
        occupied=np.flatnonzero(foreground.any(axis=tuple(i for i in range(3) if i!=axis)))
        low.append(int(occupied[0])); high.append(int(occupied[-1]+1))
    del foreground,x,image
    slices=tuple(slice(lo,hi) for lo,hi in zip(low,high))
    cropped=np.ascontiguousarray(scaled[slices]);del scaled
    working_affine[:3,3]=(working_affine@[*low,1])[:3]
    if digest(path)!=expected_sha256: raise ValueError('CT changed during preparation')
    return cropped,{'native_shape':list(obj.shape),'native_affine':obj.affine.tolist(),
                    'working_shape':list(cropped.shape),'working_affine':working_affine.tolist(),
                    'foreground_low':low,'foreground_high':high,'reference_inputs_used':False,
                    'spacing_mm':[1.5]*3,'hu_window':[-175,250]}


def run_raw(model, image, geometry, output, *, remaining_seconds, on_patch=lambda x:None):
    import torch
    import nibabel as nib
    from monai.inferers import sliding_window_inference
    from src.inference.universal_model_loading_20261105 import digest
    start=time.monotonic(); patches=0; cap=6*1024**3
    class Selected(torch.nn.Module):
        def forward(self, x):
            nonlocal patches
            if time.monotonic()-start>remaining_seconds: raise RuntimeError('Inference deadline')
            all_logits=model(x)
            if tuple(all_logits.shape)!=(1,32,96,96,96) or not torch.isfinite(all_logits).all():
                raise ValueError('Upstream32channel finite output required')
            selected=all_logits[:,[10,27]].contiguous();del all_logits
            if max(torch.cuda.max_memory_allocated(),torch.cuda.max_memory_reserved())>cap:
                raise RuntimeError('GPU memory cap')
            patches+=1;on_patch({'patch':patches,'seconds':time.monotonic()-start})
            return selected
    with torch.inference_mode():
        # Input and accumulated two-channel logits stay on CPU; only patch forwards use CUDA.
        logits=sliding_window_inference(torch.from_numpy(image)[None,None],(96,96,96),1,
            Selected(),overlap=.5,mode='gaussian',sw_device='cuda',device='cpu',padding_mode='constant',cval=0.)
        probability=torch.sigmoid(logits[0]).numpy();del logits
    pancreas=native_probability(probability[0],np.asarray(geometry['working_affine']),geometry['native_shape'],np.asarray(geometry['native_affine']))
    lesion=native_probability(probability[1],np.asarray(geometry['working_affine']),geometry['native_shape'],np.asarray(geometry['native_affine']))
    codes=codes_from_probabilities(pancreas,lesion)
    output=Path(output);output.mkdir(exist_ok=False)
    files={}
    for name,values in [('prediction',codes),('raw_pancreas',(pancreas>.5).astype(np.uint8))]:
        p=output/(name+'.nii.gz');obj=nib.Nifti1Image(values,np.asarray(geometry['native_affine']))
        obj.header.set_xyzt_units('mm');nib.save(obj,p);files[name]={'path':str(p),'sha256':digest(p)}
    return {'files':files,'patches':patches,'seconds':time.monotonic()-start,'geometry':geometry,
            'raw_threshold':.5,'decision':'strict greater than; lesion wins only in combined code map',
            'raw_pancreas_voxels':int(np.count_nonzero(pancreas>.5)),
            'peak_cuda_allocated':torch.cuda.max_memory_allocated(),
            'peak_cuda_reserved':torch.cuda.max_memory_reserved(),'reference_inputs_used':False}
