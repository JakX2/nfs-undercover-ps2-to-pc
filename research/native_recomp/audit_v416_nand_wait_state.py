#!/usr/bin/env python3
"""Classify the observed resumed wait cycle; private PCs and values never leave CI."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v414_nand_resumed_coverage import parse_trace,ENTRY,TRIAL,MAX_LOG
from audit_v413_nand_context_resume import inspect as context_gate

FIELDS=('mapped','reply','negative','pending','queued','irq','ee','eligible','x1','y1','y2','flag','expired')
STATE=re.compile(rb'V416_WAIT_STATE call=([0-9]{1,3}) lr=([0-9a-f]{1,8}) inst=([0-9]{1,20}) tb=([0-9]{1,20}) '+b' '.join(x.encode()+rb'=([01])' for x in FIELDS))
# Already independently identified public SDK entries. Unknowns are not named.
KNOWN={0x805265ac:'disable',0x805265d4:'restore',0x8052a824:'time',0x8052a844:'time',0x805293f8:'scheduler',0x805229b4:'scheduler',0x80526a3c:'scheduler',0x80519318:'ipc',0x8051906c:'ipc',0x8051905c:'ipc'}
CLASSES=('disable','restore','time','scheduler','ipc','other')

def parse(raw:bytes):
    expected=parse_trace(raw)
    trials=[];rows=[];entry=None
    for line in raw.splitlines():
        if (m:=ENTRY.fullmatch(line)):
            if entry is not None:raise ValueError('missing_state')
            entry=(int(m[1]),int(m[2],16))
        elif line.startswith(b'V416_WAIT_STATE'):
            m=STATE.fullmatch(line)
            if not m or entry is None or int(m[1])!=entry[0]:raise ValueError('state_order')
            lr=int(m[2],16);inst=int(m[3]);tb=int(m[4]);flags=dict(zip(FIELDS,map(int,m.groups()[4:])))
            if (lr&3 or inst>=2**64 or tb>=2**64 or
                flags['eligible']!=int(bool(flags['irq'] and flags['ee'])) or
                flags['reply']>flags['mapped'] or flags['negative']>flags['reply']):raise ValueError('state_geometry')
            if rows and (inst<rows[-1][2] or tb<rows[-1][3]):raise ValueError('progress_order')
            rows.append((entry[1],lr,inst,tb,flags));entry=None
        elif line==TRIAL:
            if entry is not None or len(trials)>=len(expected) or tuple(x[0] for x in rows)!=expected[len(trials)]:raise ValueError('trial_order')
            trials.append(rows);rows=[]
    if entry is not None or rows or len(trials)!=16:raise ValueError('incomplete')
    return trials

def period(route):
    # Four complete periods minimum. Ignore setup prefix, inspect last 48 entries.
    tail=route[-48:]
    for n in range(1,min(12,len(tail)//4)+1):
        if all(tail[i]==tail[i-n] for i in range(n,len(tail))):return n
    return 0

def summarize(trials):
    routes=[tuple((row[0],row[1]) for row in t) for t in trials]
    periods=[period(r) for r in routes]
    counts={k:sum(any(row[4][k] for row in t) for t in trials) for k in FIELDS}
    entries=sum(map(len,trials));unique={row[0] for t in trials for row in t}
    classes={k:sum(KNOWN.get(pc,'other')==k for pc in unique) for k in CLASSES}
    return ('V416_WAIT_CENSUS trials=16 entries='+str(entries)+' unique='+str(len(unique))+
            ' same_route='+str(sum(r==routes[0] for r in routes))+
            ' periodic='+str(sum(p>0 for p in periods))+' period='+str(periods[0] if len(set(periods))==1 else 0)+
            ' inst_progress='+str(sum(t[-1][2]>t[0][2] for t in trials))+
            ' tb_progress='+str(sum(t[-1][3]>t[0][3] for t in trials))+' '+
            ' '.join(f'{k}={v}' for k,v in counts.items())+' '+
            ' '.join(f'{k}={v}' for k,v in classes.items())+' boot_verified=0')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG or not context_gate(a.log,a.rc).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):raise ValueError('control')
        row=summarize(parse(a.log.read_bytes()))
    except (OSError,ValueError):
        print('V416_WAIT_AUDIT inspected=0');return 1
    print(row);print('V416_WAIT_AUDIT inspected=1');return 0
if __name__=='__main__':raise SystemExit(main())
