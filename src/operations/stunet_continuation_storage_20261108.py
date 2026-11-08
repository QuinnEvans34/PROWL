"""Approved 88GiB C-only backups; all original volume/free/cache gates retained."""
import shutil
from scripts.training.supervise_stunet_transfer_20261106 import size

def check_storage():
    import ctypes
    ids=[]
    for drive,expected in [('C:/','9ed7859f-4768-4f11-9788-792a793f0ee4'),('E:/','424d39a3-ac76-4f41-aa1c-8b9f5ce0b829')]:
        buf=ctypes.create_unicode_buffer(256)
        if not ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(drive.replace('/','\\'),buf,256):raise OSError('Volume identity unavailable')
        if expected not in buf.value.lower():raise ValueError('Volume identity changed')
        ids.append(buf.value)
        if shutil.disk_usage(drive).free<100*1024**3:raise RuntimeError('100GiB free-space floor')
    if ids[0]==ids[1]:raise ValueError('Backup volumes are not distinct')
    if size('C:/Users/quinn/PROWL-Backups')>88*1024**3:raise RuntimeError('88GiB backup cap')
    if size('E:/PROWL/cache')>32*1024**3:raise RuntimeError('32GiB cache cap')

