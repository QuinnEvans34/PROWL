"""Versioned diagnostic display: empty masks show context, never a fictitious detail crop."""
import io
import math
import nibabel as nib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from src.data.segmenter_content_v1 import MAX_PLANES


def render_native(ct,pancreas,lesion,affine,title,components,tick=lambda:None):
    """RAS display views only; masks and native report coordinates remain unchanged."""
    original_shape=ct.shape
    transform=nib.orientations.ornt_transform(nib.orientations.io_orientation(np.asarray(affine)),nib.orientations.axcodes2ornt(('R','A','S')))
    ct,pancreas,lesion=[nib.orientations.apply_orientation(a,transform) for a in (ct,pancreas,lesion)]
    inverse=nib.orientations.inv_ornt_aff(transform,original_shape)
    display_affine=np.asarray(affine)@inverse;spacing=nib.affines.voxel_sizes(display_affine)
    planes=[]
    def add(axis,index):
        value=(int(axis),int(index))
        if value not in planes and len(planes)<MAX_PLANES:planes.append(value)
    z=np.flatnonzero(lesion.any(axis=(0,1)))
    if len(z):
        for index in (z[0],z[len(z)//2],z[-1]):add(2,index)
    for axis in (2,1,0):
        area=lesion.sum(axis=tuple(a for a in range(3) if a!=axis))
        if area.max():add(axis,np.argmax(area))
        else:
            area=pancreas.sum(axis=tuple(a for a in range(3) if a!=axis));add(axis,np.argmax(area) if area.max() else ct.shape[axis]//2)
    forward=np.linalg.inv(inverse);unshown=[]
    for c in components:
        point=forward@np.array(c['representative_xyz']+[1]);i=int(round(point[2]))
        if (2,i) not in planes and len(planes)>=MAX_PLANES:unshown.append(c['component_id'])
        else:add(2,i)
    panels=[];panel_records=[]
    for axis,index in planes:
        tick();axes=[a for a in range(3) if a!=axis]
        image=np.take(ct,index,axis=axis).T;pm=np.take(pancreas,index,axis=axis).T;lm=np.take(lesion,index,axis=axis).T
        boxes=[None]
        if lm.any():
            ys,xs=np.nonzero(lm);boxes.append((max(0,int(xs.min())-12),max(0,int(ys.min())-12),min(image.shape[1],int(xs.max())+13),min(image.shape[0],int(ys.max())+13)))
        for detail,box in enumerate(boxes):
            if box:x0,y0,x1,y1=box;im=image[y0:y1,x0:x1];p=pm[y0:y1,x0:x1];l=lm[y0:y1,x0:x1]
            else:im,p,l=image,pm,lm
            gray=np.clip((im+100)/350*255,0,255).astype(np.uint8);rgb=np.repeat(gray[...,None],3,axis=2)
            pe=p.astype(bool)&~ndimage.binary_erosion(p.astype(bool));le=l.astype(bool)&~ndimage.binary_erosion(l.astype(bool))
            rgb[pe]=[30,220,110];rgb[le]=[255,60,210]
            source=Image.fromarray(rgb);physical=(source.width*spacing[axes[0]],source.height*spacing[axes[1]])
            scale=min(472/physical[0],370/physical[1]);size=(max(1,round(physical[0]*scale)),max(1,round(physical[1]*scale)))
            source=source.resize(size,Image.Resampling.NEAREST)
            panel=Image.new('RGB',(480,420),'#101418');panel.paste(source,((480-size[0])//2,38+(370-size[1])//2));draw=ImageDraw.Draw(panel)
            world=(display_affine@np.array([index if a==axis else 0 for a in range(3)]+[1]))[axis]
            draw.text((6,5),f'RAS {"XYZ"[axis]}={index} / {world:.2f}mm; '+('native detail' if box else 'full FOV context'),fill='white')
            draw.text((6,21),f'col {"RAS"[axes[0]]}, row {"RAS"[axes[1]]}; green pancreas / magenta lesion',fill='white')
            panels.append(panel);panel_records.append(dict(ras_axis=axis,index=index,detail=box is not None,detail_box=box,view_kind="detail" if box else "context"))
    sheet=Image.new('RGB',(1440,80+math.ceil(len(panels)/3)*420),'#101418');draw=ImageDraw.Draw(sheet)
    draw.text((10,8),title,fill='white');draw.text((10,28),'Native CT [-100,250] HU display; masks unchanged; RAS axes; technical alignment only',fill='white')
    if not lesion.any():draw.text((10,48),'EMPTY LESION: unknown reference status, not verified negative',fill='#ffb060')
    for i,panel in enumerate(panels):sheet.paste(panel,((i%3)*480,80+(i//3)*420))
    output=io.BytesIO();sheet.save(output,format='PNG');tick()
    return output.getvalue(),dict(orientation_transform=transform.tolist(),native_to_ras_voxel_affine=forward.tolist(),
                                 ras_affine=display_affine.tolist(),ras_spacing=spacing.tolist(),panels=panel_records,
                                 max_planes=MAX_PLANES,unshown_component_ids=unshown,display_only=True)
