#!/usr/bin/env python3
"""Independent bounded CFG path-length census for three exact original leaves."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from audit_os_leaf_v703 import plan
from audit_handler_suffix_v728 import target
BLR=0x4e800020
def counts(root,words,max_steps=64):
    if root&3 or not 1<=len(words)<=16 or not 1<=max_steps<=64:raise ValueError('extent')
    end=root+4*len(words);front={root};out=set()
    for n in range(1,max_steps+1):
        following=set()
        for pc in front:
            if pc&3 or not root<=pc<end:raise ValueError('fallthrough')
            w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
            if w==BLR:out.add(n);continue
            if op in (16,18):
                if w&3:raise ValueError('branch')
                dst=target(pc,w)
                if not root<=dst<end:raise ValueError('branch extent')
                following.add(dst)
                if op==16:following.add(pc+4)
            elif op==17 or op==19 and xo in (16,50,528):raise ValueError('control')
            else:following.add(pc+4)
        front=following
        if not front:break
    if not out:raise ValueError('return')
    return out
def totals(rows):
    out={25}
    for root,words in rows:out={a+b for a in out for b in counts(root,words) if a+b<=128}
    return out
def inspect(dol,elf):
    rows=plan(dol,elf)
    lengths=[counts(row[1],row[5]) for row in rows]
    for i,p in enumerate(lengths,1):
        print(f'V763_LEAF_PATHS ordinal={i} minimum={min(p)} lengths={len(p)}')
    possible=totals([(row[1],row[5]) for row in rows])
    if 43 not in possible:raise ValueError('observed length not reachable')
    print(f'V763_TIME_PATHS verified=1 observed43=1 minimum={min(possible)} possible_lengths={len(possible)} execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,UnicodeError,struct.error,IndexError):
        print('V763_TIME_PATHS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
