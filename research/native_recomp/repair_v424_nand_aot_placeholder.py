#!/usr/bin/env python3
"""Restore one authenticated, observed all-NOP AOT entry span privately.
The reduced harness deliberately does not load all DOL text into guest RAM.
Use the actual generated entry/dispatch and original ELF extent instead of
an unmapped live instruction word. Never publish private addresses or code.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct
from dataclasses import dataclass
from audit_v420_nand_sc_provenance import parse,LINE,SC_ROUTE
from audit_v414_nand_resumed_coverage import classify,TRIAL,MAX_LOG
from audit_v413_nand_context_resume import inspect as context_gate
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve
from extend_private_text import install,NOP

MAX_CPP=50_000_000
MAX_SPAN=8192
HEAD=re.compile(r'(?m)^void\s+[A-Za-z_][A-Za-z_0-9]*\s*\(CPUContext& ctx\)\s*\{')
@dataclass(frozen=True)
class Plan:
    kind:str='none';pc:int=0;size:int=0;body:int=0;dispatch:int=0;reason:str='no_placeholder';candidate:bytes|None=None
    def row(self):
        return (f'V424_REPAIR_PLAN kind={self.kind} words={self.size//4} body={self.body} dispatch={self.dispatch} '
                f'prepared={int(self.candidate is not None)} reason={self.reason} boot_verified=0')

def aot_entry(generated:str,pc:int)->tuple[int,int]:
    if not generated or len(generated)>MAX_CPP:raise ValueError('generated_geometry')
    lower=generated.lower();marker=f'nwii::runtime::trace_call(0x{pc:08x}, ctx)'
    if lower.count(marker)!=1:return 0,0
    at=lower.index(marker);heads=list(HEAD.finditer(generated))
    prior=[m for m in heads if m.start()<at]
    if not prior:return 0,0
    head=prior[-1];name=re.search(r'void\s+(\w+)\s*\(',head[0])[1].lower()
    # Require the entry marker in an actual function body and that exact
    # function in the dispatch table (not merely a matching declaration).
    dispatch=int(bool(re.search(r'\{0x'+f'{pc:08x}'+r',\s*0x[0-9a-f]+,\s*'+re.escape(name)+r'\s*\}',lower)))
    return 1,dispatch

def prepare(owner,fixture,sizes,generated,trials,reader=text_at)->Plan:
    if len(trials)!=16 or any(len(t)!=193 for t in trials):raise ValueError('trials')
    first=[]
    for t in trials:
        non_original=[]
        for pc in dict.fromkeys(e.pc for e in t if not e.resumed):
            kind,_=classify(owner,fixture,sizes,pc,reader)
            if kind!='original':non_original.append((pc,kind))
        if len(non_original)!=1 or non_original[0][1]!='nop':return Plan(reason='not_unique')
        first.append(non_original[0][0])
    if len(set(first))!=1:return Plan(reason='route_differs')
    pc=first[0];window=resolve(sizes,pc)
    if window.kind not in ('exact','interior') or not 4<=window.length<=MAX_SPAN:return Plan(reason='extent')
    size=window.length;body,dispatch=aot_entry(generated,pc)
    if not body or not dispatch:return Plan(window.kind,pc,size,body,dispatch,'aot_missing')
    before=reader(fixture,pc,size);original=reader(owner,pc,size)
    if len(before)!=size or len(original)!=size or before!=NOP*(size//4) or original==before:return Plan(window.kind,pc,size,body,dispatch,'not_nop')
    # For an interior entry restore only its unique ELF tail window. The
    # already present parent prefix is never overwritten or relocated.
    candidate=install(fixture,[(pc,before,original)])
    if reader(candidate,pc,size)!=original or install(candidate,[(pc,original,before)])!=fixture:raise ValueError('roundtrip')
    return Plan(window.kind,pc,size,body,dispatch,'ready',candidate)

def result(raw:bytes,rc:int,pc:int)->str:
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('log_geometry')
    trials=[];current=[];complete=0
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            call=int(m[1]);addr=int(m[2],16);lr=int(m[3],16);resumed=int(m[8]);sc=int(m[9])
            if call!=len(current) or call>192 or addr&3 or lr&3 or not 0x80400000<=addr<0x80600000 or (current and resumed<current[-1][3]):raise ValueError('entry_order')
            current.append((call,addr,lr,resumed,sc))
        elif line==TRIAL:
            if len(current)!=193 or len(trials)>=16:raise ValueError('trial')
            trials.append(current);current=[];complete+=1
    if current:trials.append(current)
    if len(trials)>16:raise ValueError('trial_count')
    visited=sum(any(e[1]==pc and not e[3] for e in t) for t in trials)
    status3=sum(any(e[4]==3 for e in t) for t in trials)
    resumed=sum(any(e[3] for e in t) for t in trials)
    same_retry=sum(len(t)>=48 and all(e[3] and e[4]==1 for e in t[-48:]) and set((e[1],e[2]) for e in t[-48:])==SC_ROUTE for t in trials)
    kind='zero' if rc==0 else 'timeout' if rc in (124,137) else 'signal' if rc>=128 else 'nonzero'
    return (f'V424_REPAIR_RESULT rc={rc} kind={kind} trials={len(trials)} complete={complete} '
            f'target_seen={visited} resumed={resumed} status3={status3} same_retry={same_retry} '
            f'max_calls={max((t[-1][0] for t in trials),default=0)} boot_verified=0')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','generated','baseline','candidate'):p.add_argument(n,type=Path)
    p.add_argument('--result-log',type=Path);p.add_argument('--result-cpp',type=Path);p.add_argument('--result-rc',type=int)
    a=p.parse_args()
    try:
        if a.owner.stat().st_size>20_000_000 or a.fixture.stat().st_size>20_000_000 or a.generated.stat().st_size>MAX_CPP or a.baseline.stat().st_size>MAX_LOG:raise ValueError('geometry')
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.fixture.read_bytes()
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        if not context_gate(a.baseline,0).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):raise ValueError('control')
        plan=prepare(owner,fixture,parse_functions(elf),a.generated.read_text(encoding='utf-8'),parse(a.baseline.read_bytes()))
        if a.result_log is None:
            if plan.candidate is not None:
                with a.candidate.open('xb') as f:f.write(plan.candidate)
            print(plan.row())
        else:
            if plan.candidate is None or a.result_cpp is None or a.result_rc is None or a.result_log.stat().st_size>MAX_LOG or a.result_cpp.stat().st_size>MAX_CPP or a.candidate.stat().st_size>20_000_000 or a.candidate.read_bytes()!=plan.candidate:raise ValueError('candidate')
            if aot_entry(a.result_cpp.read_text(encoding='utf-8'),plan.pc)!=(1,1):raise ValueError('candidate_aot')
            print(result(a.result_log.read_bytes(),a.result_rc,plan.pc))
            print(context_gate(a.result_log,a.result_rc).replace('V413_CONTEXT_CENSUS ','V424_CONTEXT_CENSUS ',1))
    except (OSError,ValueError,IndexError,struct.error,UnicodeError):
        print('V424_REPAIR_AUDIT inspected=0');return 1
    print('V424_REPAIR_AUDIT inspected=1');return 0
if __name__=='__main__':raise SystemExit(main())
