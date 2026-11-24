#!/usr/bin/env python3
"""Authenticate selected callback, earlier entries, live callsites and SC retry.
Only an exact complete NOP-only original callback entry may be restored.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct
from dataclasses import dataclass
from audit_v414_nand_resumed_coverage import classify,TRIAL,MAX_LOG
from audit_v416_nand_wait_state import parse as wait_parse
from audit_v413_nand_context_resume import inspect as context_gate
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from extend_private_text import install

LINE=re.compile(rb'V420_CB_ENTRY call=([0-9]{1,3}) pc=([0-9a-f]{1,8}) lr=([0-9a-f]{1,8}) ew=([0-9a-f]{1,8}) lw=([0-9a-f]{1,8}) em=([01]) lm=([01]) resumed=([01]) sc=([0-5]) r3=([0-2])')
# Previously established SDK retry route from V263–V271.
SC_ROUTE={(0x8052f830,0x80520970),(0x805265ac,0x8052f84c),(0x805265d4,0x8052f92c)}
WRITERS={0x80530ba0,0x8052f790,0x8052f830,0x80530dbc,0x8052f94c,0x8052fca4}

@dataclass(frozen=True)
class Entry:
    call:int;pc:int;lr:int;ew:int;lw:int;em:int;lm:int;resumed:int;sc:int;r3:int

def parse(raw:bytes):
    wait=wait_parse(raw);trials=[];current=[]
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry_format')
            e=Entry(int(m[1]),*(int(m[i],16) for i in range(2,6)),*(int(m[i]) for i in range(6,11)))
            if e.call!=len(current) or e.call>192 or not 0x80400000<=e.pc<0x80600000 or e.pc&3 or e.lr&3 or (not e.em and e.ew) or (not e.lm and e.lw):raise ValueError('entry_geometry')
            if (e.call==0 and e.resumed) or (current and e.resumed<current[-1].resumed):raise ValueError('phase')
            current.append(e)
        elif line==TRIAL:
            if len(current)!=193 or len(trials)>=16:raise ValueError('trial_geometry')
            resumed=[(e.pc,e.lr) for e in current if e.resumed]
            if resumed!=[(r[0],r[1]) for r in wait[len(trials)]]:raise ValueError('wait_mismatch')
            trials.append(tuple(current));current=[]
    if current or len(trials)!=16:raise ValueError('incomplete')
    return trials

def word_at(data,addr,reader):
    if not 0x80000000<=addr<=0x817ffffc or addr&3:return None
    try:return struct.unpack('>I',reader(data,addr,4))[0]
    except (ValueError,IndexError,struct.error):return None

def inspect(owner,fixture,sizes,trials,reader=text_at):
    if len(trials)!=16 or any(len(t)!=193 for t in trials):raise ValueError('geometry')
    pre=[e for t in trials for e in t if not e.resumed]
    unique=list(dict.fromkeys(e.pc for e in pre))
    counts=dict(original=0,nop=0,modified=0,missing=0,unknown=0)
    first='none';repair=None
    for pc in unique:
        kind,candidate=classify(owner,fixture,sizes,pc,reader)
        counts[kind]+=1
        if first=='none' and kind!='original':first=kind;repair=candidate
    # Check live entry/caller words independently of fixture on-disk extent.
    # A link word may belong to a caller not observed as a function entry.
    def compare(e,caller):
        at=e.lr-4 if caller else e.pc
        mapped=e.lm if caller else e.em;word=e.lw if caller else e.ew
        original=word_at(owner,at,reader);stored=word_at(fixture,at,reader)
        if not mapped or original is None or stored is None:return 'unmapped'
        if word==original==stored:return 'original'
        if word==stored:return 'fixture'
        if word==original:return 'live_original'
        return 'different'
    checks={}
    for name,selector in (('entry',False),('caller',True)):
        classes=('original','fixture','live_original','different','unmapped')
        for k in classes:checks[name+'_'+k]=sum(any(compare(e,selector)==k for e in t) for t in trials)
    repair_data=None
    if repair is not None:
        pc,before,original=repair
        # Do not repair a candidate if live memory didn't contain the same
        # first placeholder word as the actual private input.
        matches=[e for e in pre if e.pc==pc]
        if matches and all(e.em and e.ew==struct.unpack('>I',before[:4])[0] for e in matches):
            repair_data=install(fixture,[repair])
            if reader(repair_data,pc,len(original))!=original or install(repair_data,[(pc,original,before)])!=fixture:raise ValueError('roundtrip')
    resumed=[tuple(e for e in t if e.resumed) for t in trials]
    route=sum(set((e.pc,e.lr) for e in t[-48:])==SC_ROUTE for t in resumed)
    sc1=sum(all(e.sc==1 for e in t) for t in resumed)
    sc3=sum(any(e.sc==3 for e in t) for t in trials)
    writer=sum(any(e.pc in WRITERS-{0x8052f830} for e in t if not e.resumed) for t in trials)
    nand=sum(t[0].pc==0x8051e06c for t in trials)
    r3negative=sum(t[0].r3==2 for t in trials)
    row=('V420_SC_CENSUS trials=16 pre_unique='+str(len(unique))+' '+' '.join(f'{k}={v}' for k,v in counts.items())+
         f' first={first} repairable={int(repair_data is not None)} sc_route={route} sc1={sc1} sc3={sc3} writer={writer} selected_nand={nand} selected_negative={r3negative} '+
         ' '.join(f'{k}={v}' for k,v in checks.items())+' boot_verified=0')
    return row,repair_data

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('owner','elf','fixture','log','candidate'):p.add_argument(name,type=Path)
    p.add_argument('rc',type=int);p.add_argument('--no-repair',action='store_true');a=p.parse_args()
    try:
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.fixture.read_bytes()
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256 or not fixture or len(fixture)>20_000_000 or a.log.stat().st_size>MAX_LOG:raise ValueError('geometry')
        if not context_gate(a.log,a.rc).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):raise ValueError('control')
        row,candidate=inspect(owner,fixture,parse_functions(elf),parse(a.log.read_bytes()))
        if candidate is not None and not a.no_repair:
            with a.candidate.open('xb') as f:f.write(candidate)
    except (OSError,ValueError,IndexError,struct.error):
        print('V420_SC_AUDIT inspected=0');return 1
    print(row);print(f'V420_PRIVATE_REPAIR prepared={int(candidate is not None and not a.no_repair)} roundtrip={int(candidate is not None)}')
    print('V420_SC_AUDIT inspected=1');return 0
if __name__=='__main__':raise SystemExit(main())
