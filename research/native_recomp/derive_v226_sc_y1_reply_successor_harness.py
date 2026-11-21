#!/usr/bin/env python3
"""V226 original third Y1 negative IOS reply successor after second IPC read.

Extends V224's verified original native PowerPC IpcReplyHandler. Run the
unaltered second IPCReadReg helper and stop on the first later genuine
translated text function entry. Observe IRQ Y1, actual -4 response,
scheduler/guest ABI and SC without assuming the next target address.
"""
import argparse
from pathlib import Path
from derive_v224_sc_y1_reply_second_read_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    ++v224_second_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v224_second_seen;
    v226_start_inst=ctx.inst_count;
    return; // original guest IpcReplyHandler executes beyond second register read
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v215_vector_seen==1u&&v224_second_seen==1u&&
     v226_successor_seen==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.inst_count>v226_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool signal=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
          ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool negative=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          !(ctx.msr&B::MSR_EE)&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u)&&!(addr&3u);
    const uint32_t sc_address=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(sc_address)!=nullptr&&
          ctx.mmu.read8(sc_address)==1u;
    std::cout<<"V226_NEG_SUCCESSOR signal="<<signal
             <<" negative="<<negative<<" guest="<<guest
             <<" caller="<<caller<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(signal&&negative&&guest&&caller&&sc,
          "V226 original third negative Y1 reply successor lost native IRQ state");
    v226_next_pc=addr;v226_next_lr=ctx.lr;
    ++v226_successor_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v222_next_seen==1u&&
            nwii::runtime::v223_read_seen==1u&&
            nwii::runtime::v224_second_seen==1u&&
            nwii::runtime::v226_successor_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v226_next_pc&&
            c.lr==nwii::runtime::v226_next_lr&&
            c.pc>=0x80400000u&&c.pc<0x80600000u&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.valid(
                  nwii::runtime::v183_second_phys,64u)&&
            nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V226 original negative IOS Y1 successor checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V226 inherited original V224 IPC read boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v226_successor_seen=0u;
 static uint64_t v226_start_inst=0u;
 static uint32_t v226_next_pc=0u,v226_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v226_successor_seen=0u;
     nwii::runtime::v226_start_inst=0u;
     nwii::runtime::v226_next_pc=nwii::runtime::v226_next_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
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
