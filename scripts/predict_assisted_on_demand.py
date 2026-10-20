"""Operator-pinned worker entry point, invoked by the bounded local supervisor."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.inference.assisted_prediction import run

if __name__=='__main__':
    run(json.loads(Path(sys.argv[1]).read_bytes()),Path(sys.argv[2]))
