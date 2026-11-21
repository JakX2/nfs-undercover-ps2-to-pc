#!/usr/bin/env python3
"""V204 execute original second-Y2 PPCCTRL Y2 W1C, not a host ACK.

V203 owner-original reached the second registered IPC handler's control-write
helper PC=0x8051906C, LR=0x80519380. Permit that original translated
PowerPC helper to execute, then observe the actual guest MMIO write after
native bus W1C semantics. Y2 must clear while Hollywood PPC_FLAG and the
queued second IOS completion remain pending for the later IRQ-flag handler.
"""
import argparse
from pathlib import Path
from derive_v203_sc_y2_distinct_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v172_sc_y1_ack_harness import MMIO_ANCHOR

STOP='''    ++v203_distinct_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051906cu&&ctx.lr==0x80519380u,
          "V204 original second Y2 PPCCTRL control writer entry differs");
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    check(ctrl.has_value()&&((*ctrl&M::Y2)!=0u)&&
          flags.has_value()&&((*flags&H::IPC_PPC)!=0u)&&
          ipc70_bus.services().queued_replies()==1u,
          "V204 original second Y2 PPCCTRL pre-W1C state differs");
    ++v203_distinct_seen;
    v204_helper_inst=ctx.inst_count;
    v204_mmio_begin=mmio_writes.size();
    return; // execute original PPC MMIO writer with no host-synthesized write
  }'''
ACK='''     // Observe only the ORIGINAL guest PPCCTRL store after the native
     // bus applied Wii write-one-to-clear semantics.
     if(v196_live&&v203_distinct_seen==1u&&v204_ack_seen==0u&&
        (addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)){
       using H=undercover::wii::HollywoodIrq;
       const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
       const bool write=(value&M::Y2)!=0u;
       const bool w1c=ctrl.has_value()&&((*ctrl&M::Y2)==0u);
       const bool flag=flags.has_value()&&
             ((*flags&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
       const bool queued=ipc70_bus.services().queued_replies()==1u&&
             !ipc70_bus.pending_native_ios_request();
       const bool guest=ipc70_ram.cpu!=nullptr&&
             ipc70_ram.cpu->lr==0x80519380u&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u;
       const bool progressed=guest&&
             ipc70_ram.cpu->inst_count>v204_helper_inst&&
             mmio_writes.size()>v204_mmio_begin;
       const uint32_t sc_addr=guest?ipc70_ram.cpu->gpr[13]-3176u:0u;
       const bool mapped=guest&&ipc70_ram.cpu->mmu.get_ptr(sc_addr)!=nullptr;
       const bool sc=mapped&&ipc70_ram.cpu->mmu.read8(sc_addr)==1u;
       std::cout<<"V204_Y2_ACK write="<<write<<" w1c="<<w1c
                <<" flag="<<flag<<" queued="<<queued
                <<" guest="<<guest<<" progressed="<<progressed
                <<" sc="<<sc<<std::endl;
       check(write&&w1c&&flag&&queued&&guest&&progressed&&sc,
             "V204 original second Y2 PPCCTRL writer failed real W1C");
       ++v204_ack_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v201_leaf_seen==1u&&
            nwii::runtime::v202_next_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            !c.is_running&&c.lr==0x80519380u,
            "V204 original second Y2 PPCCTRL W1C was not performed by guest");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V204 original second Y2 PPCCTRL helper checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v204_ack_seen=0u;
 static uint64_t v204_helper_inst=0u;
 static size_t v204_mmio_begin=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v204_ack_seen=0u;
     nwii::runtime::v204_helper_inst=0u;
     nwii::runtime::v204_mmio_begin=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    if s.count(MMIO_ANCHOR)!=1:
        raise ValueError("V204 original Broadway MMIO callback anchor changed")
    s=once(s,MMIO_ANCHOR,MMIO_ANCHOR+"\n"+ACK.rstrip("\n"))
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
