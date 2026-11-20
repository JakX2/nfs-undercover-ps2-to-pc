#!/usr/bin/env python3
"""V158 native original SC OSLoadContext/RFI restoration checkpoint.

V157 proved the original dispatcher schedules OSLoadContext at 0x805229B4
from 0x80526CBC. Allow original translated PowerPC function to execute until
the genuine saved PC/MSR and GPR context are restored by RFI, then stop in the
already-used guest scheduling callback before entering a new reply interrupt.
This is a read-only restoration proof, not a synthetic RFI, guest register
rewrite, Starlet response, or forced external IRQ.
"""
import argparse
from pathlib import Path
from derive_v157_sc_rescheduler_next_harness import (
    derive as previous, STATE, RESET,
    NEXT_OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL, V146_ONCE,
)

STOP='''     ++v157_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x805229b4u&&ctx.lr==0x80526cbcu&&
           ctx.gpr[3]==IDLE_CONTEXT&&!(ctx.msr&0x8000u),
           "V158 original SC context-loader entry ABI differs from V157 evidence");
     v158_load_inst=ctx.inst_count;
     ++v157_next_seen;
     return; // execute original context restoration, including RFI
   }'''
CALLBACK_ANCHOR='''bool process_pending_callbacks(CPUContext& ctx){
  if(ack77_reply==1u&&reply79_irq==0u){'''
RFI_OBSERVER='''bool process_pending_callbacks(CPUContext& ctx){
  if(v141_live&&v157_next_seen==1u&&v158_rfi_seen==0u&&
     ctx.pc==sched74_resume&&ctx.inst_count>v158_load_inst){
    using V158Bus=undercover::wii::IosBus;
    using V158Mail=undercover::wii::IpcMailbox;
    using V158Irq=undercover::wii::HollywoodIrq;
    using V158Ios=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(V158Bus::IPC+V158Mail::PPCCTRL);
    const auto flags=ipc70_bus.read32(V158Bus::IPC+V158Irq::PPC_FLAG);
    const auto msg=ipc70_bus.read32(V158Bus::IPC+V158Mail::ARMMSG);
    const bool irq=ctrl.has_value()&&flags.has_value()&&msg.has_value()&&
          ((*ctrl&V158Mail::Y1)!=0u)&&((*ctrl&V158Mail::Y2)==0u)&&
          ((*flags&V158Irq::IPC_PPC)!=0u)&&*msg==v153_phys&&
          ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==V158Ios::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd&&
          ipc70_bus.services().queued_replies()==0u&&
          ipc70_bus.services().is_open(v153_fd,V158Ios::Device::File);
    const bool pc=ctx.pc==sched74_resume;
    const bool msr=ctx.msr==vector75_srr1;
    const bool gprs=ctx.gpr==vector75_gprs&&
          ctx.lr==vector75_lr&&ctx.ctr==vector75_ctr&&ctx.xer==vector75_xer;
    const bool waiting=ctx.mmu.read16(THREAD+712u)==4u&&
          ctx.mmu.read32(sleep73_queue)==THREAD;
    const bool ee=(ctx.msr&V158Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    std::cout<<"V158_SC_RFI pc="<<pc<<" msr="<<msr
             <<" regs="<<gprs<<" waiting="<<waiting
             <<" irq="<<irq<<" reply="<<reply<<" coherent="<<coherent
             <<" ee="<<ee<<" ready="<<ready<<std::endl;
    check(pc&&msr&&gprs&&waiting&&irq&&reply&&coherent,
          "V158 original SC OSLoadContext did not restore saved external context");
    ++v158_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
  if(ack77_reply==1u&&reply79_irq==0u){'''
NEXT_TRIAL='''       check(nwii::runtime::v158_rfi_seen==1u&&
             nwii::runtime::v157_next_seen==1u&&
             nwii::runtime::v156_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,
             "V158 original SC context loader did not return via restored RFI");'''

def once(s: str, a: str, b: str)->str:
    n=s.count(a)
    if n!=1:
        raise ValueError(f"V158 public source anchor count={n}: {a[:80]}")
    return s.replace(a,b,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V158 predecessor OSLoadContext stop changed")
    s=once(s,STATE,STATE+"\n static unsigned v158_rfi_seen=0;\n static uint64_t v158_load_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v158_rfi_seen=0u;\n     nwii::runtime::v158_load_inst=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,CALLBACK_ANCHOR,RFI_OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
