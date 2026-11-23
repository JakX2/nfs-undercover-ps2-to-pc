#!/usr/bin/env python3
"""V387 fail-closed public-only census of genuine NAND ACK-or-next route."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V387_NAND_ROUTE_EVENT kind=([12]) verified=([01]) y1cleared=([01]) latch=([01]) writer=([01]) next=([01])$')
TRIAL=re.compile(r'^V387_NAND_ROUTE_TRIAL kind=([12]) stopped=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    ack_any=next_any=writer_any=0
    valid=True
    expected_kind=0
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16 or entries!=trials:
                valid=False;break
            k,verify,clear,latch,writer,nxt=map(int,e.groups())
            valid=valid and bool(verify and latch and
                ((k==1 and clear and writer and not nxt) or
                 (k==2 and not clear and nxt)))
            ack_any|=int(k==1);next_any|=int(k==2);writer_any|=writer
            expected_kind=k
            entries+=1
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                valid=False;break
            k,stopped,completed=map(int,t.groups())
            valid=valid and bool(k==expected_kind and stopped and completed)
            trials+=1
    return (
        f'V387_NAND_ROUTE_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'ack_any={ack_any} next_any={next_any} writer_any={writer_any} '
        f'route_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V387_NAND_ROUTE_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V387_NAND_ROUTE_AUDIT verified=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
