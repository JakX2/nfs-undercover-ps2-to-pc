#!/usr/bin/env python3
"""V222 continue original third negative IOS Y1 hardware read to next callee.

V221 reached actual first Wii PPC read helper PC 0x8051905C from
IPCInterruptHandler. Execute its original body and observe the next
genuine callback-owned translated function call. The second IOS_Open
error remains -4 and SC stays at its observed initialization state.
"""
import argparse
from pathlib import Path
from derive_v221_sc_y1_ipc_leaf_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    v221_leaf_pc=addr;v221_leaf_lr=ctx.lr;
    ++v221_leaf_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v221_leaf_pc=addr;v221_leaf_lr=ctx.lr;
    ++v221_leaf_seen;
    v222_first_inst=ctx.inst_count;
    return; // execute original PowerPC read helper, without host intervention
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v221_leaf_seen==1u&&v222_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&ctx.pc==addr&&
     ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctl.has_value()&&flag.has_value()&&
          ((*ctl&Mail::Y1)!=0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.inst_count>v222_first_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=(ctx.lr&3u)==0u&&(addr&3u)==0u;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V222_NEG_NEXT guest="<<guest<<" caller="<<caller
             <<" reply="<<reply<<" masked="<<masked
             <<" coherent="<<coherent<<" irq="<<irq
             <<" sc="<<sc<<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&reply&&masked&&coherent&&sc,
          "V222 third negative IOS Y1 IPC hardware read lost guest or reply state");
    v222_next_pc=addr;v222_next_lr=ctx.lr;
    ++v222_next_seen;
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
            !c.is_running&&c.pc==nwii::runtime::v222_next_pc&&
            c.lr==nwii::runtime::v222_next_lr&&
            c.pc>=0x80400000u&&c.pc<0x80600000u&&
            c.lr>=0x80519318u&&c.lr<0x805194c4u&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V222 third original negative IOS Y1 IPC next callee checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V222 inherited V221 authenticated IPC read boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v222_next_seen=0u;
 static uint64_t v222_first_inst=0u;
 static uint32_t v222_next_pc=0u,v222_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v222_next_seen=0u;
     nwii::runtime::v222_first_inst=0u;
     nwii::runtime::v222_next_pc=nwii::runtime::v222_next_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
