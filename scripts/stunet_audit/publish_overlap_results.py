"""Publish only completed saved evidence; cannot run image readers or issue CLEAR."""
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-audit-20261106')
DOCS=Path('docs/stunet_audit')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    pipeline=ROOT/'reference-pipeline-02'
    if json.loads((pipeline/'result.json').read_text())['status'] not in ('COMPLETE','COMPLETE_WITH_DECLARED_BLOCKERS'):raise ValueError('Incomplete audit evidence')
    snapshot=json.loads((ROOT/'source-evidence-snapshot.json').read_text())
    for name,pin in snapshot['source_pins'].items():
        if digest(name)!=pin:raise ValueError('Retained source evidence changed')
    summary_path=ROOT/'reference-comparison-02/summary.json'
    summary=json.loads(summary_path.read_text())
    candidates_path=ROOT/'reference-comparison-02/candidates.json'
    results=json.loads(candidates_path.read_text())
    request_path=pipeline/'reference-request.json';request=json.loads(request_path.read_text())
    if len(results)!=75 or len({r['case_id'] for r in results})!=75:raise ValueError('Development accounting differs')
    if summary['reference_count']!=1204 or summary['query_count']!=75:raise ValueError('Reference scope differs')
    cohort=json.loads(Path('outputs/prowl/portable-cohort-20261012/cohort.json').read_text())
    dev={m['case_id']:m for m in cohort['members'] if m['role']=='validation'}
    if set(dev)!={r['case_id'] for r in results}:raise ValueError('Development membership differs')
    source={r['case_id']:r for r in csv.DictReader((DOCS/'source_provenance.csv').open())}
    splits={r['reference_id']:r for r in json.loads((pipeline/'verified-reference-splits.json').read_text())['rows']}
    excluded={'PanTS_00000922','PanTS_00005105','PanTS_00005370','PanTS_00007299','PanTS_00007523'}
    queries={q['case_id']:q for q in request['queries']};rows=[]
    for result in sorted(results,key=lambda r:r['case_id']):
        case=result['case_id'];candidates=result['candidates'];exact=result['exact_file_matches_all_references']
        canonical=[r['reference_id'] for r in candidates if r['match_type']=='CANONICAL_VOXEL_EQUAL']
        confirmed=sorted(set(exact)|set(canonical))
        basel='Basel' in source[case]['site_detail']
        classification='CONFIRMED_OVERLAP' if confirmed else ('SUSPECTED_OVERLAP' if basel else 'UNRESOLVED')
        top=candidates[0] if candidates else {}
        rows.append(dict(case_id=case,role='development',kd_scoring_subset=case not in excluded,
            reference_state=dev[case]['reference_state'],site_detail=source[case]['site_detail'],basel_source_flag=basel,
            query_file_sha256=queries[case]['sha256'],file_hash_matches=';'.join(exact),canonical_voxel_matches=';'.join(canonical),
            matched_publisher_partitions=';'.join(f"{r}:{splits[r]['publisher_split']}" for r in confirmed),
            top_reference=top.get('reference_id',''),top_similarity=top.get('similarity',''),
            ranked_candidates_json=json.dumps(candidates,separators=(',',':')),
            comparison_scope='Original TotalSegmentator v1 reference pool',reference_file_hashes=summary['verified_reference_file_hashes'],blocked_reference_ids=';'.join(r['case_id'] for r in summary['blocked_references']),
            reference_appearance_fingerprints=summary['references_fingerprinted'],
            exact_checkpoint_gradient_membership='NOT_VERIFIED',exact_checkpoint_selection_membership='NOT_VERIFIED',
            original_patient_crosswalk='NOT_ESTABLISHED',classification=classification,clearance_issued=False,
            recommended_action='Preserve case; separate exposed/uncertain development claims; resolve checkpoint/patient provenance before independent evaluation'))
    with (DOCS/'overlap_results.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    evidence=dict(schema='prowl.stunet.overlap-result.v1',status='COMPLETE_WITH_DECLARED_LIMITATIONS',
        development_cases=75,classifications=dict(Counter(r['classification'] for r in rows)),
        confirmed_image_cases=[{k:r[k] for k in ('case_id','file_hash_matches','canonical_voxel_matches','matched_publisher_partitions')} for r in rows if r['classification']=='CONFIRMED_OVERLAP'],
        source_institution_flagged_development=sum('Basel' in r['site_detail'] and r['role']=='validation' for r in source.values()),source_institution_flagged_train=sum('Basel' in r['site_detail'] and r['role']=='train' for r in source.values()),training_images_compared=0,
        reference_summary=summary,reference_summary_sha256=digest(summary_path),candidates_sha256=digest(candidates_path),
        reference_request_sha256=digest(request_path),cohort_sha256=digest('outputs/prowl/portable-cohort-20261012/cohort.json'),
        source_metadata_sha256=digest(DOCS/'source_provenance.csv'),csv_sha256=digest(DOCS/'overlap_results.csv'),
        patient_independence_verified=False,protected_prowl_test_images_compared=0,clinical_model_forwards=0,optimizer_updates=0,
        caveat='No match does not establish patient independence; reference-pool overlap is distinct from exact binary gradient/selection membership')
    with (DOCS/'overlap_summary.json').open('x') as f:json.dump(evidence,f,indent=2)
    print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
