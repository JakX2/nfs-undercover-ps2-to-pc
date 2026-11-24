#!/usr/bin/env python3
"""Scope the obsolete region stop to the authenticated restored callback frame."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct
from derive_v432_nand_nested_call import OWNED,STOP,GUARD,patch as patch432,audit as audit432
from trace_v427_restored_function import branch,abort_row,MAX_LOG,MAX_CPP
from repair_v424_nand_aot_placeholder import aot_entry
from audit_v420_nand_sc_provenance import LINE
from audit_v414_nand_resumed_coverage import classify,TRIAL
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

INCLUDE='#include "wii_nand_y1_exception.h"'
STATE='static unsigned v395_next_seen=0u;'
SELECT='      v396_start_inst=ctx.inst_count;'
RESET='nwii::runtime::v395_next_lr=0u;'
BEGIN=b'V437_FRAME_BEGIN valid=1'
BLR=b'V437_FRAME_BLR valid=1'
RESUME=b'V437_FRAME_RESUME valid=1'
NESTED=re.compile(rb'V437_FRAME_NESTED call=([0-9]{1,3})')
PREFIX='V432_NESTED_RESULT rc=134 kind=signal trials=1 complete=0 target_seen=1 resumed=0 status3=0 same_retry=0 max_calls=2 boot_verified=0 retired_exact=1'
HOOKS=r'''static undercover::wii::RestoredFrameWitness v437_frame{};
void v437_before_return(CPUContext& ctx){
  if(!v437_frame.active())return;
  check(v437_frame.before_return(ctx.lr,ctx.gpr[1],ctx.inst_count),"V437 restored callback BLR frame mismatch");
  std::cout<<"V437_FRAME_BLR valid=1"<<std::endl;
}
void v437_after_return(CPUContext& ctx){
  if(!v437_frame.active())return;
  check(v437_frame.after_return(ctx.pc,ctx.gpr[1],ctx.inst_count),"V437 restored callback resume frame mismatch");
  std::cout<<"V437_FRAME_RESUME valid=1"<<std::endl;
}'''
DECL='#include "runtime/cpu_context.h"\nnamespace nwii::runtime { void v437_before_return(CPUContext&); void v437_after_return(CPUContext&); }\n'

def patch_harness(source,pc,lr):
    if pc&3 or lr&3 or not 0x80400000<=pc<0x80600000 or not 0x80400000<=lr<0x80600000:raise ValueError('frame geometry')
    if 'v437_frame' in source or any(source.count(a)!=1 for a in (INCLUDE,STATE,SELECT,RESET,OWNED,STOP,GUARD)):raise ValueError('harness seam')
    select=SELECT+f'''
      check(addr==0x{pc:08x}u&&ctx.lr==0x{lr:08x}u&&v437_frame.begin(ctx.lr,ctx.gpr[1],ctx.inst_count),"V437 selected original frame mismatch");
      std::cout<<"V437_FRAME_BEGIN valid=1"<<std::endl;'''
    ownership=OWNED.replace('const bool owned','const bool v437_region_owned')+'''
    const bool owned=v437_region_owned&&!v437_frame.active();
    if(v437_region_owned&&!owned)
      std::cout<<"V437_FRAME_NESTED call="<<(v396_calls+1u)<<std::endl;'''
    pairs=((INCLUDE,INCLUDE+'\n#include "wii_restored_frame_v437.h"'),
           (STATE,STATE+'\n'+HOOKS),(SELECT,select),(RESET,RESET+'\n  nwii::runtime::v437_frame={};'),(OWNED,ownership))
    out=source
    for a,b in pairs:out=out.replace(a,b,1)
    back=out
    for a,b in reversed(pairs):
        if back.count(b)!=1:raise ValueError('roundtrip')
        back=back.replace(b,a,1)
    if back!=source or out.count(STOP)!=1 or out.count(GUARD)!=1:raise ValueError('guard')
    return out

def instrument(source,ret,lr,resume_word):
    if ret==lr or 'v437_before_return' in source:raise ValueError('instruction geometry')
    out=source
    insertions=[]
    for pc,word,hook in ((ret,0x4e800020,'before'),(lr,resume_word,'after')):
        pat=re.compile(r'(?m)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}'+r': '+f'{word:08X}'+r'\n',re.I)
        hits=list(pat.finditer(out))
        if len(hits)!=1:raise ValueError('unique instruction seam')
        line=f'    nwii::runtime::v437_{hook}_return(ctx);\n'
        at=hits[0].end()
        out=out[:at]+line+out[at:];insertions.append(line)
    back=out
    for line in insertions:
        if back.count(line)!=1:raise ValueError('roundtrip')
        back=back.replace(line,'',1)
    if back!=source:raise ValueError('roundtrip')
    return DECL+out

def entries(raw):
    if len(raw)>MAX_LOG:raise ValueError('log size')
    out=[]
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            out.append((int(m[1]),int(m[2],16),int(m[3],16),int(m[8])))
    return out

def control(owner,fixture,sizes,cpp,raw,old,new,reader=text_at):
    e=entries(raw)
    if len(e)!=3 or [x[0] for x in e]!=[0,1,2] or any(x[3] for x in e):raise ValueError('control entries')
    _,pc,lr,_=e[0];_,target,back,_=e[1]
    if sizes.get(pc)!=60 or not 0x804f0e04<=lr<0x804f0f84 or back!=pc+24:raise ValueError('frame')
    if audit432(raw,134,pc,target,back)!=PREFIX or new!=patch432(old,pc,target,back):raise ValueError('control route')
    if not abort_row(raw,new,134)[1].endswith('label=V402 extended original guest frontier incomplete'):raise ValueError('control guard')
    words=struct.unpack('>15I',reader(owner,pc,60))
    if branch(words[5],pc+20)!=('direct_link',target):raise ValueError('direct edge')
    for addr in (pc,target):
        if classify(owner,fixture,sizes,addr,reader)[0]!='original' or aot_entry(cpp,addr)!=(1,1):raise ValueError('original coverage')
    rets=[pc+4*i for i,w in enumerate(words) if w==0x4e800020]
    if len(rets)!=1:raise ValueError('return geometry')
    word=reader(owner,lr,4)
    if reader(fixture,lr,4)!=word:raise ValueError('resume instruction coverage')
    return pc,lr,rets[0],struct.unpack('>I',word)[0]

def inspect(raw,rc,owner,fixture,sizes,reader=text_at):
    if not 0<=rc<=255 or len(raw)>MAX_LOG:raise ValueError('geometry')
    phase=0;begins=returns=resumes=retired=0;last=0;pending=None
    for line in raw.splitlines():
        if line==BEGIN:
            if phase or begins>=16:raise ValueError('begin order')
            begins+=1;phase=1;last=0
        elif line==BLR:
            if phase!=1 or pending is not None:raise ValueError('blr order')
            returns+=1;phase=2
        elif line==RESUME:
            if phase!=2:raise ValueError('resume order')
            resumes+=1;phase=3
        elif line.startswith(b'V437_FRAME_NESTED'):
            m=NESTED.fullmatch(line)
            if not m or phase not in (1,2) or pending is not None or not last<int(m[1])<=192:raise ValueError('nested order')
            pending=int(m[1]);last=pending
        elif line.startswith(b'V420_CB_ENTRY') and pending is not None:
            m=LINE.fullmatch(line)
            if not m or int(m[1])!=pending:raise ValueError('nested entry')
            retired+=1;pending=None
        elif line==TRIAL:
            if pending is not None:raise ValueError('trial order')
            phase=0
        elif line.startswith(b'V437_FRAME_'):
            raise ValueError('marker')
    if pending is not None:raise ValueError('nested incomplete')
    e=entries(raw)
    unique=list(dict.fromkeys(pc for _,pc,_,_ in e))
    kinds=[classify(owner,fixture,sizes,pc,reader)[0] for pc in unique]
    first=next((k for k in kinds if k!='original'),'none')
    return (f'V437_FRAME_RESULT rc={rc} begins={begins} blr={returns} resume={resumes} nested={retired} '
            f'max_calls={max((x[0] for x in e),default=0)} unique={len(unique)} original={kinds.count("original")} first_nonoriginal={first} boot_verified=0')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','candidate','candidate_cpp','control_log','base_harness','control_harness','out_harness','out_cpp'):p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    try:
        for path,cap in ((a.owner,20_000_000),(a.elf,64_000_000),(a.candidate,20_000_000),(a.candidate_cpp,MAX_CPP),(a.control_log,MAX_LOG),(a.base_harness,24_000_000),(a.control_harness,24_000_000)):
            if path.stat().st_size>cap:raise ValueError('size')
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.candidate.read_bytes();cpp=a.candidate_cpp.read_text(encoding='utf-8')
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);old=a.base_harness.read_text(encoding='utf-8');new=a.control_harness.read_text(encoding='utf-8')
        pc,lr,ret,word=control(owner,fixture,sizes,cpp,a.control_log.read_bytes(),old,new)
        harness=patch_harness(old,pc,lr);generated=instrument(cpp,ret,lr,word)
        if a.run_log is None:
            for path in (a.out_harness,a.out_cpp):
                if path.exists() or path.is_symlink():raise ValueError('destination')
            with a.out_harness.open('x',encoding='utf-8') as f:f.write(harness)
            with a.out_cpp.open('x',encoding='utf-8') as f:f.write(generated)
            print('V437_FRAME_ROUTE installed=1 exact_return=1 cap=192 guards_preserved=1')
        else:
            if a.run_rc is None or a.run_log.stat().st_size>MAX_LOG or a.out_harness.read_text(encoding='utf-8')!=harness or a.out_cpp.read_text(encoding='utf-8')!=generated:raise ValueError('run control')
            raw=a.run_log.read_bytes();print(inspect(raw,a.run_rc,owner,fixture,sizes))
            for row in abort_row(raw,harness,a.run_rc):print(row.replace('V427_','V437_',1))
        print('V437_FRAME_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,struct.error,UnicodeError):
        print('V437_FRAME_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
