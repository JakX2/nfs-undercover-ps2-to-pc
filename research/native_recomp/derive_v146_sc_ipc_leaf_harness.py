#!/usr/bin/env python3
"""V146 execute original SC IPC handler until its first known native helper.

The V145 interrupt dispatch, IRQ registration, preserved exception context,
and queued IOS acknowledgment remain intact. We only release the test stop at
the registered IPC handler and observe its first original helper call. No PPC
instruction, original state, IOS service or MMIO register is fabricated.
"""
import argparse
from pathlib import Path
from derive_v145_sc_ipc_handler_harness import derive as previous

STATE="static unsigned v145_ipc_seen=0;"
RESET="nwii::runtime::v145_ipc_seen=0u;"
STOP='''     ++v145_ipc_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
NEXT='''     ++v145_ipc_seen;v146_enter_inst=ctx.inst_count;return;
   }
   if(v141_live&&v145_ipc_seen==1u&&
      (addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){
     const bool call=v146_leaf_seen==0u&&ctx.pc==addr&&
           ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&!(ctx.lr&3u);
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool queued=ipc70_bus.services().queued_replies()==1u&&
                       ipc70_bus.external_irq_level();
     const bool stepped=ctx.inst_count>v146_enter_inst;
     std::cout<<"V146_SC_IPC_LEAF call="<<call<<" masked="<<masked
              <<" queued="<<queued<<" stepped="<<stepped
              <<" target="<<std::hex<<addr<<std::dec<<std::endl;
     check(call&&masked&&queued&&stepped,
           "V146 original SC IPC handler first leaf call differs");
     ++v146_leaf_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&!c.is_running,
             "V145 original SC dispatcher did not enter registered IPC interrupt handler");'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&
             nwii::runtime::v146_leaf_seen==1u&&!c.is_running,
             "V146 original SC IPC handler never reached authenticated leaf call");'''

def one(s,old,new):
    n=s.count(old)
    if n!=1:raise ValueError(f"V146 native source anchor expected once, got {n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source):
    s=previous(source)
    s=one(s,STATE,STATE+"\n static unsigned v146_leaf_seen=0;\n static uint64_t v146_enter_inst=0;")
    s=one(s,RESET,RESET+"\n     nwii::runtime::v146_leaf_seen=0u;\n     nwii::runtime::v146_enter_inst=0u;")
    s=one(s,STOP,NEXT)
    s=one(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
