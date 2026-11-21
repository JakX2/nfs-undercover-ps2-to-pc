#!/usr/bin/env python3
"""V212 verify genuine second Wii IOS interrupt OSLoadContext/RFI.

V211 owner-original reached OSLoadContext at PC 0x805229B4,
LR 0x80526CBC. Record guest-selected context, allow original PPC RFI
and prove exact restored PC/MSR/GPRs/LR/CTR/XER in the normal callback.
No host RFI fabrication or guest-register write is permitted.
"""
import argparse
from pathlib import Path
from derive_v211_sc_y2_resched_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v211_target_pc=addr;v211_target_lr=ctx.lr;
    v211_final_sc=sc;v211_final_queue=queue;
    ++v211_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CONTINUE='''    const bool route=addr==0x805229b4u&&ctx.lr==0x80526cbcu;
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
    const uint32_t selected=ctx.gpr[3];
    const bool aligned=(selected&3u)==0u;
    const bool range=(selected>=0x80000000u&&selected<=0x81800000u-416u)||
          (selected>=0x90000000u&&selected<=0x94000000u-416u);
    const bool ptrmapped=range&&ctx.mmu.get_ptr(selected)!=nullptr&&
          ctx.mmu.get_ptr(selected+412u)!=nullptr;
    const bool idle=selected==IDLE_CONTEXT;
    const bool thread=selected==THREAD;
    std::cout<<"V212_Y2_LOAD route="<<route<<" masked="<<masked
             <<" aligned="<<aligned<<" mapped="<<ptrmapped
             <<" idle="<<idle<<" thread="<<thread<<std::endl;
    check(route&&masked&&aligned&&ptrmapped&&y2&&irq_down&&
          queue&&open&&!replied&&guest&&caller&&coherent&&mapped,
          "V212 original second IRQ OSLoadContext pointer or ABI invalid");
    v212_expected_pc=ctx.mmu.read32(selected+408u);
    v212_expected_msr=ctx.mmu.read32(selected+412u);
    v212_expected_lr=ctx.mmu.read32(selected+132u);
    v212_expected_ctr=ctx.mmu.read32(selected+136u);
    v212_expected_xer=ctx.mmu.read32(selected+140u);
    for(unsigned i=0u;i<32u;++i)
      v212_expected_gprs[i]=ctx.mmu.read32(selected+4u*i);
    v212_selected_idle=idle;v212_selected_thread=thread;
    v212_load_inst=ctx.inst_count;
    v211_target_pc=addr;v211_target_lr=ctx.lr;
    v211_final_sc=sc;v211_final_queue=queue;
    ++v211_next_seen;
    return; // original PowerPC OSLoadContext performs RFI itself
  }
'''
CALLBACK='''bool process_pending_callbacks(CPUContext& ctx){'''
OBSERVER='''bool process_pending_callbacks(CPUContext& ctx){
  if(v196_live&&v211_next_seen==1u&&v212_rfi_seen==0u&&
     ctx.pc==v212_expected_pc&&ctx.inst_count>v212_load_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq_down=!ipc70_bus.external_irq_level()&&ctrl.has_value()&&
          flag.has_value()&&((*ctrl&(M::Y1|M::Y2))==0u)&&
          ((*flag&H::IPC_PPC)==0u);
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool pc=ctx.pc==v212_expected_pc;
    const bool msr=ctx.msr==v212_expected_msr;
    const bool regs=ctx.gpr==v212_expected_gprs&&
          ctx.lr==v212_expected_lr&&
          ctx.ctr==v212_expected_ctr&&
          ctx.xer==v212_expected_xer;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&B::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const bool mapped=ctx.mmu.get_ptr(ctx.gpr[13]-3176u)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(ctx.gpr[13]-3176u)==1u;
    const bool ee=(ctx.msr&B::MSR_EE)!=0u;
    std::cout<<"V212_Y2_RFI pc="<<pc<<" msr="<<msr
             <<" regs="<<regs<<" irq_down="<<irq_down
             <<" queue="<<queue<<" open="<<open
             <<" coherent="<<coherent<<" sc="<<sc
             <<" ee="<<ee<<" idle="<<v212_selected_idle
             <<" thread="<<v212_selected_thread<<std::endl;
    check(pc&&msr&&regs&&irq_down&&queue&&open&&coherent&&sc,
          "V212 original second IRQ OSLoadContext did not restore native RFI state");
    ++v212_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            nwii::runtime::v208_next_seen==1u&&
            nwii::runtime::v209_next_seen==1u&&
            nwii::runtime::v210_next_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v212_expected_pc&&
            c.msr==nwii::runtime::v212_expected_msr&&
            c.gpr==nwii::runtime::v212_expected_gprs&&
            c.lr==nwii::runtime::v212_expected_lr&&
            c.ctr==nwii::runtime::v212_expected_ctr&&
            c.xer==nwii::runtime::v212_expected_xer&&
            nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
            !nwii::runtime::ipc70_bus.external_irq_level(),
            "V212 genuine second IRQ OSLoadContext RFI was not restored");
'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V212 verified V211 OSLoadContext boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v212_rfi_seen=0u;
 static uint64_t v212_load_inst=0u;
 static bool v212_selected_idle=false,v212_selected_thread=false;
 static std::array<uint32_t,32> v212_expected_gprs{};
 static uint32_t v212_expected_pc=0u,v212_expected_msr=0u;
 static uint32_t v212_expected_lr=0u,v212_expected_ctr=0u,v212_expected_xer=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v212_rfi_seen=0u;
     nwii::runtime::v212_load_inst=0u;
     nwii::runtime::v212_selected_idle=nwii::runtime::v212_selected_thread=false;
     nwii::runtime::v212_expected_gprs.fill(0u);
     nwii::runtime::v212_expected_pc=nwii::runtime::v212_expected_msr=0u;
     nwii::runtime::v212_expected_lr=nwii::runtime::v212_expected_ctr=
         nwii::runtime::v212_expected_xer=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,CALLBACK,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
