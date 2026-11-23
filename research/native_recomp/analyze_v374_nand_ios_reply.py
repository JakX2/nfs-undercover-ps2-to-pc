#!/usr/bin/env python3
"""V374: bounded private-log audit of authentic guest reply-yield attempts."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

RECORD=re.compile(
    r'^V374_NAND_REPLY_GATE n=([1-9]|1[0-6]) '
    r'yclear=([01]) flagclear=([01]) irq_before=([01]) '
    r'fired=([01]) pump=([0-9]|1[0-9]) y1=([01]) '
    r'queued=([01]) irq_after=([01]) eligible=([01])$'
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=ready_any=serviced_any=replied_any=y1_any=queued_any=irq_any=eligible_any=0
    blocked_flag_any=blocked_y_any=0
    for line in lines:
        match=RECORD.fullmatch(line)
        if not match:
            continue
        n,yclear,flagclear,irq_before,fired,pump,y1,queued,irq_after,eligible=map(
            int,match.groups())
        if (n!=count+1 or (not fired and pump!=0) or
            (fired and (not yclear or not flagclear or irq_before)) or
            (eligible and not irq_after)):
            break
        count+=1
        ready_any|=int(bool(yclear and flagclear and not irq_before))
        blocked_flag_any|=int(not flagclear)
        blocked_y_any|=int(not yclear)
        serviced_any|=fired
        replied_any|=int(bool(fired and pump==2 and y1))
        y1_any|=y1;queued_any|=queued;irq_any|=irq_after;eligible_any|=eligible
    return (
        f'V374_NAND_REPLY_CENSUS rc={rc} kind={kind} size_band={size_band(size)} '
        f'sample_complete={int(size<=WINDOW)} samples={count} '
        f'ready_any={ready_any} blocked_y_any={blocked_y_any} '
        f'blocked_flag_any={blocked_flag_any} serviced_any={serviced_any} '
        f'replied_any={replied_any} y1_any={y1_any} queued_any={queued_any} '
        f'irq_any={irq_any} eligible_any={eligible_any}'
    )

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_log',type=Path)
    parser.add_argument('native_exit',type=int)
    args=parser.parse_args()
    try:
        print(inspect(args.private_log,args.native_exit))
    except (OSError,ValueError):
        print('V374_NAND_REPLY_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V374_NAND_REPLY_AUDIT verified=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
