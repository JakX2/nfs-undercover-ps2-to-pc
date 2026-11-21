#!/usr/bin/env python3
"""V230 original negative Y1 callback preparation via OSClearContext.

Extend authenticated V229 guest callback-preparation path by executing
original OSClearContext and observing actual OSSetCurrentContext entry.
Preserve the negative -4 IOS response, cleared Y1/IRQ and guest stack.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v229_sc_y1_post_cache_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    v229_next_pc=addr;v229_next_lr=ctx.lr;
    ++v229_call_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80522af4u&&ctx.lr==0x80519290u,
          "V230 original negative reply OSClearContext callsite changed");
    v229_next_pc=addr;v229_next_lr=ctx.lr;
    ++v229_call_seen;
    v230_start_inst=ctx.inst_count;
    return; // execute genuine OSClearContext
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v229_call_seen==1u&&
     v230_context_seen==0u&&ctx.pc==addr&&
     addr==0x805228ccu&&ctx.lr==0x80519298u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&(M::Y1|M::Y2))==0u)&&
          ((*flag&H::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool wire=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.inst_count>v230_start_inst&&
          ctx.gpr[13]==v147_first_r13&&
          (ctx.msr&B::MSR_EE)==0u;
    const bool context=ctx.gpr[3]==ctx.gpr[1]+8u&&
          ctx.mmu.get_ptr(ctx.gpr[3])!=nullptr;
    const uint32_t sda=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(sda)!=nullptr&&
          ctx.mmu.read8(sda)==1u;
    std::cout<<"V230_CONTEXT_NEXT irq_down="<<clear
             <<" wire="<<wire<<" guest="<<guest
             <<" context="<<context<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(clear&&wire&&guest&&context&&sc,
          "V230 original third negative IOS reply context switch ABI differs");
    ++v230_context_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=nwii::runtime::ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      check(stopped&&nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v227_ack_seen==1u&&
            nwii::runtime::v228_next_seen==1u&&
            nwii::runtime::v229_call_seen==1u&&
            nwii::runtime::v230_context_seen==1u&&
            ctrl.has_value()&&flag.has_value()&&
            ((*ctrl&(M::Y1|M::Y2))==0u)&&
            ((*flag&H::IPC_PPC)==0u)&&
            !nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid&&
            !c.is_running&&c.pc==0x805228ccu&&c.lr==0x80519298u&&
            c.gpr[3]==c.gpr[1]+8u,
            "V230 third negative IOS reply OSClear-to-OSSetContext checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V230 inherited V229 original OS context boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v230_context_seen=0u;
 static uint64_t v230_start_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v230_context_seen=0u;
     nwii::runtime::v230_start_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
