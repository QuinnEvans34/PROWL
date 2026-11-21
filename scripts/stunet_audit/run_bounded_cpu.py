"""Use the retained Mac supervisor for a fresh audit worker, never a training launcher."""
import argparse
import os
from pathlib import Path
import sys

from src.operations.mac_pilot_supervision_v1 import run

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=int, default=180)
    p.add_argument("command", nargs=argparse.REMAINDER)
    a = p.parse_args()
    assert 0 < a.seconds <= 300 and a.command
    a.output.mkdir(exist_ok=False)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="-1", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2")
    ok = run(a.command, a.output, seconds=a.seconds, rss_bytes=8*1024**3, env=env)
    sys.exit(0 if ok else 1)
