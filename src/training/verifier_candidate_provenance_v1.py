"""Three reserved roles with checkpoint-bound, empirical generator exposure."""
from src.data.verifier_candidate_inputs_v1 import partition_roles

def validate_records(records, partition, *, checkpoint_sha256, receipt_sha256,
                     actual_generator_ids, required_ids):
    roles=partition_roles(partition)
    if set(actual_generator_ids)!=set(partition['roles']['generator_train']):
        raise ValueError('Actual generator exposure differs from frozen partition')
    wanted=set(required_ids)
    if not wanted or not wanted<=set(roles):raise ValueError('Invalid candidate scope')
    seen=set()
    for r in records:
        n=r['case_id']
        if n in seen or n not in wanted or r['role']!=roles[n]:raise ValueError('Duplicate/misassigned candidate patient')
        seen.add(n)
        if r['checkpoint_sha256']!=checkpoint_sha256 or r['generator_receipt_sha256']!=receipt_sha256:
            raise ValueError('Generator identity changed')
        for key in ('prediction_sha256','ct_sha256','pancreas_sha256'):
            h=r[key]
            if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Missing identity')
        if r['gap_voxels']!=0 or r['candidate_count']<0:raise ValueError('Incomplete prediction')
    if seen!=wanted:raise ValueError('Missing patient, including empty predictions')
    return True
