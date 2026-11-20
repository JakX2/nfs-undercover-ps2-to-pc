#!/usr/bin/env python3
"""V158 native original SC OSLoadContext/RFI restoration checkpoint.

V157 proved the original dispatcher schedules OSLoadContext at 0x805229B4
from 0x80526CBC. Allow original translated PowerPC function to execute until
the guest-selected saved PC/MSR and GPR context are restored by RFI, then stop in the
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
CONTINUE='''     using V158Mem=undercover::wii::IosBus;
     const uint32_t selected=ctx.gpr[3];
     const bool route=addr==0x805229b4u&&ctx.lr==0x80526cbcu;
     const bool masked=(ctx.msr&V158Mem::MSR_EE)==0u;
     const bool aligned=(selected&3u)==0u;
     const bool range=(selected>=0x80000000u&&selected<=0x81800000u-416u)||
           (selected>=0x90000000u&&selected<=0x94000000u-416u);
     const bool mapped=range&&ctx.mmu.get_ptr(selected)!=nullptr&&
           ctx.mmu.get_ptr(selected+412u)!=nullptr;
     const bool idle=selected==IDLE_CONTEXT;
     const bool thread=selected==THREAD;
     std::cout<<"V158_SC_LOAD_ARG route="<<route<<" masked="<<masked
              <<" aligned="<<aligned<<" mapped="<<mapped
              <<" idle="<<idle<<" thread="<<thread<<std::endl;
     check(route&&masked&&aligned&&mapped,
           "V158 original SC context-loader pointer/ABI is invalid");
     v158_expected_pc=ctx.mmu.read32(selected+408u);
     v158_expected_msr=ctx.mmu.read32(selected+412u);
     v158_expected_lr=ctx.mmu.read32(selected+132u);
     v158_expected_ctr=ctx.mmu.read32(selected+136u);
     v158_expected_xer=ctx.mmu.read32(selected+140u);
     for(unsigned i=0u;i<32u;++i)
       v158_expected_gprs[i]=ctx.mmu.read32(selected+4u*i);
     v158_load_inst=ctx.inst_count;
     std::cout<<"V158_SC_LOAD_ENTRY route=1"<<std::endl;
     ++v157_next_seen;
     return; // execute original guest-selected context restoration, including RFI
   }'''
CALLBACK_ANCHOR='''bool process_pending_callbacks(CPUContext& ctx){'''
RFI_OBSERVER='''bool process_pending_callbacks(CPUContext& ctx){
  if(v141_live&&v157_next_seen==1u&&v158_rfi_seen==0u&&
     ctx.pc==v158_expected_pc&&ctx.inst_count>v158_load_inst){
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
    const bool pc=ctx.pc==v158_expected_pc;
    const bool msr=ctx.msr==v158_expected_msr;
    const bool gprs=ctx.gpr==v158_expected_gprs&&
          ctx.lr==v158_expected_lr&&ctx.ctr==v158_expected_ctr&&
          ctx.xer==v158_expected_xer;
    const bool waiting=ctx.mmu.read16(THREAD+712u)==4u&&
          ctx.mmu.read32(sleep73_queue)==THREAD;
    const bool ee=(ctx.msr&V158Bus::MSR_EE)!=0u;
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
    const bool old_pc=ctx.pc==sched74_resume;
    std::cout<<"V158_SC_RFI pc="<<pc<<" msr="<<msr
             <<" regs="<<gprs<<" waiting="<<waiting
             <<" irq="<<irq<<" reply="<<reply<<" coherent="<<coherent
             <<" ee="<<ee<<" ready="<<ready<<" old_pc="<<old_pc<<std::endl;
    check(pc&&msr&&gprs&&waiting&&irq&&reply&&coherent,
          "V158 original SC OSLoadContext did not restore guest-selected context");
    ++v158_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
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
    s=once(s,STATE,STATE+'''
 static unsigned v158_rfi_seen=0;
 static uint64_t v158_load_inst=0;
 static std::array<uint32_t,32> v158_expected_gprs{};
 static uint32_t v158_expected_pc=0,v158_expected_msr=0;
 static uint32_t v158_expected_lr=0,v158_expected_ctr=0,v158_expected_xer=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v158_rfi_seen=0u;
     nwii::runtime::v158_load_inst=0u;
     nwii::runtime::v158_expected_gprs.fill(0u);
     nwii::runtime::v158_expected_pc=nwii::runtime::v158_expected_msr=0u;
     nwii::runtime::v158_expected_lr=nwii::runtime::v158_expected_ctr=
         nwii::runtime::v158_expected_xer=0u;''')
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
