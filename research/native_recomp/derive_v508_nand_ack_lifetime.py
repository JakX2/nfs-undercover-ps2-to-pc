#!/usr/bin/env python3
"""V508: preserve historical IRQ ACK proof across the original callback.

Only install on the independently authenticated V471 control and V506
ordered ACK history. Keep both event-time checks, all later guest guards,
and the final IRQ snapshot as a diagnostic. No PC, registers, guest RAM,
mailbox, IRQ state or translated instruction is modified.
"""
import argparse
import hashlib
from pathlib import Path
import re
import struct
from derive_v478_nand_post_return import terminal,trace,ack_history,ACK_GUARD,MAX_LOG,MAX_CPP,RESUME,inspect,abort_row
from make_osinit_execparams_v28 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
STATE='static uint64_t v389_y1_inst=0u;'
RESET='  nwii::runtime::v389_y1_inst=0u;'
ACK='''        check(verified,
              "V389 original NAND PPC_FLAG guest W1C failed distinct ACK proof");'''
POST='''    check(guest&&clear&&registered&&masked,
          "V390 original NAND post-ACK guest successor not authenticated");'''
FINAL='''  const bool v389_completed=v388_completed&&
       nwii::runtime::v389_flag_seen==1u&&
       nwii::runtime::v389_after_y1&&
       nwii::runtime::v388_kind==1u&&
       v389_ctrl.has_value()&&v389_flag.has_value()&&
       ((*v389_ctrl&(undercover::wii::IpcMailbox::Y1|
                     undercover::wii::IpcMailbox::Y2))==0u)&&
       ((*v389_flag&undercover::wii::HollywoodIrq::IPC_PPC)==0u)&&
       !nwii::runtime::ipc70_bus.external_irq_level();'''
NEW_FINAL=FINAL.replace('const bool v389_completed=v388_completed&&\n       nwii::runtime::v389_flag_seen==1u&&\n       nwii::runtime::v389_after_y1&&\n       nwii::runtime::v388_kind==1u&&','const bool v508_final_clear=')+'''
  const bool v508_historical=nwii::runtime::v508_ack_inst!=0u&&
       nwii::runtime::v508_post_inst>nwii::runtime::v508_ack_inst&&
       nwii::runtime::v508_ack_inst>nwii::runtime::v389_y1_inst&&
       nwii::runtime::v508_post_inst<=c.inst_count&&
       nwii::runtime::v390_call_seen==1u;
  const bool v389_completed=v388_completed&&
       nwii::runtime::v389_flag_seen==1u&&
       nwii::runtime::v389_after_y1&&nwii::runtime::v388_kind==1u&&v508_historical;
  std::cout<<"V508_NAND_ACK_TRIAL history="<<unsigned(v508_historical)
           <<" final_clear="<<unsigned(v508_final_clear)
           <<" completed="<<unsigned(v389_completed)<<std::endl;'''
GUARD='''  check(v389_completed,
        "V389 original NAND Hollywood flag ACK did not release native IRQ");'''
EVENT=re.compile(rb'V508_NAND_ACK_TRIAL history=([01]) final_clear=([01]) completed=([01])')
def eligible(owner,fixture,sizes,cpp,harness,raw):
    p=terminal(owner,fixture,sizes,cpp,harness,raw)
    if p.ready or p.owned or not ack_history(raw,harness).endswith('stale_candidate=1 boot_verified=0'):
        raise ValueError('history not authenticated')
    return p
def patch(harness):
    if 'v508_' in harness or any(harness.count(s)!=1 for s in (STATE,RESET,ACK,POST,FINAL,GUARD)):
        raise ValueError('seam')
    pairs=((STATE,STATE+'\nstatic uint64_t v508_ack_inst=0u,v508_post_inst=0u;'),
           (RESET,RESET+'\n  nwii::runtime::v508_ack_inst=nwii::runtime::v508_post_inst=0u;'),
           (ACK,ACK+'''
        check(v508_ack_inst==0u&&ipc70_ram.cpu->inst_count>v389_y1_inst,
              "V508 repeated or unordered ACK event");
        v508_ack_inst=ipc70_ram.cpu->inst_count;'''),
           (POST,POST+'''
    check(v508_ack_inst!=0u&&v508_post_inst==0u&&ctx.inst_count>v508_ack_inst,
          "V508 missing or unordered post-ACK event");
    v508_post_inst=ctx.inst_count;'''),
           (FINAL,NEW_FINAL))
    out=harness
    for a,b in pairs:out=out.replace(a,b,1)
    back=out
    for a,b in reversed(pairs):
        if back.count(b)!=1:raise ValueError('reverse seam')
        back=back.replace(b,a,1)
    if back!=harness or out.count(GUARD)!=1:raise ValueError('guard')
    return out
def outcome(raw,rc,owner,fixture,sizes,p):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('log')
    e=trace(raw);key=lambda x:(x[0],x[1],x[2],x[7])
    if tuple(map(key,e[:len(p.prefix)]))!=tuple(map(key,p.prefix)):raise ValueError('prefix')
    lines=raw.splitlines();rows=[(i,EVENT.fullmatch(l)) for i,l in enumerate(lines) if l.startswith(b'V508_NAND_ACK_TRIAL ')]
    if len(rows)!=1 or rows[0][1] is None or lines.index(RESUME)>=rows[0][0]:raise ValueError('event')
    hist,clear,done=map(int,rows[0][1].groups())
    if not hist or not done:raise ValueError('historical ACK failed')
    # Passing this assertion is not the same as completing the callback.
    result=inspect(raw,rc,owner,fixture,sizes).replace('V437_FRAME_RESULT','V508_FRAME_RESULT',1)
    return result+f' history=1 final_clear={clear}'
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','harness','control','output'):p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    def get(path,cap,as_text=False):
        if path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if as_text else path.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000);harness=get(a.harness,24_000_000,True)
        q=eligible(owner,fixture,sizes,get(a.cpp,MAX_CPP,True),harness,get(a.control,MAX_LOG))
        new=patch(harness)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V508_NAND_ACK_ROUTE installed=1 event_checks=1 final_snapshot=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('candidate identity')
            raw=get(a.run_log,MAX_LOG)
            print(outcome(raw,a.run_rc,owner,fixture,sizes,q))
            print(abort_row(raw,new,a.run_rc)[0].replace('V427_ABORT_CENSUS','V508_ABORT_CENSUS',1))
        print('V508_NAND_ACK_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V508_NAND_ACK_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
