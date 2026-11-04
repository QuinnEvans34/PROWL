"""Preserve voxel occupancy on upsampling and tiny support on downsampling."""
import numpy as np
from scipy import ndimage
from src.data.verifier_views_20261031 import make_views as original, POLICY as ORIGINAL_POLICY
POLICY=dict(ORIGINAL_POLICY,version='verifier-two-view-20261031-v2',
    support='nearest_neighbor_voxel_occupancy_plus_conservative_center_splat')

def make_views(image,probability,component_map,component_id,affine,*,size=64):
    stored,meta=original(image,probability,component_map,component_id,affine,size=size)
    support=(component_map==component_id).astype(np.uint8)
    for i,key in enumerate(('global_view','detail_view')):
        m=meta[key];low=np.asarray(m['low_voxel_edges']);step=np.asarray(m['step_voxels'])
        grid=np.stack(np.meshgrid(*(low[k]-.5+(np.arange(size)+.5)*step[k] for k in range(3)),indexing='ij'))
        occupancy=ndimage.map_coordinates(support,grid,order=0,mode='constant',cval=0,prefilter=False)
        stored[i,2]=np.maximum(stored[i,2],occupancy)
        m['support_output_voxels']=int(stored[i,2].sum())
        m['support_method']=POLICY['support']
    return stored,meta
