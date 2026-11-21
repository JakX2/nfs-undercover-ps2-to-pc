#!/usr/bin/env python3
"""V201: execute original second-Y2 IPC handler to its first helper call.

V200 owner-original selected IRQ slot 27, entering registered PowerPC
handler 0x80519318 with LR 0x80526CAC. Continue original instructions,
observe the first handler-owned native helper entry, and preserve the
unconsumed second IOS_Open completion. No guest/IOS writes are injected.
"""
import argparse
from pathlib import Path
from derive_v200_sc_y2_ipc_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v200_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v200_ipc_seen;
    v201_ipc_inst=ctx.inst_count;
    return; // execute original registered PowerPC IPC handler body
  }'''
OBSERVER='''  // Earlier NAND/IPC observers belong to the original first-interrupt
  // phase; they must not assert an empty IOS queue for the second Y2 IRQ.
  // This read-only observer recognizes only authentic IPC-handler callsites.
  if(v196_live&&v200_ipc_seen==1u&&v201_leaf_seen==0u&&
     (addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){
    const bool call=ctx.pc==addr&&ctx.lr>=0x80519318u&&
          ctx.lr<0x805194c4u&&!(ctx.lr&3u);
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const bool queued=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool stepped=ctx.inst_count>v201_ipc_inst;
    const bool prior=v196_resume==0x8052f830u&&
          v196_srr1!=0u&&v199_disable_seen==1u;
    std::cout<<"V201_Y2_LEAF call="<<call<<" masked="<<masked
             <<" queued="<<queued<<" stepped="<<stepped
             <<" prior="<<prior<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(call&&masked&&queued&&stepped&&prior,
          "V201 original second Y2 IPC handler did not reach native first helper");
    v201_leaf_pc=addr;v201_leaf_lr=ctx.lr;
    ++v201_leaf_seen;
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
            !c.is_running&&c.pc==nwii::runtime::v201_leaf_pc&&
            c.lr==nwii::runtime::v201_leaf_lr&&
            (c.pc==0x8051905cu||c.pc==0x8051906cu||
             c.pc==0x8051b060u),
            "V201 original second Y2 IPC handler did not enter authentic helper");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V201 original second Y2 IPC entry boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v201_leaf_seen=0u;
 static uint64_t v201_ipc_inst=0u;
 static uint32_t v201_leaf_pc=0u,v201_leaf_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v201_leaf_seen=0u;
     nwii::runtime::v201_ipc_inst=0u;
     nwii::runtime::v201_leaf_pc=nwii::runtime::v201_leaf_lr=0u;''')
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
