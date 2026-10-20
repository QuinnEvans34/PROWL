"""Inference-only numerical helpers extracted from the pinned October 20 source handoff.
No training/provider/optimizer imports. See ON-DEMAND-INFERENCE-2026-10-20.md.
"""
from itertools import product
import numpy as np
import nibabel as nib
from scipy import ndimage


# Source SHA-256: a71c155f66f1f08207eb656961ea2768bef67d4f67aee9e76f4499f979dd0d9d


def geometry(shape, affine):
    a = np.asarray(affine, dtype=float)
    if len(shape) != 3 or any(int(n) != n or n < 1 for n in shape):
        raise ValueError('Nonempty 3D source required')
    if a.shape != (4, 4) or not np.isfinite(a).all() or abs(np.linalg.det(a[:3, :3])) < 1e-10:
        raise ValueError('Invalid affine')
    original = nib.orientations.io_orientation(a)
    ras = nib.orientations.axcodes2ornt(('R', 'A', 'S'))
    forward = nib.orientations.ornt_transform(original, ras)
    inverse = nib.orientations.ornt_transform(ras, original)
    canonical_shape = np.asarray(shape)[np.argsort(forward[:, 0].astype(int))]
    return dict(source_shape=list(map(int, shape)), source_affine=a.tolist(),
                shape=canonical_shape.tolist(), forward=forward.tolist(), inverse=inverse.tolist(),
                affine=(a @ nib.orientations.inv_ornt_aff(forward, shape)).tolist())


def orient(array, record, *, inverse=False):
    expected = record['shape' if inverse else 'source_shape']
    if array.shape != tuple(expected):
        raise ValueError('Array/geometry mismatch')
    return nib.orientations.apply_orientation(array, np.asarray(record['inverse' if inverse else 'forward']))


def starts(length, window=144, stride=72):
    if length < 1 or window < 1 or not 1 <= stride <= window:
        raise ValueError('Invalid tiling')
    last = max(0, length-window)
    return sorted(set(list(range(0, last+1, stride)) + [last]))


def tiles(shape, window=144, stride=72):
    return list(product(*(starts(n, window, stride) for n in shape)))


def extract(array, origin, window=144):
    if len(origin) != 3 or any(type(int(o)) is not int or o != int(o) or o < 0 or o > max(0, n-window)
                              for o, n in zip(origin, array.shape)):
        raise ValueError('Invalid window origin')
    slices = tuple(slice(int(o), min(int(o)+window, n)) for o, n in zip(origin, array.shape))
    view = array[slices]
    out = np.zeros((window,)*3, dtype=array.dtype)
    out[tuple(slice(0, n) for n in view.shape)] = view
    return out, dict(pad_low=[0]*3, normalized_shape=list(view.shape))


def blend_weight(window=144):
    w = 1-np.abs((np.arange(window, dtype=np.float32)+.5)*2/window-1)
    return np.maximum(w[:, None, None]*w[None, :, None]*w[None, None, :], 1e-3)


# Source SHA-256: 7a923af2811a72694ea5cf94d9aa3e416eec5b1000c9cd638d5d6e2f5b81736e


POLICY = {'version':'physical-detail-windows-1', 'spacing_tolerance_mm':1e-5}


def physical_geometry(native):
    affine=np.array(native['affine'],dtype=float)
    spacing=np.linalg.norm(affine[:3,:3],axis=0)
    factors=np.maximum(1,np.ceil(spacing-POLICY['spacing_tolerance_mm'])).astype(np.int64)
    shape=np.asarray(native['shape'],dtype=np.int64)
    fine_affine=affine.copy()
    fine_affine[:3,3]=(affine @ [*((1/factors-1)/2),1])[:3]
    fine_affine[:3,:3]/=factors[None]
    return dict(version=POLICY['version'],native=native,factors=factors.tolist(),
                native_shape=shape.tolist(),shape=(shape*factors).tolist(),affine=fine_affine.tolist(),
                spacing_mm=(spacing/factors).tolist())


def coordinate_map(origin, valid_shape, factors):
    axes=[(np.arange(n,dtype=float)+o+.5)/f-.5 for o,n,f in zip(origin,valid_shape,factors)]
    return np.array(np.meshgrid(*axes,indexing='ij'))


def sample_window(array, record, origin, *, order, window=144):
    if array.shape!=tuple(record['native_shape']) or order not in (0,1):raise ValueError('Invalid source/order')
    if len(origin)!=3 or any(o!=int(o) or o<0 or o>max(0,n-window) for o,n in zip(origin,record['shape'])):
        raise ValueError('Invalid physical window')
    if record['factors']==[1,1,1]:return extract(array,origin,window)
    valid=[min(window,n-int(o)) for o,n in zip(origin,record['shape'])]
    coords=coordinate_map(origin,valid,record['factors'])
    values=ndimage.map_coordinates(array,coords,order=order,mode='nearest',prefilter=False)
    result=np.zeros((window,)*3,dtype=array.dtype)
    result[tuple(slice(0,n) for n in valid)]=values
    return result,dict(pad_low=[0]*3,normalized_shape=valid)


def native_destination(record, origin, window=144):
    """Native centers represented by this tile; no labels are consulted."""
    bounds=[];axes=[]
    for n,f,o,fine_n in zip(record['native_shape'],record['factors'],origin,record['shape']):
        last=min(o+window,fine_n)-1
        low=max(0,int(np.ceil((o+.5)/f-.5-1e-9)))
        high=min(n,int(np.floor((last+.5)/f-.5+1e-9))+1)
        bounds.append(slice(low,high))
        axes.append(f*(np.arange(low,high,dtype=float)+.5)-.5-o)
    return tuple(bounds),np.array(np.meshgrid(*axes,indexing='ij'))


class PhysicalReconstructor:
    def __init__(self, record, classes=3, window=144):
        self.record,self.window=record,window
        self.total=np.zeros((classes,*record['native_shape']),np.float32)
        self.weight=np.zeros(record['native_shape'],np.float32)
        self.kernel=blend_weight(window);self.seen=set()

    def add(self, origin, probabilities):
        origin=tuple(origin)
        if origin in self.seen or probabilities.shape!=(self.total.shape[0],self.window,self.window,self.window):
            raise ValueError('Duplicate or invalid prediction')
        if not np.isfinite(probabilities).all() or probabilities.min()<0 or probabilities.max()>1:
            raise ValueError('Invalid probabilities')
        if any(o<0 or o>max(0,n-self.window) for o,n in zip(origin,self.record['shape'])):raise ValueError('Invalid tile origin')
        if self.record['factors']==[1,1,1]:
            destination=tuple(slice(o,min(o+self.window,n)) for o,n in zip(origin,self.record['native_shape']))
            source=tuple(slice(0,s.stop-s.start) for s in destination)
            weight=self.kernel[source]
            self.total[(slice(None),*destination)]+=probabilities[(slice(None),*source)]*weight
            self.weight[destination]+=weight;self.seen.add(origin);return
        destination,coords=native_destination(self.record,origin,self.window)
        if coords.shape[1] and coords.shape[2] and coords.shape[3]:
            weight=ndimage.map_coordinates(self.kernel,coords,order=1,mode='nearest',prefilter=False)
            for k in range(self.total.shape[0]):
                values=ndimage.map_coordinates(probabilities[k],coords,order=1,mode='nearest',prefilter=False)
                self.total[(k,*destination)]+=values*weight
            self.weight[destination]+=weight
        self.seen.add(origin)

    def finish(self, expected_tiles):
        if self.seen!=set(map(tuple,expected_tiles)) or not np.all(self.weight>0):raise ValueError('Reconstruction gap or missing tile')
        self.total/=self.weight[None]
        return self.total
