#!/usr/bin/env python3
"""Predict, separately score, or compare an explicitly pinned fixed development cohort."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.inference.fixed_cohort_evaluation import (
    read_pinned, validate_plan, run_predictions, score_predictions, compare_reports, write_new,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='stage', required=True)
    for stage in ('predict', 'score'):
        command = commands.add_parser(stage)
        command.add_argument('--plan', required=True)
        command.add_argument('--plan-sha256', required=True)
        if stage == 'predict':
            command.add_argument('--output-dir', required=True, help='Fresh output directory')
        else:
            command.add_argument('--journal', required=True)
            command.add_argument('--report', required=True, help='New JSON report; never overwrites')
    command = commands.add_parser('compare')
    command.add_argument('--baseline', required=True)
    command.add_argument('--baseline-sha256', required=True)
    command.add_argument('--candidate', required=True)
    command.add_argument('--candidate-sha256', required=True)
    command.add_argument('--report', required=True)
    args = parser.parse_args()
    if args.stage != 'predict' and Path(args.report).exists():
        parser.error('Report already exists; select a new path')
    if args.stage == 'compare':
        result = compare_reports(read_pinned(args.baseline, args.baseline_sha256),
                                 read_pinned(args.candidate, args.candidate_sha256))
        write_new(args.report, result)
    else:
        plan = validate_plan(read_pinned(args.plan, args.plan_sha256))
        if args.stage == 'predict':
            print(run_predictions(plan, args.plan_sha256, args.output_dir))
        else:
            write_new(args.report, score_predictions(plan, args.plan_sha256, args.journal))
    if args.stage != 'predict':
        print(Path(args.report).resolve())


if __name__ == '__main__':
    main()
