#!/usr/bin/env python3
"""V199 execute original second IOS Y2 timebase and reach scheduler-disable.

V198 authentic guest reached timebase PC 0x8052A824 LR 0x80526C84,
with masked EE and second IOS completion queued. Continue original PPC
into the dispatcher's scheduler-disable helper without forged IOS steps.
"""
import argparse
from pathlib import Path
from derive_v198_sc_y2_time_harness import (
    derive as previous,OBSERVER as PREVIOUS_OBSERVER,NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE,RESET,once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v198_time_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v198_time_seen;
    v199_time_inst=ctx.inst_count;
    return; // original Wii timebase helper executes and returns
  }'''
OBSERVER='''  if(v196_live&&v198_time_seen==1u&&v199_disable_seen==0u&&
     addr==0x805293f8u){
    const bool route=ctx.pc==addr&&ctx.lr==0x80526c98u&&
          v196_vector_seen==1u&&v196_handler_seen==1u&&
          v197_dispatch_seen==1u;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool progressed=ctx.inst_count>v199_time_inst;
    const bool resume=v196_resume==0x8052f830u&&v196_srr1!=0u;
    std::cout<<"V199_Y2_DISABLE route="<<route<<" masked="<<masked
             <<" pending="<<pending<<" progressed="<<progressed
             <<" resume="<<resume<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(route&&masked&&pending&&progressed&&resume,
          "V199 original second IOS Y2 timebase did not reach scheduler disable");
    ++v199_disable_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            !c.is_running&&c.pc==0x805293f8u,
            "V199 original second IOS Y2 timebase did not reach scheduler-disable helper");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V199 authentic second IOS Y2 timebase stop changed")
    s=once(s,STATE,STATE+'''
 static unsigned v199_disable_seen=0u;
 static uint64_t v199_time_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v199_disable_seen=0u;
     nwii::runtime::v199_time_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
