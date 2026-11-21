#!/usr/bin/env python3
"""V215: deliver actual negative IOS_Open Y1 to authentic Wii external vector.

V212 owner-original validated RFI restoring the real game-selected thread,
MSR.EE=1. At this authenticated host yield, publish the queued second
IOS response through native IOS, preserving its real -4 Invalid code;
use tested Broadway hardware exception entry to the original 0x80000500
handler, never synthesize a successful descriptor or guest branch.
"""
import argparse
from pathlib import Path
from derive_v212_sc_y2_rfi_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    ++v212_rfi_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CONTINUE='''    ++v212_rfi_seen;
    using V215Bus=undercover::wii::IosBus;
    using V215Mail=undercover::wii::IpcMailbox;
    using V215Irq=undercover::wii::HollywoodIrq;
    using V215IOS=undercover::wii::StmIos;
    const uint32_t original_pc=ctx.pc,original_msr=ctx.msr;
    const uint32_t original_lr=ctx.lr,original_ctr=ctx.ctr,original_xer=ctx.xer;
    const auto original_gprs=ctx.gpr;
    const uint64_t original_inst=ctx.inst_count;
    const bool eligible=(original_msr&V215Bus::MSR_EE)!=0u&&
          !ctx.dispatch_saved_ctx&&v212_selected_thread;
    const bool pre=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request()&&
          !ipc70_bus.external_irq_level()&&
          ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==V215IOS::Open;
    check(eligible&&pre,
          "V215 restored original second IRQ thread not ready for native IOS publication");
    // Genuine host Starlet completion at the verified game-chosen RFI
    // boundary. Do not invent or force a successful file handle.
    undercover::wii::IosYieldScheduler v215_scheduler(ipc70_bus);
    const auto result=v215_scheduler.service_one(ctx.msr);
    const auto ctrl=ipc70_bus.read32(V215Bus::IPC+V215Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(V215Bus::IPC+V215Irq::PPC_FLAG);
    const bool pump=result.progress==V215IOS::Pump::Replied&&
          result.serviced_steps==1u;
    const bool published=ipc70_ram.read32(v183_second_phys)==V215IOS::Reply&&
          ipc70_ram.read32(v183_second_phys+8u)==V215IOS::Open&&
          int32_t(ipc70_ram.read32(v183_second_phys+4u))==V215IOS::Invalid;
    const bool signaled=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&V215Mail::Y1)!=0u)&&
          ((*ctrl&V215Mail::Y2)==0u)&&
          ((*flag&V215Irq::IPC_PPC)!=0u)&&
          ipc70_bus.external_irq_level()&&
          ipc70_bus.external_exception_pending(ctx.msr);
    const bool empty=ipc70_bus.services().queued_replies()==0u;
    const bool cpu=ctx.pc==original_pc&&ctx.msr==original_msr&&
          ctx.lr==original_lr&&ctx.ctr==original_ctr&&
          ctx.xer==original_xer&&ctx.inst_count==original_inst&&
          ctx.gpr==original_gprs;
    check(pump&&published&&signaled&&empty&&cpu,
          "V215 second IOS negative reply not published before original Y1 vector");
    const auto vector_result=undercover::wii::enter_external_irq(
          ctx,ipc70_bus,irq74_vector,true);
    const bool entered=vector_result==undercover::wii::ExternalEntry::Entered&&
          ctx.pc==undercover::wii::ExternalVector;
    const bool saved=ctx.srr0==original_pc&&
          ctx.srr1==(original_msr&undercover::wii::ExternalSrr1Mask)&&
          ctx.msr==(original_msr&~undercover::wii::ExternalMsrClear);
    const bool registers=ctx.gpr==original_gprs&&
          ctx.lr==original_lr&&ctx.ctr==original_ctr&&ctx.xer==original_xer;
    const bool masked=!ipc70_bus.external_exception_pending(ctx.msr)&&
          ipc70_bus.external_irq_level();
    const bool sc_ready=ctx.mmu.get_ptr(ctx.gpr[13]-3176u)!=nullptr&&
          ctx.mmu.read8(ctx.gpr[13]-3176u)==1u;
    std::cout<<"V215_Y1_VECTOR pump="<<pump<<" published="<<published
             <<" signal="<<signaled<<" empty="<<empty
             <<" cpu="<<cpu<<" entered="<<entered<<" saved="<<saved
             <<" regs="<<registers<<" masked="<<masked
             <<" sc="<<sc_ready<<std::endl;
    check(entered&&saved&&registers&&masked&&sc_ready,
          "V215 real second negative Y1 did not enter original Wii vector");
    v215_saved_pc=original_pc;v215_saved_msr=original_msr;
    v215_saved_lr=original_lr;v215_saved_ctr=original_ctr;
    v215_saved_xer=original_xer;
    v215_original_gprs=original_gprs;
    ++v215_vector_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v211_next_seen==1u&&
            nwii::runtime::v212_rfi_seen==1u&&
            nwii::runtime::v215_vector_seen==1u&&
            !c.is_running&&
            c.pc==undercover::wii::ExternalVector&&
            c.srr0==nwii::runtime::v215_saved_pc&&
            c.srr1==(nwii::runtime::v215_saved_msr&
                      undercover::wii::ExternalSrr1Mask)&&
            c.msr==(nwii::runtime::v215_saved_msr&
                    ~undercover::wii::ExternalMsrClear)&&
            c.gpr==nwii::runtime::v215_original_gprs&&
            c.lr==nwii::runtime::v215_saved_lr&&
            c.ctr==nwii::runtime::v215_saved_ctr&&
            c.xer==nwii::runtime::v215_saved_xer&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_ram.read32(nwii::runtime::v183_second_phys)==
                  undercover::wii::StmIos::Reply&&
            int32_t(nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v183_second_phys+4u))==
                  undercover::wii::StmIos::Invalid,
            "V215 real negative reply Y1 vector entry did not preserve Wii state");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V215 inherited owner-verified V212 RFI boundary changed")
    s=once(s,STATE,STATE+'''
 static unsigned v215_vector_seen=0u;
 static uint32_t v215_saved_pc=0u,v215_saved_msr=0u;
 static uint32_t v215_saved_lr=0u,v215_saved_ctr=0u,v215_saved_xer=0u;
 static std::array<uint32_t,32> v215_original_gprs{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v215_vector_seen=0u;
     nwii::runtime::v215_saved_pc=nwii::runtime::v215_saved_msr=0u;
     nwii::runtime::v215_saved_lr=nwii::runtime::v215_saved_ctr=
         nwii::runtime::v215_saved_xer=0u;
     nwii::runtime::v215_original_gprs.fill(0u);''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))
