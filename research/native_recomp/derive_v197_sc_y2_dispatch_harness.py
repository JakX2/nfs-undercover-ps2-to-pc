#!/usr/bin/env python3
"""V197 execute the original second IOS Y2 OS exception handler to dispatcher.

The owner-original V196 checkpoint executed the installed PowerPC vector
from the second Y2 hardware IRQ and stopped at 0x80526CE0. The V197 test
continues that authentic handler and observes the original 0x80526A3C
IRQ dispatcher while independently verifying saved nonvolatile registers,
SRRs and pending IOS reply, without fabricated guest or hardware writes.
"""
import argparse
from pathlib import Path
from derive_v196_sc_y2_vector_harness import (
    derive as previous,OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL,
)
from derive_v194_osrestore_next_harness import STATE,RESET,once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
STOP='''    ++v196_handler_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v196_handler_seen;
    v197_handler_inst=ctx.inst_count;
    return; // execute authentic second Y2 original Wii OS handler
  }'''
OBSERVER='''  if(v196_live&&v196_handler_seen==1u&&v197_dispatch_seen==0u&&
     addr==0x80526a3cu){
    const uint32_t frame=ctx.gpr[4];
    const bool mapped=frame!=0u&&!(frame&7u)&&
          ctx.mmu.get_ptr(frame)!=nullptr&&
          ctx.mmu.get_ptr(frame+415u)!=nullptr;
    const bool route=v196_vector_seen==1u&&ctx.pc==addr&&
          ctx.gpr[3]==4u&&mapped;
    bool regs=route;
    if(route){
      for(unsigned i=6u;i<32u;++i)
        regs&=ctx.mmu.read32(frame+4u*i)==v196_gprs[i];
    }
    const bool status=route&&
          ctx.mmu.read32(frame+408u)==v196_resume&&
          ctx.mmu.read32(frame+412u)==v196_srr1&&
          ctx.mmu.read32(frame+132u)==v196_lr&&
          ctx.mmu.read32(frame+136u)==v196_ctr&&
          ctx.mmu.read32(frame+140u)==v196_xer;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool progressed=ctx.inst_count>v197_handler_inst;
    std::cout<<"V197_Y2_DISPATCH route="<<route
             <<" regs="<<regs<<" status="<<status
             <<" pending="<<pending<<" progressed="<<progressed
             <<" resume="<<std::hex<<v196_resume
             <<" pc="<<addr<<std::dec<<std::endl;
    check(route&&regs&&status&&pending&&progressed,
          "V197 original second IOS exception handler did not dispatch preserved PowerPC frame");
    ++v197_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PREVIOUS_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            !c.is_running&&c.pc==0x80526ce0u,
            "V196 second original IOS Y2 vector did not reach native OS exception handler");'''
NEW_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            !c.is_running&&c.pc==0x80526a3cu,
            "V197 original Wii second Y2 handler did not enter real IRQ dispatcher");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(PREVIOUS_END)!=1:
        raise ValueError("V197 authentic V196 handler stop or owner trial changed")
    s=once(s,STATE,STATE+'''
 static unsigned v197_dispatch_seen=0u;
 static uint64_t v197_handler_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v197_dispatch_seen=0u;
     nwii::runtime::v197_handler_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL.replace(PREVIOUS_END,NEW_END,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
