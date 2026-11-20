#!/usr/bin/env python3
"""V153 deliver queued SC SYSCONF IOS reply at original post-IRQ yield boundary.

V152 proved the authentic SC dispatcher reaches 0x80529434 from 0x80526CB0
after PPCCTRL Y2 and Hollywood PPC_FLAG W1C. Unlike the older V77 STM request,
this SC request is a read-only SYSCONF file open with a returned file descriptor.

At this precise guest function boundary, authorize *one* deterministic native
IosYieldScheduler step and inspect its real reply wire, mailbox and interrupt.
All original PPC instructions and previously queued IOS request bytes remain
unchanged. This stops before executing 0x80529434, restoring the interrupted
guest context, servicing the second IRQ or updating the SC SDA status byte.
"""
import argparse
from pathlib import Path
from derive_v152_sc_post_helper_harness import (
    derive as previous, STATE, RESET, OBSERVER, NEXT_TRIAL as TRIAL,
)

NEXT_OBSERVER=OBSERVER.replace(
    '''     ++v152_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }''',
    '''     using V153Bus=undercover::wii::IosBus;
     using V153Mail=undercover::wii::IpcMailbox;
     using V153Irq=undercover::wii::HollywoodIrq;
     using V153Ios=undercover::wii::StmIos;
     const bool route=addr==POST_OWNER&&ctx.lr==0x80526cb0u;
     const auto req=ipc70_bus.read32(V153Bus::IPC+V153Mail::PPCMSG);
     const bool request=req.has_value()&&*req!=0u&&
           !(*req&31u)&&ipc70_ram.valid(*req,64u)&&
           ipc70_ram.read32(*req)==V153Ios::Open;
     const auto ctrl_before=ipc70_bus.read32(V153Bus::IPC+V153Mail::PPCCTRL);
     const auto irq_before=ipc70_bus.read32(V153Bus::IPC+V153Irq::PPC_FLAG);
     const bool cleared=ctrl_before.has_value()&&irq_before.has_value()&&
           ((*ctrl_before&V153Mail::Y2)==0u)&&
           ((*irq_before&V153Irq::IPC_PPC)==0u)&&
           !ipc70_bus.external_irq_level();
     const bool v153_queued=ipc70_bus.services().queued_replies()==1u;
     check(route&&request&&cleared&&v153_queued&&!(ctx.msr&V153Bus::MSR_EE),
           "V153 SC reply scheduling boundary or outstanding native request differs");
     undercover::wii::IosYieldScheduler scheduler(ipc70_bus);
     const auto state=scheduler.service_one(ctx.msr);
     const auto ctrl_after=ipc70_bus.read32(V153Bus::IPC+V153Mail::PPCCTRL);
     const auto irq_after=ipc70_bus.read32(V153Bus::IPC+V153Irq::PPC_FLAG);
     const auto arm=ipc70_bus.read32(V153Bus::IPC+V153Mail::ARMMSG);
     const bool progressed=state.progress==V153Ios::Pump::Replied&&
           state.serviced_steps==1u&&state.broadway_irq_level&&
           !state.guest_exception_ready;
     const bool reply=ipc70_ram.read32(*req)==V153Ios::Reply&&
           ipc70_ram.read32(*req+8u)==V153Ios::Open&&
           arm.has_value()&&*arm==*req;
     const auto result=int32_t(ipc70_ram.read32(*req+4u));
     const bool fd=result>=0&&
           uint32_t(result)<V153Ios::DescriptorCount&&
           ipc70_bus.services().is_open(unsigned(result),V153Ios::Device::File);
     const bool signal=ctrl_after.has_value()&&irq_after.has_value()&&
           ((*ctrl_after&V153Mail::Y1)!=0u)&&
           ((*ctrl_after&V153Mail::Y2)==0u)&&
           ((*irq_after&V153Irq::IPC_PPC)!=0u)&&
           ipc70_bus.external_irq_level()&&
           ipc70_bus.services().queued_replies()==0u;
     std::cout<<"V153_SC_REPLY route="<<route<<" cleared="<<cleared
              <<" service="<<progressed<<" wire="<<reply
              <<" fd="<<fd<<" signal="<<signal<<std::endl;
     check(progressed&&reply&&fd&&signal,
           "V153 native IOS scheduler did not publish authentic SC file-open reply");
     v153_phys=*req;v153_fd=uint32_t(result);
     ++v152_next_seen;++v153_bridge_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }''',
)

NEXT_TRIAL='''       using V153Bus=undercover::wii::IosBus;
       using V153Mail=undercover::wii::IpcMailbox;
       using V153Irq=undercover::wii::HollywoodIrq;
       using V153Ios=undercover::wii::StmIos;
       const auto v153_ctrl=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Mail::PPCCTRL);
       const auto v153_arm=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Mail::ARMMSG);
       const auto v153_flags=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Irq::PPC_FLAG);
       const auto v153_phys=nwii::runtime::v153_phys;
       const auto v153_fd=nwii::runtime::v153_fd;
       const bool v153_bridge=nwii::runtime::v153_bridge_seen==1u&&
             nwii::runtime::v152_next_seen==1u&&
             c.pc==POST_OWNER&&c.lr==0x80526cb0u&&!c.is_running;
       const bool v153_wire=nwii::runtime::ipc70_ram.valid(v153_phys,64u)&&
             nwii::runtime::ipc70_ram.read32(v153_phys)==V153Ios::Reply&&
             nwii::runtime::ipc70_ram.read32(v153_phys+4u)==v153_fd&&
             nwii::runtime::ipc70_ram.read32(v153_phys+8u)==V153Ios::Open&&
             v153_arm.has_value()&&*v153_arm==v153_phys&&
             nwii::runtime::ipc70_bus.services().is_open(
                   v153_fd,V153Ios::Device::File);
       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             ((*v153_ctrl&V153Mail::Y1)!=0u)&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);
       const bool v153_drained=nwii::runtime::ipc70_bus.services().queued_replies()==0u;
       const bool v153_irq=nwii::runtime::ipc70_bus.external_irq_level()&&
             !nwii::runtime::ipc70_bus.external_exception_pending(c.msr)&&
             (c.msr&V153Bus::MSR_EE)==0u;
       std::cout<<"V153_SC_REPLY_STATE bridge="<<v153_bridge
                <<" wire="<<v153_wire<<" mail="<<v153_mail
                <<" drained="<<v153_drained<<" irq="<<v153_irq<<std::endl;
       check(v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq&&
             nwii::runtime::v149_ack_seen==1u&&
             nwii::runtime::v150_flag_seen==1u&&
             nwii::runtime::v151_next_seen==1u,
             "V153 original SC IRQ did not deliver queued SYSCONF file-open reply");'''

def once(source: str, old: str, new: str) -> str:
    count=source.count(old)
    if count!=1:
        raise ValueError(f"V153 original-free source anchor count differs: {count}")
    return source.replace(old,new,1)

def derive(source: str) -> str:
    if NEXT_OBSERVER==OBSERVER or "service_one(ctx.msr)" not in NEXT_OBSERVER:
        raise ValueError("V153 SC service boundary derivation failed closed")
    s=previous(source)
    s=once(s,STATE,STATE+'''
 static unsigned v153_bridge_seen=0;
 static uint32_t v153_phys=0,v153_fd=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v153_bridge_seen=0u;
     nwii::runtime::v153_phys=nwii::runtime::v153_fd=0u;''')
    s=once(s,OBSERVER,NEXT_OBSERVER)
    s=once(s,TRIAL,TRIAL.replace(
        '''             nwii::runtime::v152_next_seen==1u&&!c.is_running,''',
        '''             nwii::runtime::v152_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,''',1).replace(
        "V152 original post-IRQ helper did not execute until next native guest call",
        "V153 original SC IRQ did not reach native IOS service boundary",1)
        +"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
