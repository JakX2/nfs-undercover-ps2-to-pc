#!/usr/bin/env python3
"""V224 original third negative-Y1 IpcReplyHandler's second PPC register read.

V223 owner-original execution reached the first IPCReadReg at
0x8051905C / LR=0x805190E8. Execute that helper and native handler
into its second call of the same read helper with LR=0x805190FC.
Preserve the actual -4 IOS reply, IRQ and SC state without forcing code.
"""
import argparse
from pathlib import Path
from derive_v223_sc_y1_reply_read_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
STOP='''    ++v223_read_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v223_read_seen;
    v224_first_inst=ctx.inst_count;
    return; // original hardware read helper and handler resume
  }'''
# V80's original first reply MMIO witness must not require ARMMSG to
# refer to the *first* request after the third negative-Y1 IRQ has
# legitimately published the second request. Preserve its early proof.
V80_ARM_FIRST='''     if(reply79_irq==1u&&irq76_ipc&&
        (addr==undercover::wii::IosBus::IPC+undercover::wii::IpcMailbox::ARMMSG||'''
V80_ARM_SCOPED='''     if(reply79_irq==1u&&irq76_ipc&&v215_vector_seen==0u&&
        (addr==undercover::wii::IosBus::IPC+undercover::wii::IpcMailbox::ARMMSG||'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v223_read_seen==1u&&v224_second_seen==0u&&
     addr==0x8051905cu&&ctx.pc==addr&&
     ctx.lr==0x805190fcu){
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
    const bool guest=ctx.inst_count>v224_first_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
          !ipc70_bus.external_exception_pending(ctx.msr);
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool sc=ctx.mmu.get_ptr(scaddr)!=nullptr&&
          ctx.mmu.read8(scaddr)==1u;
    std::cout<<"V224_NEG_SECOND_READ irq="<<irq<<" wire="<<wire
             <<" guest="<<guest<<" masked="<<masked<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(irq&&wire&&guest&&masked&&sc,
          "V224 third original IpcReplyHandler second native IPC read differs");
    ++v224_second_seen;
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
            nwii::runtime::v224_second_seen==1u&&
            !c.is_running&&c.pc==0x8051905cu&&c.lr==0x805190fcu&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V224 original negative Y1 IpcReplyHandler second IPC read checkpoint failed");'''
def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V224 V223 authentic first IPC read anchor changed")
    s=once(s,STATE,STATE+'''
 static unsigned v224_second_seen=0u;
 static uint64_t v224_first_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v224_second_seen=0u;
     nwii::runtime::v224_first_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,V80_ARM_FIRST,V80_ARM_SCOPED)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
