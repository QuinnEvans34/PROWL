"""On-demand physical windows without spatial downsampling or a dense fine-grid cache.

Integer upsampling subdivides acquired voxel cells, preserving their full field.
Closest-RAS axes and acquired obliquity remain; coarse axes become <=1mm (header
tolerance 1e-5mm), while already finer axes are unchanged.
"""
from itertools import product
import numpy as np
from scipy import ndimage
from src.data.segmenter_native_windows_v1 import starts, blend_weight, extract

POLICY=dict(version='physical-detail-windows-1',maximum_spacing_mm=1.,spacing_tolerance_mm=1e-5,
            grid='integer_subdivision_of_native_voxel_cells',window=144,stride=72,
            image='linear_on_HU_windowed_CT',target='nearest',padding='high_side_zero',
            inference='full_CT_fine_grid_tiles_native_center_probability_blend',
            training='complete_lesion_cover_then_component_jitter_every_fourth_uniform_CT',
            empty_training='complete_pancreas_cover_then_one_anchor_every_fourth_uniform_CT')


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


def coverage_bank(mask, record, window=144):
    if mask.shape!=tuple(record['native_shape']) or not mask.any():raise ValueError('Coverage source')
    axes=[]
    for axis,(n,factor) in enumerate(zip(record['shape'],record['factors'])):
        support=np.flatnonzero(mask.any(axis=tuple(i for i in range(3) if i!=axis)))
        low=int(support[0])*factor;high=(int(support[-1])+1)*factor
        if high-low<=window:axes.append([int(np.clip((low+high-window)//2,0,max(0,n-window)))])
        else:axes.append(sorted(set(min(low+s,n-window) for s in starts(high-low,window,window))))
    return list(product(*axes))


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
