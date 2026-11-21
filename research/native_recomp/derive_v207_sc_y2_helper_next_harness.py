#!/usr/bin/env python3
"""V207: execute authentic second Y2 IPC post-ACK helper 0x8051B060.

V206 owner-original verified next PPC entry 0x8051B060, LR=0x805193A4
after *both* authentic guest W1C writes, with second IOS_Open queued and
SC status 1. Resume that exact original function and observe its next
real native callee and whether the second IOS response remains queued or
has been published. Never pump the IOS queue, alter the game context, or
synthesize MMIO activity from the test hook.
"""
import argparse
from pathlib import Path
from derive_v206_sc_y2_post_flag_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v206_post_pc=addr;v206_post_lr=ctx.lr;
    ++v206_post_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051b060u&&ctx.lr==0x805193a4u&&
          ack&&irq_down&&queued&&open&&guest&&masked&&coherent&&sc,
          "V207 expected V206 owner-verified post-flag IPC helper entry");
    v206_post_pc=addr;v206_post_lr=ctx.lr;
    ++v206_post_seen;
    v207_start_inst=ctx.inst_count;
    return; // execute original PowerPC helper at 0x8051B060
  }'''
OBSERVER='''  if(v196_live&&v206_post_seen==1u&&v207_next_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool ack=ctrl.has_value()&&((*ctrl&Mail::Y2)==0u);
    const bool irq_down=!ipc70_bus.external_irq_level();
    const bool queued=ipc70_bus.services().queued_replies()==1u;
    const bool bounded=ipc70_bus.services().queued_replies()<=1u;
    const bool open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool replied=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply;
    const bool guest=ctx.inst_count>v207_start_inst&&
          ctx.gpr[13]==v147_first_r13&&!(addr&3u);
    const bool caller=ctx.lr>=0x80400000u&&
          ctx.lr<0x80600000u&&!(ctx.lr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const bool irqflag=flag.has_value()&&
          (((*flag&Irq::IPC_PPC)!=0u)==ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    std::cout<<"V207_Y2_NEXT ack="<<ack<<" irq_down="<<irq_down
             <<" queued="<<queued<<" open="<<open<<" replied="<<replied
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" irqflag="<<irqflag
             <<" mapped="<<mapped<<" sc="<<sc<<" ee="<<ee
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(ack&&bounded&&(open||replied)&&guest&&caller&&coherent&&
          irqflag&&mapped,
          "V207 original second Y2 post-ACK helper successor state differs");
    v207_next_pc=addr;v207_next_lr=ctx.lr;
    v207_sc=sc;v207_queue=queued;v207_reply=replied;
    ++v207_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v207_next_pc&&
            c.lr==nwii::runtime::v207_next_lr&&
            c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
            c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v207_sc&&
            (nwii::runtime::ipc70_bus.services().queued_replies()==1u)==
                nwii::runtime::v207_queue,
            "V207 second Y2 post-ACK original helper successor not reached");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V207 owner-verified V206 PPC successor changed")
    s=once(s,STATE,STATE+'''
 static unsigned v207_next_seen=0u;
 static uint64_t v207_start_inst=0u;
 static uint32_t v207_next_pc=0u,v207_next_lr=0u,v207_sc=0u;
 static bool v207_queue=false,v207_reply=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v207_next_seen=0u;
     nwii::runtime::v207_start_inst=0u;
     nwii::runtime::v207_next_pc=nwii::runtime::v207_next_lr=nwii::runtime::v207_sc=0u;
     nwii::runtime::v207_queue=nwii::runtime::v207_reply=false;''')
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
