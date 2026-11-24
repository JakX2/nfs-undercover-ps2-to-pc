#!/usr/bin/env python3
"""Private owner static geometry preflight: never print instructions or addresses."""
import argparse
import hashlib
import struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL
from prepare_v529_si_discovery import expectations as si
from prepare_v534_sram_read import expectations as sram
from prepare_v549_thread_init import expectations as thread
from prepare_v556_audio_reset import expectations as audio
STAGES=(('si',si),('sram',sram),('thread',thread),('audio',audio))
def inspect(data,digest=OWNER_SHA,stages=STAGES):
    if not 256<=len(data)<=MAX_DOL or hashlib.sha256(data).hexdigest()!=digest:
        raise ValueError('identity')
    passed=[]
    for name,fn in stages:
        try:fn(data,digest)
        except (ValueError,struct.error,IndexError,KeyError):
            return tuple(passed),name
        passed.append(name)
    return tuple(passed),'none'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        passed,failed=inspect(a.dol.read_bytes())
        for name,_ in STAGES:
            print(f'V558_GEOMETRY_STAGE scope={name} verified={int(name in passed)} attempted={int(name in passed or name==failed)} boot_verified=0')
        print(f'V558_GEOMETRY_RESULT stages={len(passed)} failure={failed} boot_verified=0')
        return 0 if failed=='none' else 1
    except (OSError,ValueError,struct.error):
        print('V558_GEOMETRY_RESULT identity=0 boot_verified=0');return 1
if __name__=='__main__':raise SystemExit(main())
