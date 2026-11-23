#!/usr/bin/env python3
"""V388 public original NAND bounded trace or real Y1 W1C audit."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V388_NAND_BOUNDARY kind=([12]) verified=([01]) calls=([0-9]|1[0-6]) writer=([01]) read=([01]) cache=([01]) y1clear=([01]) latch=([01])$')
TRIAL=re.compile(r'^V388_NAND_BOUNDED_TRIAL kind=([12]) calls=([0-9]|1[0-6]) stopped=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0; ack_any=bounded_any=writer_any=read_any=cache_any=0
    good=True
    expected_kind=expected_calls=-1
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16 or entries!=trials:good=False;break
            k,verified,calls,writer,read,cache,clear,latch=map(int,e.groups())
            good=good and bool(verified and latch and
                ((k==1 and clear) or (k==2 and not clear and calls==16)))
            ack_any|=int(k==1);bounded_any|=int(k==2)
            writer_any|=writer;read_any|=read;cache_any|=cache
            expected_kind=k;expected_calls=calls;entries+=1
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:good=False;break
            k,calls,stopped,completed=map(int,t.groups())
            good=good and bool(k==expected_kind and
                calls==expected_calls and stopped and completed)
            trials+=1
    return (
        f'V388_NAND_BOUNDED_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'ack_any={ack_any} bounded_any={bounded_any} '
        f'writer_any={writer_any} read_any={read_any} cache_any={cache_any} '
        f'bounded_verified={int(bool(good and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V388_NAND_BOUNDED_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V388_NAND_BOUNDED_AUDIT verified=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
