#!/usr/bin/env python3
"""V148 run repeated authentic SC IPC read-helper calls to a different leaf.

The original SC IPC interrupt handler has now been observed calling
0x8051905C twice. We allow additional genuine read-helper calls with a
finite budget, then stop at the first different function whose LR is inside
the original IPC handler. No guest opcodes or IOS state are modified.
"""
import argparse
from pathlib import Path
from derive_v147_sc_ipc_next_harness import (
    derive as previous, NEXT_TRIAL as TRIAL,
    V146_OBSERVER,
)

STATE="static unsigned v147_next_seen=0;"
RESET="nwii::runtime::v147_next_seen=0u;"
V147_STOP='''     ++v147_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
V148_CONTINUE='''     ++v147_next_seen;
     v148_start_inst=ctx.inst_count;return;
   }'''
V148_OBSERVER='''   if(v141_live&&v147_next_seen==1u&&v148_distinct_seen==0u&&
      ctx.pc==addr&&ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u){
     const bool first=v147_first_target==0x8051905cu&&v146_leaf_seen==1u;
     const bool caller=!(ctx.lr&3u)&&addr>=0x80400000u&&addr<0x80600000u;
     const bool advanced=ctx.inst_count>v148_start_inst&&
           ctx.gpr[13]==v147_first_r13;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool queued=ipc70_bus.services().queued_replies()==1u;
     const bool irq=ipc70_bus.external_irq_level();
     if(addr==0x8051905cu){
       ++v148_more_reads;
       if(v148_more_reads>32u){
         std::cout<<"V148_SC_IPC_READ_LIMIT count="<<v148_more_reads<<std::endl;
         check(false,"V148 SC IPC control-read loop exceeded bounded guest call budget");
       }
       check(first&&caller&&advanced&&masked&&queued,
             "V148 original SC IPC repeated read changed pending IRQ/ABI");
       v148_start_inst=ctx.inst_count;
       return;
     }
     std::cout<<"V148_SC_IPC_DISTINCT first="<<first<<" caller="<<caller
              <<" advanced="<<advanced<<" masked="<<masked
              <<" queued="<<queued<<" irq="<<irq
              <<" reads="<<v148_more_reads
              <<" target="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(first&&caller&&advanced&&masked&&queued,
           "V148 original SC IPC handler did not advance to valid distinct helper");
     ++v148_distinct_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&
             nwii::runtime::v146_leaf_seen==1u&&
             nwii::runtime::v147_next_seen==1u&&
             nwii::runtime::v148_distinct_seen==1u&&!c.is_running,
             "V148 original SC IPC read helpers did not reach a new target");'''

def once(s:str,old:str,new:str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V148 source anchor count={n}: {old[:80]}")
    return s.replace(old,new,1)

def derive(source:str)->str:
    s=previous(source)
    s=once(s,STATE,STATE+'''
 static unsigned v148_more_reads=0,v148_distinct_seen=0;
 static uint64_t v148_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v148_more_reads=nwii::runtime::v148_distinct_seen=0u;
     nwii::runtime::v148_start_inst=0u;''')
    s=once(s,V147_STOP,V148_CONTINUE)
    s=once(s,V146_OBSERVER,V148_OBSERVER+V146_OBSERVER)
    s=once(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
