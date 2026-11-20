#!/usr/bin/env python3
"""V166 original second SC reply interrupt restores nested OS interrupt state.

Verified V165 owner-original execution reached 0x805265D4 with LR 0x8052941C.
Run that original OSRestoreInterrupts PowerPC function to the next authentic
guest call. Preserve IOS_Open file descriptor, original Y1 and the saved thread.
Observe, rather than assume, guest MSR EE and external IRQ deliverability.
No synthetic callback, PowerPC instructions, guest memory writes, or IOS pump.
"""
import argparse
from pathlib import Path
from derive_v165_sc_y1_post_osdi_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    V165_FINAL, V165_CHECK,
)

STOP='''    ++v165_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==INT_RESTORE&&ctx.lr==0x8052941cu,
          "V166 original SC second reply nested OSRestore ABI differs from V165");
    v166_start_inst=ctx.inst_count;
    ++v165_next_seen;
    return; // execute original OSRestoreInterrupts guest body
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v165_next_seen==1u&&v166_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&Mail::Y1)!=0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v166_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool call=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const bool ipc=addr==0x80519318u;
    const bool helper=addr==INT_DISABLE||addr==INT_RESTORE;
    std::cout<<"V166_SC_POST_RESTORE irq="<<irq<<" reply="<<reply
             <<" guest="<<guest<<" call="<<call<<" coherent="<<coherent
             <<" ee="<<ee<<" ready="<<ready<<" ipc="<<ipc
             <<" helper="<<helper<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&guest&&call&&coherent,
          "V166 SC second reply nested restore did not reach valid guest successor");
    v166_target_pc=addr;v166_target_lr=ctx.lr;
    ++v166_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V166_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_leaf_seen==1u&&
               (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running,'''
V166_CHECK='''             ((c.pc==INT_DISABLE||c.pc==INT_RESTORE)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr))&&
             !c.is_running,'''
V165_TRIAL_END='''             c.pc==nwii::runtime::v165_target_pc&&
             c.lr==nwii::runtime::v165_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
V166_TRIAL_END='''             ((c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr)||
              (nwii::runtime::v166_next_seen==1u&&
               c.pc==nwii::runtime::v166_target_pc&&
               c.lr==nwii::runtime::v166_target_lr))&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v166_next_seen==1u&&
             nwii::runtime::v165_next_seen==1u&&
             nwii::runtime::v164_leaf_seen==1u&&
             nwii::runtime::v163_next_seen==1u&&
             c.pc==nwii::runtime::v166_target_pc&&
             c.lr==nwii::runtime::v166_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V166 second SC reply nested interrupt restore did not reach real guest call");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V166 original-free derived anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
        PREVIOUS_TRIAL.count(V165_TRIAL_END)!=1 or
        s.count(V165_CHECK)!=1 or s.count(V165_FINAL)!=1):
        raise ValueError("V166 predecessor V165 original guest route or trial differs")
    s=once(s,STATE,STATE+'''
 static unsigned v166_next_seen=0;
 static uint64_t v166_start_inst=0;
 static uint32_t v166_target_pc=0,v166_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v166_next_seen=0u;
     nwii::runtime::v166_start_inst=0u;
     nwii::runtime::v166_target_pc=nwii::runtime::v166_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,V165_FINAL,V166_FINAL)
    s=once(s,V165_CHECK,V166_CHECK)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V165_TRIAL_END,V166_TRIAL_END,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
