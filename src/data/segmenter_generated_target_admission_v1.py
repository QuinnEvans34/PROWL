"""Validate finished teacher payloads against the actual corrected input provider.

No inference, training, copying or launch authority. Returns a manifest only after
all members pass. The caller must publish it separately without changing producer
artifacts. Partial inputs are permitted only for explicitly marked qualification.
"""
from pathlib import Path
import math
import numpy as np
from src.data.manifest_records import canonical, digest
from src.data.segmenter_teacher_cache_v1 import (
    SCHEMA, QUANTIZATION_ERROR, identity_for, sha,
)


def admit(root, request, result, resources, provider, *, qualification_only=False):
    train = list(provider.control['train'])
    if (len(train) != len(set(train)) or set(train) & set(provider.control['validation'])
            or request['train'] != train):
        raise ValueError('Producer/provider training membership differs')
    if provider.pin != digest(canonical(provider.control)):
        raise ValueError('Provider identity changed')
    members = result['members']
    if not members or not set(members) <= set(train):
        raise ValueError('Empty or protected teacher membership')
    if not qualification_only and (
        result.get('success') is not True or result.get('complete') is not True
        or set(members) != set(train) or resources.get('success') is not True
        or resources.get('workers_reaped') is not True or resources.get('exit_code') != 0
    ):
        raise ValueError('Complete, successfully reaped target generation required')
    teacher = request['teacher']
    common = dict(teacher_sha256=teacher['weights']['sha256'],
        teacher_config_sha256=digest(canonical(teacher['config'])),
        teacher_mapping_sha256=digest(canonical(teacher['labels'])),
        preprocessing_sha256=digest(canonical(request['preprocessing_policy'])),
        control_sha256=provider.pin)
    admitted = {}
    for name, row in members.items():
        _, small = provider.cache_member(name)
        identity = identity_for(name, small, common)  # also rejects unsafe names
        if (row['case_id'] != name or row['source_ct_sha256'] != small['source_sha256']['ct']
                or row['native_geometry'] != small['geometry']):
            raise ValueError('Generated target source/grid mismatch')
        mapping = row['reconstruction']; voxels = math.prod(small['geometry']['shape'])
        if (mapping['method'] != 'RAS_world_linear_slabbed'
                or mapping['native_voxels'] != voxels
                or mapping['covered_voxels'] != voxels or mapping['out_of_field_voxels'] != 0):
            raise ValueError('Incomplete teacher reconstruction coverage')
        path = Path(root)/(name+'.npz')
        if path.stat().st_size != row['bytes'] or sha(path) != row['payload_sha256']:
            raise ValueError('Generated payload changed')
        with np.load(path, allow_pickle=False) as data:
            if data.files != ['probability']:
                raise ValueError('Unexpected probability payload')
            values = data['probability']
            if values.dtype != np.uint16 or list(values.shape) != small['geometry']['shape']:
                raise ValueError('Generated payload shape/type mismatch')
        admitted[name] = dict(schema=SCHEMA, identity=identity,
            shape=list(values.shape), storage='uint16_probability_round_to_nearest_div65535',
            support='entire_native_region', payload_sha256=row['payload_sha256'],
            bytes=row['bytes'], max_quantization_error=float(QUANTIZATION_ERROR))
        del values
    return dict(schema=SCHEMA, control_sha256=provider.pin, members=admitted,
        complete=not qualification_only, qualification_only=qualification_only,
        producer_request_sha256=digest(canonical(request)),
        producer_result_sha256=digest(canonical(result)),
        producer_resources_sha256=digest(canonical(resources))), common
