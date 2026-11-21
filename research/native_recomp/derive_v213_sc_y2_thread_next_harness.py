#!/usr/bin/env python3
"""V213 original Wii post-second-IRQ RFI guest thread next call.

V212 owner-original 16/16 proved an exact native OSLoadContext/rfi of
the selected original game thread (PC/MSR/GPRs/LR/CTR/XER). Continue
that restored guest execution until the next native PowerPC function
entry, without touching the IOS queue, guest registers or game memory.
"""
import argparse
from pathlib import Path
from derive_v212_sc_y2_rfi_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    ++v212_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CONTINUE='''    ++v212_rfi_seen;
    v213_start_inst=ctx.inst_count;
    // Preserve the game-restored PC, MSR, GPRs and scheduler state.
    // Continue unchanged original instructions after guest RFI.
  }
'''
OBSERVER='''  if(v196_live&&v212_rfi_seen==1u&&v213_call_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq_down=!ipc70_bus.external_irq_level()&&
          ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&(Mail::Y1|Mail::Y2))==0u)&&
          ((*flag&Irq::IPC_PPC)==0u);
    const bool queued=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool guest=ctx.inst_count>v213_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u)&&!(addr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    std::cout<<"V213_Y2_THREAD guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" irq_down="<<irq_down<<" queued="<<queued
             <<" open="<<open<<" sc="<<sc<<" ee="<<ee
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped&&irq_down&&queued&&open,
          "V213 original guest after second IRQ RFI state differs");
    v213_next_pc=addr;v213_next_lr=ctx.lr;v213_final_sc=sc;
    ++v213_call_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v210_next_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v213_call_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v213_next_pc&&
            c.lr==nwii::runtime::v213_next_lr&&
            c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
            c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v213_final_sc&&
            nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
            !nwii::runtime::ipc70_bus.external_irq_level(),
            "V213 second IRQ restored thread did not call original guest code");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V213 inherited original V212 RFI boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v213_call_seen=0u;
 static uint64_t v213_start_inst=0u;
 static uint32_t v213_next_pc=0u,v213_next_lr=0u,v213_final_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v213_call_seen=0u;
     nwii::runtime::v213_start_inst=0u;
     nwii::runtime::v213_next_pc=nwii::runtime::v213_next_lr=
         nwii::runtime::v213_final_sc=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))
