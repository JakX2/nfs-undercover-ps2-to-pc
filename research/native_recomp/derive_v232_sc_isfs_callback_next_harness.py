#!/usr/bin/env python3
"""V232 native Wii original _isfsFuncCb body and next indirect caller.

Continue owner-verified V231 callback entry into its original PowerPC
instructions. Record the first real nested function call, preserving
the actual -4 IOS_Open response, IRQ cleared and SC state. Retain the verified V225 ISFS AOT root while probing the genuine
nested callback target. Do not inject a guest call or callback.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v231_sc_y1_isfs_callback_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

# The legacy first-open allocator check must not intercept the
# third original negative IOS reply callback's own allocator/free.
# Scope only the caller of that historical first-open observer.
OPEN71_OLD='''   if(open71_trace(addr,ctx))return;'''
OPEN71_SCOPED='''   if(v231_callback_seen==0u&&open71_trace(addr,ctx))return;'''

STOP='''    v231_target_pc=addr;v231_target_lr=ctx.lr;
    ++v231_callback_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v231_target_pc=addr;v231_target_lr=ctx.lr;
    ++v231_callback_seen;
    v232_start_inst=ctx.inst_count;
    return; // execute original _isfsFuncCb translated PowerPC body
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v231_callback_seen==1u&&
     v232_next_seen==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.inst_count>v232_start_inst&&
     ctx.lr>=0x80400000u&&ctx.lr<0x80600000u){
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
    const uint32_t data=ctx.gpr[31];
    const bool mapped=data<=0xfffffef7u&&
          ctx.mmu.get_ptr(data)!=nullptr&&
          ctx.mmu.get_ptr(data+263u)!=nullptr;
    const bool selected=mapped&&ctx.mmu.read32(data+256u)==addr;
    const bool from_isfs=ctx.lr>=0x804f0e04u&&ctx.lr<0x804f0f84u;
    const bool nested=addr==0x8051e06cu&&ctx.lr==0x804f0f54u;
    const bool result=ctx.gpr[3]==uint32_t(IOS::Invalid);
    const bool userdata=mapped&&ctx.gpr[4]==ctx.mmu.read32(data+260u);
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          (ctx.msr&B::MSR_EE)==0u;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V232_ISFS_NEXT clear="<<clear<<" wire="<<wire
             <<" guest="<<guest<<" sc="<<sc
             <<" mapped="<<mapped<<" selected="<<selected
             <<" from_isfs="<<from_isfs
             <<" nested="<<nested<<" result="<<result
             <<" userdata="<<userdata
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(clear&&wire&&guest&&sc,
          "V232 original ISFS callback successor lost native Wii state");
    v232_next_pc=addr;v232_next_lr=ctx.lr;
    ++v232_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
OPEN71_OLD=''' static bool open71_trace(uint32_t addr,CPUContext&ctx){
   if(!stm70_open)return false;'''
OPEN71_SCOPED=''' static bool open71_trace(uint32_t addr,CPUContext&ctx){
   // The original V71 first-open allocator ABI must not be rechecked
   // after the third reply has entered the separate ISFS completion.
   if(v231_callback_seen==1u)return false;
   if(!stm70_open)return false;'''
NEXT_END='''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=nwii::runtime::ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      check(stopped&&nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v228_next_seen==1u&&
            nwii::runtime::v230_context_seen==1u&&
            nwii::runtime::v231_callback_seen==1u&&
            nwii::runtime::v232_next_seen==1u&&
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
            !c.is_running&&c.pc==nwii::runtime::v232_next_pc&&
            c.lr==nwii::runtime::v232_next_lr&&
            c.pc>=0x80400000u&&c.pc<0x80600000u&&
            c.lr>=0x80400000u&&c.lr<0x80600000u,
            "V232 original ISFS callback did not enter native successor");'''

def derive(source:str)->str:
    s=previous(source)
    # Guard only this legacy observer, not the real allocator or IOS path.
    s=once(s,OPEN71_OLD,OPEN71_SCOPED)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V232 authenticated V231 callback entry changed")
    s=once(s,STATE,STATE+'''
 static unsigned v232_next_seen=0u;
 static uint64_t v232_start_inst=0u;
 static uint32_t v232_next_pc=0u,v232_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v232_next_seen=0u;
     nwii::runtime::v232_start_inst=0u;
     nwii::runtime::v232_next_pc=nwii::runtime::v232_next_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OPEN71_OLD,OPEN71_SCOPED)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
