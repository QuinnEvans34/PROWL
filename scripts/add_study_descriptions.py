#!/usr/bin/env python3
"""Add a de-identified study description to each Workbench case in results.json.

Reads the dataset manifest (outputs/manifest.csv: `ct phase`, `sex`, `age`) and writes
`study = {phase, sex, age, source}` per case so the UI can show "CT abdomen · Arterial phase".
Display-only; blank fields are left out rather than guessed.

Usage:
  python3 scripts/add_study_descriptions.py --results ui/public/cases/results.json --manifest outputs/manifest.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def describe(row: dict) -> dict:
    study = {'source': 'PanTS'}
    phase = (row.get('ct phase') or '').strip()
    if phase:
        study['phase'] = phase
    sex = (row.get('sex') or '').strip().upper()
    if sex in {'M', 'F'}:
        study['sex'] = sex
    try:
        age = float(row.get('age') or '')
        if 0 < age < 120:
            study['age'] = round(age)
    except ValueError:
        pass
    return study


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    results = json.loads(args.results.read_text())
    with args.manifest.open(newline='') as handle:
        rows = {row['case_id']: row for row in csv.DictReader(handle) if row.get('case_id') in results}
    for case_id, entry in results.items():
        if case_id in rows:
            entry['study'] = describe(rows[case_id])
            print(case_id, entry['study'])
        else:
            print(case_id, 'not in manifest; left unchanged')
    args.results.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
