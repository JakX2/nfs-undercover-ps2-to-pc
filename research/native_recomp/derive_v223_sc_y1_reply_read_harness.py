#!/usr/bin/env python3
"""V223 execute original third negative Y1 IpcReplyHandler to first IPC read.

The previous V222 owner-native checkpoint reached IpcReplyHandler at
0x805190C0 via IPCInterruptHandler. Let original PPC advance to its
first register-read helper without modifying guest state or IOS result -4.
"""
import argparse
from pathlib import Path
from derive_v222_sc_y1_ipc_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    v222_next_pc=addr;v222_next_lr=ctx.lr;
    ++v222_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v222_next_pc=addr;v222_next_lr=ctx.lr;
    ++v222_next_seen;
    v223_enter_inst=ctx.inst_count;
    return; // execute actual original IpcReplyHandler
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v222_next_seen==1u&&v223_read_seen==0u&&
     addr==0x8051905cu&&ctx.pc==addr){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
          ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool wire=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool caller=ctx.lr==0x805190e8u&&
          v222_next_pc==0x805190c0u&&
          v222_next_lr==0x80519354u;
    const bool guest=ctx.inst_count>v223_enter_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V223_NEG_REPLY_READ irq="<<irq<<" wire="<<wire
             <<" caller="<<caller<<" guest="<<guest
             <<" masked="<<masked<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&wire&&caller&&guest&&masked&&sc,
          "V223 authentic negative IOS reply handler first hardware read differs");
    ++v223_read_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            nwii::runtime::v216_vector_seen==1u&&
            nwii::runtime::v216_handler_seen==1u&&
            nwii::runtime::v217_dispatch_seen==1u&&
            nwii::runtime::v218_next_seen==1u&&
            nwii::runtime::v219_disable_seen==1u&&
            nwii::runtime::v220_ipc_seen==1u&&
            nwii::runtime::v221_leaf_seen==1u&&
            nwii::runtime::v222_next_seen==1u&&
            nwii::runtime::v223_read_seen==1u&&
            !c.is_running&&c.pc==0x8051905cu&&c.lr==0x805190e8u&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V223 original negative IOS IpcReplyHandler first read checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V223 original V222 authenticated reply handler changed")
    s=once(s,STATE,STATE+'''
 static unsigned v223_read_seen=0u;
 static uint64_t v223_enter_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v223_read_seen=0u;
     nwii::runtime::v223_enter_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
