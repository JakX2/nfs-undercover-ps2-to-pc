#!/usr/bin/env python3
"""V387 bounded follow-up to original NAND IPC second-read successor.

V386 owner-original executed the first successor from IpcReplyHandler's
second PPC read, but neither the historical writer/callsite pair nor the
cache call matched. Continue that authentic original function and stop at
the first of: (1) a real Broadway PPCCTRL.Y1 W1C performed by the game;
(2) the next genuine linked translated guest call. Neither is invented.

V352 owns MMIO transport. Inject only *post-write witness checks* inside
its original bus call; keep guest PC, memory, IOS reply and time untouched.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from derive_v352_nand_mailbox_route import HEADER,INJECTION

STATE_OLD='static bool v386_active=false;'
STATE_NEW='''static bool v386_active=false;
static bool v387_active=false;
static unsigned v387_event=0u;
static uint64_t v387_start_inst=0u;
static uint32_t v387_next_pc=0u,v387_next_lr=0u;'''
V386_COMPLETE='''  check(v386_completed,
        "V386 original NAND reply handler failed to call next guest helper");'''
TAIL='  continue; // finish this authenticated NAND-only bounded trial'
MARKER='V387_NAND_ROUTE_EVENT kind='
TRIAL='V387_NAND_ROUTE_TRIAL kind='
MMIO_BEFORE='''      const bool accepted=ipc70_bus.write32(addr,value);'''
MMIO_BEFORE_NEW='''      const auto v387_prior=(v387_active&&control)?
            ipc70_bus.read32(addr):std::optional<uint32_t>{};
      const bool accepted=ipc70_bus.write32(addr,value);'''
MMIO_END='''      mmio_writes.emplace_back(addr,value);
      return;'''
MMIO_END_NEW=r"""      mmio_writes.emplace_back(addr,value);
      if(v387_active&&control&&(value&M::Y1)!=0u&&v387_event==0u){
        using H=undercover::wii::HollywoodIrq;
        const auto after=ipc70_bus.read32(addr);
        const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
        const bool before=v387_prior.has_value()&&
             ((*v387_prior&M::Y1)!=0u);
        const bool cleared=after.has_value()&&
             ((*after&(M::Y1|M::Y2))==0u);
        const bool latch=flag.has_value()&&
             ((*flag&H::IPC_PPC)!=0u);
        const bool guest=ipc70_ram.cpu!=nullptr&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u&&
             ipc70_ram.cpu->inst_count>v387_start_inst;
        const bool valid=before&&cleared&&latch&&
             ipc70_bus.external_irq_level()&&guest;
        std::cout<<"V387_NAND_ROUTE_EVENT kind=1 verified="<<unsigned(valid)
                 <<" y1cleared="<<unsigned(cleared)
                 <<" latch="<<unsigned(latch)
                 <<" writer=1 next=0"<<std::endl;
        check(valid,"V387 original NAND Y1 W1C lost Broadway/IRQ state");
        v387_event=1u;
        ipc70_ram.cpu->is_running=false;
        throw ExceptionStop{};
      }
      return;"""
TRACE=r"""
  // V387 event 2: a second original guest-linked function call after V386.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v387_active&&v387_event==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.pc==addr&&ctx.inst_count>v387_start_inst&&
     ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&
     (ctx.lr&3u)==0u){
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
    const bool guest=ctx.pc==addr&&v385_second_seen==1u&&
         v386_next_seen==1u&&ctx.inst_count>v387_start_inst;
    const bool writer=addr==0x8051906cu;
    const bool valid=guest&&registered&&masked&&signal;
    std::cout<<"V387_NAND_ROUTE_EVENT kind=2 verified="<<unsigned(valid)
             <<" y1cleared=0 latch="<<unsigned(signal)
             <<" writer="<<unsigned(writer)<<" next=1"
             <<std::endl;
    check(valid,"V387 original NAND second guest successor lost Y1 state");
    v387_next_pc=addr;v387_next_lr=ctx.lr;
    v387_event=2u;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
RESUME=r"""  const bool v387_preempted=v386_completed&&!c.is_running&&
       nwii::runtime::v386_next_seen==1u&&
       c.pc==nwii::runtime::v386_next_pc&&
       c.lr==nwii::runtime::v386_next_lr;
  check(v387_preempted,
        "V387 original NAND reply successor was not paused at guest function");
  nwii::runtime::v387_active=true;
  nwii::runtime::v387_event=0u;
  nwii::runtime::v387_next_pc=nwii::runtime::v387_next_lr=0u;
  nwii::runtime::v387_start_inst=c.inst_count;
  c.is_running=true; // resume authentic original guest successor
  bool v387_stopped=false;
  try{run_game(c);}catch(const ExceptionStop&){v387_stopped=true;}
  nwii::runtime::v387_active=false;
  const bool v387_event_valid=nwii::runtime::v387_event==1u||
        (nwii::runtime::v387_event==2u&&
         c.pc==nwii::runtime::v387_next_pc&&
         c.lr==nwii::runtime::v387_next_lr);
  const bool v387_completed=v387_stopped&&v387_event_valid&&
        !c.is_running;
  std::cout<<"V387_NAND_ROUTE_TRIAL kind="<<nwii::runtime::v387_event
           <<" stopped="<<unsigned(v387_stopped)
           <<" completed="<<unsigned(v387_completed)<<std::endl;
  check(v387_completed,
        "V387 original NAND successor reached neither guest ACK nor guest call");
"""

def patch(s:str)->str:
    if (s.count(STATE_OLD)!=1 or s.count(HEADER)!=1 or
        s.count(INJECTION)!=1 or s.count(V386_COMPLETE)!=1 or
        s.count(TAIL)!=1 or
        s.count('V386_NAND_NEXT_ENTRY guest=')!=1 or
        s.count('V386_NAND_NEXT_TRIAL stopped=')!=1 or
        s.count('V385_NAND_ARMMSG_MIRROR coherent=')!=1 or
        MARKER in s or TRIAL in s or 'v387_active' in s):
        raise ValueError('V387 original NAND V386/MMIO transport seam changed')
    if INJECTION.count(MMIO_BEFORE)!=1 or INJECTION.count(MMIO_END)!=1:
        raise ValueError('V387 exact native original MMIO W1C seam changed')
    native=INJECTION.replace(MMIO_BEFORE,MMIO_BEFORE_NEW,1)
    native=native.replace(MMIO_END,MMIO_END_NEW,1)
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(INJECTION,native,1)
    out=out.replace('void trace_call(uint32_t addr, CPUContext&ctx){',
                    'void trace_call(uint32_t addr, CPUContext&ctx){'+TRACE,1)
    out=out.replace(V386_COMPLETE,V386_COMPLETE+'\n'+RESUME,1)
    if (out.count(MARKER)!=2 or out.count(TRIAL)!=1 or
        out.count('try{run_game(c);}')!=s.count('try{run_game(c);}')+1 or
        out.count('V352_NAND_BUS kind=')!=s.count('V352_NAND_BUS kind=')):
        raise ValueError('V387 guest route not unique')
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
        with a.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(staged)
    except (ValueError,OSError):
        print('V387_NAND_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V387_NAND_ROUTE installed=1 original_guest=1 ack_or_next=1 no_forced_reply=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
