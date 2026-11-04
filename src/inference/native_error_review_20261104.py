"""Saved native arrays only. Axis-aligned lossless display, no inference/resampling."""
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont
from src.inference.native_review_overlays_20261103 import canonical,plane,plane_choices,selected_component

def crop_bounds(selected2d,spacing_xy,margin_mm=20):
    yy,xx=np.where(selected2d)
    if not len(xx):raise ValueError("Selected target absent from chosen slice")
    mx,my=np.ceil(margin_mm/np.asarray(spacing_xy)).astype(int)
    return (max(0,int(xx.min())-mx),max(0,int(yy.min())-my),min(selected2d.shape[1],int(xx.max())+mx+1),min(selected2d.shape[0],int(yy.max())+my+1))

def outline(mask):return mask & ~ndimage.binary_erosion(mask)

def render(ct,pan,les,pred,selected,aff,original_aff,roi_low,roi_high,caption):
    rows=plane_choices(selected,aff);spacing=np.linalg.norm(aff[:3,:3],axis=0)
    canvas=Image.new("RGB",(1560,1420),(18,18,18));d=ImageDraw.Draw(canvas)
    font=ImageFont.load_default(size=16);small=ImageFont.load_default(size=14)
    d.text((12,8),caption,fill="white",font=font)
    d.text((12,34),"Lesion REF yellow / PRED magenta / overlap green | Pancreas REF blue / PRED cyan | ROI orange",fill="white",font=font)
    d.text((12,58),"Rows: full native context + contours; enlarged CT alone; enlarged CT + contours. HU [-100,250]. White circle = target.",fill="white",font=small)
    d.text((12,79),"Lossless RAS permutation/flip, no deobliquing. Indices are zero-based. Reference-unit assumptions retained in manifest.",fill="white",font=small)
    for j,row in enumerate(rows):
        hu=plane(ct,row);pa=plane(pan,row);ref=plane(les,row);pr=plane(pred==2,row);pp=plane(pred==1,row);sel=plane(selected,row)
        gray=(np.clip((hu+100)/350,0,1)*255).astype(np.uint8);rgb=np.repeat(gray[:,:,None],3,axis=2);overlay=rgb.copy()
        for mask,color in [(outline(pa),(70,150,255)),(outline(pp),(0,240,240)),(ref & ~pr,(255,220,0)),(pr & ~ref,(255,0,200)),(pr & ref,(0,255,130))]:
            overlay[mask]=(overlay[mask]*.25+np.array(color)*.75).astype(np.uint8)
        x,y=row['x_axis'],row['y_axis'];h,w=hu.shape
        roi=np.zeros(hu.shape,bool)
        if roi_low[row['axis']]<=row['index']<roi_high[row['axis']]:
            roi[h-roi_high[y]:h-roi_low[y],roi_low[x]:roi_high[x]]=True
        overlay[outline(roi)]=(255,140,0)
        box=crop_bounds(sel,[spacing[x],spacing[y]])
        row['zoom_pixel_box_xy_half_open']=list(box)
        point=np.array(row['centroid_ras_voxel']);point[row['axis']]=row['index']
        row['original_native_voxel_at_target']=(np.linalg.inv(original_aff)@aff@np.r_[point,1])[:3].tolist()
        d.text((j*520+10,108),f"{row['plane']} RAS axis {row['axis']} index {row['index']}",fill="white",font=font)
        d.text((j*520+10,131),"world RAS mm "+','.join(f"{v:.1f}" for v in row['world_ras_mm']),fill="white",font=small)
        d.text((j*520+10,151),"native XYZ "+','.join(f"{v:.1f}" for v in row['original_native_voxel_at_target']),fill="white",font=small)
        for k,arr in enumerate([overlay,rgb,overlay]):
            b=(0,0,w,h) if k==0 else box;l,t,r,bot=b;view=arr[t:bot,l:r]
            physical=np.array([(r-l)*spacing[x],(bot-t)*spacing[y]])
            size=np.maximum(1,np.rint(physical*min(490/physical[0],375/physical[1])).astype(int))
            image=Image.fromarray(view).resize(tuple(size),Image.Resampling.NEAREST)
            left=j*520+15+(490-int(size[0]))//2;top=180+k*400+(375-int(size[1]))//2
            canvas.paste(image,(left,top))
            centroid=row['centroid_ras_voxel'];cx=left+(centroid[x]+.5-l)/(r-l)*size[0];cy=top+(h-centroid[y]-.5-t)/(bot-t)*size[1]
            if k!=1:d.ellipse((cx-14,cy-14,cx+14,cy+14),outline="white",width=1)
            le,ri,to,bo=row['edges']
            for pos,txt in [((left,top+int(size[1])//2),le),((left+int(size[0])-14,top+int(size[1])//2),ri),((left+int(size[0])//2,top),to),((left+int(size[0])//2,top+int(size[1])-17),bo)]:d.text(pos,txt,fill="white",font=small)
    d.text((12,1390),"Representative saved-output review; not annotation adjudication or clinical diagnosis. No new scoring/inference.",fill="white",font=small)
    return canvas,rows
