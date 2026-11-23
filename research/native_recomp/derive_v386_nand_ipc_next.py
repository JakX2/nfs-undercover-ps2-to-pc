#!/usr/bin/env python3
"""V386: resume original second NAND IPC read until next linked guest helper.

V385 authenticates IpcReplyHandler's second IPCReadReg call at
0x8051905C (LR 0x805190FC). Resume exactly this stopped translated guest
function and observe the next original helper called by the reply handler.
Classify the known 0x8051906C PPCCTRL writer and cache entry, but do not
require either, synthesize guest PC, IOS reply, ACK or a NAND callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v385_second_seen=0u;'
STATE_NEW='''static unsigned v385_second_seen=0u;
static bool v386_active=false;
static unsigned v386_next_seen=0u;
static uint64_t v386_start_inst=0u;
static uint32_t v386_next_pc=0u,v386_next_lr=0u;'''
TAIL='  continue; // finish this authenticated NAND-only bounded trial'
MARKER='V386_NAND_NEXT_ENTRY guest='
TRIAL='V386_NAND_NEXT_TRIAL stopped='
TRACE=r"""
  // V386: only after V385 verified the original *second* read boundary.
  if(v250_candidate_mode&&v250_nand_seen==1u&&v386_active&&
     v385_second_seen==1u&&v386_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.pc==addr&&ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&
     (ctx.lr&3u)==0u&&ctx.inst_count>v386_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool signal=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v386_start_inst&&
         v383_reply_seen==1u&&v384_read_seen==1u&&v385_second_seen==1u;
    const bool writer=addr==0x8051906cu&&ctx.lr==0x8051910cu;
    const bool cache=addr==0x80522294u;
    std::cout<<"V386_NAND_NEXT_ENTRY guest="<<unsigned(guest)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" signal="<<unsigned(signal)
             <<" writer="<<unsigned(writer)
             <<" cache="<<unsigned(cache)
             <<std::endl;
    check(guest&&registered&&masked&&signal,
          "V386 authentic NAND second IPC read did not reach original guest helper");
    v386_next_pc=addr;v386_next_lr=ctx.lr;
    ++v386_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
RESUME=r"""  // Resume only the validated original guest IPCReadReg entry at V385.
  const bool v386_preempted=!c.is_running&&
       c.pc==0x8051905cu&&c.lr==0x805190fcu&&
       nwii::runtime::v385_second_seen==1u;
  check(v386_preempted,
        "V386 original second PPC read was not paused at verified call");
  nwii::runtime::v386_active=true;
  nwii::runtime::v386_next_seen=0u;
  nwii::runtime::v386_next_pc=nwii::runtime::v386_next_lr=0u;
  nwii::runtime::v386_start_inst=c.inst_count;
  c.is_running=true; // resume original PPC function at its saved entry
  bool v386_stopped=false;
  try{run_game(c);}catch(const ExceptionStop&){v386_stopped=true;}
  nwii::runtime::v386_active=false;
  const bool v386_completed=v386_stopped&&
       nwii::runtime::v386_next_seen==1u&&
       !c.is_running&&c.pc==nwii::runtime::v386_next_pc&&
       c.lr==nwii::runtime::v386_next_lr;
  std::cout<<"V386_NAND_NEXT_TRIAL stopped="<<unsigned(v386_stopped)
           <<" next="<<unsigned(nwii::runtime::v386_next_seen==1u)
           <<" completed="<<unsigned(v386_completed)<<std::endl;
  check(v386_completed,
        "V386 original NAND reply handler failed to call next guest helper");
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(TAIL)!=1 or
        source.count('const bool v385_completed=')!=1 or
        source.count('"V385 original NAND IpcReplyHandler second reader not entered");')!=1 or
        source.count('V385_NAND_SECOND_READ caller=')!=1 or
        source.count('V385_NAND_SECOND_READ_TRIAL first=')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source or 'v386_active' in source):
        raise ValueError('V386 original NAND read/resume checkpoint seam changed')
    s=source.replace(STATE_OLD,STATE_NEW,1)
    s=s.replace(HEAD,HEAD+TRACE,1)
    s=s.replace(TAIL,RESUME+TAIL,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or
        s.count(TAIL)!=1 or
        s.count('c.is_running=true; // resume original PPC function')!=1 or
        s.count('try{run_game(c);}')!=source.count('try{run_game(c);}')+1):
        raise ValueError('V386 original IPC read execution injected twice')
    return s

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        with a.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(patch(a.prior_private_harness.read_text(encoding='utf-8')))
    except (ValueError,OSError):
        print('V386_NAND_NEXT_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V386_NAND_NEXT_ROUTE installed=1 original_guest=1 resume_second_read=1 classify_only=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
