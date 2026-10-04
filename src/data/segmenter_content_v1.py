"""Native diagnostic content only; no eligibility, mask edits, ROI or model input."""
import hashlib
import io
import itertools
import math
import zlib
import nibabel as nib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from src.data.binary_label_policy import APPROVED_POLICY, decode_binary

CHUNK = 1024**2
MAX_COMPONENTS = 4096
MAX_PLANES = 18


class BudgetError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise ValueError(message)


def reserve(counts, key, amount, limits):
    if amount < 0 or counts[key] + amount > limits[key]:
        raise BudgetError('Read/allocation ceiling: ' + key)


def hash_exact(stream, row, counts, limits, tick):
    size = row['compressed_bytes']; reserve(counts, 'hash_bytes', size, limits)
    h = hashlib.sha256(); left = size
    while left:
        tick(); n = min(CHUNK, left); reserve(counts, 'hash_bytes', n, limits)
        raw = stream.read(n); counts['hash_bytes'] += len(raw)
        require(raw and len(raw) <= n, 'Truncated hash read')
        h.update(raw); left -= len(raw)
    require(h.hexdigest() == row['sha256'], 'Source compressed hash mismatch')
    return h.hexdigest()


def parse_header(raw, row):
    require(len(raw) == 348 and raw[:4] in (b'\x5c\x01\x00\x00', b'\x00\x00\x01\x5c'), 'Not NIfTI-1')
    h = nib.Nifti1Header.from_fileobj(io.BytesIO(raw), check=False)
    shape = tuple(int(n) for n in h.get_data_shape()); dtype = h.get_data_dtype()
    affine = h.get_best_affine(); offset = float(h['vox_offset'])
    require(bytes(h['magic']) == b'n+1\x00' and len(shape) == 3 and all(n > 0 for n in shape), 'Unsupported single-file 3D header')
    require(math.prod(shape) <= 46_219_264 and dtype.kind in 'iuf' and dtype.itemsize <= 8, 'Header allocation/type envelope')
    require(offset == 352 and offset + math.prod(shape)*dtype.itemsize == row['expanded_bytes'], 'Payload envelope/offset changed')
    expected = np.dtype(row['dtype'])
    require(dtype.kind == expected.kind and dtype.itemsize == expected.itemsize, 'Stored datatype changed')
    g = row['geometry']
    require(list(shape) == g['shape_xyz'] and np.isfinite(affine).all() and np.allclose(
        affine, np.array(g['affine_ras']).reshape(4,4), rtol=0, atol=1e-5), 'Native geometry changed')
    spacing = tuple(float(n) for n in h.get_zooms())
    require(all(math.isfinite(n) and n > 0 for n in spacing) and
            np.allclose(spacing,g['spacing_mm_xyz'],rtol=0,atol=1e-5), 'Native spacing changed')
    slope, inter = h.get_slope_inter(); slope, inter = (1.,0.) if slope is None else (slope,inter)
    require(math.isfinite(slope) and math.isfinite(inter), 'Invalid scaling')
    units = list(h.get_xyzt_units())
    if row['kind'] == 'lesion':
        previous = row['header']
        require(hashlib.sha256(raw).hexdigest() == previous['decompressed_header_sha256'], 'Lesion header identity changed')
        expected_scaling = dict(slope=previous['effective_slope'],intercept=previous['effective_intercept'])
        expected_units = previous['units']
    else:
        expected_scaling = row['retained_content']['effective_scaling']; expected_units = row['retained_content']['units']
    require(dict(slope=slope,intercept=inter) == expected_scaling and units == expected_units, 'Scaling/units changed')
    require(units[0] == 'mm' if row['kind'] == 'ct' else units[0] in ('mm','unknown'), 'Unresolved spatial context')
    return h, dict(shape=list(shape),dtype=dtype.str,affine=affine.tolist(),spacing=list(spacing),units=units,
                   slope=slope,intercept=inter,offset=352,header_sha256=hashlib.sha256(raw).hexdigest())


def decode_exact(stream, row, counts, limits, tick):
    """One bounded gzip member; exact payload, CRC, no trailing members/bytes or proxy rereads."""
    size = row['compressed_bytes']; expected = row['expanded_bytes']
    reserve(counts,'decode_bytes',size,limits); reserve(counts,'expanded_bytes',expected,limits)
    decoder = zlib.decompressobj(16+zlib.MAX_WBITS); digest = hashlib.sha256()
    left=size; used=0; buffer=None; prefix=bytearray(); header=None; pending=b''
    while left or pending:
        tick()
        if not pending:
            n=min(65536,left); reserve(counts,'decode_bytes',n,limits)
            pending=stream.read(n);counts['decode_bytes']+=len(pending);left-=len(pending)
            require(pending and len(pending)<=n,'Truncated compressed decode read');digest.update(pending)
        # First expose exactly the header, validate before allocating the declared array.
        capacity=348-len(prefix) if buffer is None else min(CHUNK,expected-used+1)
        part=decoder.decompress(pending,capacity);pending=decoder.unconsumed_tail
        if buffer is None:
            reserve(counts,'expanded_bytes',len(part),limits)
            prefix.extend(part);counts['expanded_bytes']+=len(part)
            if len(prefix)==348:
                h,header=parse_header(bytes(prefix),row)
                reserve(counts,'expanded_bytes',expected-348,limits)
                buffer=bytearray(expected);buffer[:348]=prefix;used=348
        else:
            require(used+len(part)<=expected,'Expanded payload exceeds exact envelope')
            reserve(counts,'expanded_bytes',len(part),limits)
            buffer[used:used+len(part)]=part;used+=len(part);counts['expanded_bytes']+=len(part)
        if decoder.eof:
            require(not decoder.unused_data and not pending and left==0,'Trailing gzip bytes or members')
            break
    require(decoder.eof and buffer is not None and used==expected,'Truncated gzip/payload')
    require(digest.hexdigest()==row['sha256'],'Compressed bytes changed during decode')
    require(buffer[348:352]==b'\x00'*4,'Unsupported NIfTI extension flag')
    stored=np.frombuffer(buffer,dtype=h.get_data_dtype(),offset=352).reshape(tuple(header['shape']),order='F')
    tick()
    return stored,header,dict(compressed_bytes=size,expanded_bytes=used,sha256=digest.hexdigest(),gzip_eof_crc_verified=True)


def target_content(stored, header, tick=lambda:None):
    order='F' if stored.flags.f_contiguous and not stored.flags.c_contiguous else 'C'
    flat=np.ravel(stored,order=order); decoded=np.empty(flat.shape,dtype=np.uint8);hist={};normalized=0
    for start in range(0,len(flat),CHUNK):
        tick();piece=flat[start:start+CHUNK]
        require(np.isfinite(piece).all(),'Nonfinite stored target')
        values,counts=np.unique(piece,return_counts=True)
        require(len(hist)+len(values)<=512,'Stored value table exceeds diagnostic envelope')
        for value,count in zip(values,counts):hist[float(value)]=hist.get(float(value),0)+int(count)
        semantic=piece.astype(np.float64)*header['slope']+header['intercept']
        binary,report=decode_binary(semantic.reshape((-1,1,1)),policy=APPROVED_POLICY)
        decoded[start:start+len(piece)]=binary.ravel();normalized+=report['normalized_voxels']
    # K order agrees with the native F payload; synthetic arrays may be C-contiguous.
    mask=decoded.reshape(stored.shape,order=order)
    pairs=[dict(stored=v,count=n,semantic=v*header['slope']+header['intercept']) for v,n in sorted(hist.items())]
    return mask,dict(policy=APPROVED_POLICY,absolute_tolerance=1e-6,relative_tolerance=0,
                     semantic_value_counts=pairs,normalized_voxels=normalized,foreground_voxels=int(np.count_nonzero(mask)),
                     max_endpoint_residual=max(min(abs(p['semantic']),abs(p['semantic']-1)) for p in pairs),eligibility='not_assessed')


def bounds(mask):
    if not np.any(mask):return None
    result=[]
    for axis in range(3):
        indices=np.flatnonzero(mask.any(axis=tuple(a for a in range(3) if a!=axis)))
        result.append([int(indices[0]),int(indices[-1])])
    return result


def world_bounds(box,affine):
    if box is None:return None
    points=np.array([p+(1,) for p in itertools.product(*[(b[0],b[1]) for b in box])])
    world=(np.asarray(affine)@points.T).T[:,:3]
    return [[float(world[:,a].min()),float(world[:,a].max())] for a in range(3)]


def component_content(lesion,pancreas,affine,tick=lambda:None):
    tick();labels,count=ndimage.label(lesion,structure=np.ones((3,3,3),dtype=np.uint8));tick()
    if count>MAX_COMPONENTS:raise BudgetError('All component records exceed4096; explicit resource hold, no truncation')
    sizes=np.zeros(count+1,dtype=np.int64);flat=labels.ravel()
    for start in range(0,flat.size,CHUNK):
        tick();sizes+=np.bincount(flat[start:start+CHUNK],minlength=count+1)
    boxes=ndimage.find_objects(labels,max_label=count);records=[]
    for i,slices in enumerate(boxes,1):
        tick();box=[[s.start,s.stop-1] for s in slices]
        local=labels[slices];first=np.unravel_index(int(np.argmax(local==i)),local.shape)
        representative=[int(v+s.start) for v,s in zip(first,slices)]
        records.append(dict(component_id=i,voxels=int(sizes[i]),bounds_xyz=box,
                            world_center_bounds_mm=world_bounds(box,affine),representative_xyz=representative,
                            source_boundary_contact=any(b[0]==0 or b[1]==lesion.shape[a]-1 for a,b in enumerate(box))))
    tick();total=int(np.count_nonzero(lesion)); overlap=int(np.count_nonzero(lesion & pancreas))
    assert sum(r['voxels'] for r in records)==total
    return dict(connectivity=26,component_count=int(count),components=records,lesion_voxels=total,
                pancreas_voxels=int(np.count_nonzero(pancreas)),inside_pancreas_voxels=overlap,
                outside_pancreas_voxels=total-overlap,bounds_xyz=bounds(lesion),
                world_center_bounds_mm=world_bounds(bounds(lesion),affine),
                lesion_reference_status='visible_positive_candidate_not_qualified' if total else 'unknown_empty_not_verified_negative')


def analyze(arrays,headers,tick=lambda:None):
    ct=arrays['ct'].astype(np.float32)*headers['ct']['slope']+headers['ct']['intercept'];tick()
    require(np.isfinite(ct).all(),'Nonfinite CT semantic values')
    pancreas,p_report=target_content(arrays['pancreas'],headers['pancreas'],tick)
    lesion,l_report=target_content(arrays['lesion'],headers['lesion'],tick)
    require(ct.shape==pancreas.shape==lesion.shape,'Native three-way grid mismatch')
    metrics=component_content(lesion,pancreas,headers['ct']['affine'],tick)
    metrics.update(ct_finite=True,ct_range=[float(ct.min()),float(ct.max())],pancreas_decode=p_report,lesion_decode=l_report,
                   technical_holds=[] if p_report['foreground_voxels'] else ['empty_pancreas_reference'])
    return ct,pancreas,lesion,metrics


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
        else:boxes.append(None)
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
            draw.text((6,5),f'RAS {"XYZ"[axis]}={index} / {world:.2f}mm; '+('native detail' if detail else 'full FOV'),fill='white')
            draw.text((6,21),f'col {"RAS"[axes[0]]}, row {"RAS"[axes[1]]}; green pancreas / magenta lesion',fill='white')
            panels.append(panel);panel_records.append(dict(ras_axis=axis,index=index,detail=bool(detail),detail_box=box))
    sheet=Image.new('RGB',(1440,80+math.ceil(len(panels)/3)*420),'#101418');draw=ImageDraw.Draw(sheet)
    draw.text((10,8),title,fill='white');draw.text((10,28),'Native CT [-100,250] HU display; masks unchanged; RAS axes; technical alignment only',fill='white')
    if not lesion.any():draw.text((10,48),'EMPTY LESION: unknown reference status, not verified negative',fill='#ffb060')
    for i,panel in enumerate(panels):sheet.paste(panel,((i%3)*480,80+(i//3)*420))
    output=io.BytesIO();sheet.save(output,format='PNG');tick()
    return output.getvalue(),dict(orientation_transform=transform.tolist(),native_to_ras_voxel_affine=forward.tolist(),
                                 ras_affine=display_affine.tolist(),ras_spacing=spacing.tolist(),panels=panel_records,
                                 max_planes=MAX_PLANES,unshown_component_ids=unshown,display_only=True)
