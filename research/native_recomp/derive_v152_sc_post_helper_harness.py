#!/usr/bin/env python3
"""V152 execute the original SC IPC post-ACK helper at 0x8051B060.

The authenticated V151 handler call at LR 0x805193A4 is allowed to run.
Observe the next native translated function entry with guest/IRQ/queue checks.
Do not assume a handler return or mutate guest state to complete one.
"""
import argparse
from pathlib import Path
from derive_v151_sc_post_flag_harness import (
    derive as previous, NEXT_TRIAL as TRIAL, V146_ONCE,
)

STATE="static unsigned v151_next_seen=0;"
RESET="nwii::runtime::v151_next_seen=0u;"
STOP='''     ++v151_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x8051b060u&&ctx.lr==0x805193a4u,
           "V152 original post-IRQ first helper/callsite differs");
     ++v151_next_seen;
     v152_start_inst=ctx.inst_count;return;
   }'''
OBSERVER='''   if(v141_live&&v151_next_seen==1u&&v152_next_seen==0u&&ctx.pc==addr){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using H=undercover::wii::HollywoodIrq;
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
     const bool clean=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&M::Y2)==0u)&&((*flags&H::IPC_PPC)==0u);
     const bool idle=!ipc70_bus.external_irq_level();
     const bool queued=ipc70_bus.services().queued_replies()==1u;
     const bool guest=(ctx.msr&0x8000u)==0u&&
          ctx.gpr[13]==v147_first_r13&&ctx.inst_count>v152_start_inst;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V152_SC_POST_HELPER clean="<<clean<<" idle="<<idle
              <<" queued="<<queued<<" guest="<<guest<<" text="<<text
              <<" target="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(clean&&idle&&queued&&guest&&text,
           "V152 authentic post-IRQ helper did not reach valid guest successor");
     ++v152_next_seen;
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
             nwii::runtime::v148_distinct_seen==1u&&
             nwii::runtime::v149_helper_seen==1u&&
             nwii::runtime::v149_ack_seen==1u&&
             nwii::runtime::v150_flag_seen==1u&&
             nwii::runtime::v151_next_seen==1u&&
             nwii::runtime::v152_next_seen==1u&&!c.is_running,
             "V152 original post-IRQ helper did not execute until next native guest call");'''

def once(s:str,a:str,b:str)->str:
    n=s.count(a)
    if n!=1:raise ValueError(f"V152 source-only anchor count={n}: {a[:74]}")
    return s.replace(a,b,1)

def derive(source:str)->str:
    s=previous(source)
    s=once(s,STATE,STATE+"\n static unsigned v152_next_seen=0;\n static uint64_t v152_start_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v152_next_seen=0u;\n     nwii::runtime::v152_start_inst=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,V146_ONCE,OBSERVER+V146_ONCE)
    s=once(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
