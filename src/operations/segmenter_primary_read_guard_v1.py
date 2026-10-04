"""Supplemental primary-read denial covering path and directory-descriptor APIs."""
import builtins
import fcntl
import io
import os
from pathlib import Path
import sys
import stat
from src.data.source_inventory_records import require
PRIMARY='/Volumes/PROWL-Data'


def fd_path(fd):
    if sys.platform=='darwin':
        try:return os.fsdecode(fcntl.fcntl(fd,50,b'\x00'*1024).split(b'\x00',1)[0]) # F_GETPATH
        except OSError:
            info=os.fstat(fd)
            require(stat.S_ISFIFO(info.st_mode) and info.st_nlink==0,'Unknown descriptor cannot bypass guard')
            return '/dev/anonymous-pipe'
    return os.readlink('/proc/self/fd/'+str(fd))


def check_path(path,*,dir_fd=None):
    if isinstance(path,int):resolved=fd_path(path)
    else:
        value=os.fsdecode(path)
        # Also deny the primary volume component before its root can be opened relatively.
        require('PROWL-Data' not in Path(value).parts,'Primary path component forbidden')
        if dir_fd is not None and not os.path.isabs(value):value=os.path.join(fd_path(dir_fd),value)
        resolved=os.path.realpath(value)
    require(not (resolved==PRIMARY or resolved.startswith(PRIMARY+'/')),'Primary path/descriptor reads forbidden')


def install():
    """Fresh worker only; no primary handles are opened before installation."""
    def audit(event,args):
        if event in ('open','os.listdir','os.scandir') and args:check_path(args[0])
    # Audit hooks alone do not receive dir_fd for os.open. Wrap that API explicitly.
    original_open=os.open
    def guarded_open(path,flags,mode=0o777,*,dir_fd=None):
        check_path(path,dir_fd=dir_fd)
        return original_open(path,flags,mode,dir_fd=dir_fd)
    os.open=guarded_open
    sys.addaudithook(audit)
