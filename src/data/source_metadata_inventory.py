"""Bounded PanTS directory/stat observation. Never opens source payloads."""
from collections import Counter
import os
from pathlib import Path
import resource
import stat
import sys
import time

from src.data.manifest_records import canonical


class MetadataInventory:
    def __init__(self, root, *, check_mount, seconds=600, max_entries=350000,
                 max_memory=512*1024**2, max_output=64*1024**2):
        self.root=Path(root)
        if not self.root.is_absolute() or self.root.resolve(strict=True)!=self.root:
            raise ValueError('Canonical existing source root required')
        self.check_mount=check_mount
        check_mount()
        self.device=self.root.stat().st_dev
        self.started=time.monotonic();self.last_mount=self.started
        self.seconds=seconds;self.max_entries=max_entries;self.max_memory=max_memory;self.max_output=max_output
        self.entries=0;self.outside=Counter()

    def guard(self):
        now=time.monotonic()
        if now-self.started>=self.seconds:raise TimeoutError('Metadata time budget exceeded')
        if self.entries>self.max_entries:raise ValueError('Directory entry budget exceeded')
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform!='darwin':rss*=1024
        if rss>self.max_memory:raise MemoryError('Metadata memory budget exceeded')
        if now-self.last_mount>=2:
            self.check_mount();self.last_mount=time.monotonic()

    def scan(self,path):
        """Enumerate one known-layout directory, rejecting links/special/cross-device entries."""
        self.guard()
        before=path.lstat()
        if not stat.S_ISDIR(before.st_mode) or before.st_dev!=self.device:
            raise ValueError('Unsafe source directory')
        rows={}
        with os.scandir(path) as entries:
            for entry in entries:
                self.entries+=1;self.guard()
                info=entry.stat(follow_symlinks=False)
                if info.st_dev!=self.device or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                    raise ValueError('Symlink, special file or different device in source')
                rows[entry.name]=info
        after=path.lstat()
        if (before.st_dev,before.st_ino,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_mtime_ns,after.st_ctime_ns):
            raise ValueError('Source directory changed during enumeration')
        return rows

    def run(self,shards,labels,roles):
        """shards maps safe directory names to exact expected study IDs; roles includes tests.

        Publisher-test label directories are counted by name only, never traversed.
        Missing selected-purpose files are recorded, not silently dropped.
        """
        all_ids=[sid for ids in shards.values() for sid in ids]
        if len(all_ids)!=len(set(all_ids)) or set(all_ids)!={sid for sid in roles if roles[sid]!='test'}:
            raise ValueError('Shard scope must cover each publisher-training identity once')
        for name in [*shards,labels]:
            if not name or Path(name).name!=name or name in ('.','..') or '\\' in name:
                raise ValueError('Unsafe directory binding')
        rows=[]
        def record(sid,kind,path,info):
            if info is not None and not stat.S_ISREG(info.st_mode):raise ValueError('Expected regular payload')
            rows.append(dict(study_id='pants:study:'+sid,protected_role=roles[sid],kind=kind,
                uri=path.relative_to(self.root).as_posix(),state='missing' if info is None else 'present',
                bytes=None if info is None else info.st_size,content_sha256=None,
                observation=None if info is None else dict(device=info.st_dev,inode=info.st_ino,
                    mtime_ns=info.st_mtime_ns,ctime_ns=info.st_ctime_ns)))
        for shard,ids in sorted(shards.items()):
            path=self.root/shard;found=self.scan(path)
            if set(found)-set(ids):raise ValueError('Unexpected study entry in CT shard')
            for sid in sorted(ids):
                contents=self.scan(path/sid) if sid in found else {}
                if set(contents)-{'ct.nii.gz'}:raise ValueError('Unexpected CT study layout')
                record(sid,'ct',path/sid/'ct.nii.gz',contents.get('ct.nii.gz'))
        labelroot=self.root/labels;found=self.scan(labelroot)
        if set(found)-set(roles):raise ValueError('Unexpected label study identity')
        test_directories=0
        for sid in sorted(roles):
            if roles[sid]=='test':
                test_directories+=int(sid in found)
                continue
            case=labelroot/sid
            contents=self.scan(case) if sid in found else {}
            if set(contents)-{'segmentations','combined_labels.nii.gz'}:raise ValueError('Unexpected label study layout')
            for name,info in contents.items():
                if name=='segmentations':continue
                if not stat.S_ISREG(info.st_mode):raise ValueError('Unexpected combined-label type')
                self.outside['combined_labels.nii.gz']+=1
            masks=self.scan(case/'segmentations') if 'segmentations' in contents else {}
            for name,info in masks.items():
                if not stat.S_ISREG(info.st_mode) or not name.endswith('.nii.gz'):
                    raise ValueError('Unexpected segmentation layout')
                if name!='pancreas.nii.gz':self.outside[name]+=1
            record(sid,'pancreas',case/'segmentations'/'pancreas.nii.gz',masks.get('pancreas.nii.gz'))
        self.guard();self.check_mount()
        rows.sort(key=lambda r:(r['study_id'],r['kind']))
        summary=dict(schema_version='1.0.0',assurance='directory_entries_and_stat_only',
            entries_observed=self.entries,elapsed_seconds=time.monotonic()-self.started,
            file_count=len(rows),present=sum(r['state']=='present' for r in rows),
            missing=sum(r['state']=='missing' for r in rows),
            bytes_by_kind={kind:sum(r['bytes'] or 0 for r in rows if r['kind']==kind) for kind in ('ct','pancreas')},
            outside_purpose_structure_counts=dict(sorted(self.outside.items())),
            publisher_test_directories_seen=test_directories,publisher_test_payloads_inspected=0,
            content_hashes_computed=0,eligibility_granted=0)
        payload=b''.join(canonical(r) for r in rows)
        if len(payload)+len(canonical(summary))>self.max_output:raise ValueError('Evidence output budget exceeded')
        return payload,summary
