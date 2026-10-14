"""Connect a verified handoff and PANORAMA metadata to Windows, without training.

Publishes fresh candidate-only files. Does not create an accepted cohort review,
rehash CTs, copy old cache observations, or invoke a preparation/training worker.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.panorama_setup import classify
from src.training.experiment_config import load_experiment, preflight


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smoke_session(session):
    """A three-update setup run must not inherit a 500-step warmup."""
    return dict(session, warmup_steps=1, lr_horizon_steps=3)


def beneath(root, relative):
    # Refuse both Windows and POSIX traversal even when tested on a different OS.
    if not relative or '\\' in relative or ':' in relative or '..' in relative.split('/'):
        raise ValueError('Unsafe relative source path')
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root) or result == root or not result.is_file():
        raise ValueError('Missing/outside source path: '+relative)
    return result


def save_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False)+'\n')


def build(handoff, pants_ct, panorama, workbook_values, output):
    h, ctroot, p, out = [Path(v).resolve() for v in (handoff, pants_ct, panorama, output)]
    if out.exists():
        raise FileExistsError(out)
    # The workbook export is an intermediate, pinned back to the publisher workbook.
    workbook = json.loads(Path(workbook_values).read_text())
    workbook_path = Path(workbook['source']).resolve()
    if not workbook_path.is_relative_to(p):
        raise ValueError('Workbook outside selected source')
    if digest(workbook_path) != '2ae925de8067600db62e186a91844dec6555dab2b17cafd33b886b8c99f19ea7':
        raise ValueError('PANORAMA publisher workbook changed')
    headers, *values = workbook['values']
    if headers != ['PANORAMA_patient_id','PANORAMA_study_id','anonymized_study_date',
                   'patient_age','patient_sex','scanner','label','level'] or len(values) != 2238:
        raise ValueError('PANORAMA metadata schema/count changed')
    inventory = json.loads((h/'metadata/source-file-hashes.json').read_text())
    hashes = {(r['case_id'], r['kind']):r['sha256'] for r in inventory}
    if len(hashes) != len(inventory) or len(hashes) != 4224:
        raise ValueError('Incomplete/duplicate PanTS source inventory')
    with (h/'metadata/admitted-portable-manifest.csv').open(newline='') as stream:
        portable = list(csv.DictReader(stream))
    rows, observations = [], {}
    for r in portable:
        name = r['case_id']
        if not re.fullmatch(r'PanTS_\d{8}', name):
            raise ValueError('Invalid PanTS ID')
        paths = dict(ct=beneath(ctroot, r['ct_match_key']),
                     pancreas=beneath(h, r['pancreas_relative']), lesion=beneath(h, r['lesion_relative']))
        rows.append(dict(case_id=name, protected_role=r['protected_role'],
            **{k+'_path':str(v) for k,v in paths.items()},
            historical_has_lesion=str(r['target_state']=='positive'), target_state=r['target_state']))
        observations[name] = {k:dict(path=str(v), bytes=v.stat().st_size,
            modified_ns=v.stat().st_mtime_ns, inode=v.stat().st_ino, device=v.stat().st_dev,
            expected_sha256=hashes[(name,k)], current_bytes_hashed=False) for k,v in paths.items()}
    if len(rows) != 1408 or len({r['case_id'] for r in rows}) != 1408:
        raise ValueError('PanTS cohort mismatch')
    selected = {}
    for role, filename in [('train','train.txt'),('development','development.txt')]:
        selected[role] = (h/'splits/admitted'/filename).read_text().split()
        if [r['case_id'] for r in rows if r['protected_role']==role] != selected[role]:
            raise ValueError('Ordered PanTS membership mismatch')
    if [len(selected[k]) for k in ('train','development')] != [1333,75]:
        raise ValueError('Admitted cardinality changed')
    # Reconcile every transfer entry with its actual path/size; no payload hash claim.
    entries = [json.loads(line) for line in (p/'TRANSFER-SHA256.jsonl').read_text().splitlines()]
    images, labels, observed = {}, {}, set()
    for entry in entries:
        path = beneath(p, entry['path'])
        if path in observed or path.stat().st_size != entry['bytes']:
            raise ValueError('Duplicate or changed PANORAMA transfer entry')
        observed.add(path)
        if not path.name.endswith('.nii.gz'):
            continue
        is_ct = entry['path'].startswith('batch_')
        sid = path.name.removesuffix('_0000.nii.gz') if is_ct else path.name.removesuffix('.nii.gz')
        target = images if is_ct else labels
        if sid in target:
            raise ValueError('Duplicate PANORAMA study file')
        target[sid] = dict(path=str(path), expected_sha256=entry['sha256'], bytes=entry['bytes'])
        if not is_ct:
            membership = set(path.parts) & {'manual_labels','automatic_labels'}
            if len(membership) != 1:
                raise ValueError('Unknown label directory provenance')
            target[sid]['method'] = 'human_manual' if 'manual_labels' in membership else 'machine_generated'
    records = []
    for value in values:
        r = dict(zip(headers,value))
        sid, subject = r['PANORAMA_study_id'], r['PANORAMA_patient_id']
        # Numeric patient IDs are exact integer identifiers, never float-string IDs.
        if isinstance(subject, (float,int)) and not isinstance(subject,bool) and int(subject)==subject:
            subject=str(int(subject))
        if not isinstance(sid,str) or sid not in images or sid not in labels:
            raise ValueError('Metadata/CT/label join failed')
        record = classify(sid,subject,r['label'],r['level'],labels[sid]['method'])
        record.update(ct=images[sid], label=labels[sid], metadata_row=len(records)+2,
            metadata_workbook_sha256=digest(workbook_path),
            pending=['local_content_and_geometry','machine_pancreas_visual_review',
                     'exact_and_calibrated_approximate_duplicates','frozen_subject_grouped_cohort'])
        records.append(record)
    names = [r['publisher_study_id'] for r in records]
    if len(names)!=len(set(names)) or set(names)!=set(images) or set(names)!=set(labels):
        raise ValueError('Incomplete/duplicate/orphan PANORAMA join')
    counts = Counter(r['disposition'] for r in records)
    expected = dict(excluded_declared_import=274, quarantined_manual_non_pdac=3,
                    not_generic_lesion_supervision=1383,
                    expert_pdac_candidate_pending_qc_and_duplicates=382,
                    optional_machine_pdac_candidate_not_primary=196)
    if dict(counts) != expected or len({r['subject_id'] for r in records}) != 2224:
        raise ValueError('PANORAMA source populations changed')
    out.mkdir(parents=True)
    with (out/'pants-manifest.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    spec=yaml.safe_load((h/'configs/mac-original.yaml').read_text())
    spec['name']='pants_setup_20261010'
    spec['base_config']=str(ROOT/'configs/level45.yaml')
    spec['recipe']['device']='cuda'
    spec['recipe']['full_segmenter'].update(output_dir='E:/PROWL/artifacts/pants_setup_20261010',
        cache_dir='E:/PROWL/cache/pants-setup-20261010',backup_dir='C:/Users/quinn/PROWL-Backups',
        backup_cap_bytes=26*1024**3)
    spec['recipe']['full_segmenter']['session']=smoke_session(spec['recipe']['full_segmenter']['session'])
    spec['run']=dict(max_updates=3,validate_every=3,checkpoint_every=1,log_every=1,
                     cache='disk',max_seconds=600,min_free_bytes=100*1024**3)
    spec['cohort']=dict(manifest=str(out/'pants-manifest.csv'),train_ids=str(h/'splits/admitted/train.txt'),
        development_ids=str(h/'splits/admitted/development.txt'),original_train_ids=str(h/'splits/original/train.txt'),
        original_development_ids=str(h/'splits/original/val.txt'),test_ids=str(h/'splits/original/test.txt'),review=None)
    spec['initialization'].update(checkpoint=str(h/'weights/supervised_suprem_segresnet_2100.pth'),
        source_review=str(h/'metadata/suprem-development-source-review.json'))
    candidate=out/'pants-candidate.yaml'
    with candidate.open('x') as stream:yaml.safe_dump(spec,stream,sort_keys=False)
    report=preflight(load_experiment(candidate),inspect_payload_paths=True,source_review_mode='development_use')
    if report['errors'] != ['Current cohort/label review is pending']:
        save_json(out/'unexpected-preflight.json',report)
        raise ValueError('Unexpected preflight issues: '+str(report['errors']))
    save_json(out/'pants-preflight.json',report)
    save_json(out/'pants-source-observations.json',observations)
    with (out/'panorama-candidates.jsonl').open('x') as stream:
        for r in records:stream.write(json.dumps(r,allow_nan=False)+'\n')
    save_json(out/'paths.json',dict(schema='windows-data-setup-v1',scientific_runs_enabled=False,
        pants_ct=str(ctroot),pants_labels=str(h/'labels'),panorama_source=str(p),
        pretrained_weights=spec['initialization']['checkpoint'],
        pants_candidate_config=str(candidate),panorama_catalog=str(out/'panorama-candidates.jsonl'),
        note='Setup-only explicit paths; not the legacy APFS storage registry or training admission'))
    summary=dict(scope='local_paths_and_candidate_catalog_only',pants_train=1333,pants_development=75,
        pants_preflight_expected_block=report['errors'],panorama_studies=len(records),
        panorama_subjects=2224,panorama_dispositions=dict(counts),source_workbook=workbook['source'],
        source_sheet=workbook['sheet'],full_content_qualified=False,training_started=False,
        CT_payloads_read=0,prepared_cache_exists=False,
        pins={str(x):digest(x) for x in [h/'SHA256SUMS.json',h/'metadata/source-file-hashes.json',
            p/'TRANSFER-SHA256.jsonl',Path(workbook_values),workbook_path,candidate]})
    save_json(out/'summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('handoff','pants-ct','panorama','workbook-values','output'):
        parser.add_argument('--'+name,required=True)
    print(json.dumps(build(**vars(parser.parse_args())),indent=2))
