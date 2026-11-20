#!/usr/bin/env python3
"""V164 run authentic second SC reply scheduler-disable code to next helper.

V163 proved original Wii scheduler-disable at 0x805293F8 (LR 0x80526C98).
Run that exact original PowerPC function to its first translated callee,
preserving published SYSCONF IOS_Open, Y1 interrupt and running thread context.
The inherited first-IRQ nested helper assertion remains active for its
original phase but not for the later verified second Y1 interrupt.
"""
import argparse
from pathlib import Path
from derive_v163_sc_y1_disable_harness import (
    derive as previous, STATE, RESET,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    TRACE_ANCHOR
)

STOP='''    ++v163_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805293f8u&&ctx.lr==0x80526c98u,
          "V164 second SC scheduler-disable callsite differs from V163");
    ++v163_next_seen;
    v164_start_inst=ctx.inst_count;
    return; // run authentic Wii scheduler interrupt-disable guest code
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v163_next_seen==1u&&v164_next_seen==0u&&
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
    const bool stepped=ctx.inst_count>v164_start_inst&&
          ctx.pc==addr&&ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u&&
          !(ctx.lr&3u);
    std::cout<<"V164_SC_DISABLE_NEXT irq="<<irq<<" reply="<<reply
             <<" masked="<<masked<<" stepped="<<stepped
             <<" caller="<<caller<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&masked&&stepped&&caller,
          "V164 original SC reply scheduler-disable next native call differs");
    ++v164_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
FIRST_PHASE='''   if(v141_live&&v144_disable_seen==1u&&
      (addr==INT_DISABLE||addr==INT_RESTORE)&&'''
SCOPED_PHASE='''   if(v141_live&&v144_disable_seen==1u&&
      v161_dispatch_seen==0u&&
      (addr==INT_DISABLE||addr==INT_RESTORE)&&'''
V163_END='''             c.pc==0x805293f8u&&c.lr==0x80526c98u&&
             !c.is_running,'''
V164_END='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_next_seen==1u&&
               c.pc>=0x80400000u&&c.pc<0x80600000u&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u))&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v164_next_seen==1u&&
             nwii::runtime::v163_next_seen==1u&&
             nwii::runtime::v162_next_seen==1u&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             c.lr>=0x805293f8u&&c.lr<0x80529434u&&
             !c.is_running,
             "V164 original second SC scheduler-disable did not call native helper");'''

def once(s: str, old: str, new: str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V164 public anchor count={n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V163_END)!=1:
        raise ValueError("V164 inherited SC scheduler-disable stop or trial changed")
    s=once(s,STATE,STATE+'''
 static unsigned v164_next_seen=0;
 static uint64_t v164_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v164_next_seen=0u;
     nwii::runtime::v164_start_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,FIRST_PHASE,SCOPED_PHASE)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V163_END,V164_END,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
