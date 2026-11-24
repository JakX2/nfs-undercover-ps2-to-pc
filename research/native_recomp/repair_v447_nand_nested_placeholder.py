#!/usr/bin/env python3
"""Restore the next observed original-only nested function in V437's private image."""
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
from audit_v414_nand_resumed_coverage import classify,MAX_LOG
from repair_v424_nand_aot_placeholder import aot_entry,MAX_CPP,MAX_SPAN
from derive_v437_nand_restored_frame import entries,inspect,instrument
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve
from extend_private_text import install,NOP

CONTROL='V437_FRAME_RESULT rc=134 begins=1 blr=0 resume=0 nested=2 max_calls=4 unique=5 original=4 first_nonoriginal=nop boot_verified=0'
class RepairRejected(ValueError):
    # Fixed stage names only; never expose exception messages or owner PCs.
    def __init__(self,reason,ordinal=0,body=0,dispatch=0):
        self.reason=reason;self.ordinal=ordinal;self.body=body;self.dispatch=dispatch
        super().__init__('private repair rejected')
    def row(self):
        return f'V452_REPAIR_REJECT reason={self.reason} ordinal={self.ordinal} body={self.body} dispatch={self.dispatch}'

def require(ok,reason,ordinal=0,body=0,dispatch=0):
    if not ok:raise RepairRejected(reason,ordinal,body,dispatch)

@dataclass(frozen=True)
class Plan:
    pc:int
    size:int
    kind:str
    candidate:bytes
    prefix:tuple
    def row(self):
        return f'V447_REPAIR_PLAN kind={self.kind} words={self.size//4} body=1 dispatch=1 restored=1 roundtrip=1 boot_verified=0'

def plan(owner,fixture,sizes,cpp,raw,reader=text_at):
    try:e=entries(raw)
    except ValueError:raise RepairRejected('entry_parse') from None
    require(len(e)==5 and [x[0] for x in e]==list(range(5)),'entry_order')
    for i,x in enumerate(e,1):
        require(not x[3] and not x[1]&3 and not x[2]&3,'entry_state',i)
        require(0x80400000<=x[1]<0x80600000,'entry_range',i)
    require(len({x[1] for x in e})==5,'entry_unique')
    try:summary=inspect(raw,134,owner,fixture,sizes,reader)
    except ValueError:raise RepairRejected('control_parse') from None
    require(summary==CONTROL,'control_result')
    for i,x in enumerate(e,1):
        require(classify(owner,fixture,sizes,x[1],reader)[0]==('nop' if i==5 else 'original'),'coverage',i)
    pc=e[-1][1];w=resolve(sizes,pc)
    require(w.kind in ('exact','interior') and 4<=w.length<=MAX_SPAN,'extent',5)
    body,dispatch=aot_entry(cpp,pc)
    require((body,dispatch)==(1,1),'aot_entry',5,body,dispatch)
    try:before=reader(fixture,pc,w.length);original=reader(owner,pc,w.length)
    except (ValueError,IndexError,struct.error):raise RepairRejected('mapping',5) from None
    require(len(before)==w.length and len(original)==w.length and before==NOP*(w.length//4) and original!=before,'placeholder',5)
    try:
        candidate=install(fixture,[(pc,before,original)])
        require(reader(candidate,pc,w.length)==original and install(candidate,[(pc,original,before)])==fixture,'roundtrip',5)
    except RepairRejected:raise
    except (ValueError,IndexError,struct.error):raise RepairRejected('installation',5) from None
    for i,x in enumerate(e,1):
        require(classify(owner,candidate,sizes,x[1],reader)[0]=='original','new_coverage',i)
    return Plan(pc,w.length,w.kind,candidate,tuple(e))

def frame_geometry(owner,fixture,sizes,p,reader=text_at):
    _,pc,lr,_=p.prefix[0]
    if sizes.get(pc)!=60 or not 0x804f0e04<=lr<0x804f0f84:raise ValueError('frame')
    words=struct.unpack('>15I',reader(owner,pc,60))
    rets=[pc+4*i for i,w in enumerate(words) if w==0x4e800020]
    word=reader(owner,lr,4)
    if len(rets)!=1 or reader(fixture,lr,4)!=word:raise ValueError('resume')
    return rets[0],lr,struct.unpack('>I',word)[0]

def regenerated(owner,fixture,sizes,p,old_cpp,old_observed,new_cpp,reader=text_at):
    geometry=frame_geometry(owner,fixture,sizes,p,reader)
    if instrument(old_cpp,*geometry)!=old_observed or aot_entry(new_cpp,p.pc)!=(1,1):raise ValueError('generation')
    # Preserve exact native entry provenance for the whole observed prefix.
    if any(aot_entry(new_cpp,x[1])!=(1,1) for x in p.prefix):raise ValueError('prefix AOT')
    return instrument(new_cpp,*geometry)

def outcome(raw,rc,owner,sizes,p,reader=text_at):
    e=entries(raw)
    if tuple(e[:5])!=p.prefix:raise ValueError('route changed before restored entry')
    if classify(owner,p.candidate,sizes,p.pc,reader)[0]!='original':raise ValueError('restoration')
    return inspect(raw,rc,owner,p.candidate,sizes,reader).replace('V437_FRAME_RESULT','V447_FRAME_RESULT',1)+' restored_entry=1'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','old_cpp','control_log','old_observed','candidate'):parser.add_argument(n,type=Path)
    parser.add_argument('--new-cpp',type=Path);parser.add_argument('--out-cpp',type=Path)
    parser.add_argument('--run-log',type=Path);parser.add_argument('--run-rc',type=int);a=parser.parse_args()
    def read(path,cap,as_text=False):
        if path is None or path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if as_text else path.read_bytes()
    stage='input'
    try:
        owner=read(a.owner,20_000_000);elf=read(a.elf,64_000_000);fixture=read(a.fixture,20_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        stage='symbols'
        sizes=parse_functions(elf);stage='source';old=read(a.old_cpp,MAX_CPP,True);observed=read(a.old_observed,MAX_CPP,True)
        stage='plan'
        p=plan(owner,fixture,sizes,old,read(a.control_log,MAX_LOG))
        stage='frame'
        if instrument(old,*frame_geometry(owner,fixture,sizes,p))!=observed:raise ValueError('control instrumentation')
        stage='destination'
        if a.new_cpp is None:
            if a.out_cpp or a.run_log or a.run_rc is not None or a.candidate.exists() or a.candidate.is_symlink():raise ValueError('destination')
            with a.candidate.open('xb') as f:f.write(p.candidate)
            print(p.row())
        else:
            if read(a.candidate,20_000_000)!=p.candidate or a.out_cpp is None:raise ValueError('candidate')
            stage='regeneration'
            new=regenerated(owner,fixture,sizes,p,old,observed,read(a.new_cpp,MAX_CPP,True))
            stage='output'
            if a.run_log is None:
                if a.run_rc is not None or a.out_cpp.exists() or a.out_cpp.is_symlink():raise ValueError('destination')
                with a.out_cpp.open('x',encoding='utf-8') as f:f.write(new)
                print('V447_REPAIR_ROUTE installed=1 frame_preserved=1')
            else:
                if a.run_rc is None or read(a.out_cpp,MAX_CPP,True)!=new:raise ValueError('candidate code')
                stage='outcome'
                print(outcome(read(a.run_log,MAX_LOG),a.run_rc,owner,sizes,p))
        print('V447_REPAIR_AUDIT inspected=1');return 0
    except RepairRejected as e:
        print(e.row());print('V447_REPAIR_AUDIT inspected=0');return 1
    except (OSError,ValueError,IndexError,struct.error,UnicodeError):
        print(f'V452_REPAIR_REJECT reason={stage} ordinal=0 body=0 dispatch=0')
        print('V447_REPAIR_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
