#!/usr/bin/env python3
"""V209: execute original second Y2 scheduler OSDI helper 0x805265AC.

V208 owner-original reached PC=0x805265AC/LR=0x80529448 following the
same scheduler path previously encountered in the first IOS reply. Guest
hardware Y2 and Hollywood interrupt cause are cleared; second IOS_Open
completion still queued and SC status 1. Execute the original PowerPC
OSDisableInterrupts routine and observe the next real function entry.
No guest register edits, manual interrupt or host IOS service pumping.
"""
import argparse
from pathlib import Path
from derive_v208_sc_y2_scheduler_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''    v208_target_pc=addr;v208_target_lr=ctx.lr;
    v208_final_sc=sc;v208_final_queue=queue;
    ++v208_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805265acu&&ctx.lr==0x80529448u&&
          y2&&irq_down&&queue&&open&&!replied&&guest&&
          caller&&coherent&&mapped&&sc==1u&&!ee,
          "V209 original second Y2 scheduler OSDI differs from V208");
    v208_target_pc=addr;v208_target_lr=ctx.lr;
    v208_final_sc=sc;v208_final_queue=queue;
    ++v208_next_seen;
    v209_start_inst=ctx.inst_count;
    return; // execute original Wii OSDisableInterrupts code
  }'''
OBSERVER='''  if(v196_live&&v208_next_seen==1u&&v209_next_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool y2=ctrl.has_value()&&((*ctrl&Mail::Y2)==0u);
    const bool irq_down=!ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u;
    const bool bounded=ipc70_bus.services().queued_replies()<=1u;
    const bool open=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool replied=v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply;
    const bool guest=ctx.inst_count>v209_start_inst&&
          ctx.gpr[13]==v147_first_r13&&!(addr&3u);
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const bool mapped=ctx.mmu.get_ptr(ctx.gpr[13]-3176u)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(ctx.gpr[13]-3176u):0u;
    const bool ee=(ctx.msr&Bus::MSR_EE)!=0u;
    const bool flagknown=flag.has_value();
    std::cout<<"V209_Y2_OSDI y2="<<y2<<" irq_down="<<irq_down
             <<" queue="<<queue<<" open="<<open<<" replied="<<replied
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" sc="<<sc<<" ee="<<ee
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(y2&&flagknown&&bounded&&(open||replied)&&
          guest&&caller&&coherent&&mapped,
          "V209 authentic second Y2 OSDI successor guest or IOS state differs");
    v209_target_pc=addr;v209_target_lr=ctx.lr;
    v209_final_sc=sc;v209_final_queue=queue;
    ++v209_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            nwii::runtime::v208_next_seen==1u&&
            nwii::runtime::v209_next_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v209_target_pc&&
            c.lr==nwii::runtime::v209_target_lr&&
            c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
            c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v209_final_sc&&
            (nwii::runtime::ipc70_bus.services().queued_replies()==1u)==
                nwii::runtime::v209_final_queue,
            "V209 original second Y2 OSDI did not reach next PowerPC call");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V209 V208 original OSDI boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v209_next_seen=0u;
 static uint64_t v209_start_inst=0u;
 static uint32_t v209_target_pc=0u,v209_target_lr=0u,v209_final_sc=0u;
 static bool v209_final_queue=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v209_next_seen=0u;
     nwii::runtime::v209_start_inst=0u;
     nwii::runtime::v209_target_pc=nwii::runtime::v209_target_lr=nwii::runtime::v209_final_sc=0u;
     nwii::runtime::v209_final_queue=false;''')
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
