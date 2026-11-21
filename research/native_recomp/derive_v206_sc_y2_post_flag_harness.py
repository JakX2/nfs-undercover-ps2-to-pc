#!/usr/bin/env python3
"""V206: resume original second IOS Y2 handler after both guest W1C ACKs.

V205 owner-original verified Broadway PPCCTRL.Y2 and Hollywood PPC_FLAG
were cleared by original translated PowerPC stores, IRQ down and exactly
one IOS completion still queued. Continue guest execution through the
next *actual* function entry. Observe coherent mailbox, IOS and SC state.
No service pump, guest context patch, or synthesized acknowledgement.
"""
import argparse
from pathlib import Path
from derive_v205_sc_y2_flag_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''       ++v205_flag_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }'''
CONTINUE='''       ++v205_flag_seen;
       v206_after_flag_inst=ipc70_ram.cpu->inst_count;
       // Return to the untouched original PowerPC IRQ handler.
     }'''
OBSERVER='''  if(v196_live&&v205_flag_seen==1u&&v206_post_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool ack=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y2)==0u)&&((*flag&Irq::IPC_PPC)==0u);
    const bool irq_down=!ipc70_bus.external_irq_level();
    const bool queued=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (!masked&&ipc70_bus.external_irq_level());
    const bool guest=ctx.inst_count>v206_after_flag_inst&&
          ctx.gpr[13]==v147_first_r13&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u)&&!(addr&3u);
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(sc_addr)==1u;
    std::cout<<"V206_Y2_POST ack="<<ack
             <<" irq_down="<<irq_down<<" queued="<<queued
             <<" open="<<open<<" guest="<<guest
             <<" masked="<<masked<<" coherent="<<coherent
             <<" sc="<<sc<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(ack&&irq_down&&queued&&open&&guest&&masked&&coherent&&sc,
          "V206 original second Y2 IRQ post-flag guest continuation differs");
    v206_post_pc=addr;v206_post_lr=ctx.lr;
    ++v206_post_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      using V206Bus=undercover::wii::IosBus;
      using V206Mail=undercover::wii::IpcMailbox;
      using V206Irq=undercover::wii::HollywoodIrq;
      const auto v206_ctrl=nwii::runtime::ipc70_bus.read32(
            V206Bus::IPC+V206Mail::PPCCTRL);
      const auto v206_flag=nwii::runtime::ipc70_bus.read32(
            V206Bus::IPC+V206Irq::PPC_FLAG);
      const bool v206_clean=v206_ctrl.has_value()&&v206_flag.has_value()&&
            ((*v206_ctrl&V206Mail::Y2)==0u)&&
            ((*v206_flag&V206Irq::IPC_PPC)==0u)&&
            !nwii::runtime::ipc70_bus.external_irq_level();
      const bool v206_queued=nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
            !nwii::runtime::ipc70_bus.pending_native_ios_request();
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            v206_clean&&v206_queued&&
            !c.is_running&&c.pc==nwii::runtime::v206_post_pc&&
            c.lr==nwii::runtime::v206_post_lr,
            "V206 second IOS Y2 handler did not reach next original PPC call");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V206 original V205 Hollywood W1C boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v206_post_seen=0u;
 static uint64_t v206_after_flag_inst=0u;
 static uint32_t v206_post_pc=0u,v206_post_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v206_post_seen=0u;
     nwii::runtime::v206_after_flag_inst=0u;
     nwii::runtime::v206_post_pc=nwii::runtime::v206_post_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
