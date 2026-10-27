"""Engineering-only four-update executor exercise, with injectable CPU test dependencies."""
import json
import os
from pathlib import Path
import shutil
import torch
from src.operations.kd_gpu_qualification_v1 import write, LIMITS
from src.data.segmenter_teacher_cache_v1 import sha
from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
from src.training.segmenter_errata_kd_session_v1 import ErrataKDSession
from src.training.segmenter_kd_evidence_executor_v1 import execute, journal_value


def usage(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


class EngineeringHorizon:
    """Bound executor iterations only; preserve the student's 24k recipe/state."""
    def __init__(self, session):
        self.session = session
        self.config = dict(session.config, max_steps=4)
    def __getattr__(self, name):
        return getattr(self.session, name)



def exercise(root, stage, request, *, inputs, targets, student, kd, tick, compare, evaluate, backup_admission):
    destination = Path(root)/stage
    def save(path, value):
        with path.open('xb') as stream:
            torch.save(value, stream); stream.flush(); os.fsync(stream.fileno())
    rows = []
    if stage in ('reference','zero'):
        session = student() if stage == 'reference' else kd(0)
        for _ in range(4):
            tick(); row = session.update(inputs); tick(); rows.append(journal_value(row))
            if stage == 'zero' and row['teacher_accessed']:
                raise ValueError('Zero-KD accessed teacher')
        state = session.state() if stage == 'reference' else session.student.state()
        save(destination/'state.pt', state)
        if stage == 'zero':
            compare(state, torch.load(root/'reference/state.pt', weights_only=True, map_location='cpu'))
            reference = json.loads((root/'reference/updates.json').read_text())
            for a,b in zip(reference, rows):
                if any(a[key] != b[key] for key in ('batch_sha256','input_view','member_id','learning_rate')):
                    raise ValueError('Zero-KD input trace differs')
    elif stage == 'producer':
        session = kd(.1)
        bound = BoundDistillationSession(session, targets)
        backup = Path(request['backup']); backup.mkdir()
        copies = {}
        def preserve(path):
            tick()
            target = backup / f'{session.step:06d}-{path.name}'
            size = path.stat().st_size; backup_admission(size)
            if usage(backup)+size > LIMITS['backup_bytes']:
                raise ValueError('Qualification backup cap')
            with path.open('rb') as source, target.open('xb') as dest:
                shutil.copyfileobj(source,dest);dest.flush();os.fsync(dest.fileno())
            fd = os.open(backup, os.O_RDONLY)
            try: os.fsync(fd)
            finally: os.close(fd)
            if sha(path) != sha(target): raise ValueError('Independent backup mismatch')
            copies[str(target)] = sha(target)
        def native(s,p,name,progress):
            row = evaluate(s,p,name,progress)
            positive = row['metrics']['lesion']['target_voxels'] > 0
            if positive != (name == request['development']['positive']):
                raise ValueError('Expected positive/empty development role differs')
            return row
        def track(row):
            if row['event']=='update':
                if not row['teacher_accessed'] or row['kd_weight'] <= 0:
                    raise ValueError('Positive KD path not exercised')
                rows.append(row)
        execute(EngineeringHorizon(bound), inputs, destination/'execution',
                validate_every=4,checkpoint_every=1,tick=tick,checkpoint_hook=preserve,
                evaluator=native,validation_names=list(request['development'].values()),track=track)
        if not any(row['eligible_voxels'] > 0 for row in rows):
            raise ValueError('No eligible teacher supervision')
        reference = json.loads((root/'reference/updates.json').read_text())
        for a,b in zip(reference,rows):
            if any(a[k]!=b[k] for k in ('batch_sha256','input_view','member_id','learning_rate')):
                raise ValueError('Positive KD input trace differs')
        write(destination/'backups.json', copies)
        write(destination/'identity.json', session.identity)
        save(destination/'expected.pt', session.state())
    else:
        copies = json.loads((root/'producer/backups.json').read_text())
        checkpoint = Path(request['backup'])/'000003-last.pt'
        if copies.get(str(checkpoint)) != sha(checkpoint):
            raise ValueError('Cold backup changed')
        saved = torch.load(checkpoint,weights_only=True,map_location='cpu')
        identity = json.loads((root/'producer/identity.json').read_text())
        session = ErrataKDSession.restore(saved['session'],identity)
        if session.step != 3: raise ValueError('Cold checkpoint step differs')
        tick(); row = session.update(inputs,targets); tick(); rows=[journal_value(row)]
        compare(session.state(),torch.load(root/'producer/expected.pt',weights_only=True,map_location='cpu'))
        expected = json.loads((root/'producer/updates.json').read_text())[-1]
        for key in ('batch_sha256','input_view','member_id','learning_rate'):
            if rows[0][key] != expected[key]: raise ValueError('Cold input trace differs')
    tick(); write(destination/'updates.json', rows)
    evidence = {str(p.resolve()):sha(p) for p in destination.rglob('*')
                if p.is_file() and p.name not in ('worker.log','process.json','guardian-ready.json')}
    if stage == 'producer': evidence.update(copies)
    write(destination/'result.json',dict(success=True,stage=stage,scientific_updates=0,
          engineering_updates=len(rows),evidence=evidence,scientific_ready=False,
          scope='four-update engineering; two native development cases only',
          rtol=1.3e-6,atol=1e-5))

