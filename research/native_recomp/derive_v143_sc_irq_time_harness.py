#!/usr/bin/env python3
"""V143 execute original SC IRQ dispatcher to its authenticated timebase call.

All V142 guest and external IRQ state remains intact. This only extends the
execution stop to the first original timebase helper call, with no original
instruction or synthetic status changes.
"""
import argparse
from pathlib import Path
from derive_v142_sc_dispatch_harness import derive as previous

STATE="static unsigned v142_dispatch_seen=0;"
RESET="nwii::runtime::v142_dispatch_seen=0u;"
STOP='''     ++v142_dispatch_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
REPLACE='''     ++v142_dispatch_seen;
     v143_dispatch_inst=ctx.inst_count;return;
   }
   if(v141_live && v142_dispatch_seen==1u && addr==0x8052a824u){
     const bool time=ctx.pc==addr&&ctx.lr==0x80526c84u&&v143_time_seen==0u;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool pending=ipc70_bus.services().queued_replies()==1u&&
                        ipc70_bus.external_irq_level();
     const bool progressed=ctx.inst_count>v143_dispatch_inst;
     std::cout<<"V143_SC_TIME time="<<time<<" masked="<<masked
              <<" pending="<<pending<<" progressed="<<progressed<<std::endl;
     check(time&&masked&&pending&&progressed,
           "V143 original SC IRQ dispatcher did not reach authentic timebase helper");
     ++v143_time_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&!c.is_running,
             "V142 original SC external vector did not enter authentic IRQ dispatcher");'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&!c.is_running,
             "V143 original SC dispatcher did not call authenticated timebase helper");'''

def one(s,old,new):
    n=s.count(old)
    if n!=1:raise ValueError(f"V143 owner-free harness anchor expected once, found {n}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source):
    s=previous(source)
    s=one(s,STATE,STATE+"\n static unsigned v143_time_seen=0;\n static uint64_t v143_dispatch_inst=0;")
    s=one(s,RESET,RESET+"\n     nwii::runtime::v143_time_seen=0u;\n     nwii::runtime::v143_dispatch_inst=0u;")
    s=one(s,STOP,REPLACE)
    s=one(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
