"""Deterministic native review displays; no model calls or data-driven inference."""
import numpy as np
import nibabel as nib
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont

PLANES=[('Axial',2,0,1,'L','R','A','P'),('Coronal',1,0,2,'L','R','S','I'),('Sagittal',0,1,2,'P','A','S','I')]
COLORS=dict(pancreas=(70,150,255),reference=(255,220,0),prediction=(255,0,200),overlap=(0,255,130))

def canonical(array,affine):
    orientation=nib.orientations.io_orientation(affine)
    transform=nib.orientations.ornt_transform(orientation,nib.orientations.axcodes2ornt(('R','A','S')))
    a=np.asarray(affine)@nib.orientations.inv_ornt_aff(transform,array.shape)
    spacing=np.linalg.norm(a[:3,:3],axis=0)
    if not np.allclose(a[:3,:3]/spacing,np.eye(3),atol=1e-5,rtol=0):raise ValueError('Unsupported non-axis-aligned review transform; no deobliquing')
    return nib.orientations.apply_orientation(array,transform),a,transform

def selected_component(mask,row):
    labels,n=ndimage.label(mask,structure=np.ones((3,3,3),np.uint8));i=row['component_id']
    if i<1 or i>n:raise ValueError('Missing declared component')
    selected=labels==i;del labels
    if int(selected.sum())!=row['voxels']:raise ValueError('Component voxels differ from saved score')
    box=[[int(v.min()),int(v.max())+1] for v in [np.flatnonzero(selected.any(axis=tuple(k for k in range(3) if k!=j))) for j in range(3)]]
    if box!=row['bounds_xyz_half_open']:raise ValueError('Component bounds differ')
    return selected

def plane_choices(mask,affine):
    if not mask.any():raise ValueError('Empty selected component')
    axes=[np.asarray(mask.sum(axis=tuple(k for k in range(3) if k!=j)),dtype=np.int64) for j in range(3)]
    centroid=np.array([(np.arange(len(v))*v).sum()/v.sum() for v in axes])
    rows=[]
    for title,axis,x,y,*edges in PLANES:
        index=int(np.argmax(axes[axis]));point=centroid.copy();point[axis]=index
        rows.append(dict(plane=title,axis=axis,index=index,x_axis=x,y_axis=y,world_ras_mm=(affine@[*point,1])[:3].tolist(),
            selection='maximum selected-component voxel area; smallest slice index breaks ties',edges=edges,centroid_ras_voxel=centroid.tolist()))
    return rows

def plane(array,row):return np.flipud(np.take(array,row['index'],axis=row['axis']).T)

def sheet(ct,pancreas,lesion,predictions,selected,affine,caption):
    choices=plane_choices(selected,affine);spacing=np.linalg.norm(affine[:3,:3],axis=0)
    canvas=Image.new('RGB',(1560,1020),(18,18,18));d=ImageDraw.Draw(canvas);font=ImageFont.load_default(size=19);small=ImageFont.load_default(size=15)
    d.text((16,10),caption,fill='white',font=font)
    d.text((16,38),'Yellow: reference lesion | Magenta: predicted lesion | Green: overlap | Blue outline: reference pancreas',fill='white',font=small)
    d.text((16,61),'HU [-100, 250]; native planes, lossless RAS permutation/flip; same slices/window/scale across arms. Circle marks selected component.',fill='white',font=small)
    for arm_index,(arm,pred) in enumerate(predictions.items()):
        top=100+arm_index*450;d.text((16,top),arm,fill='white',font=font)
        for j,row in enumerate(choices):
            hu=plane(ct,row);pa=plane(pancreas,row);ref=plane(lesion,row);pr=plane(pred==2,row)
            gray=(np.clip((hu+100)/350,0,1)*255).astype(np.uint8);rgb=np.repeat(gray[:,:,None],3,axis=2)
            edge=pa & ~ndimage.binary_erosion(pa)
            for mask,color in [(edge,COLORS['pancreas']),(ref & ~pr,COLORS['reference']),(pr & ~ref,COLORS['prediction']),(pr & ref,COLORS['overlap'])]:
                rgb[mask]=(rgb[mask]*.35+np.array(color)*.65).astype(np.uint8)
            h,w=hu.shape;physical=np.array([w*spacing[row['x_axis']],h*spacing[row['y_axis']]])
            target=np.maximum(1,np.rint(physical*min(470/physical[0],350/physical[1])).astype(int));im=Image.fromarray(rgb).resize(tuple(target),Image.Resampling.NEAREST)
            left=j*520+25+(470-int(target[0]))//2;upper=top+52+(350-int(target[1]))//2;canvas.paste(im,(left,upper))
            d.text((j*520+25,top+26),row['plane']+' | RAS mm '+','.join(f'{x:.1f}' for x in row['world_ras_mm']),fill='white',font=small)
            centroid=row['centroid_ras_voxel'];cx=left+(centroid[row['x_axis']]+.5)/w*target[0];cy=upper+(h-centroid[row['y_axis']]-.5)/h*target[1]
            d.ellipse((cx-13,cy-13,cx+13,cy+13),outline='white',width=1)
            le,ri,to,bo=row['edges'];d.text((left,upper+int(target[1])//2),le,fill='white',font=font);d.text((left+int(target[0])-16,upper+int(target[1])//2),ri,fill='white',font=font)
            d.text((left+int(target[0])//2,upper),to,fill='white',font=font);d.text((left+int(target[0])//2,upper+int(target[1])-20),bo,fill='white',font=font)
    d.text((16,1000),'Representative slices only. Reference annotations are not clinical diagnoses; no exhaustive clinical review.',fill='white',font=small)
    return canvas,choices
