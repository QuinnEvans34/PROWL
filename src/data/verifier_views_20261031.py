"""Prediction-defined two-view intake; no ground truth is accepted by this API."""
import numpy as np
from scipy import ndimage

POLICY=dict(version='verifier-two-view-20261031',size=64,context_mm=10.,detail_spacing_mm=1.,
    channels=['windowed_CT','lesion_probability','candidate_support','valid_CT'],
    global_view='complete_component_plus_10mm_physical_cube',detail_view='64mm_cube_at_candidate_probability_maximum',
    support='conservative_native_voxel_center_splat',probability='linear_plus_candidate_max_splat',
    storage='float16_checked_against_float32',hu_window=[-100,250])

def view(image,probability,coordinates,spacing,center,side_mm,size=64):
    if image.shape!=probability.shape or image.ndim!=3 or not np.isfinite(image).all() or not np.isfinite(probability).all():raise ValueError('Invalid aligned inputs')
    spacing=np.asarray(spacing,float);center=np.asarray(center,float);coords=np.asarray(coordinates,int)
    if coords.ndim!=2 or coords.shape[1]!=3 or not len(coords) or (spacing<=0).any() or side_mm<=0:raise ValueError('Invalid component/view')
    if (coords<0).any() or (coords>=np.asarray(image.shape)).any():raise ValueError('Component outside source')
    step=side_mm/(size*spacing);low=center+.5-side_mm/(2*spacing)
    axes=[low[i]-.5+(np.arange(size)+.5)*step[i] for i in range(3)]
    grid=np.stack(np.meshgrid(*axes,indexing='ij'))
    ct=ndimage.map_coordinates(image,grid,order=1,mode='constant',cval=0,prefilter=False)
    prob=ndimage.map_coordinates(probability,grid,order=1,mode='constant',cval=0,prefilter=False)
    valid=np.all((grid>=0)&(grid<=(np.asarray(image.shape)-1)[:,None,None,None]),axis=0)
    mapped=np.floor((coords+.5-low)/step).astype(int);inside=np.all((mapped>=0)&(mapped<size),axis=1)
    selected=mapped[inside];support=np.zeros((size,)*3,np.float32)
    if len(selected):
        idx=tuple(selected.T);support[idx]=1
        np.maximum.at(prob,idx,probability[tuple(coords[inside].T)])
    result=np.stack([ct,prob,support,valid.astype(np.float32)]).astype(np.float32)
    return result,dict(low_voxel_edges=low.tolist(),step_voxels=step.tolist(),spacing_mm=[side_mm/size]*3,
        source_component_voxels=len(coords),represented_source_voxels=int(inside.sum()),support_output_voxels=int(support.sum()),
        valid_fraction=float(valid.mean()),size=size)

def make_views(image,probability,component_map,component_id,affine,*,size=64):
    if component_map.shape!=image.shape:raise ValueError('Component alignment')
    coords=np.argwhere(component_map==component_id)
    if component_id<=0 or not len(coords):raise ValueError('Empty candidate')
    spacing=np.linalg.norm(np.asarray(affine)[:3,:3],axis=0)
    low,high=coords.min(0),coords.max(0)+1;center=(low+high-1)/2
    side=float(np.max((high-low)*spacing)+2*POLICY['context_mm'])
    global_view,g=view(image,probability,coords,spacing,center,side,size)
    if g['represented_source_voxels']!=len(coords):raise ValueError('Global component clipped')
    anchor=coords[np.argmax(probability[tuple(coords.T)])]
    local_view,l=view(image,probability,coords,spacing,anchor,64.,size)
    arrays=np.stack([global_view,local_view]);stored=arrays.astype(np.float16)
    error=float(np.max(np.abs(stored.astype(np.float32)-arrays)))
    if error>0.00025 or not np.isfinite(stored).all() or not np.array_equal(stored[:,2:],arrays[:,2:]):
        raise ValueError('Storage precision')
    return stored,dict(global_view=g,detail_view=l,detail_anchor=anchor.tolist(),storage_max_abs_error=error,
        complete_component_coverage=True,detail_is_partial_context=l['represented_source_voxels']!=len(coords))
