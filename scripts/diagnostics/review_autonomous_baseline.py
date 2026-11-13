"""Admit a hash-bound saved metadata export; never load models or images."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.operations.autonomous_baseline_review_v1 import read_bound, review, markdown


def unit_dispositions(result):
    groups = {}
    for key, assumed in (("declared_mm", False), ("assumed_mm", True)):
        cases = [row for row in result["cases"] if row["physical_units_assumed"] is assumed]
        positive = [row for row in cases if row["positive"]]
        empty = [row for row in cases if not row["positive"]]
        groups[key] = dict(completed=len(cases), positive=len(positive), reference_empty=len(empty),
                           positive_with_overlap=sum(row["any_overlap"] for row in positive),
                           reference_empty_with_alarm=sum(row["empty_alarm"] for row in empty))
    return dict(requested=result["aggregate"]["requested"], completed_by_reference_units=groups,
                failures_by_case=result["failures"], scope="saved_exposed_development_dispositions")


def run(source, output, *, sha256, request_sha256, ready_sha256):
    document = read_bound(source, sha256)
    result = review(document, request_sha256=request_sha256, ready_sha256=ready_sha256)
    result["export_sha256"] = sha256
    rendered = markdown(result)
    # Validate everything before creating evidence; never overwrite prior attempts.
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    (out / "review.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (out / "review.md").write_text(rendered)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--ready-sha256", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output")
    mode.add_argument("--unit-dispositions", action="store_true", help="Print unit and failure counts from saved metadata")
    args = parser.parse_args()
    if args.unit_dispositions:
        document = read_bound(args.source, args.sha256)
        result = review(document, request_sha256=args.request_sha256, ready_sha256=args.ready_sha256)
        print(json.dumps(unit_dispositions(result), indent=2, allow_nan=False))
    else:
        result = run(args.source, args.output, sha256=args.sha256,
                     request_sha256=args.request_sha256, ready_sha256=args.ready_sha256)
        print(json.dumps(result["aggregate"], allow_nan=False))
