"""Rebuildable native contour views from the cached normalized ROI; no original CT reads."""
from io import BytesIO
import math
import nibabel as nib
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from src.data import segmenter_geometry_v1 as geometry
from src.data.manifest_records import digest
from src.data.source_inventory_records import require

def render(image,pancreas,lesion,prediction,case,step,weights_sha256,*,tick=lambda:None):
    t=case['transform'];geometry.validate_record(t,case['transform_sha256']);require(image.shape==(1,144,144,144) and image.dtype==np.float32 and np.isfinite(image).all() and image.min()>=0 and image.max()<=1 and pancreas.shape==lesion.shape==prediction.shape==tuple(t['source_shape']),'Review view input geometry')
    gray=geometry._restore_one(image[0],t,order=1,cval=0,tick=tick);orientation=np.asarray(t['orientation_forward']);affine=np.asarray(t['source_affine'])@nib.orientations.inv_ornt_aff(orientation,t['source_shape']);spacing=nib.affines.voxel_sizes(affine)
    gray,pancreas,lesion,prediction=[nib.orientations.apply_orientation(a,orientation) for a in (gray,pancreas,lesion,prediction)];planes=[]
    def add(axis,index):
        p=(int(axis),int(index))
        if p not in planes and len(planes)<18:planes.append(p)
    z=np.flatnonzero(lesion.any(axis=(0,1)))
    if len(z):
        for index in (z[0],z[len(z)//2],z[-1]):add(2,index)
    for axis in (2,1,0):
        area=lesion.sum(axis=tuple(a for a in range(3) if a!=axis))
        if not area.max():area=pancreas.sum(axis=tuple(a for a in range(3) if a!=axis))
        add(axis,np.argmax(area) if area.max() else gray.shape[axis]//2)
    unshown=[];forward=np.linalg.inv(nib.orientations.inv_ornt_aff(orientation,t['source_shape']))
    for c in case['reference_components']:
        point=forward@np.array([v[0] for v in c['bounds_xyz_half_open']]+[1]);index=int(round(point[2]))
        if (2,index) not in planes and len(planes)>=18:unshown.append(c['component_id'])
        else:add(2,index)
    panels=[];records=[]
    for axis,index in planes:
        tick();axes=[a for a in range(3) if a!=axis];g=np.take(gray,index,axis=axis).T;refp=np.take(pancreas,index,axis=axis).T;refl=np.take(lesion,index,axis=axis).T;pred=np.take(prediction,index,axis=axis).T;rgb=np.repeat(np.clip(g*255,0,255).astype(np.uint8)[...,None],3,axis=2)
        for mask,color in [(refp,[30,220,110]),(refl,[255,70,210]),(pred==1,[255,210,40]),(pred==2,[30,180,255])]:
            edge=mask.astype(bool)&~ndimage.binary_erosion(mask.astype(bool));rgb[edge]=color
        im=Image.fromarray(rgb);physical=(im.width*spacing[axes[0]],im.height*spacing[axes[1]]);scale=min(472/physical[0],350/physical[1]);size=(max(1,round(physical[0]*scale)),max(1,round(physical[1]*scale)));im=im.resize(size,Image.Resampling.NEAREST);panel=Image.new('RGB',(480,390),'#101418');panel.paste(im,((480-size[0])//2,30+(350-size[1])//2));ImageDraw.Draw(panel).text((6,5),f'RAS {"XYZ"[axis]}={index}; col {"RAS"[axes[0]]}, row {"RAS"[axes[1]]}',fill='white');panels.append(panel);records.append(dict(ras_axis=axis,index=index))
    sheet=Image.new('RGB',(1440,90+390*math.ceil(len(panels)/3)),'#101418');draw=ImageDraw.Draw(sheet);draw.text((10,8),case['study_id']+f' | committed step {step} | native contour review',fill='white');draw.text((10,28),'Gray: reconstructed normalized cached ROI; outside ROI has no CT information',fill='white');draw.text((10,48),'Reference: green pancreas, magenta lesion | Prediction: yellow class1, cyan class2',fill='white');draw.text((10,68),'Display only; original target/prediction counts unchanged; no clinical interpretation',fill='white')
    for n,p in enumerate(panels):sheet.paste(p,((n%3)*480,90+(n//3)*390))
    raw=BytesIO();sheet.save(raw,format='PNG');png=raw.getvalue();tick();return png,dict(study_id=case['study_id'],protected_role=case['protected_role'],completed_updates=step,weights_sha256=weights_sha256,image_sha256=case['image_sha256'],transform_sha256=case['transform_sha256'],source='normalized_cached_ROI_display_not_original_CT',outside_roi_CT_information=False,display_only=True,panels=records,unshown_reference_component_ids=unshown,png_sha256=digest(png))
