"""Apply the fixed endpoint rule to two complete native development reports."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))


def main():
    from src.training.pants_native_evaluation import paired_decision
    from src.training.experiment_config import sha256
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--early',type=Path,required=True);p.add_argument('--final',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    early=json.loads(a.early.read_text());final=json.loads(a.final.read_text())
    assert early['step']==8000 and final['step']==24000,'Wrong fixed checkpoints'
    for key in ('identity_sha256','scope','detection_rule','prediction_rule'):
        assert early[key]==final[key], 'Different evaluation/recipe identities'
    assert early['complete_development_cohort'] and final['complete_development_cohort']
    assert len(early['cases'])==len(final['cases'])==75
    result=paired_decision(early['cases'],final['cases'])
    result['evidence_sha256']={str(a.early):sha256(a.early),str(a.final):sha256(a.final)}
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')


if __name__=='__main__':main()
