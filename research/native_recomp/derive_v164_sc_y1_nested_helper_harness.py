#!/usr/bin/env python3
"""V164 run original SC second-reply scheduler-disable into nested IRQ helper.

V163's first-class owner-original checkpoint targets scheduler disable
0x805293F8 (LR 0x80526C98), after the genuine second Y1 IRQ timebase call.
At this phase the IOS_Open reply has already been published and Y1 is pending;
first-IRQ checks demanding queued_replies()==1 are no longer applicable.
Only test observers are phase-scoped. No PowerPC body, guest CPU state,
mailbox state, status flag, IRQ latch or IOS service is written or faked.
"""
import argparse
from pathlib import Path
from derive_v163_sc_y1_disable_harness import (
    derive as previous, STATE, RESET, OBSERVATION as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, TRACE_ANCHOR,
)

STOP='''    ++v163_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805293f8u&&ctx.lr==0x80526c98u,
          "V164 original second SC IRQ scheduler-disable entry differs from V163");
    v164_start_inst=ctx.inst_count;
    ++v163_next_seen;
    return; // execute original guest scheduler-disable function
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v163_next_seen==1u&&v164_leaf_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto control=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=control.has_value()&&flags.has_value()&&
          ((*control&Mail::Y1)!=0u)&&((*control&Mail::Y2)==0u)&&
          ((*flags&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool guest=ctx.pc==addr&&ctx.inst_count>v164_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x805293f8u&&
          ctx.lr<0x80529434u&&!(ctx.lr&3u);
    const bool target=addr==INT_DISABLE||addr==INT_RESTORE;
    std::cout<<"V164_SC_Y1_NESTED irq="<<irq<<" reply="<<reply
             <<" masked="<<masked<<" guest="<<guest
             <<" caller="<<caller<<" target="<<target
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&masked&&guest&&caller&&target,
          "V164 SC reply IRQ scheduler disable did not reach authentic nested helper");
    ++v164_leaf_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
OLD_NESTED='''   if(v141_live&&v144_disable_seen==1u&&
      (addr==INT_DISABLE||addr==INT_RESTORE)&&
      ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u){'''
SCOPED_NESTED='''   if(v141_live&&v144_disable_seen==1u&&
      v161_dispatch_seen==0u&&
      (addr==INT_DISABLE||addr==INT_RESTORE)&&
      ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u){'''
OLD_REGISTERED='''   if(v141_live&&v144_disable_seen==1u&&addr==0x80519318u){'''
SCOPED_REGISTERED='''   if(v141_live&&v144_disable_seen==1u&&
      v161_dispatch_seen==0u&&addr==0x80519318u){'''
OLD_V144='''   if(v141_live&&v143_time_seen==1u&&addr==0x805293f8u){'''
SCOPED_V144='''   if(v141_live&&v143_time_seen==1u&&
      v161_dispatch_seen==0u&&addr==0x805293f8u){'''
V163_FINAL='''             c.pc==0x805293f8u&&c.lr==0x80526c98u&&
             !c.is_running,'''
V164_FINAL='''             ((c.pc==0x805293f8u&&c.lr==0x80526c98u)||
              (nwii::runtime::v164_leaf_seen==1u&&
               (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
               c.lr>=0x805293f8u&&c.lr<0x80529434u))&&
             !c.is_running,'''
NEXT_TRIAL='''       check(nwii::runtime::v164_leaf_seen==1u&&
             nwii::runtime::v163_next_seen==1u&&
             nwii::runtime::v162_next_seen==1u&&
             nwii::runtime::v161_dispatch_seen==1u&&
             (c.pc==INT_DISABLE||c.pc==INT_RESTORE)&&
             c.lr>=0x805293f8u&&c.lr<0x80529434u&&
             !c.is_running,
             "V164 second SC reply scheduler helper did not reach real IRQ leaf");'''

def once(s: str, old: str, new: str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V164 original-free anchor count={count}: {old[:78]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    for anchor in (STOP,OLD_NESTED,OLD_REGISTERED,OLD_V144):
        if s.count(anchor)!=1:
            raise ValueError(f"V164 inherited first-phase observer changed: {anchor[:65]}")
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V163_FINAL)!=1:
        raise ValueError("V164 original predecessor V163 checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v164_leaf_seen=0;
 static uint64_t v164_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v164_leaf_seen=0u;
     nwii::runtime::v164_start_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,OLD_NESTED,SCOPED_NESTED)
    s=once(s,OLD_REGISTERED,SCOPED_REGISTERED)
    s=once(s,OLD_V144,SCOPED_V144)
    s=once(s,PREVIOUS_TRIAL,
           PREVIOUS_TRIAL.replace(V163_FINAL,V164_FINAL,1)+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
