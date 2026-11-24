#!/usr/bin/env python3
"""V471: restore the uniquely observed NOP span after the V464 missing body.
The private owner image, original ELF, candidate bytes, generated code and
trace lineage are authenticated before any additional repair. No private
addresses or bytes are emitted by this tool.
"""
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
from audit_v414_nand_resumed_coverage import classify,MAX_LOG
from derive_v437_nand_restored_frame import entries,inspect,instrument
from repair_v424_nand_aot_placeholder import aot_entry,MAX_CPP,MAX_SPAN
from repair_v447_nand_nested_placeholder import plan as prior_plan,regenerated,frame_geometry
from repair_v464_nand_missing_span import plan as missing_plan
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve
from extend_private_text import install,NOP

CONTROL='V437_FRAME_RESULT rc=134 begins=1 blr=0 resume=0 nested=2 max_calls=34 unique=23 original=22 first_nonoriginal=nop boot_verified=0'
@dataclass(frozen=True)
class NextPlan:
    pc:int
    size:int
    kind:str
    candidate:bytes
    prefix:tuple

def plan(owner,fixture,sizes,cpp,raw,prior_prefix):
    if inspect(raw,134,owner,fixture,sizes)!=CONTROL:raise ValueError('control')
    e=entries(raw)
    if len(e)!=35 or [x[0] for x in e]!=list(range(35)) or any(x[3] or x[1]&3 or x[2]&3 or not 0x80400000<=x[1]<0x80600000 for x in e):
        raise ValueError('route')
    if not prior_prefix or tuple(e[:len(prior_prefix)])!=tuple(prior_prefix):raise ValueError('lineage')
    unique=list(dict.fromkeys(x[1] for x in e))
    kinds=[classify(owner,fixture,sizes,pc)[0] for pc in unique]
    if len(unique)!=23 or kinds.count('original')!=22 or kinds.count('nop')!=1:raise ValueError('coverage')
    pc=unique[kinds.index('nop')]
    first=next(i for i,x in enumerate(e) if x[1]==pc)
    if first<len(prior_prefix) or aot_entry(cpp,pc)!=(1,1):raise ValueError('entry')
    w=resolve(sizes,pc)
    if w.kind not in ('exact','interior') or not 4<=w.length<=MAX_SPAN:raise ValueError('extent')
    before=text_at(fixture,pc,w.length);original=text_at(owner,pc,w.length)
    if before!=NOP*(w.length//4) or len(original)!=w.length or before==original:raise ValueError('placeholder')
    candidate=install(fixture,[(pc,before,original)])
    if text_at(candidate,pc,w.length)!=original or install(candidate,[(pc,original,before)])!=fixture:raise ValueError('roundtrip')
    if any(classify(owner,candidate,sizes,x)[0]!='original' for x in unique):raise ValueError('new coverage')
    return NextPlan(pc,w.length,w.kind,candidate,tuple(e[:first+1]))

def outcome(raw,rc,owner,sizes,p):
    e=entries(raw)
    if tuple(e[:len(p.prefix)])!=p.prefix:raise ValueError('repaired entry not reached')
    return inspect(raw,rc,owner,p.candidate,sizes).replace('V437_FRAME_RESULT','V471_FRAME_RESULT',1)+' restored_entry=1'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','base','base_cpp','base_log','base_observed','previous','previous_cpp','previous_observed','previous_log',
              'missing','missing_cpp','missing_observed','missing_log','candidate'):
        p.add_argument(n,type=Path)
    p.add_argument('--new-cpp',type=Path);p.add_argument('--out-cpp',type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int)
    a=p.parse_args()
    def read(path,cap,as_text=False):
        if path is None or path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if as_text else path.read_bytes()
    stage='input'
    try:
        owner=read(a.owner,20_000_000);elf=read(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);base=read(a.base,20_000_000);base_cpp=read(a.base_cpp,MAX_CPP,True)
        stage='previous'
        prior=prior_plan(owner,base,sizes,base_cpp,read(a.base_log,MAX_LOG))
        previous=read(a.previous,20_000_000);prev_cpp=read(a.previous_cpp,MAX_CPP,True)
        if prior.candidate!=previous or regenerated(owner,base,sizes,prior,base_cpp,read(a.base_observed,MAX_CPP,True),prev_cpp)!=read(a.previous_observed,MAX_CPP,True):raise ValueError('previous identity')
        stage='missing'
        missing=missing_plan(owner,previous,sizes,prev_cpp,read(a.previous_log,MAX_LOG),prior)
        fixture=read(a.missing,20_000_000);cpp=read(a.missing_cpp,MAX_CPP,True)
        geometry=frame_geometry(owner,base,sizes,prior)
        if fixture!=missing.candidate or instrument(cpp,*geometry)!=read(a.missing_observed,MAX_CPP,True) or any(aot_entry(cpp,pc)!=(1,1) for pc in {x[1] for x in missing.prefix}):raise ValueError('missing identity')
        stage='plan'
        q=plan(owner,fixture,sizes,cpp,read(a.missing_log,MAX_LOG),missing.prefix)
        if a.new_cpp is None:
            if a.out_cpp or a.run_log or a.run_rc is not None or a.candidate.exists() or a.candidate.is_symlink():raise ValueError('destination')
            with a.candidate.open('xb') as f:f.write(q.candidate)
            print(f'V471_REPAIR_PLAN kind={q.kind} words={q.size//4} restored=1 roundtrip=1 boot_verified=0')
        else:
            stage='instrument'
            if read(a.candidate,20_000_000)!=q.candidate or a.out_cpp is None:raise ValueError('candidate')
            new=read(a.new_cpp,MAX_CPP,True)
            if any(aot_entry(new,pc)!=(1,1) for pc in {x[1] for x in q.prefix}):raise ValueError('AOT prefix')
            observed=instrument(new,*geometry)
            if a.run_log is None:
                if a.run_rc is not None or a.out_cpp.exists() or a.out_cpp.is_symlink():raise ValueError('destination')
                with a.out_cpp.open('x',encoding='utf-8') as f:f.write(observed)
                print('V471_REPAIR_ROUTE installed=1 frame_preserved=1')
            else:
                stage='outcome'
                if a.run_rc is None or read(a.out_cpp,MAX_CPP,True)!=observed:raise ValueError('candidate code')
                print(outcome(read(a.run_log,MAX_LOG),a.run_rc,owner,sizes,q))
        print('V471_REPAIR_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,struct.error,UnicodeError):
        print(f'V471_REPAIR_REJECT stage={stage}');print('V471_REPAIR_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
