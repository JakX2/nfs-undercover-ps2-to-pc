#!/usr/bin/env python3
"""V205: original second-Y2 Hollywood IPC PPC_FLAG write-one-to-clear.

V204 owner-original executed the genuine PPCCTRL Y2 W1C with Hollywood
PPC_FLAG still asserted and a second IOS completion queued. Allow the
translated original code to continue and inspect the actual guest write
to Hollywood PPC_FLAG after the native bus applies W1C, without injecting
a host acknowledgment, IOS reply, or guest instruction.
"""
import argparse
from pathlib import Path
from derive_v204_sc_y2_ack_harness import (
    derive as previous, ACK as PREVIOUS_ACK,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v172_sc_y1_ack_harness import MMIO_ANCHOR

STOP='''       ++v204_ack_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }'''
CONTINUE='''       ++v204_ack_seen;
       v205_after_y2_inst=ipc70_ram.cpu->inst_count;
       // Resume original PowerPC code to its separate Hollywood flag ACK.
     }'''
OBSERVER='''     if(v196_live&&v204_ack_seen==1u&&v205_flag_seen==0u&&
        (addr==B::IPC+H::PPC_FLAG||addr==B::MIRROR+H::PPC_FLAG)){
       const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
       const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const bool write=(value&H::IPC_PPC)!=0u;
       const bool cleared=flags.has_value()&&((*flags&H::IPC_PPC)==0u);
       const bool ctrl_clear=ctrl.has_value()&&((*ctrl&M::Y2)==0u);
       const bool irq_down=!ipc70_bus.external_irq_level();
       const bool queued=ipc70_bus.services().queued_replies()==1u&&
             !ipc70_bus.pending_native_ios_request();
       const bool guest=ipc70_ram.cpu!=nullptr&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u;
       const bool progressed=guest&&
             ipc70_ram.cpu->inst_count>v205_after_y2_inst;
       const uint32_t sc_addr=guest?ipc70_ram.cpu->gpr[13]-3176u:0u;
       const bool mapped=guest&&ipc70_ram.cpu->mmu.get_ptr(sc_addr)!=nullptr;
       const bool sc=mapped&&ipc70_ram.cpu->mmu.read8(sc_addr)==1u;
       std::cout<<"V205_Y2_FLAG write="<<write
                <<" cleared="<<cleared<<" ctrl="<<ctrl_clear
                <<" irq_down="<<irq_down<<" queued="<<queued
                <<" guest="<<guest<<" progressed="<<progressed
                <<" sc="<<sc<<std::endl;
       check(write&&cleared&&ctrl_clear&&irq_down&&queued&&
             guest&&progressed&&sc,
             "V205 original second Y2 Hollywood PPC_FLAG W1C failed");
       ++v205_flag_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
'''
NEXT_END='''      using V205Bus=undercover::wii::IosBus;
      using V205Mail=undercover::wii::IpcMailbox;
      using V205Irq=undercover::wii::HollywoodIrq;
      const auto v205_ctrl=nwii::runtime::ipc70_bus.read32(
            V205Bus::IPC+V205Mail::PPCCTRL);
      const auto v205_flag=nwii::runtime::ipc70_bus.read32(
            V205Bus::IPC+V205Irq::PPC_FLAG);
      const bool v205_clear=v205_ctrl.has_value()&&v205_flag.has_value()&&
            ((*v205_ctrl&V205Mail::Y2)==0u)&&
            ((*v205_flag&V205Irq::IPC_PPC)==0u)&&
            !nwii::runtime::ipc70_bus.external_irq_level();
      const bool v205_queued=nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
            !nwii::runtime::ipc70_bus.pending_native_ios_request();
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v201_leaf_seen==1u&&
            nwii::runtime::v202_next_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&v205_clear&&
            v205_queued&&!c.is_running,
            "V205 original second Y2 Hollywood IRQ flag not cleared by guest");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_ACK.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V205 original second Y2 PPCCTRL W1C checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v205_flag_seen=0u;
 static uint64_t v205_after_y2_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v205_flag_seen=0u;
     nwii::runtime::v205_after_y2_inst=0u;''')
    s=once(s,PREVIOUS_ACK,PREVIOUS_ACK.replace(STOP,CONTINUE,1))
    if s.count(MMIO_ANCHOR)!=1:
        raise ValueError("V205 original Broadway MMIO callback anchor changed")
    s=once(s,MMIO_ANCHOR,MMIO_ANCHOR+"\n"+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
