#!/usr/bin/env python3
"""V144 native SC interrupt dispatcher passes timebase into scheduler disable.

The original PPC timebase helper executes and returns; we observe the original
scheduler-disable function entry with authenticated return address. All guest
instructions, pending IOS replies and interrupt-controller state are preserved.
"""
import argparse
from pathlib import Path
from derive_v143_sc_irq_time_harness import derive as previous

STATE="static unsigned v143_time_seen=0;"
RESET="nwii::runtime::v143_time_seen=0u;"
STOP='''     ++v143_time_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
NEXT='''     ++v143_time_seen;v144_time_inst=ctx.inst_count;return;
   }
   if(v141_live&&v143_time_seen==1u&&addr==0x805293f8u){
     const bool route=ctx.pc==addr&&ctx.lr==0x80526c98u&&
           v142_dispatch_seen==1u&&v144_disable_seen==0u;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool pending=ipc70_bus.services().queued_replies()==1u&&
                        ipc70_bus.external_irq_level();
     const bool progressed=ctx.inst_count>v144_time_inst;
     std::cout<<"V144_SC_DISABLE route="<<route<<" masked="<<masked
              <<" pending="<<pending<<" progressed="<<progressed<<std::endl;
     check(route&&masked&&pending&&progressed,
           "V144 original SC IRQ dispatcher did not call scheduler interrupt-disable helper");
     ++v144_disable_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&!c.is_running,
             "V143 original SC dispatcher did not call authenticated timebase helper");'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&!c.is_running,
             "V144 original SC dispatcher did not reach scheduler interrupt-disable helper");'''

def one(s,old,new):
    n=s.count(old)
    if n!=1:raise ValueError(f"V144 native harness source anchor expected once, found {n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source):
    s=previous(source)
    s=one(s,STATE,STATE+"\n static unsigned v144_disable_seen=0;\n static uint64_t v144_time_inst=0;")
    s=one(s,RESET,RESET+"\n     nwii::runtime::v144_disable_seen=0u;\n     nwii::runtime::v144_time_inst=0u;")
    s=one(s,STOP,NEXT)
    s=one(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
