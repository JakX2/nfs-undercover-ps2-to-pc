#!/usr/bin/env python3
"""Write an explicit, original-free EXI owner-test profile.

This is a test fixture, not a retail Wii hardware identity or SRAM dump.
The caller supplies all numeric fields and all 64 bytes. Never overwrite
an existing file or resolve a symlink as the output.
"""
import argparse
from pathlib import Path
import os
import re
def number(s):
    if not re.fullmatch(r'[0-9a-fA-F]{8}',s):raise argparse.ArgumentTypeError('expected eight hex digits')
    return int(s,16)
def encode(id_value,di_config,rtc_seconds,latency,sram):
    vals=(id_value,di_config,rtc_seconds,latency)
    if any(type(v) is not int or not 0<=v<=0xffffffff for v in vals) or not 1<=latency<=1000000:
        raise ValueError('profile number')
    if not isinstance(sram,bytes) or len(sram)!=64:raise ValueError('SRAM geometry')
    return ('UNDERCOVER_EXI_PROFILE_V1\n'+
            ''.join(f'{key}={v:08x}\n' for key,v in zip(('id','di_config','rtc_seconds','latency'),vals))+
            'sram='+sram.hex()+'\n').encode('ascii')
def create(path,payload):
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0)
    fd=os.open(path,flags,0o600)
    try:
        with os.fdopen(fd,'wb') as out:out.write(payload)
    except BaseException:
        # Never delete or replace an existing path on failed exclusive create.
        raise
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--id',type=number,required=True)
    p.add_argument('--di-config',type=number,required=True)
    p.add_argument('--rtc-seconds',type=number,required=True)
    p.add_argument('--latency',type=number,required=True)
    p.add_argument('--sram-hex',required=True)
    a=p.parse_args()
    try:
        if not re.fullmatch(r'[0-9a-fA-F]{128}',a.sram_hex):raise ValueError('SRAM hex')
        create(a.output,encode(a.id,a.di_config,a.rtc_seconds,a.latency,bytes.fromhex(a.sram_hex)))
    except (OSError,ValueError):
        print('V505_EXI_TEST_PROFILE created=0');return 1
    print('V505_EXI_TEST_PROFILE created=1 synthetic=1 bytes=64');return 0
if __name__=='__main__':raise SystemExit(main())
