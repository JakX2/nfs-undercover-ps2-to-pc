#!/usr/bin/env python3
"""Restore only the uniquely observed missing original function extent.

Authenticate the previous private image and generated source via V447
before this additional repair. Do not publish addresses or owner bytes.
"""
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
from audit_v414_nand_resumed_coverage import classify,MAX_LOG
from derive_v437_nand_restored_frame import entries,inspect,instrument
from repair_v424_nand_aot_placeholder import aot_entry,MAX_CPP,MAX_SPAN
from repair_v447_nand_nested_placeholder import plan as previous_plan,regenerated,frame_geometry,outcome
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve
from extend_private_text import NOP,unpack,repack,install

CONTROL='V447_FRAME_RESULT rc=134 begins=1 blr=0 resume=0 nested=2 max_calls=192 unique=6 original=5 first_nonoriginal=missing boot_verified=0 restored_entry=1'

@dataclass(frozen=True)
class MissingPlan:
    pc:int
    size:int
    mapped:int
    kind:str
    candidate:bytes
    prefix:tuple

def restore_missing(owner,fixture,sizes,pc):
    w=resolve(sizes,pc)
    if w.kind not in ('exact','interior') or not 4<=w.length<=MAX_SPAN:raise ValueError('extent')
    if classify(owner,fixture,sizes,pc)[0]!='missing':raise ValueError('not missing')
    original=text_at(owner,pc,w.length)
    slots=unpack(fixture)
    end=pc+w.length
    overlap=[s for s in slots if s[2]<end and pc<s[2]+len(s[3])]
    if len(overlap)>1 or (overlap and (overlap[0][0] or overlap[0][2]>pc)):
        raise ValueError('overlap')
    present=b''
    if overlap:
        _,_,base,body=overlap[0]
        present=bytes(body[pc-base:min(len(body),end-base)])
    if len(present)>=w.length or len(present)%4:raise ValueError('geometry')
    # Only exact original prefix words or explicit NOP placeholders may
    # already exist. Preserve all unrelated bytes and reject modified stubs.
    for i in range(0,len(present),4):
        if present[i:i+4] not in (original[i:i+4],NOP):raise ValueError('modified')
    expected=present+NOP*((w.length-len(present))//4)
    candidate=install(fixture,[(pc,expected,original)])
    if text_at(candidate,pc,w.length)!=original:raise ValueError('coverage')
    # Restore old bytes, remove only newly extended tail, and repack to
    # prove complete reversible DOL identity, including existing metadata.
    back=install(candidate,[(pc,original,expected)])
    restored=unpack(back)
    if len(restored)!=len(slots):raise ValueError('slots')
    trimmed=[]
    for a,b in zip(slots,restored):
        if a[:3]!=b[:3] or len(a[3])>len(b[3]):raise ValueError('relocation')
        trimmed.append((*b[:3],b[3][:len(a[3])]))
    if repack(fixture,trimmed)!=fixture:raise ValueError('roundtrip')
    return w,candidate,len(present)

def plan(owner,fixture,sizes,cpp,raw,prior):
    if outcome(raw,134,owner,sizes,prior)!=CONTROL:raise ValueError('control')
    e=entries(raw)
    if len(e)!=193 or [x[0] for x in e]!=list(range(193)) or any(x[3] or x[1]&3 or x[2]&3 or not 0x80400000<=x[1]<0x80600000 for x in e):
        raise ValueError('route')
    unique=list(dict.fromkeys(x[1] for x in e))
    kinds=[classify(owner,fixture,sizes,pc)[0] for pc in unique]
    if len(unique)!=6 or kinds.count('original')!=5 or kinds.count('missing')!=1:
        raise ValueError('coverage')
    pc=unique[kinds.index('missing')]
    if aot_entry(cpp,pc)!=(1,1):raise ValueError('aot')
    first=next(i for i,x in enumerate(e) if x[1]==pc)
    w,candidate,present=restore_missing(owner,fixture,sizes,pc)
    if any(classify(owner,candidate,sizes,x)[0]!='original' for x in unique):raise ValueError('restoration')
    return MissingPlan(pc,w.length,present,w.kind,candidate,tuple(e[:first+1]))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','base','base_cpp','base_log','base_observed','previous','previous_cpp','previous_observed','previous_log','candidate'):
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
        base_observed=read(a.base_observed,MAX_CPP,True)
        stage='previous'
        prior=previous_plan(owner,base,sizes,base_cpp,read(a.base_log,MAX_LOG))
        fixture=read(a.previous,20_000_000);cpp=read(a.previous_cpp,MAX_CPP,True)
        if prior.candidate!=fixture or regenerated(owner,base,sizes,prior,base_cpp,base_observed,cpp)!=read(a.previous_observed,MAX_CPP,True):raise ValueError('previous identity')
        stage='plan'
        raw=read(a.previous_log,MAX_LOG)
        q=plan(owner,fixture,sizes,cpp,raw,prior)
        if a.new_cpp is None:
            if a.out_cpp or a.run_log or a.run_rc is not None or a.candidate.exists() or a.candidate.is_symlink():raise ValueError('destination')
            with a.candidate.open('xb') as f:f.write(q.candidate)
            print(f'V464_MISSING_PLAN kind={q.kind} words={q.size//4} mapped_words={q.mapped//4} restored=1 roundtrip=1 boot_verified=0')
        else:
            stage='instrument'
            if read(a.candidate,20_000_000)!=q.candidate or a.out_cpp is None:raise ValueError('candidate')
            new=read(a.new_cpp,MAX_CPP,True)
            if any(aot_entry(new,x[1])!=(1,1) for x in q.prefix):raise ValueError('AOT prefix')
            observed=instrument(new,*frame_geometry(owner,base,sizes,prior))
            if a.run_log is None:
                if a.run_rc is not None or a.out_cpp.exists() or a.out_cpp.is_symlink():raise ValueError('destination')
                with a.out_cpp.open('x',encoding='utf-8') as f:f.write(observed)
                print('V464_MISSING_ROUTE installed=1 frame_preserved=1')
            else:
                stage='outcome'
                if a.run_rc is None or read(a.out_cpp,MAX_CPP,True)!=observed:raise ValueError('candidate code')
                result=read(a.run_log,MAX_LOG);e=entries(result)
                if tuple(e[:len(q.prefix)])!=q.prefix:raise ValueError('route changed before repair')
                print(inspect(result,a.run_rc,owner,q.candidate,sizes).replace('V437_FRAME_RESULT','V464_FRAME_RESULT',1)+' restored_entry=1')
        print('V464_MISSING_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,struct.error,UnicodeError):
        print(f'V464_MISSING_REJECT stage={stage}');print('V464_MISSING_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
