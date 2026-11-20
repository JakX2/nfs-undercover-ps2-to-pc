#!/usr/bin/env python3
"""V151 allow original SC Hollywood IRQ flag W1C to return into guest code.

This read-only observer stops at the next genuine PowerPC function entry
after the original handler clears Y2 and the Hollywood IPC interrupt flag.
It does not complete the queued IOS reply, fabricate SC readiness, or
change owner game instructions. The successor PC is discovered, not guessed.
"""
import argparse
from pathlib import Path
from derive_v150_sc_irq_flag_harness import derive as previous, NEXT_TRIAL as TRIAL, V146_ONCE

STATE="static unsigned v150_flag_seen=0;"
RESET="nwii::runtime::v150_flag_seen=0u;"
MMIO_STOP='''       ++v150_flag_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
     return;'''
MMIO_CONTINUE='''       ++v150_flag_seen;
       v151_flag_inst=ipc70_ram.cpu->inst_count;
     }
     return;'''
OBSERVER='''   if(v141_live&&v150_flag_seen==1u&&v151_next_seen==0u&&ctx.pc==addr){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     using H=undercover::wii::HollywoodIrq;
     const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
     const bool cleared=control.has_value()&&flags.has_value()&&
           ((*control&M::Y2)==0u)&&((*flags&H::IPC_PPC)==0u);
     const bool irq_down=!ipc70_bus.external_irq_level();
     const bool queued=ipc70_bus.services().queued_replies()==1u;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool progressed=ctx.inst_count>v151_flag_inst&&
           ctx.gpr[13]==v147_first_r13;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V151_SC_AFTER_FLAG cleared="<<cleared
              <<" irq_down="<<irq_down<<" queued="<<queued
              <<" masked="<<masked<<" progressed="<<progressed
              <<" text="<<text<<" target="<<std::hex<<addr
              <<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(cleared&&irq_down&&queued&&masked&&progressed&&text,
           "V151 SC IRQ clear did not reach a valid original next call");
     ++v151_next_seen;
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
             nwii::runtime::v151_next_seen==1u&&!c.is_running,
             "V151 SC IRQ clear did not proceed to next authenticated guest call");'''

def once(s:str,a:str,b:str)->str:
    n=s.count(a)
    if n!=1:raise ValueError(f"V151 source-only anchor count={n}: {a[:75]}")
    return s.replace(a,b,1)

def derive(source:str)->str:
    s=previous(source)
    s=once(s,STATE,STATE+"\n static unsigned v151_next_seen=0;\n static uint64_t v151_flag_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v151_next_seen=0u;\n     nwii::runtime::v151_flag_inst=0u;")
    s=once(s,MMIO_STOP,MMIO_CONTINUE)
    s=once(s,V146_ONCE,OBSERVER+V146_ONCE)
    s=once(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
