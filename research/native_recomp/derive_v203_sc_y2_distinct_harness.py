#!/usr/bin/env python3
"""V203: execute repeated second-Y2 IPC reads until a distinct PPC helper.

V202 owner-original returned from the first 0x8051905C IPC read and called
the same helper again, LR 0x8051935C. Follow authentic guest callsites with
a strict bound of 32 further reads; stop at the first different handler-owned
PowerPC helper while preserving the unconsumed second IOS_Open completion.
"""
import argparse
from pathlib import Path
from derive_v202_sc_y2_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v202_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v202_next_seen;
    v203_start_inst=ctx.inst_count;
    return; // original repeated IPC read executes
  }'''
OBSERVER='''  if(v196_live&&v202_next_seen==1u&&v203_distinct_seen==0u&&
     ctx.pc==addr&&ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u){
    const bool first=v202_next_pc==0x8051905cu&&
          v202_next_lr==0x8051935cu&&v201_leaf_seen==1u;
    const bool caller=addr>=0x80400000u&&addr<0x80600000u&&
          !(addr&3u)&&!(ctx.lr&3u);
    const bool progressed=ctx.inst_count>v203_start_inst&&
          ctx.gpr[13]==v202_first_r13;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool queued=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    if(addr==0x8051905cu){
      ++v203_extra_reads;
      check(v203_extra_reads<=32u,
            "V203 original second Y2 IPC read loop exceeded 32 calls");
      check(first&&caller&&progressed&&masked&&queued,
            "V203 original second Y2 repeated IPC read lost guest/IRQ state");
      v203_start_inst=ctx.inst_count;
      return;
    }
    std::cout<<"V203_Y2_DISTINCT first="<<first<<" caller="<<caller
             <<" progressed="<<progressed<<" masked="<<masked
             <<" queued="<<queued<<" reads="<<v203_extra_reads
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(first&&caller&&progressed&&masked&&queued,
          "V203 original second Y2 IPC reads did not reach a distinct helper");
    v203_distinct_pc=addr;v203_distinct_lr=ctx.lr;
    ++v203_distinct_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v201_leaf_seen==1u&&
            nwii::runtime::v202_next_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v203_extra_reads<=32u&&
            !c.is_running&&c.pc==nwii::runtime::v203_distinct_pc&&
            c.lr==nwii::runtime::v203_distinct_lr&&
            c.pc!=0x8051905cu,
            "V203 original second Y2 IPC handler failed to reach distinct helper");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V203 authenticated original second Y2 helper successor changed")
    s=once(s,STATE,STATE+'''
 static unsigned v203_extra_reads=0u,v203_distinct_seen=0u;
 static uint64_t v203_start_inst=0u;
 static uint32_t v203_distinct_pc=0u,v203_distinct_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v203_extra_reads=nwii::runtime::v203_distinct_seen=0u;
     nwii::runtime::v203_start_inst=0u;
     nwii::runtime::v203_distinct_pc=nwii::runtime::v203_distinct_lr=0u;''')
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
