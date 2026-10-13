"""Owned descriptors and real SQLite spill: synthetic files only."""
import os
import sqlite3
import tempfile
import pytest
from src.retrieval import resumable_selection as rs


def test_unlinked_bytes_counted_once_and_cap_enforced(tmp_path):
    before=rs.unlinked_file_bytes(tmp_path.stat().st_dev)
    with tempfile.TemporaryFile(dir=tmp_path) as stream:
        stream.write(b'x'*8192);stream.flush()
        duplicate=os.dup(stream.fileno())
        try:
            assert rs.unlinked_file_bytes(tmp_path.stat().st_dev)==before+8192
            with pytest.raises(OSError,match='directory budget'):
                rs.SelectionBudget(tmp_path,max_gib=4096/1024**3,free_gib=0)
        finally:
            os.close(duplicate)


def test_actual_sqlite_spill_observed(tmp_path):
    budget=rs.SelectionBudget(tmp_path,max_gib=1,free_gib=0)
    db=sqlite3.connect(tmp_path/'spill.sqlite')
    prior=db.execute('PRAGMA temp_store_directory').fetchone()
    try:
        escaped=str(tmp_path).replace("'","''")
        db.execute(f"PRAGMA temp_store_directory='{escaped}'")
        db.execute('PRAGMA temp_store=FILE');db.execute('PRAGMA cache_size=-1024')
        db.execute('PRAGMA threads=0')
        db.execute('CREATE TABLE invented(k TEXT)')
        db.executemany('INSERT INTO invented VALUES (?)',((str(20000-i).zfill(8)+'x'*2048,) for i in range(20000)))
        db.commit()
        def check():
            budget.check(force=True);return 0
        db.set_progress_handler(check,5000)
        db.execute('CREATE INDEX ordered ON invented(k)');db.commit()
        assert budget.peak_unlinked_bytes>0
        assert budget.peak_accounted_bytes>=budget.peak_unlinked_bytes
    finally:
        db.set_progress_handler(None,0)
        old=(prior[0] if prior else '').replace("'","''")
        db.execute(f"PRAGMA temp_store_directory='{old}'")
        db.close()
