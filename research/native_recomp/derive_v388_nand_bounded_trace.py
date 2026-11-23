#!/usr/bin/env python3
"""V388: bounded original NAND IPC reply call-chain or first real Y1 W1C.

The owner-authenticated V387 outcome was 12 original guest successor calls
without PPCCTRL.Y1 acknowledgement. Resume from that genuine stopped call
and execute up to 16 additional AOT function entries or stop on the first
original guest Y1 MMIO W1C. No guest PC/branch/IOS reply is fabricated.
Only sanitized event/call-class booleans leave the owner-private run.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from derive_v387_nand_reply_route import MMIO_BEFORE_NEW,MMIO_END_NEW
HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static bool v387_active=false;'
STATE_NEW='''static bool v387_active=false;
static bool v388_active=false;
static unsigned v388_kind=0u,v388_calls=0u;
static uint64_t v388_start_inst=0u;
static bool v388_writer=false,v388_read=false,v388_cache=false;
static uint32_t v388_stop_pc=0u,v388_stop_lr=0u;'''
TRIAL_ANCHOR='''  check(v387_completed,
        "V387 original NAND successor reached neither guest ACK nor guest call");'''
MARKER='V388_NAND_BOUNDARY kind='
TRIAL='V388_NAND_BOUNDED_TRIAL kind='
ACK=r"""      if(v388_active&&control&&(value&M::Y1)!=0u&&v388_kind==0u){
        using H=undercover::wii::HollywoodIrq;
        const auto now=ipc70_bus.read32(addr);
        const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
        const bool prior=v387_prior.has_value()&&
             ((*v387_prior&M::Y1)!=0u);
        const bool cleared=now.has_value()&&
             ((*now&(M::Y1|M::Y2))==0u);
        const bool latch=flag.has_value()&&
             ((*flag&H::IPC_PPC)!=0u);
        const bool guest=ipc70_ram.cpu!=nullptr&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u&&
             ipc70_ram.cpu->inst_count>v388_start_inst;
        const bool valid=prior&&cleared&&latch&&
             ipc70_bus.external_irq_level()&&guest;
        std::cout<<"V388_NAND_BOUNDARY kind=1 verified="<<unsigned(valid)
                 <<" calls="<<v388_calls
                 <<" writer="<<unsigned(v388_writer)
                 <<" read="<<unsigned(v388_read)
                 <<" cache="<<unsigned(v388_cache)
                 <<" y1clear="<<unsigned(cleared)
                 <<" latch="<<unsigned(latch)<<std::endl;
        check(valid,"V388 original NAND guest Y1 W1C failed independent latch proof");
        v388_kind=1u;
        ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
      }
"""
TRACE=r"""
  // V388: follow at most 16 original native function entries, not host loops.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v388_kind==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.pc==addr&&(addr&3u)==0u&&ctx.inst_count>v388_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool latch=flag.has_value()&&
          ((*flag&H::IPC_PPC)!=0u);
    const bool y1=ctrl.has_value()&&
          ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u);
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool signal=y1&&latch&&ipc70_bus.external_irq_level();
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
          ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    check(masked&&signal&&registered,
          "V388 original NAND bounded IRQ trace lost live guest Y1");
    v388_writer=v388_writer||(addr==0x8051906cu);
    v388_read=v388_read||(addr==0x8051905cu);
    v388_cache=v388_cache||(addr==0x80522294u);
    ++v388_calls;
    if(v388_calls==16u){
      std::cout<<"V388_NAND_BOUNDARY kind=2 verified=1"
               <<" calls="<<v388_calls
               <<" writer="<<unsigned(v388_writer)
               <<" read="<<unsigned(v388_read)
               <<" cache="<<unsigned(v388_cache)
               <<" y1clear=0 latch="<<unsigned(latch)<<std::endl;
      v388_stop_pc=ctx.pc;v388_stop_lr=ctx.lr;
      v388_kind=2u;
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
"""
RESUME=r"""  // The V387 owner checkpoint ended on a further real original call.
  const bool v388_preempted=v387_completed&&!c.is_running&&
        nwii::runtime::v387_event==2u&&
        c.pc==nwii::runtime::v387_next_pc&&
        c.lr==nwii::runtime::v387_next_lr;
  check(v388_preempted,
        "V388 original NAND continuation was not at verified V387 call");
  nwii::runtime::v388_active=true;
  nwii::runtime::v388_kind=nwii::runtime::v388_calls=0u;
  nwii::runtime::v388_start_inst=c.inst_count;
  nwii::runtime::v388_writer=nwii::runtime::v388_read=
      nwii::runtime::v388_cache=false;
  nwii::runtime::v388_stop_pc=nwii::runtime::v388_stop_lr=0u;
  c.is_running=true; // execute up to 16 authentic translated guest calls
  bool v388_stopped=false;
  try{run_game(c);}catch(const ExceptionStop&){v388_stopped=true;}
  nwii::runtime::v388_active=false;
  const bool v388_capped=nwii::runtime::v388_kind==2u&&
        nwii::runtime::v388_calls==16u&&
        c.pc==nwii::runtime::v388_stop_pc&&
        c.lr==nwii::runtime::v388_stop_lr;
  const bool v388_completed=v388_stopped&&!c.is_running&&
        (nwii::runtime::v388_kind==1u||v388_capped);
  std::cout<<"V388_NAND_BOUNDED_TRIAL kind="<<nwii::runtime::v388_kind
           <<" calls="<<nwii::runtime::v388_calls
           <<" stopped="<<unsigned(v388_stopped)
           <<" completed="<<unsigned(v388_completed)<<std::endl;
  check(v388_completed,
        "V388 original NAND bounded guest call chain yielded no verified stop");
"""
def patch(s:str)->str:
    if (s.count(HEAD)!=1 or s.count(STATE_OLD)!=1 or
        s.count(MMIO_BEFORE_NEW)!=1 or
        s.count(MMIO_END_NEW)!=1 or
        s.count(TRIAL_ANCHOR)!=1 or
        s.count('V387_NAND_ROUTE_EVENT kind=')!=2 or
        s.count('V387_NAND_ROUTE_TRIAL kind=')!=1 or
        s.count('V385_NAND_ARMMSG_MIRROR coherent=')!=1 or
        MARKER in s or TRIAL in s or 'v388_active' in s):
        raise ValueError('V388 authenticated V387/MMIO source seam changed')
    first=MMIO_BEFORE_NEW.replace('v387_active&&control',
                                  '(v387_active||v388_active)&&control',1)
    if first==MMIO_BEFORE_NEW or not MMIO_END_NEW.endswith('      return;'):
        raise ValueError('V388 original PPCCTRL bus pre/post-state hook moved')
    end=MMIO_END_NEW.replace('      return;',ACK+'      return;',1)
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(MMIO_BEFORE_NEW,first,1)
    out=out.replace(MMIO_END_NEW,end,1)
    out=out.replace(HEAD,HEAD+TRACE,1)
    out=out.replace(TRIAL_ANCHOR,TRIAL_ANCHOR+'\n'+RESUME,1)
    if (out.count(MARKER)!=2 or out.count(TRIAL)!=1 or
        out.count('try{run_game(c);}')!=s.count('try{run_game(c);}')+1):
        raise ValueError('V388 original NAND bounded trace not uniquely installed')
    return out
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        staged=patch(a.prior_private_harness.read_text(encoding='utf-8'))
        with a.next_private_harness.open('x',encoding='utf-8') as out:out.write(staged)
    except (ValueError,OSError):
        print('V388_NAND_BOUNDED_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V388_NAND_BOUNDED_ROUTE installed=1 original_guest=1 cap=16 native_ack_only=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
