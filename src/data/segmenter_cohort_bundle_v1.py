"""Metadata-only cohort derivation; the disk adapter must first replay D-319."""
from src.data.cohort_records_v3 import build_cohort as build_parent
from src.data.segmenter_cohort_v1 import build_cohort, checked_members, validate_pair
from src.data.segmenter_qualification_v1 import POLICY_SHA256, PURPOSES
from src.data.source_inventory_records import content_hash, require


def context_for(derived, bases, parents=()):
    return dict(manifest=derived['manifest'], trusted_manifest_sha256=content_hash(derived['manifest']),
        trusted_policy_sha256=POLICY_SHA256, base_membership_bytes=bases,
        evidence_by_sha256={h:b.encode() for h,b in derived['evidence'].items()},
        trusted_evidence_sha256=set(derived['evidence']),
        qualifications_by_id={q['qualification_id']:q for q in derived['qualifications']},
        trusted_qualification_sha256={q['qualification_id']:content_hash(q) for q in derived['qualifications']},
        cohorts_by_id={p['cohort_id']:p for p in parents},
        trusted_cohort_sha256={p['cohort_id']:content_hash(p) for p in parents})


def freeze(derived, bases, expected_members, *, family):
    require(set(expected_members)=={'train','validation'}, 'Exact two-role selection required')
    ctx=context_for(derived,bases); parents=[]; children=[]
    for role in ('train','validation'):
        ids=[p['study_id'] for p in derived['manifest']['protection'] if p['protected_role']==role]
        parent=build_parent(cohort_id=f'cohort:{family}-protection-{role}:v1',cohort_family_id=family,
            capability='protection_only',protected_role=role,study_ids=ids,requested_count=len(ids),parent_ids=[],context=ctx)
        parents.append(parent);ctx['cohorts_by_id'][parent['cohort_id']]=parent
        ctx['trusted_cohort_sha256'][parent['cohort_id']]=content_hash(parent)
        purpose=next(p for p,(r,_) in PURPOSES.items() if r==role)
        children.append(build_cohort(name=family+'-'+role,study_ids=expected_members[role],
            requested_count=len(expected_members[role]),purpose=purpose,parent_id=parent['cohort_id'],context=ctx))
    result=dict(parents=parents,cohorts=children)
    resolve(derived,bases,result,expected_members)
    return result


def resolve(derived,bases,bundle,expected_members):
    require(set(bundle)=={'parents','cohorts'} and len(bundle['parents'])==len(bundle['cohorts'])==2,
        'Exact parent/child inventory required')
    parents=bundle['parents']; children=bundle['cohorts']
    require([p['protected_role'] for p in parents]==['train','validation'] and
        [c['protected_role'] for c in children]==['train','validation'], 'Canonical role order required')
    ctx=context_for(derived,bases,parents)
    for c in children:
        require([m['study_id'] for m in c['members']]==sorted(expected_members[c['protected_role']]),
            'Missing/extra or substituted fixed membership')
    report=validate_pair(*children,trusted_train_sha256=content_hash(children[0]),
        trusted_validation_sha256=content_hash(children[1]),**ctx)
    descriptors={op:checked_members(c,trusted_record_sha256=content_hash(c),operation=op,**ctx)
        for op,c in zip(('optimizer','evaluator'),children)}
    return report,descriptors
