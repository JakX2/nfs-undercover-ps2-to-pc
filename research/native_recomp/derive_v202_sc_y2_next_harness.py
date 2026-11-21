#!/usr/bin/env python3
"""V202 execute the second Y2 IPC read helper and observe its next PPC call.

V201 owner-original confirmed first IPC helper PC 0x8051905C with
LR 0x8051933C, EE masked, and one second IOS_Open completion queued.
Continue the actual guest helper, stop at the next call originating in the
registered IPC handler, and record its destination. No host ack or guest
instruction/register manipulation is permitted.
"""
import argparse
from pathlib import Path
from derive_v201_sc_y2_leaf_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v201_leaf_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v201_leaf_seen;
    v202_first_pc=addr;v202_first_lr=ctx.lr;
    v202_first_r13=ctx.gpr[13];
    v202_first_inst=ctx.inst_count;
    return; // original IPC read helper executes and returns
  }'''
OBSERVER='''  if(v196_live&&v201_leaf_seen==1u&&v202_next_seen==0u&&
     ctx.pc==addr&&ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u){
    const bool first=v202_first_pc==0x8051905cu&&
          v202_first_lr==0x8051933cu&&v200_ipc_seen==1u;
    const bool caller=addr>=0x80400000u&&addr<0x80600000u&&
          !(addr&3u)&&!(ctx.lr&3u);
    const bool stepped=ctx.inst_count>v202_first_inst&&
          ctx.gpr[13]==v202_first_r13;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool queued=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    std::cout<<"V202_Y2_NEXT first="<<first<<" caller="<<caller
             <<" stepped="<<stepped<<" masked="<<masked
             <<" queued="<<queued<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(first&&caller&&stepped&&masked&&queued,
          "V202 original second Y2 IPC read helper did not return to handler call");
    v202_next_pc=addr;v202_next_lr=ctx.lr;
    ++v202_next_seen;
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
            nwii::runtime::v202_first_pc==0x8051905cu&&
            nwii::runtime::v202_first_lr==0x8051933cu&&
            !c.is_running&&c.pc==nwii::runtime::v202_next_pc&&
            c.lr==nwii::runtime::v202_next_lr,
            "V202 original second Y2 IPC read helper failed to reach next call");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V202 authenticated second Y2 first-read checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v202_next_seen=0u;
 static uint64_t v202_first_inst=0u;
 static uint32_t v202_first_pc=0u,v202_first_lr=0u,v202_first_r13=0u;
 static uint32_t v202_next_pc=0u,v202_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v202_next_seen=0u;
     nwii::runtime::v202_first_inst=0u;
     nwii::runtime::v202_first_pc=nwii::runtime::v202_first_lr=
       nwii::runtime::v202_first_r13=0u;
     nwii::runtime::v202_next_pc=nwii::runtime::v202_next_lr=0u;''')
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
