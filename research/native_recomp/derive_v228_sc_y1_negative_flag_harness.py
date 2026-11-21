#!/usr/bin/env python3
"""V228 verify original third negative Y1 Hollywood flag W1C.

After V227 authenticated guest PPCCTRL Y1 W1C, resume original code,
observe the separate Hollywood PPC_FLAG write-one-to-clear via the
native bus and stop at the original DCInvalidateRange call. Do not
synthesize flag ACK, queue change, success result, or cache operation.
"""
import argparse
from pathlib import Path
from derive_v227_sc_y1_negative_ack_harness import (
    derive as previous, ACK as PREVIOUS_ACK, NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''       ++v227_ack_seen;
       ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
     }'''
CONTINUE='''       ++v227_ack_seen;
       v228_start_inst=ipc70_ram.cpu->inst_count;
       v228_mmio_begin=mmio_writes.size();
       // Resume original PPC to its distinct Hollywood PPC_FLAG ACK.
     }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v227_ack_seen==1u&&
     v228_next_seen==0u&&addr==0x80522294u&&
     ctx.pc==addr&&ctx.lr==0x80519124u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool y1clear=ctrl.has_value()&&
          ((*ctrl&(M::Y1|M::Y2))==0u);
    const bool flag_clear=flag.has_value()&&
          ((*flag&H::IPC_PPC)==0u);
    const bool irq_down=!ipc70_bus.external_irq_level();
    unsigned flag_writes=0u;
    for(size_t i=v228_mmio_begin;i<mmio_writes.size();++i){
      const auto& write=mmio_writes[i];
      if((write.first==B::IPC+H::PPC_FLAG||
          write.first==B::MIRROR+H::PPC_FLAG)&&
         (write.second&H::IPC_PPC)!=0u)
        ++flag_writes;
    }
    const bool flag_w1c=flag_writes==1u;
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.inst_count>v228_start_inst&&
          ctx.gpr[13]==v147_first_r13&&
          (ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V228_NEG_FLAG y1="<<y1clear
             <<" w1c="<<flag_w1c<<" flag="<<flag_clear
             <<" irq_down="<<irq_down<<" reply="<<reply
             <<" guest="<<guest<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(y1clear&&flag_w1c&&flag_clear&&irq_down&&
          reply&&guest&&sc,
          "V228 original negative Y1 Hollywood flag W1C or cache-helper call differs");
    ++v228_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      using V228Bus=undercover::wii::IosBus;
      using V228Mail=undercover::wii::IpcMailbox;
      using V228Irq=undercover::wii::HollywoodIrq;
      const auto v228_ctrl=nwii::runtime::ipc70_bus.read32(
            V228Bus::IPC+V228Mail::PPCCTRL);
      const auto v228_flag=nwii::runtime::ipc70_bus.read32(
            V228Bus::IPC+V228Irq::PPC_FLAG);
      check(stopped&&nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v224_second_seen==1u&&
            nwii::runtime::v226_successor_seen==1u&&
            nwii::runtime::v227_ack_seen==1u&&
            nwii::runtime::v228_next_seen==1u&&
            v228_ctrl.has_value()&&v228_flag.has_value()&&
            ((*v228_ctrl&(V228Mail::Y1|V228Mail::Y2))==0u)&&
            ((*v228_flag&V228Irq::IPC_PPC)==0u)&&
            !nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid&&
            !c.is_running&&c.pc==0x80522294u&&c.lr==0x80519124u&&
            c.mmu.read8(c.gpr[13]-3176u)==1u,
            "V228 original negative Y1 flag ACK and cache helper checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_ACK.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V228 authenticated third Y1 PPCCTRL ACK checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v228_next_seen=0u;
 static uint64_t v228_start_inst=0u;
 static size_t v228_mmio_begin=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v228_next_seen=0u;
     nwii::runtime::v228_start_inst=0u;
     nwii::runtime::v228_mmio_begin=0u;''')
    s=once(s,PREVIOUS_ACK,PREVIOUS_ACK.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
