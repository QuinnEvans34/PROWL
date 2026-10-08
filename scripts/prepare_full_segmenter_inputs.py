#!/usr/bin/env python3
"""Map a selected cohort to the mounted extraction without decoding patient payloads.

Historical lesion flags are retained as evidence, never promoted to negative-label acceptance.
The output is a candidate manifest, not a scientific cohort acceptance certificate.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_ids(path):
    values = Path(path).read_text().split()
    if not values or len(set(values)) != len(values):
        raise ValueError(f"Empty/duplicate IDs: {path}")
    return values


def prepare(root, historical, train, development, original_train, original_dev, test, output):
    root, output = Path(root).resolve(), Path(output)
    groups = {k: read_ids(v) for k, v in dict(train=train, development=development,
        original_train=original_train, original_dev=original_dev, test=test).items()}
    if not set(groups['train']) <= set(groups['original_train']):
        raise ValueError('Training selection outside original training split')
    if not set(groups['development']) <= set(groups['original_dev']):
        raise ValueError('Development selection outside original development split')
    if set(groups['train']) & set(groups['development']) or (
            set(groups['train']) | set(groups['development'])) & set(groups['test']):
        raise ValueError('Protected role overlap')
    with Path(historical).open(newline='') as stream:
        historical_rows = list(csv.DictReader(stream))
    rows = {r['case_id']: r for r in historical_rows}
    if len(rows) != len(historical_rows):
        raise ValueError('Duplicate historical manifest IDs')
    records, missing = [], []
    for role in ('train', 'development'):
        for name in groups[role]:
            number = int(name.removeprefix('PanTS_'))
            if name != f'PanTS_{number:08d}' or not 1 <= number <= 9000:
                raise ValueError(f'Not a training/development source case: {name}')
            start = ((number - 1) // 1000) * 1000 + 1
            image = root / f'PanTSMini_ImageTr_{start:08d}_{start+999:08d}' / name / 'ct.nii.gz'
            labels = root / 'PanTSMini_Label' / name / 'segmentations'
            old = rows[name]
            record = dict(case_id=name, protected_role=role, ct_path=str(image),
                pancreas_path=str(labels / 'pancreas.nii.gz'),
                lesion_path=str(labels / 'pancreatic_lesion.nii.gz'),
                historical_has_lesion=old['has_lesion'], target_state='unreviewed')
            for column in ('ct_path', 'pancreas_path', 'lesion_path'):
                path = Path(record[column])
                if not path.is_file(): missing.append(dict(case_id=name, column=column, path=str(path)))
            records.append(record)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'manifest.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    for role in ('train', 'development'):
        (output / f'{role}.txt').write_text('\n'.join(groups[role]) + '\n')
    report = dict(state='candidate_paths_checked_not_label_qualified', source_root=str(root),
        training_cases=len(groups['train']), development_cases=len(groups['development']),
        missing=missing, payloads_decoded=0, historical_manifest_sha256=
        hashlib.sha256(Path(historical).read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256((output / 'manifest.csv').read_bytes()).hexdigest())
    (output / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('root', 'historical', 'train', 'development', 'original-train', 'original-dev', 'test', 'output'):
        parser.add_argument('--' + field, required=True)
    args = vars(parser.parse_args())
    result = prepare(**args)
    print(json.dumps(result, indent=2))
