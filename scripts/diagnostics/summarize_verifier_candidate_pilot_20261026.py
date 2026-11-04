"""CPU-only measured budget projection; does not authorize full candidate export."""
import json,math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.segmenter_native_windows_v1 import tiles
from src.training.experiment_config import sha256
OUT=Path('E:/PROWL/readiness/verifier-candidate-pilot-20261026-a01')

def main():
    read=lambda p:json.loads(p.read_text())
    result=read(OUT/'result.json');resources=read(OUT/'resources.json');request=read(OUT/'request.json')
    if not result['passed'] or not resources['success'] or not resources['workers_reaped'] or resources['exit_code']!=0:
        raise ValueError('Pilot not complete/successful/reaped')
    rows=result['cases']
    if [r['case_id'] for r in rows]!=request['cases']:raise ValueError('Case accounting')
    if any(not r['baseline_exact'] or not r['archive_exact'] or r['gap_voxels'] or r['annotation_outside_region'] for r in rows):raise ValueError('Pilot quality')
    partitions=read(Path('E:/PROWL/readiness/verifier-generator-20261023-a01/partitions.json'))
    cache=Path('E:/PROWL/cache/varied-targets-20261022-a01');counts={}
    for role in ('verifier_fit','verifier_tune','verifier_calibration'):
        metadata=[read(cache/(n+'.json')) for n in partitions['roles'][role]]
        counts[role]=dict(patients=len(metadata),tiles=sum(len(tiles(m['record']['shape'])) for m in metadata),
            raw_prediction_bytes=sum(math.prod(m['geometry']['shape'])*5 for m in metadata))
    ratios=[r['artifact_bytes']/(request['estimates'][r['case_id']]['region_voxels']*5) for r in rows]
    raw=sum(r['raw_prediction_bytes'] for r in counts.values());totaltiles=sum(r['tiles'] for r in counts.values())
    actualcache=sum(p.stat().st_size for p in Path('E:/PROWL/cache').rglob('*') if p.is_file())
    actualbackup=sum(p.stat().st_size for p in Path('C:/Users/quinn/PROWL-Backups').rglob('*') if p.is_file())
    summary=dict(status='PILOT_ENGINEERING_PASS_FULL_STAGE_NOT_AUTHORIZED',
        result_sha256=sha256(OUT/'result.json'),request_sha256=sha256(OUT/'request.json'),
        roles=counts,pilot_seconds=resources['seconds'],peak_owned_rss_bytes=resources['peak_owned_rss_bytes'],
        peak_gpu_reserved=result['peak_gpu_reserved'],pilot_archive_bytes=sum(r['artifact_bytes'] for r in rows),
        pilot_candidates=sum(r['candidate_count'] for r in rows),pilot_true_candidates=sum(r['true_candidates'] for r in rows),
        pilot_false_candidates=sum(r['false_candidates'] for r in rows),
        full_raw_bytes=raw,compression_ratio_range=[min(ratios),max(ratios)],
        full_projected_compressed_bytes_range=[int(raw*min(ratios)),int(raw*max(ratios))],
        conservative_seconds_at_slowest_pilot_seconds_per_tile=totaltiles*max(r['seconds']/r['tiles'] for r in rows),
        timing_caveat='Pilot includes TWO inference passes plus labels/figures; full export will use one, but no measured single-pass full-stage duration exists.',
        storage_caveat='Compression range is descriptive, not a guarantee; use raw size plus overhead for caps.',
        existing_cache_bytes=actualcache,existing_backup_bytes=actualbackup,
        existing_cache_cap_bytes=32*1024**3,existing_backup_cap_bytes=27917287424,
        raw_plus_cache_bytes=raw+actualcache,raw_plus_backup_bytes=raw+actualbackup,
        proposed_full_stage=dict(seconds=16*3600,rss_bytes=12*1024**3,gpu_bytes=6*1024**3,
            combined_cache_and_prediction_cap_bytes=64*1024**3,combined_backup_cap_bytes=40*1024**3,
            free_disk_floor_bytes=100*1024**3,requires_explicit_budget_approval=True,
            optimizer_updates=0,development_cases=0,test_cases=0))
    with (OUT/'budget-review.json').open('x') as f:json.dump(summary,f,indent=2)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
