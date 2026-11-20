#!/usr/bin/env python3
"""V163 execute authentic second SC IRQ timebase function to next scheduler call.

The V162 owner-original 16-trial trace established PC 0x8052A824,
LR 0x80526C84. Release that observed timebase function and execute original
PowerPC code to the scheduler's next interrupt-disable helper. Retain the
published SYSCONF IOS_Open reply and Broadway Y1 interrupt. No synthetic
PowerPC instructions, guest status writes, IOS pumping or control transfer.
"""
import argparse
from pathlib import Path
from derive_v162_sc_reply_next_harness import (
    derive as previous, STATE, RESET,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    TRACE_ANCHOR
)

STOP='''    ++v162_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8052a824u&&ctx.lr==0x80526c84u,
          "V163 original second SC IRQ timebase checkpoint differs from V162");
    v163_start_inst=ctx.inst_count;
    ++v162_next_seen;
    return; // execute real Wii timebase guest helper
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v162_next_seen==1u&&v163_next_seen==0u&&addr==0x805293f8u){
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v163_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr==0x80526c98u;
    std::cout<<"V163_SC_Y1_DISABLE irq="<<irq<<" reply="<<reply
             <<" masked="<<masked<<" guest="<<guest<<" caller="<<caller
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&reply&&masked&&guest&&caller,
          "V163 original second SC IRQ timebase did not reach disable helper");
    ++v163_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_TRIAL='''       check(nwii::runtime::v163_next_seen==1u&&
             nwii::runtime::v162_next_seen==1u&&
             nwii::runtime::v161_dispatch_seen==1u&&
             c.pc==0x805293f8u&&c.lr==0x80526c98u&&
             !c.is_running,
             "V163 original second SC IRQ timebase did not advance to scheduler disable");'''

def once(s: str, old: str, new: str)->str:
    count=s.count(old)
    if count!=1:raise ValueError(f"V163 public source anchor count={count}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V163 inherited V162 original timebase stop differs")
    s=once(s,STATE,STATE+'''
 static unsigned v163_next_seen=0;
 static uint64_t v163_start_inst=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v163_next_seen=0u;
     nwii::runtime::v163_start_inst=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
