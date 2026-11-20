#!/usr/bin/env python3
"""V157 execute original SC rescheduler from verified post-reply IRQ path.

V156 owner-native execution reached rescheduler 0x80529940 from 0x80526CB4,
after original interrupt restore returned masked (MSR EE=0). The SYSCONF
IOS_Open reply, Y1 and Hollywood IPC flag remain pending. Execute the
authentic rescheduler body and capture the next genuine translated guest call.
The prior STM path's 0x80529718 tail is research context only, not fabricated
as a target or forced by this harness.
"""
import argparse
from pathlib import Path
from derive_v156_sc_after_restore_harness import (
    derive as previous, STATE, RESET,
    NEXT_OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL, V146_ONCE,
)

STOP='''     ++v156_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x80529940u&&ctx.lr==0x80526cb4u,
           "V157 original SC rescheduler callsite does not match V156 owner proof");
     v157_first_inst=ctx.inst_count;
     ++v156_next_seen;
     return; // run original rescheduler; never force a thread-select call
   }'''
NEXT_OBSERVER='''   if(v141_live&&v156_next_seen==1u&&v157_next_seen==0u&&ctx.pc==addr){
     using V157Bus=undercover::wii::IosBus;
     using V157Mail=undercover::wii::IpcMailbox;
     using V157Irq=undercover::wii::HollywoodIrq;
     using V157Ios=undercover::wii::StmIos;
     const auto control=ipc70_bus.read32(V157Bus::IPC+V157Mail::PPCCTRL);
     const auto flags=ipc70_bus.read32(V157Bus::IPC+V157Irq::PPC_FLAG);
     const auto arm=ipc70_bus.read32(V157Bus::IPC+V157Mail::ARMMSG);
     const bool y1=control.has_value()&&flags.has_value()&&arm.has_value()&&
           ((*control&V157Mail::Y1)!=0u)&&((*control&V157Mail::Y2)==0u)&&
           ((*flags&V157Irq::IPC_PPC)!=0u)&&*arm==v153_phys&&
           ipc70_bus.external_irq_level();
     const bool reply=ipc70_ram.valid(v153_phys,64u)&&
           ipc70_ram.read32(v153_phys)==V157Ios::Reply&&
           ipc70_ram.read32(v153_phys+4u)==v153_fd&&
           ipc70_bus.services().queued_replies()==0u&&
           ipc70_bus.services().is_open(v153_fd,V157Ios::Device::File);
     const bool progressed=ctx.inst_count>v157_first_inst&&
           ctx.gpr[13]==v147_first_r13;
     const bool target=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     const bool ee=(ctx.msr&V157Bus::MSR_EE)!=0u;
     const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
     const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
     std::cout<<"V157_SC_RESCHED_NEXT y1="<<y1<<" reply="<<reply
              <<" progressed="<<progressed<<" target="<<target
              <<" coherent="<<coherent<<" ee="<<ee<<" ready="<<ready
              <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(y1&&reply&&progressed&&target&&coherent,
           "V157 original SC rescheduler did not reach valid next guest call");
     ++v157_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
NEXT_TRIAL='''       check(nwii::runtime::v157_next_seen==1u&&
             nwii::runtime::v156_next_seen==1u&&
             nwii::runtime::v155_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,
             "V157 original SC rescheduler did not execute through next native call");'''

def once(source: str, old: str, new: str)->str:
    n=source.count(old)
    if n!=1:raise ValueError(f"V157 public derived harness anchor count={n}: {old[:70]}")
    return source.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V157 inherited original rescheduler stop differs")
    s=once(s,STATE,STATE+"\n static unsigned v157_next_seen=0;\n static uint64_t v157_first_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v157_next_seen=0u;\n     nwii::runtime::v157_first_inst=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,V146_ONCE,NEXT_OBSERVER+V146_ONCE)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
