#!/usr/bin/env python3
"""V165 continue authentic second SC reply IRQ after nested interrupt-disable.

V164 verified the original second-IRQ scheduler at 0x805293F8 called
OSDisableInterrupts 0x805265AC, LR 0x8052940C. Execute that genuine helper
and discover the next original translated function entry. Report whether it
is the registered IPC callback or another scheduler helper; do not assume.
The SC IOS_Open reply, Y1 and guest CPU state remain untouched.
"""
import argparse
from pathlib import Path
from derive_v164_sc_y1_nested_helper_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, V164_FINAL, TRACE_ANCHOR,
)

STOP='''    ++v164_leaf_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==INT_DISABLE&&ctx.lr==0x8052940cu,
          "V165 authentic second SC IRQ nested OSDI callsite differs from V164");
    v165_start_inst=ctx.inst_count;
    ++v164_leaf_seen;
    return; // run original interrupt-disable helper body
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v164_leaf_seen==1u&&v165_next_seen==0u&&
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
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v165_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool ipc=addr==0x80519318u;
    const bool helper=addr==INT_DISABLE||addr==INT_RESTORE;
    std::cout<<"V165_SC_POST_OSDI irq="<<irq<<" reply="<<reply
             <<" masked="<<masked<<" guest="<<guest<<" caller="<<caller
             <<" ipc="<<ipc<<" helper="<<helper
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&masked&&guest&&caller,
          "V165 second SC reply OSDisable did not advance to legitimate guest");
    v165_target_pc=addr;v165_target_lr=ctx.lr;
    ++v165_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
V165_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_leaf_seen==1u&&
               (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr&&
               c.pc>=0x80400000u&&c.pc<0x80600000u))&&
             !c.is_running,'''
V164_CHECK='''             (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
             c.lr>=0x805293f8u&&c.lr<0x80529434u&&
             !c.is_running,'''
V165_CHECK='''             ((c.pc==INT_DISABLE||c.pc==INT_RESTORE)||
              (nwii::runtime::v165_next_seen==1u&&
               c.pc==nwii::runtime::v165_target_pc&&
               c.lr==nwii::runtime::v165_target_lr))&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v165_next_seen==1u&&
             nwii::runtime::v164_leaf_seen==1u&&
             nwii::runtime::v163_next_seen==1u&&
             nwii::runtime::v162_next_seen==1u&&
             c.pc==nwii::runtime::v165_target_pc&&
             c.lr==nwii::runtime::v165_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V165 original SC reply interrupt-disable did not reach genuine next call");'''

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V165 fail-closed original-free anchor count={n}: {old[:72]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V164_CHECK)!=1:
        raise ValueError("V165 inherited V164 exact OSDI checkpoint differs")
    s=once(s,STATE,STATE+'''
 static unsigned v165_next_seen=0;
 static uint64_t v165_start_inst=0;
 static uint32_t v165_target_pc=0,v165_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v165_next_seen=0u;
     nwii::runtime::v165_start_inst=0u;
     nwii::runtime::v165_target_pc=nwii::runtime::v165_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,V164_FINAL,V165_FINAL)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V164_CHECK,V165_CHECK,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
