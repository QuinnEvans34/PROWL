"""CT-only two-stage prediction; no manifest, reference-mask or scoring inputs.

Models are supplied by trusted application code after checkpoint/provenance review.
This module proves an inference data boundary, not absence of training leakage.
"""
from hashlib import sha256
from pathlib import Path
import json
import math
import nibabel as nib
import numpy as np
import torch
from monai.inferers import sliding_window_inference
from src.data import localizer_preprocessing_v4 as local_geometry
from src.data import segmenter_predicted_roi_v2 as region
from src.data.source_inventory_records import content_hash, require


def predict(image, affine, *, source_identity, localizer, segmenter, localizer_sha256,
            segmenter_sha256, localizer_recipe, patch_size=(144,144,144),
            tensor_shape=(144,144,144), device='cpu', max_sampling_voxels=16_000_000, region_policy='all_support'):
    """Models receive image tensors only; the localizer sees the entire CT grid."""
    require(region_policy in ('all_support','largest_component_26'), 'Unknown localizer region policy')
    require(device in ('cpu','mps','cuda'), 'Explicit backend required')
    require(len(patch_size)==3 and all(type(v) is int and 16<=v<=192 and v%8==0 for v in patch_size),
            'Supported sliding-window patch required')
    for pin in (localizer_sha256,segmenter_sha256):
        require(isinstance(pin,str) and len(pin)==64 and all(c in '0123456789abcdef' for c in pin),
                'Model checksum required')
    prepared=local_geometry.preprocess(image,affine,localizer_recipe)  # Deliberately no target.
    x=prepared['image'].as_tensor();transform=prepared['transform_record']
    localizer.to(device).eval();segmenter.to(device).eval()
    with torch.inference_mode():
        logits=sliding_window_inference(x[None],patch_size,1,localizer,overlap=.25,
            mode='constant',padding_mode='constant',sw_device=device,device='cpu')
        require(tuple(logits.shape)==(1,2,*x.shape[1:]) and torch.isfinite(logits).all().item(),
                'Localizer must return finite two-class logits')
        processed=logits[0].argmax(0,keepdim=True);del logits
        native=local_geometry.restore_to_source(processed,transform,discrete=True)
        mask=native.as_tensor()[0].numpy().astype(np.uint8);del native,prepared,processed,x
        from src.inference.localizer_region_selection import select_region
        mask,selection=select_region(mask,region_policy)
        prediction=dict(schema_version='1.0.0',task='binary_pancreas',prediction_id='localizer-output',
            run_id='autonomous-cascade-v1',model_sha256=localizer_sha256,source_identity=source_identity,
            native_shape=list(mask.shape),native_affine=np.asarray(affine).tolist(),units='mm',
            full_volume=True,binary_mask_sha256=sha256(mask.tobytes()).hexdigest())
        plan=region.plan_predicted_roi(mask,affine,source_identity=source_identity,
            prediction_record=prediction,trusted_prediction_record_sha256=content_hash(prediction),
            tensor_shape=tensor_shape,max_sampling_voxels=max_sampling_voxels)
        pin=content_hash(plan)
        crop=region.prepare_predicted_image(image,affine,source_identity=source_identity,
            plan=plan,trusted_plan_sha256=pin)
        logits=segmenter(torch.from_numpy(crop)[None,None].to(device))
        require(tuple(logits.shape)==(1,3,*tensor_shape) and torch.isfinite(logits).all().item(),
                'Segmenter must return finite three-class logits')
        codes=logits[0].argmax(0).cpu().numpy().astype(np.uint8)
        result=region.restore_predicted_codes(codes,plan=plan,trusted_plan_sha256=pin)
    return result,dict(component='autonomous-cascade-v1',source_identity=source_identity,
        model_sha256=dict(localizer=localizer_sha256,segmenter=segmenter_sha256),
        localizer_recipe=localizer_recipe,localizer_transform=transform,patch_size=list(patch_size),
        overlap=.25,localizer_decision='argmax_then_'+region_policy,region_selection=selection,region_plan=plan,device=device,
        output_decision='tensor_argmax_then_nearest_native',reference_inputs_used=False,
        inference_claim='CT-only code path; training/selection provenance requires separate review')


def run_case(ct_path, output_dir, *, case_id, expected_ct_sha256, spatial_units_review=None, **model_options):
    """Read one named NIfTI CT, write a fresh result/failure; never discover sibling files.

    Only mm NIfTI scans are supported here. DICOM conversion and unknown-unit
    adjudication must happen separately, without reference-mask assistance.
    """
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=False)
    report=dict(case_id=case_id,status='failed',reference_inputs_used=False)
    try:
        path=Path(ct_path)
        require(path.suffixes[-2:]==['.nii','.gz'] or path.suffix=='.nii','NIfTI CT required')
        h=sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        require(h.hexdigest()==expected_ct_sha256,'CT bytes differ from declared input')
        img=nib.load(path)
        require(len(img.shape)==3 and math.prod(img.shape)<=model_options['localizer_recipe']['max_source_voxels'],
                'CT allocation envelope')
        from src.inference.spatial_units import resolve_mm
        report['spatial_units']=resolve_mm(img.header.get_xyzt_units()[0],h.hexdigest(),spatial_units_review)
        image=np.asarray(img.dataobj,dtype=np.float32)
        result,evidence=predict(image,img.affine,source_identity=dict(study_id=case_id,ct_sha256=h.hexdigest()),
                                **model_options)
        target=output/'prediction.nii.gz'
        exported=nib.Nifti1Image(result,img.affine);exported.set_sform(img.affine,code=1)
        exported.header.set_xyzt_units('mm');nib.save(exported,target)
        restored=nib.load(target)
        require(restored.shape==img.shape and np.array_equal(np.asarray(restored.dataobj),result)
                and np.allclose(restored.affine,img.affine,rtol=0,atol=1e-5),'Export changed native grid')
        report.update(status='complete',prediction_sha256=sha256(target.read_bytes()).hexdigest(),
            prediction_array_sha256=sha256(result.tobytes()).hexdigest(),evidence=evidence)
        return report
    except Exception as exc:
        report.update(error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        (output/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
