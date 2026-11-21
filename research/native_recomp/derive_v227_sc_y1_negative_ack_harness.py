#!/usr/bin/env python3
"""V227 execute the original third negative-Y1 PPCCTRL W1C.

Continue the V226-authenticated original PowerPC IPCWriteReg function at
0x8051906C (LR=0x8051910C). Observe only the real guest MMIO store after
the existing Broadway bus applies write-one-to-clear, keeping the genuine
-4 IOS_Open reply intact. Hollywood PPC_FLAG requires a separate W1C.
"""
import argparse
from pathlib import Path
from derive_v226_sc_y1_reply_successor_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v172_sc_y1_ack_harness import MMIO_ANCHOR
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v226_next_pc=addr;v226_next_lr=ctx.lr;
    ++v226_successor_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051906cu&&ctx.lr==0x8051910cu,
          "V227 original third negative Y1 PPCCTRL writer callsite differs");
    v226_next_pc=addr;v226_next_lr=ctx.lr;
    ++v226_successor_seen;
    v227_writer_inst=ctx.inst_count;
    v227_writes_before=mmio_writes.size();
    return; // original PowerPC MMIO writer executes unmodified
  }'''
ACK='''     if(v215_vector_seen==1u&&v226_successor_seen==1u&&
        v227_ack_seen==0u&&
        (addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)){
       using IOS=undercover::wii::StmIos;
       const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
       const bool wrote=(value&M::Y1)!=0u&&
             mmio_writes.size()>v227_writes_before;
       const bool cleared=control.has_value()&&
             ((*control&M::Y1)==0u)&&((*control&M::Y2)==0u);
       const bool flag=flags.has_value()&&
             ((*flags&H::IPC_PPC)!=0u);
       const bool irq=ipc70_bus.external_irq_level();
       const bool wire=ipc70_ram.valid(v183_second_phys,64u)&&
             ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
             ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
             int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
             ipc70_bus.services().queued_replies()==0u;
       const bool guest=ipc70_ram.cpu!=nullptr&&
             ipc70_ram.cpu->lr==0x8051910cu&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u&&
             ipc70_ram.cpu->gpr[13]==v147_first_r13;
       const bool advanced=guest&&
             ipc70_ram.cpu->inst_count>v227_writer_inst;
       const uint32_t scaddr=guest?ipc70_ram.cpu->gpr[13]-3176u:0u;
       const bool sc=guest&&ipc70_ram.cpu->mmu.get_ptr(scaddr)!=nullptr&&
             ipc70_ram.cpu->mmu.read8(scaddr)==1u;
       std::cout<<"V227_NEG_Y1_ACK wrote="<<wrote
                <<" cleared="<<cleared<<" flag="<<flag
                <<" irq="<<irq<<" wire="<<wire
                <<" guest="<<guest<<" advanced="<<advanced
                <<" sc="<<sc<<std::endl;
       check(wrote&&cleared&&flag&&irq&&wire&&guest&&advanced&&sc,
             "V227 original third negative Y1 PPCCTRL W1C was not performed by game code");
       ++v227_ack_seen;
       ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
     }'''
NEXT_END='''      using V227Bus=undercover::wii::IosBus;
      using V227Mail=undercover::wii::IpcMailbox;
      using V227Irq=undercover::wii::HollywoodIrq;
      const auto v227_ctrl=nwii::runtime::ipc70_bus.read32(
            V227Bus::IPC+V227Mail::PPCCTRL);
      const auto v227_flag=nwii::runtime::ipc70_bus.read32(
            V227Bus::IPC+V227Irq::PPC_FLAG);
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v222_next_seen==1u&&
            nwii::runtime::v223_read_seen==1u&&
            nwii::runtime::v224_second_seen==1u&&
            nwii::runtime::v226_successor_seen==1u&&
            nwii::runtime::v227_ack_seen==1u&&
            v227_ctrl.has_value()&&v227_flag.has_value()&&
            ((*v227_ctrl&V227Mail::Y1)==0u)&&
            ((*v227_ctrl&V227Mail::Y2)==0u)&&
            ((*v227_flag&V227Irq::IPC_PPC)!=0u)&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid&&
            !c.is_running&&c.lr==0x8051910cu,
            "V227 third negative Y1 real PPCCTRL W1C checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V227 V226 original PPCCTRL writer checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v227_ack_seen=0u;
 static uint64_t v227_writer_inst=0u;
 static size_t v227_writes_before=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v227_ack_seen=0u;
     nwii::runtime::v227_writer_inst=0u;
     nwii::runtime::v227_writes_before=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    if s.count(MMIO_ANCHOR)!=1:
        raise ValueError("V227 native guest MMIO W1C post-write anchor changed")
    s=once(s,MMIO_ANCHOR,MMIO_ANCHOR+"\n"+ACK)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
