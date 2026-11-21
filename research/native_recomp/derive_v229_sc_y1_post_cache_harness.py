#!/usr/bin/env python3
"""V229 execute original cache helper to next negative Y1 reply callee.

V228 verified real original Y1/PPC_FLAG W1C and the DCInvalidateRange
entry. This stage executes that cache helper and follows only genuine
PowerPC call entries, retaining original -4 reply and clear interrupt.
NWiiRecomp callback AOT root is a separate analysis-only runner change.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v228_sc_y1_negative_flag_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    ++v228_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v228_next_seen;
    v229_start_inst=ctx.inst_count;
    return; // original DCInvalidateRange and reply handler continue
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v228_next_seen==1u&&
     v229_call_seen==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.inst_count>v229_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&(M::Y1|M::Y2))==0u)&&
          ((*flag&H::IPC_PPC)==0u)&&
          !ipc70_bus.external_irq_level();
    const bool negative=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          (ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x805190c0u&&
          ctx.lr<0x80519318u&&!(ctx.lr&3u)&&!(addr&3u);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    const bool context=addr==0x80522af4u||addr==0x805228ccu;
    const bool callback=addr==0x804f0e04u;
    std::cout<<"V229_NEG_POST_CACHE clear="<<clear
             <<" negative="<<negative<<" guest="<<guest
             <<" caller="<<caller<<" sc="<<sc
             <<" context="<<context<<" callback="<<callback
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(clear&&negative&&guest&&caller&&sc,
          "V229 original negative Y1 post-invalidate guest call differs");
    v229_next_pc=addr;v229_next_lr=ctx.lr;
    ++v229_call_seen;
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
            !c.is_running&&c.pc==nwii::runtime::v229_next_pc&&
            c.lr==nwii::runtime::v229_next_lr&&
            c.pc>=0x80400000u&&c.pc<0x80600000u,
            "V229 genuine negative reply post-cache guest successor failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V229 previous original cache-helper entry changed")
    s=once(s,STATE,STATE+'''
 static unsigned v229_call_seen=0u;
 static uint64_t v229_start_inst=0u;
 static uint32_t v229_next_pc=0u,v229_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v229_call_seen=0u;
     nwii::runtime::v229_start_inst=0u;
     nwii::runtime::v229_next_pc=nwii::runtime::v229_next_lr=0u;''')
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
