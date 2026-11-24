#!/usr/bin/env python3
"""Authenticated post-context entry coverage and exact private NOP repair.
No guest PCs, code bytes, symbol names or generated source are published.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct
from audit_v413_nand_context_resume import inspect as context_gate
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from resolve_v308_descendant_boundaries import resolve
from extend_private_text import NOP, install

ENTRY=re.compile(rb'V414_RESUMED_ENTRY call=([0-9]{1,3}) pc=([0-9a-f]{8})')
BEGIN=re.compile(rb'V414_RESUMED_BEGIN after=([0-9]{1,3})')
RESTORE=b'V413_CONTEXT_RESTORE regs=1 msr=1 coherent=1 interrupted=1'
TRIAL=b'V413_CONTEXT_TRIAL complete=1'
MAX_LOG=8_000_000
MAX_CALLS=192
MAX_TRIALS=16
MAX_REPAIR=8192

def parse_trace(raw:bytes)->list[tuple[int,...]]:
    if len(raw)>MAX_LOG:raise ValueError('log_size')
    traces=[];current=[];restored=False;last=None
    for line in raw.splitlines():
        if line==RESTORE:
            if restored or current:raise ValueError('restore_order')
            restored=True
        elif line.startswith(b'V414_RESUMED_BEGIN'):
            m=BEGIN.fullmatch(line)
            if not m or not restored or last is not None or int(m[1])>=MAX_CALLS:
                raise ValueError('begin_order')
            last=int(m[1])
        elif line.startswith(b'V414_RESUMED_ENTRY'):
            m=ENTRY.fullmatch(line)
            if not m or not restored or last is None or len(current)>=MAX_CALLS:
                raise ValueError('entry_order')
            call=int(m[1]);pc=int(m[2],16)
            if not 1<=call<=MAX_CALLS or call!=last+1 or pc&3 or not 0x80400000<=pc<0x80600000:
                raise ValueError('entry_geometry')
            current.append(pc);last=call
        elif line==TRIAL:
            if not restored or not current or last!=MAX_CALLS or len(traces)>=MAX_TRIALS:
                raise ValueError('trial_geometry')
            traces.append(tuple(current));restored=False;current=[];last=None
    if restored or current or len(traces)!=MAX_TRIALS:
        raise ValueError('incomplete')
    return traces

def classify(owner:bytes, fixture:bytes, sizes:dict[int,int], pc:int, reader=text_at):
    window=resolve(sizes,pc)
    if not window.length:return 'unknown',None
    try:
        authentic=reader(owner,pc,window.length)
        if len(authentic)!=window.length:raise ValueError('owner_span')
    except (ValueError,IndexError,struct.error):return 'unknown',None
    try:before=reader(fixture,pc,window.length)
    except (ValueError,IndexError,struct.error):return 'missing',None
    if len(before)!=len(authentic):return 'missing',None
    if before==authentic:return 'original',None
    # Only a COMPLETE exact ELF function made entirely of NOPs may be repaired.
    # Mixed original/stub spans could contain intentional harness seams.
    if before==NOP*(len(before)//4):
        if window.kind=='exact' and 16<=len(before)<=MAX_REPAIR:
            return 'nop',(pc,before,authentic)
        return 'nop',None
    return 'modified',None

def inspect(owner:bytes,fixture:bytes,sizes:dict[int,int],traces:list[tuple[int,...]],reader=text_at):
    if len(traces)!=MAX_TRIALS or any(not 1<=len(t)<=MAX_CALLS for t in traces):
        raise ValueError('trace_geometry')
    # Preserve chronological order: the earliest observed safe repair target.
    unique=list(dict.fromkeys(pc for trial in traces for pc in trial))
    counts=dict(original=0,nop=0,modified=0,missing=0,unknown=0)
    first=None;first_class='none'
    for pc in unique:
        kind,repair=classify(owner,fixture,sizes,pc,reader)
        counts[kind]+=1
        if first_class=='none' and kind!='original':
            first_class=kind;first=repair
    candidate=None
    if first is not None:
        pc,before,authentic=first
        # No relocation or growth: the exact same DOL bytes must round trip.
        candidate=install(fixture,[first])
        if reader(candidate,pc,len(authentic))!=authentic or install(candidate,[(pc,authentic,before)])!=fixture:
            raise ValueError('roundtrip')
    result=(f'V414_RESUMED_COVERAGE trials={len(traces)} entries={sum(map(len,traces))} '
            f'unique={len(unique)} '+' '.join(f'{k}={v}' for k,v in counts.items())+
            f' first={first_class} repairable={int(candidate is not None)} '
            f'all_original={int(counts["original"]==len(unique))} boot_verified=0')
    return result,candidate

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('owner','elf','fixture','log','candidate'):p.add_argument(name,type=Path)
    p.add_argument('rc',type=int);p.add_argument('--no-repair',action='store_true');a=p.parse_args()
    try:
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.fixture.read_bytes()
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
            raise ValueError('digest')
        if not fixture or len(fixture)>20_000_000 or a.log.stat().st_size>MAX_LOG:
            raise ValueError('geometry')
        if not context_gate(a.log,a.rc).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):
            raise ValueError('context_gate')
        result,candidate=inspect(owner,fixture,parse_functions(elf),parse_trace(a.log.read_bytes()))
        if candidate is not None and not a.no_repair:
            with a.candidate.open('xb') as stream:stream.write(candidate)
    except (OSError,ValueError,IndexError,struct.error):
        print('V414_COVERAGE_AUDIT inspected=0');return 1
    print(result)
    print(f'V414_PRIVATE_REPAIR prepared={int(candidate is not None and not a.no_repair)} roundtrip={int(candidate is not None)}')
    print('V414_COVERAGE_AUDIT inspected=1');return 0
if __name__=='__main__':raise SystemExit(main())
