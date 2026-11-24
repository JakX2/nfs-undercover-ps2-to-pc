#!/usr/bin/env python3
"""Historical V390 post-ACK successor proof after authenticated V508 replay.

The V390 event-time guest/clear/registered/masked check remains unchanged.
Retain the earlier final PC/LR alternatives as a separate diagnostic. The
candidate does not change guest execution, later checks or device state.
"""
import argparse
from pathlib import Path
import hashlib
import re
import struct
from derive_v508_nand_ack_lifetime import eligible,patch as patch508,outcome, next_guard,EVENT
from derive_v478_nand_post_return import MAX_LOG,MAX_CPP,abort_row,GUARD_CLASSES,tracked_public_source
from make_osinit_execparams_v28 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
BEGIN='  const bool v390_completed='
END='  std::cout<<"V390_NAND_POST_ACK_TRIAL'
GUARD='''  check(v390_completed,
        "V390 original NAND guest never left Hollywood ACK for next callee");'''
CONTROL_ROW='V508_FRAME_RESULT rc=134 begins=1 blr=1 resume=1 nested=2 max_calls=44 unique=25 original=25 first_nonoriginal=none boot_verified=0 history=1 final_clear=0'
NEW='''  const bool v390_completed=v389_completed&&v508_historical&&
       nwii::runtime::v390_call_seen==1u&&
       nwii::runtime::v390_call_pc>=0x80400000u&&nwii::runtime::v390_call_pc<0x80600000u&&
       (nwii::runtime::v390_call_pc&3u)==0u&&
       nwii::runtime::v390_call_lr>=0x805190c0u&&nwii::runtime::v390_call_lr<0x80519318u&&
       (nwii::runtime::v390_call_lr&3u)==0u&&
       nwii::runtime::v508_post_inst>nwii::runtime::v508_ack_inst&&
       nwii::runtime::v508_post_inst<=c.inst_count;
  std::cout<<"V542_NAND_SUCCESSOR_TRIAL history="<<unsigned(v390_completed)
           <<" legacy_stop="<<unsigned(v542_legacy_successor)<<std::endl;
'''
MARKER=re.compile(rb'V542_NAND_SUCCESSOR_TRIAL history=([01]) legacy_stop=([01])')
def authenticated(owner,fixture,sizes,cpp,base,control,prior,raw,rc=134):
    p=eligible(owner,fixture,sizes,cpp,base,control)
    if prior!=patch508(base) or rc!=134 or outcome(raw,rc,owner,fixture,sizes,p)!=CONTROL_ROW:
        raise ValueError('V508 predecessor')
    rows=next_guard(raw,rc,prior,Path(__file__).resolve().parent,())
    if len(rows)!=1 or ' class=post_ack ' not in rows[0]:raise ValueError('successor guard')
    return p
def patch(source):
    if 'v542_' in source or any(source.count(s)!=1 for s in (BEGIN,END,GUARD,'const bool v508_historical=')):
        raise ValueError('seam')
    a=source.index(BEGIN);b=source.index(END,a)
    old=source[a:b]
    if not old.endswith(';\n') or any(s not in old for s in ('v389_completed','v390_call_seen','v390_call_pc','v390_call_lr','c.pc==','c.lr==')):
        raise ValueError('legacy proof')
    new=old.replace(BEGIN,'  const bool v542_legacy_successor=',1)+NEW
    out=source[:a]+new+source[b:]
    if out.replace(new,old,1)!=source or out.count(GUARD)!=1:raise ValueError('roundtrip')
    return out
def inspect(raw,rc,owner,fixture,sizes,p):
    row=outcome(raw,rc,owner,fixture,sizes,p)
    matches=[MARKER.fullmatch(l) for l in raw.splitlines() if l.startswith(b'V542_NAND_SUCCESSOR_TRIAL ')]
    if len(matches)!=1 or matches[0] is None or matches[0][1]!=b'1':raise ValueError('successor event')
    return row.replace('V508_FRAME_RESULT','V542_FRAME_RESULT',1)+' successor=1 legacy_stop='+matches[0][2].decode()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','base','control','prior','prior_log','output'):p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    def get(path,cap,as_text=False):
        if path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if as_text else path.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000);prior=get(a.prior,24_000_000,True)
        q=authenticated(owner,fixture,sizes,get(a.cpp,MAX_CPP,True),get(a.base,24_000_000,True),get(a.control,MAX_LOG),prior,get(a.prior_log,MAX_LOG))
        new=patch(prior)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V542_NAND_SUCCESSOR_ROUTE installed=1 legacy_snapshot=1 later_guards=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('identity')
            raw=get(a.run_log,MAX_LOG);print(inspect(raw,a.run_rc,owner,fixture,sizes,q))
            census=abort_row(raw,new,a.run_rc)[0]
            print(census.replace('V427_ABORT_CENSUS','V542_ABORT_CENSUS',1))
            host=Path(__file__).resolve().parent
            for row in next_guard(raw,a.run_rc,new,host,tracked_public_source(host)):
                print(row.replace('V517_NAND_','V542_NAND_',1))
        print('V542_NAND_SUCCESSOR_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V542_NAND_SUCCESSOR_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
