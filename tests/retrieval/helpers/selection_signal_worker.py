"""Synthetic process-fault worker. Not a production execution entrypoint."""
import json
import multiprocessing
from pathlib import Path
import signal
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from src.retrieval import resumable_selection as rs
from scripts.retrieval.select_pubmed_corpus import install_signal_handlers

def main():
    args=json.loads(Path(sys.argv[1]).read_text())
    marker=Path(sys.argv[2]); boundary=sys.argv[3]
    install_signal_handlers()

    def hold():
        marker.write_text(json.dumps({'children':[p.pid for p in multiprocessing.active_children()]}))
        while True:
            signal.pause()

    if boundary=='evaluation':
        original=rs.evaluate
        count=0
        def evaluate(*a,**kw):
            nonlocal count
            count+=1
            if count==3: hold()  # One committed row, one pending row.
            return original(*a,**kw)
        rs.evaluate=evaluate
    elif boundary=='export':
        original=rs.record_bytes
        count=0
        def record_bytes(*a):
            nonlocal count
            count+=1
            if count==2: hold()
            return original(*a)
        rs.record_bytes=record_bytes
    elif boundary=='publication':
        original=rs.os.replace
        def replace(src,dst):
            if Path(dst).name=='candidate-pmids.txt': hold()
            return original(src,dst)
        rs.os.replace=replace
    else:
        raise ValueError(boundary)
    # Batch interval 1 forces the first commit; the wrapper delays the second save.
    if boundary=='evaluation':
        original_save=rs.save
        count_save=0
        def save(db,cp):
            nonlocal count_save
            count_save+=1
            if count_save==2: hold()  # second row inserted; cursor uncommitted
            return original_save(db,cp)
        rs.save=save
    rs.run(**args)


if __name__ == "__main__":
    main()
