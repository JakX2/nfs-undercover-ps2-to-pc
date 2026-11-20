#!/usr/bin/env python3
"""V147 execute V146's genuine first IPC leaf and observe its next caller-owned BL.

The authenticated translated Wii code runs unchanged. This observer watches
the *next original function entry with LR inside the installed IPC handler*
after the already-verified first leaf at 0x8051905C. It does not infer a
successor, alter guest memory, service IOS or acknowledge the queued reply.
"""
import argparse
from pathlib import Path
from derive_v146_sc_ipc_leaf_harness import derive as previous, NEXT_TRIAL

STATE="static unsigned v146_leaf_seen=0;"
RESET="nwii::runtime::v146_leaf_seen=0u;"
V146_STOP='''     ++v146_leaf_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
V146_OBSERVER='''   if(v141_live&&v145_ipc_seen==1u&&
      (addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){'''

V147_CONTINUE='''     ++v146_leaf_seen;
     v147_first_target=addr;v147_first_lr=ctx.lr;
     v147_first_inst=ctx.inst_count;v147_first_r13=ctx.gpr[13];
     return;
   }'''
V147_OBSERVER='''   if(v141_live&&v146_leaf_seen==1u&&v147_next_seen==0u&&
      ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&ctx.pc==addr){
     const bool first=v147_first_target==0x8051905cu&&
           v147_first_lr>=0x80519318u&&v147_first_lr<0x805194c4u;
     const bool caller=ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&
           !(ctx.lr&3u)&&addr>=0x80400000u&&addr<0x80600000u;
     const bool progressed=ctx.inst_count>v147_first_inst&&
           ctx.gpr[13]==v147_first_r13;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool queued=ipc70_bus.services().queued_replies()==1u;
     const bool irq=ipc70_bus.external_irq_level();
     std::cout<<"V147_SC_IPC_NEXT first="<<first<<" caller="<<caller
              <<" progressed="<<progressed<<" masked="<<masked
              <<" queued="<<queued<<" irq="<<irq
              <<" target="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(first&&caller&&progressed&&masked&&queued,
           "V147 authentic IPC handler next call lost leaf/IRQ/reply state");
     ++v147_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
TRIAL=NEXT_TRIAL
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&
             nwii::runtime::v146_leaf_seen==1u&&
             nwii::runtime::v147_next_seen==1u&&!c.is_running,
             "V147 original SC IPC first helper did not lead to a caller-owned next call");'''

def once(src: str, old: str, new: str) -> str:
    count=src.count(old)
    if count!=1:
        raise ValueError("V147 source anchor count differs: "+str(count)+" "+old[:72])
    return src.replace(old,new,1)

def derive(source: str) -> str:
    src=previous(source)
    src=once(src,STATE,STATE+'''
 static unsigned v147_next_seen=0;
 static uint32_t v147_first_target=0,v147_first_lr=0,v147_first_r13=0;
 static uint64_t v147_first_inst=0;''')
    src=once(src,RESET,RESET+'''
     nwii::runtime::v147_next_seen=0u;
     nwii::runtime::v147_first_target=nwii::runtime::v147_first_lr=
       nwii::runtime::v147_first_r13=0u;
     nwii::runtime::v147_first_inst=0u;''')
    src=once(src,V146_STOP,V147_CONTINUE)
    src=once(src,V146_OBSERVER,V147_OBSERVER+V146_OBSERVER)
    src=once(src,TRIAL,NEXT_TRIAL)
    return src

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
