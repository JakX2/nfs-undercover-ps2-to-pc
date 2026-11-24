#!/usr/bin/env python3
"""Audit V391 successor history; replay only if the original event is proven."""
import argparse,hashlib,re,struct
from pathlib import Path
from derive_v542_nand_successor_lifetime import authenticated as auth542,patch as patch542,inspect as inspect542
from derive_v508_nand_ack_lifetime import patch as patch508,next_guard
from derive_v478_nand_post_return import MAX_LOG,MAX_CPP,abort_row,tracked_public_source
from make_osinit_execparams_v28 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
BEGIN='  const bool v391_completed='
END='  std::cout<<"V391_NAND_POST_ACK_TRIAL'
GUARD='''  check(v391_completed,
        "V391 original NAND post-ACK call trace did not reach real boundary");'''
EVENT=re.compile(rb'V391_NAND_POST_ACK_EVENT kind=([12]) verified=([01]) owner=([01]) cache=([01]) context=([01]) callback=([01]) cap=([01])')
POST=re.compile(rb'V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=[01] context=[01]')
TRIAL=re.compile(rb'V391_NAND_POST_ACK_TRIAL kind=([012]) stopped=([01]) completed=([01])')
PROOF=re.compile(rb'V551_NAND_CHAIN_TRIAL history=([01]) legacy_stop=([01])')
NEW='''  const bool v391_completed=v390_completed&&
       nwii::runtime::v391_kind==1u&&
       nwii::runtime::v391_calls>=1u&&nwii::runtime::v391_calls<=16u&&
       nwii::runtime::v391_next_pc>=0x80400000u&&nwii::runtime::v391_next_pc<0x80600000u&&
       (nwii::runtime::v391_next_pc&3u)==0u&&
       nwii::runtime::v391_next_lr>=0x805190c0u&&nwii::runtime::v391_next_lr<0x80519318u&&
       (nwii::runtime::v391_next_lr&3u)==0u&&
       nwii::runtime::v392_start_inst>nwii::runtime::v508_post_inst&&
       nwii::runtime::v392_start_inst<=c.inst_count;
  std::cout<<"V551_NAND_CHAIN_TRIAL history="<<unsigned(v391_completed)
           <<" legacy_stop="<<unsigned(v551_legacy_chain)<<std::endl;
'''
def one(lines,prefix,pattern):
    rows=[(i,pattern.fullmatch(l)) for i,l in enumerate(lines) if l.startswith(prefix)]
    if len(rows)!=1 or rows[0][1] is None:raise ValueError('missing or repeated event')
    return rows[0]
def history(raw,require_trial=True):
    if len(raw)>MAX_LOG:raise ValueError('log size')
    lines=raw.splitlines()
    a,_=one(lines,b'V390_NAND_POST_ACK ',POST)
    b,event=one(lines,b'V391_NAND_POST_ACK_EVENT ',EVENT)
    if not a<b or event.groups()[:3]!=(b'1',b'1',b'1') or event[7]!=b'0':raise ValueError('owner successor')
    if require_trial:
        c,trial=one(lines,b'V391_NAND_POST_ACK_TRIAL ',TRIAL)
        if not b<c or trial[1]!=b'1' or trial[3]!=b'0':raise ValueError('legacy trial')
    return 'V551_NAND_CHAIN_HISTORY owner=1 ordered=1 verified=1 boot_verified=0'
def patch(source):
    if 'v551_' in source or any(source.count(s)!=1 for s in (BEGIN,END,GUARD,'v392_start_inst=ctx.inst_count;')):
        raise ValueError('seam')
    a=source.index(BEGIN);b=source.index(END,a);old=source[a:b]
    if not old.endswith(';\n') or any(s not in old for s in ('v390_completed','v391_kind','v391_calls','v391_next_pc','v391_next_lr','c.pc==','c.lr==')):
        raise ValueError('legacy proof')
    new=old.replace(BEGIN,'  const bool v551_legacy_chain=',1)+NEW
    out=source[:a]+new+source[b:]
    if out.replace(new,old,1)!=source or out.count(GUARD)!=1:raise ValueError('roundtrip')
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','base','control','prior','prior_log','candidate','candidate_log','output'):p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    def get(path,cap,as_text=False):
        if path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if as_text else path.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000);prior=get(a.prior,24_000_000,True)
        q=auth542(owner,fixture,sizes,get(a.cpp,MAX_CPP,True),get(a.base,24_000_000,True),get(a.control,MAX_LOG),prior,get(a.prior_log,MAX_LOG))
        candidate=get(a.candidate,24_000_000,True);raw=get(a.candidate_log,MAX_LOG)
        if candidate!=patch542(prior) or not inspect542(raw,134,owner,fixture,sizes,q).endswith('successor=1 legacy_stop=0'):raise ValueError('V542 control')
        if not abort_row(raw,candidate,134)[1].endswith('label=V391 original NAND post-ACK call trace did not reach real boundary'):raise ValueError('guard identity')
        print(history(raw));new=patch(candidate)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V551_NAND_CHAIN_ROUTE installed=1 legacy_snapshot=1 later_guards=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('candidate identity')
            raw=get(a.run_log,MAX_LOG);history(raw,False)
            _,m=one(raw.splitlines(),b'V551_NAND_CHAIN_TRIAL ',PROOF)
            if m[1]!=b'1':raise ValueError('historical proof')
            row=inspect542(raw,a.run_rc,owner,fixture,sizes,q)
            print(row.replace('V542_FRAME_RESULT','V551_FRAME_RESULT',1)+' chain=1 chain_legacy='+m[2].decode())
            host=Path(__file__).resolve().parent
            for row in next_guard(raw,a.run_rc,new,host,tracked_public_source(host)):
                print(row.replace('V517_NAND_','V551_NAND_',1))
        print('V551_NAND_CHAIN_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V551_NAND_CHAIN_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
