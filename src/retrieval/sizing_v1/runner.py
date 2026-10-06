"""Run S orchestration: prior-run proof, preflight, capped transfers, sizing parses, journal.

The caps come from the run S record. They are constants here and cannot be loosened by
configuration. The signed copy's machine-readable sidecar (``RunConfig``) must confirm the memory
and expansion figures exactly.

There is **no live binding** in this module. Volume observations, transport, clock, the parser
launcher and the filesystem hook (``fsio``, from ``sizing_v1.1``) are all injected. The S1 binding
supplies a guarded hook and volume probe; until it is accepted, the CLI refuses execution.
"""
import hashlib
import os
import re
import signal

from src.retrieval.sizing_v1 import (GIB, MIB, TOOL_NAME, TOOL_VERSION, Interrupted,
                                     PreflightFailed, RunRefused, SizingStop, VolumeCheckFailed)
from src.retrieval.sizing_v1 import listings
from src.retrieval.sizing_v1.fsio import PlainFs
from src.retrieval.sizing_v1.journal import Journal, JournalUnwritable, RunLock, plan_run
from src.retrieval.sizing_v1.parser import manifest_bytes_for
from src.retrieval.sizing_v1.transfer import (HEADER_RESERVE, Budget, Origins, ScratchDir, TransferContext,
                                              fetch, head_size)

NETWORK_CAP = 10 * GIB
SCRATCH_CAP = 40 * GIB
RUN_SECONDS = 2 * 60 * 60
ATTEMPTS = 2
STALL_SECONDS = 5 * 60
CHECK_INTERVAL = 60
MESH_FALLBACK_ALLOWANCE = 1 * GIB
MEMORY_CAP = 4 * GIB
EXPANSION_LIMIT = 20
LISTING_LIMIT = 16 * MIB
MD5_LIMIT = 4 * 1024
PROJECTION_FACTOR = 1.5
MEMORY_METHOD = 'watchdog: child process, resident set polled every 0.5 s, killed above the cap'
CODE_FILES = ('src/retrieval/sizing_v1/__init__.py', 'src/retrieval/sizing_v1/fsio.py',
              'src/retrieval/sizing_v1/listings.py',
              'src/retrieval/sizing_v1/transfer.py', 'src/retrieval/sizing_v1/parser.py',
              'src/retrieval/sizing_v1/journal.py', 'src/retrieval/sizing_v1/runner.py',
              'scripts/retrieval/run_s_sizing_v1.py')
REQUIRED_CONFIG = ('signed_copy_sha256', 'baseline_url', 'update_url', 'mesh_url', 'mesh_name',
                   'fallback_dir', 'scratch_root', 'receipts_dir', 'executor', 'tool_code_hash',
                   'user_agent', 'headroom_floor_bytes', 'volume_uuid', 'volume_mount',
                   'memory_cap_bytes', 'expansion_limit')
_STRINGS = ('signed_copy_sha256', 'baseline_url', 'update_url', 'mesh_url', 'mesh_name', 'fallback_dir',
            'scratch_root', 'receipts_dir', 'executor', 'tool_code_hash', 'user_agent', 'volume_uuid',
            'volume_mount')
_BARE_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')


def code_identity(repo_root):
    """SHA-256 over the tool's files (relative path, NUL, bytes, NUL), in a fixed order."""
    h = hashlib.sha256()
    for rel in CODE_FILES:
        with open(os.path.join(repo_root, rel), 'rb') as fh:
            data = fh.read()
        h.update(rel.encode('utf-8') + b'\0' + data + b'\0')
    return h.hexdigest()


def validate_config(config):
    if not isinstance(config, dict):
        raise RunRefused('run config must be a JSON object')
    missing = [k for k in REQUIRED_CONFIG if config.get(k) in (None, '')]
    if missing:
        raise RunRefused(f'run config is missing {missing}')
    wrong = [k for k in _STRINGS if not isinstance(config[k], str)]
    wrong += [k for k in ('memory_cap_bytes', 'expansion_limit', 'headroom_floor_bytes')
              if isinstance(config[k], bool) or not isinstance(config[k], int)]
    if wrong:
        raise RunRefused(f'run config fields have the wrong type: {wrong}')
    if not _BARE_NAME.fullmatch(config['mesh_name']):
        raise RunRefused('MeSH file name must be a bare file name')
    if config['memory_cap_bytes'] != MEMORY_CAP or config['expansion_limit'] != EXPANSION_LIMIT:
        raise RunRefused('signed memory cap / expansion limit must confirm 4 GiB and 20x exactly')
    if not config['mesh_url'].endswith('/' + config['mesh_name']):
        raise RunRefused('MeSH URL does not end with the literal MeSH file name')
    for key in ('baseline_url', 'update_url'):
        if not config[key].endswith('/'):
            raise RunRefused(f'{key} must be a literal directory URL ending in /')
    fallback = os.path.realpath(config['fallback_dir'])
    for key in ('scratch_root', 'receipts_dir'):
        root = os.path.realpath(config[key])
        if fallback == root or fallback.startswith(root + os.sep):
            raise RunRefused('fallback journal directory must be outside scratch and receipts')
    probe = fallback
    while True:
        if os.path.exists(os.path.join(probe, '.git')):
            raise RunRefused('fallback journal directory must be outside any Git checkout')
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return config


class _Run:
    def __init__(self, config, transport, clock, wall, volume, launcher, journal, budget, fs):
        self.fs = fs
        self.config = config
        self.transport = transport
        self.clock = clock
        self.wall = wall
        self.volume = volume
        self.launcher = launcher
        self.journal = journal
        self.budget = budget
        self.deadline = clock() + RUN_SECONDS

    def volume_check(self, when, need):
        try:
            obs = self.volume.observe()
        except Exception as exc:   # noqa: BLE001 - an unreadable volume is a failed check
            self.journal.append('volume_check', ok=False, when=when, error=f'{type(exc).__name__}: {exc}')
            raise VolumeCheckFailed('volume observation failed', when=when) from exc
        if not isinstance(obs, dict):
            raise VolumeCheckFailed('volume observation is not a mapping', when=when)
        reading = dict(when=when, uuid=obs.get('uuid'), mount=obs.get('mount'), writable=obs.get('writable'),
                       free_bytes=obs.get('free_bytes'), required_free=need)
        ok = (obs.get('uuid') == self.config['volume_uuid'] and obs.get('mount') == self.config['volume_mount']
              and obs.get('writable') is True and isinstance(obs.get('free_bytes'), int)
              and obs['free_bytes'] >= need)
        self.journal.append('volume_check', ok=ok, **reading)
        if not ok:
            raise VolumeCheckFailed('volume identity or free space check failed', **reading)

    def remaining_need(self):
        return self.config['headroom_floor_bytes'] + self.budget.scratch_remaining()

    def execute(self):
        cfg = self.config
        self.volume_check('start', cfg['headroom_floor_bytes'] + SCRATCH_CAP)
        subdir = f'sizing-{self.journal.run_id}'
        try:
            self.fs.mkdir_exclusive('scratch', subdir)
        except FileExistsError as exc:
            raise SizingStop('scratch run directory already exists', reason='scratch_collision',
                             path=subdir) from exc
        except (OSError, ValueError) as exc:
            raise SizingStop(f'scratch run directory cannot be created: {exc}', reason='scratch_unavailable',
                             path=subdir) from exc
        scratch = ScratchDir(self.fs, subdir)
        origins = Origins([cfg['baseline_url'], cfg['update_url'], cfg['mesh_url']])
        ctx = TransferContext(transport=self.transport, budget=self.budget, origins=origins, clock=self.clock,
                              deadline=self.deadline, emit=self.journal.append,
                              periodic_check=lambda: self.volume_check('periodic', self.remaining_need()),
                              stall_seconds=STALL_SECONDS, attempts=ATTEMPTS, check_interval=CHECK_INTERVAL)

        # Preflight 1: freeze both listings (their bytes count against both caps).
        frozen = {}
        for key, url, fname in (('baseline', cfg['baseline_url'], 'listing-baseline.html'),
                                ('updates', cfg['update_url'], 'listing-updates.html')):
            self.volume_check('before_file', self.remaining_need())
            r = fetch(ctx, url, scratch, fname, max_body=LISTING_LIMIT, keep_bytes=True, kind='listing')
            if b'</html>' not in r['data'][-4096:].lower():
                raise PreflightFailed('listing appears truncated (no closing </html>)', which=key)
            frozen[key] = r
            self.journal.append('listing_frozen', which=key, sha256=r['sha256'], bytes=r['bytes'], path=r['path'])
        # Preflight 2-3: resolve from the frozen bytes only.
        baseline = listings.resolve_baseline(listings.parse_listing(frozen['baseline']['data']))
        updates = listings.resolve_updates(listings.parse_listing(frozen['updates']['data']))
        # Preflight 4: MeSH size from HEAD, else the fixed 1 GiB allowance.
        mesh_size = head_size(ctx, cfg['mesh_url'])
        mesh_allowance = mesh_size if mesh_size is not None else MESH_FALLBACK_ALLOWANCE
        # Preflight 5: record before transfer; cap pre-check.
        n_requests = 2 * (len(baseline['samples']) + len(updates['samples'])) + 1
        planned = listings.planned_bytes(baseline, updates, mesh_allowance) + n_requests * HEADER_RESERVE
        self.journal.append('preflight_resolved', baseline=baseline, updates=updates,
                            mesh=dict(name=cfg['mesh_name'], url=cfg['mesh_url'], head_size=mesh_size,
                                      allowance=mesh_allowance),
                            planned_bytes_upper=planned, counters=self.budget.snapshot())
        if self.budget.network_used + planned > self.budget.network_limit:
            raise PreflightFailed('planned transfers would exceed the network cap; nothing transferred',
                                  planned=planned)

        samples = ([dict(s, role='baseline', base=cfg['baseline_url']) for s in baseline['samples']]
                   + [dict(s, role='update', base=cfg['update_url']) for s in updates['samples']])
        files = []
        for s in samples:
            self.volume_check('before_file', self.remaining_need())
            md5_receipt = fetch(ctx, s['base'] + s['name'] + '.md5', scratch, s['name'] + '.md5',
                                max_body=MD5_LIMIT, keep_bytes=True, kind='md5')
            expected = listings.parse_md5_file(md5_receipt['data'], s['name'])
            self.volume_check('before_file', self.remaining_need())
            r = fetch(ctx, s['base'] + s['name'], scratch, s['name'], expected_md5=expected,
                      max_body=s['size_upper'])
            files.append(dict(sample=s, receipt=r, md5_file_sha256=md5_receipt['sha256']))
        self.volume_check('before_file', self.remaining_need())
        mesh = fetch(ctx, cfg['mesh_url'], scratch, cfg['mesh_name'], max_body=mesh_allowance)

        measured = []
        for f in files:
            self.volume_check('before_parse', self.remaining_need())
            name, r = f['sample']['name'], f['receipt']
            out_rel = scratch.rel(name + '.sizing.jsonl.gz')
            self.journal.append('parse_start', name=name, counters=self.budget.snapshot())
            need = self.remaining_need()
            try:
                out_fh = self.fs.create_exclusive('scratch', out_rel)
            except FileExistsError as exc:
                raise SizingStop('scratch name collision', reason='scratch_collision', path=out_rel) from exc
            except (OSError, ValueError) as exc:
                raise SizingStop(f'scratch file cannot be created: {exc}', reason='scratch_write_failed',
                                 path=out_rel) from exc
            allowance = self.budget.scratch_remaining()
            written, charged = None, False
            try:
                with out_fh, self.fs.open_read('scratch', r['rel']) as src_fh:
                    try:
                        m = self.launcher.parse(src=src_fh, out=out_fh, source_file=name,
                                                compressed_size=r['bytes'], scratch_allowance=allowance,
                                                seconds_left=max(0.0, self.deadline - self.clock()),
                                                expansion_limit=EXPANSION_LIMIT,
                                                periodic=lambda need=need: self.volume_check('periodic_parse', need))
                    finally:
                        try:
                            written = os.fstat(out_fh.fileno()).st_size     # by handle, no name lookup
                        except (OSError, ValueError):
                            written = None
                self.budget.charge_scratch(m['scratch_charged'])
                charged = True
            except BaseException:
                if not charged:
                    self._charge_partial(written, r['bytes'], allowance)
                raise
            manifest = manifest_bytes_for(m)
            self.budget.charge_scratch(len(manifest))
            self._write_manifest(out_rel + '.manifest.json', manifest)
            m = dict(m, manifest_bytes=len(manifest), output_path=self.fs.display('scratch', out_rel),
                     role=f['sample']['role'], listed_size=f['sample']['size_text'],
                     cumulative_scratch_after=self.budget.scratch_used)
            measured.append(m)
            self.journal.append('parsed', measurements=m, counters=self.budget.snapshot())

        if len(measured) != len(files) or any(not f['receipt']['md5_verified'] for f in files):
            raise SizingStop('not every sample was verified and measured', reason='incomplete_measurement')
        ratios = [m['parsed_ratio'] for m in measured]
        years = {}
        for m in measured:
            for year, count in m['observed_years'].items():
                years[year] = years.get(year, 0) + count
        representativeness = dict(
            baseline_positions='first, middle and last by file-sequence position (not publication date)',
            baseline_names=[s['name'] for s in baseline['samples']],
            update_names=[s['name'] for s in updates['samples']], observed_years=years,
            parsed_ratios=ratios, largest_ratio=max(ratios), projection_factor=PROJECTION_FACTOR,
            projection_ratio=max(ratios) * PROJECTION_FACTOR,
            projection_note='largest sampled ratio x 1.5 is a projection, not proof that the store fits')
        self.journal.append('representativeness', **representativeness)
        return dict(listings={k: dict(sha256=v['sha256'], bytes=v['bytes']) for k, v in frozen.items()},
                    baseline_totals=dict(file_count=baseline['file_count'], listed_bytes_upper=baseline['listed_bytes_upper']),
                    update_totals=dict(file_count=updates['file_count'], listed_bytes_upper=updates['listed_bytes_upper']),
                    mesh=dict(bytes=mesh['bytes'], sha256=mesh['sha256']), measured=len(measured),
                    representativeness=representativeness)

    def _write_manifest(self, rel, data):
        try:
            with self.fs.create_exclusive('scratch', rel) as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        except FileExistsError as exc:
            raise SizingStop('scratch name collision', reason='scratch_collision', path=rel) from exc
        except (OSError, ValueError) as exc:
            raise SizingStop(f'manifest write failed: {exc}', reason='scratch_write_failed', path=rel) from exc

    def _charge_partial(self, written, compressed_size, allowance):
        """Parse not charged normally: charge an upper bound.

        The parser's meter keeps decompressed plus written bytes within ``allowance``. With the
        output size known (from ``fstat`` on the handle), the bound is that size plus the smaller of
        the 20x guard and the rest of the allowance; otherwise it is the whole allowance.
        """
        if written is None:
            charge = allowance
        else:
            charge = written + min(EXPANSION_LIMIT * compressed_size, max(0, allowance - written))
        clamped = charge > self.budget.scratch_remaining()
        self.budget.scratch_used = min(self.budget.scratch_cap, self.budget.scratch_used + charge)
        try:
            self.journal.append('parse_failed_charge', on_disk=written, charged=charge,
                                decompressed_upper=EXPANSION_LIMIT * compressed_size, clamped_to_cap=clamped,
                                counters=self.budget.snapshot())
        except SizingStop:
            pass


def run_sizing(config, *, transport, clock, wall, volume, launcher, run_id, code_hash, fs=None):
    """Executes one run S attempt against injected dependencies. Returns the final status.

    ``fs`` is the filesystem hook (``fsio``). It defaults to ``PlainFs`` over the configured paths;
    the S1 binding passes its guarded implementation, whose ``roots()`` must equal the configured
    scratch, receipts and fallback paths.
    """
    validate_config(config)
    if not isinstance(run_id, str) or not _BARE_NAME.fullmatch(run_id):
        raise RunRefused('run id must be a bare name')
    if code_hash != config['tool_code_hash']:
        raise RunRefused('tool code hash does not match the signed copy')
    if fs is None:
        fs = PlainFs(config['scratch_root'], config['receipts_dir'], config['fallback_dir'])
    roots = fs.roots()
    for area, key in (('scratch', 'scratch_root'), ('receipts', 'receipts_dir'), ('fallback', 'fallback_dir')):
        if not isinstance(roots.get(area), str) or os.path.realpath(roots[area]) != os.path.realpath(config[key]):
            raise RunRefused(f'filesystem hook {area} root does not match the configured {key}')
    lock = RunLock(fs, config['signed_copy_sha256'])
    try:
        return _locked_run(config, transport, clock, wall, volume, launcher, run_id, code_hash, fs)
    finally:
        lock.release()


def _locked_run(config, transport, clock, wall, volume, launcher, run_id, code_hash, fs):
    run_index, inherited, prior = plan_run(fs, config['signed_copy_sha256'])
    budget = Budget(NETWORK_CAP, SCRATCH_CAP, network_used=inherited['network_used'],
                    scratch_used=inherited['scratch_used'])
    journal = Journal(fs, run_id, config['signed_copy_sha256'], wall)
    try:
        try:
            journal.append('start', run_index=run_index, tool=TOOL_NAME, tool_version=TOOL_VERSION,
                           code_hash=code_hash, executor=config['executor'], host=config.get('host'),
                           sources=dict(baseline=config['baseline_url'], updates=config['update_url'],
                                        mesh=config['mesh_url'], mesh_name=config['mesh_name']),
                           fallback_dir=config['fallback_dir'], prior_runs=prior,
                           caps=dict(network=NETWORK_CAP, network_reserve=budget.network_reserve,
                                     scratch=SCRATCH_CAP, seconds=RUN_SECONDS, attempts=ATTEMPTS,
                                     stall_seconds=STALL_SECONDS, memory=MEMORY_CAP, expansion=EXPANSION_LIMIT),
                           memory_method=MEMORY_METHOD, counters=budget.snapshot())
            summary = _Run(config, transport, clock, wall, volume, launcher, journal, budget, fs).execute()
        except SizingStop as exc:
            status = f'stopped_{exc.reason}'
            journal.final(status, message=str(exc), detail=exc.detail, counters=budget.snapshot())
            return status
        except Interrupted:
            journal.final('interrupted', counters=budget.snapshot())
            return 'interrupted'
        except JournalUnwritable:
            raise
        except Exception as exc:   # noqa: BLE001 - unexpected failures still end with a final status
            journal.final('stopped_internal_error', message=f'{type(exc).__name__}: {exc}',
                          counters=budget.snapshot())
            return 'stopped_internal_error'
        journal.final('completed', summary=summary, counters=budget.snapshot())
        return 'completed'
    finally:
        journal.close()


def install_signal_handlers():
    """CLI only: termination, quit, hang-up and terminal-stop signals raise Interrupted.

    The journal then records ``interrupted`` and the parser's process group is killed. Ctrl-Z
    (SIGTSTP) is treated as an interruption rather than a suspension, because a suspended parent
    would leave the parser child running without its memory watchdog.
    """
    def handler(signum, frame):
        raise Interrupted(f'signal {signum}')
    previous = {}
    for name in ('SIGTERM', 'SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGTSTP'):
        sig = getattr(signal, name, None)
        if sig is not None:
            previous[sig] = signal.signal(sig, handler)
    return previous
