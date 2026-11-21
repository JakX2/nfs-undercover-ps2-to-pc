#!/usr/bin/env python3
"""V198: execute original Wii second Y2 IRQ dispatcher to native timebase.

Follows V197 owner-authenticated real PPC entry 0x80526A3C. Do not
fake an IOS completion, guest status or dispatcher return. Record the
first authentic original timebase helper call with preserved exception
resume state and one pending second IOS_Open completion.
"""
import argparse
from pathlib import Path
from derive_v197_sc_y2_dispatch_harness import (
    derive as previous,OBSERVER as PREVIOUS_OBSERVER,NEW_END as PREVIOUS_TRIAL_END,
)
from derive_v194_osrestore_next_harness import STATE,RESET,once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v197_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v197_dispatch_seen;
    v198_dispatch_inst=ctx.inst_count;
    return; // execute authentic original IRQ dispatcher
  }'''
OBSERVER='''  if(v196_live&&v197_dispatch_seen==1u&&v198_time_seen==0u&&
     addr==0x8052a824u){
    const bool time=ctx.pc==addr&&ctx.lr==0x80526c84u&&
          v196_vector_seen==1u&&v196_handler_seen==1u;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool progressed=ctx.inst_count>v198_dispatch_inst;
    // V197 verified the original saved SRR0/SRR1 in the interrupt
    // frame. The live SRR0 is not an ABI-preserved register through the
    // guest exception handler and may be rewritten by original PPC.
    const bool resume=v196_resume==0x8052f830u&&
          v196_srr1!=0u&&v197_dispatch_seen==1u;
    std::cout<<"V198_Y2_TIME time="<<time<<" masked="<<masked
             <<" pending="<<pending<<" progressed="<<progressed
             <<" resume="<<resume<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(time&&masked&&pending&&progressed&&resume,
          "V198 original second Y2 IRQ dispatcher did not call native Wii timebase");
    ++v198_time_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            !c.is_running&&c.pc==0x8052a824u,
            "V198 original second IOS Y2 dispatcher did not call original timebase helper");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_TRIAL_END)!=1:
        raise ValueError("V198 original second IOS Y2 dispatcher stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v198_time_seen=0u;
 static uint64_t v198_dispatch_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v198_time_seen=0u;
     nwii::runtime::v198_dispatch_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
