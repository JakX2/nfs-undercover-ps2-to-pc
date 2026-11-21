#!/usr/bin/env python3
"""V221: run the genuine third-Y1 negative IPC handler to its first helper.

V220 verified the original registered IPCInterruptHandler at 0x80519318
with IRQ slot 27 and the saved CPU frame. Execute its unchanged PowerPC
body until its first native hardware helper. No guest state or successful
IOS response is injected; the original IOS_Open -4 result stays intact.
"""
import argparse
from pathlib import Path
from derive_v220_sc_y1_ipc_handler_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    ++v220_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v220_ipc_seen;
    v221_ipc_inst=ctx.inst_count;
    return; // execute original registered PowerPC IPC handler body
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v220_ipc_seen==1u&&v221_leaf_seen==0u&&
     (addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool signal=ctl.has_value()&&flag.has_value()&&
          ((*ctl&M::Y1)!=0u)&&((*ctl&M::Y2)==0u)&&
          ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool reply=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid&&
          ipc70_bus.services().queued_replies()==0u;
    const bool call=ctx.pc==addr&&ctx.lr>=0x80519318u&&
          ctx.lr<0x805194c4u&&!(ctx.lr&3u);
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const bool stepped=ctx.inst_count>v221_ipc_inst&&
          ctx.gpr[13]==v147_first_r13;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V221_NEG_LEAF call="<<call<<" masked="<<masked
             <<" signal="<<signal<<" reply="<<reply
             <<" stepped="<<stepped<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(call&&masked&&signal&&reply&&stepped&&sc,
          "V221 original third Y1 IPC handler failed to enter native helper");
    v221_leaf_pc=addr;v221_leaf_lr=ctx.lr;
    ++v221_leaf_seen;
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
            !c.is_running&&c.pc==nwii::runtime::v221_leaf_pc&&
            c.lr==nwii::runtime::v221_leaf_lr&&
            (c.pc==0x8051905cu||c.pc==0x8051906cu||
             c.pc==0x8051b060u)&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V221 third negative Y1 IPC first hardware helper checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V221 inherited V220 IPC handler entry changed")
    s=once(s,STATE,STATE+'''
 static unsigned v221_leaf_seen=0u;
 static uint64_t v221_ipc_inst=0u;
 static uint32_t v221_leaf_pc=0u,v221_leaf_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v221_leaf_seen=0u;
     nwii::runtime::v221_ipc_inst=0u;
     nwii::runtime::v221_leaf_pc=nwii::runtime::v221_leaf_lr=0u;''')
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
