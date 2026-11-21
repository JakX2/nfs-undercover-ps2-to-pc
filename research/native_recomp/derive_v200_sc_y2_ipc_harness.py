#!/usr/bin/env python3
"""V200: run original second Y2 scheduler-disable and observe IPC IRQ dispatch.

V199 stopped at the authentic PowerPC scheduler-disable entry 0x805293F8.
Continue the original helper and dispatcher. Confirm the *second* interrupt's
registered slot 27, installed handler, saved exception frame, and queued
second IOS completion independently of the earlier first-IRQ V145 trial.
No emulated service pump or guest register/memory alteration is introduced.
"""
import argparse
from pathlib import Path
from derive_v199_sc_y2_disable_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v199_disable_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v199_disable_seen;
    v200_disable_inst=ctx.inst_count;
    return; // execute original scheduler-disable and IRQ dispatch
  }'''
OBSERVER='''  // V98's NAND-registration observer expects an idle IOS queue. The
  // genuine later Y2 scheduler reuses the same IRQ helper function entries
  // with one pending reply. Retire only these authenticated nested calls;
  // never mask an actual mismatch in the current IRQ state or early V98.
  if(v196_live&&v199_disable_seen==1u&&v200_ipc_seen==0u&&
     (addr==INT_DISABLE||addr==INT_RESTORE)&&
     ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u){
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    check(masked&&pending,
          "V200 original second Y2 scheduler nested helper lost pending IOS state");
    return;
  }
  // The first IPC IRQ's V145 observer has already been phase-retired.
  // Do not infer this second dispatch from V145: inspect live guest state.
  if(v196_live&&v199_disable_seen==1u&&v200_ipc_seen==0u&&
     addr==0x80519318u){
    const uint32_t frame=ctx.gpr[4];
    const bool mapped=frame!=0u&&!(frame&7u)&&
          ctx.mmu.get_ptr(frame)!=nullptr&&
          ctx.mmu.get_ptr(frame+415u)!=nullptr;
    const bool registered=ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr;
    const bool dispatch=ctx.pc==addr&&ctx.ctr==addr&&
          ctx.gpr[3]==27u&&ctx.lr>=0x80526c98u&&
          ctx.lr<=0x80526cacu&&!(ctx.lr&3u)&&
          v196_vector_seen==1u&&v196_handler_seen==1u&&
          v197_dispatch_seen==1u&&v198_time_seen==1u;
    const bool context=mapped&&
          ctx.mmu.read32(frame+408u)==v196_resume&&
          ctx.mmu.read32(frame+412u)==v196_srr1&&
          ctx.mmu.read32(frame+132u)==v196_lr&&
          ctx.mmu.read32(frame+136u)==v196_ctr&&
          ctx.mmu.read32(frame+140u)==v196_xer;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool progressed=ctx.inst_count>v200_disable_inst;
    const bool resume=v196_resume==0x8052f830u&&v196_srr1!=0u;
    std::cout<<"V200_Y2_IPC dispatch="<<dispatch
             <<" context="<<context<<" registered="<<registered
             <<" masked="<<masked<<" pending="<<pending
             <<" progressed="<<progressed<<" resume="<<resume
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(dispatch&&context&&registered&&masked&&pending&&
          progressed&&resume,
          "V200 original second Y2 dispatcher did not select registered IPC handler");
    ++v200_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            !c.is_running&&c.pc==0x80519318u,
            "V200 original second Y2 dispatcher did not reach registered IPC handler");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V200 original second Y2 scheduler boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v200_ipc_seen=0u;
 static uint64_t v200_disable_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v200_ipc_seen=0u;
     nwii::runtime::v200_disable_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
