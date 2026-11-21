#!/usr/bin/env python3
"""V219 resume original OSGetTime then reach OSDisableScheduler.

V218 owner verified the third negative Y1 IRQ dispatcher's call to the
original 0x8052A824 OSGetTime. Execute that genuine 24-byte guest helper
then return through the original dispatcher into OSDisableScheduler
0x805293F8. The -4 IOS_Open reply remains unchanged.
"""
import argparse
from pathlib import Path
from derive_v218_sc_y1_dispatch_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    v218_next_pc=addr;v218_next_lr=ctx.lr;
    ++v218_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v218_next_pc=addr;v218_next_lr=ctx.lr;
    ++v218_next_seen;
    v219_osgettime_inst=ctx.inst_count;
    return; // execute original OSGetTime and resume Wii IRQ dispatcher
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v218_next_seen==1u&&v219_disable_seen==0u&&
     addr==0x805293f8u&&ctx.pc==addr){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool irq=ctl.has_value()&&flag.has_value()&&
          ((*ctl&Mail::Y1)!=0u)&&((*ctl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          ctx.inst_count>v219_osgettime_inst;
    const bool caller=ctx.lr==0x80526c98u;
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V219_NEG_OSDI guest="<<guest
             <<" caller="<<caller<<" masked="<<masked
             <<" irq="<<irq<<" reply="<<reply<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&masked&&irq&&reply&&sc,
          "V219 original negative Y1 dispatcher did not reach OSDisableScheduler");
    ++v219_disable_seen;
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
            !c.is_running&&c.pc==0x805293f8u&&c.lr==0x80526c98u&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V219 original negative Y1 OSGetTime scheduler successor failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V219 authenticated V218 OSGetTime boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v219_disable_seen=0u;
 static uint64_t v219_osgettime_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v219_disable_seen=0u;
     nwii::runtime::v219_osgettime_inst=0u;''')
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
