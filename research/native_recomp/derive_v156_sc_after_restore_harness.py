#!/usr/bin/env python3
"""V156 run authenticated original SC scheduler interrupt-restore function.

V155 owner-original execution reached 0x805265D4 from 0x80529458 with a
published SYSCONF IOS_Open reply, Broadway Y1 and Hollywood IPC IRQ.
Run that original helper without injecting or discarding an interrupt, then
observe the next translated guest function and the resulting MSR EE state.
Neither an IRQ vector entry nor a callback is claimed at this checkpoint.
"""
import argparse
from pathlib import Path
from derive_v155_sc_after_disable_harness import (
    derive as previous, STATE, RESET,
    NEXT_OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL, V146_ONCE,
)

STOP='''     ++v155_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x805265d4u&&ctx.lr==0x80529458u,
           "V156 original SC scheduler restore-interrupt callsite differs");
     v156_first_inst=ctx.inst_count;
     ++v155_next_seen;
     return; // execute original interrupt-restore helper, not a host substitute
   }'''
NEXT_OBSERVER='''   if(v141_live&&v155_next_seen==1u&&v156_next_seen==0u&&ctx.pc==addr){
     using V156Bus=undercover::wii::IosBus;
     using V156Mail=undercover::wii::IpcMailbox;
     using V156Irq=undercover::wii::HollywoodIrq;
     using V156Ios=undercover::wii::StmIos;
     const auto control=ipc70_bus.read32(V156Bus::IPC+V156Mail::PPCCTRL);
     const auto flags=ipc70_bus.read32(V156Bus::IPC+V156Irq::PPC_FLAG);
     const auto arm=ipc70_bus.read32(V156Bus::IPC+V156Mail::ARMMSG);
     const bool irq=control.has_value()&&flags.has_value()&&arm.has_value()&&
           ((*control&V156Mail::Y1)!=0u)&&((*control&V156Mail::Y2)==0u)&&
           ((*flags&V156Irq::IPC_PPC)!=0u)&&*arm==v153_phys&&
           ipc70_bus.external_irq_level();
     const bool reply=ipc70_ram.valid(v153_phys,64u)&&
           ipc70_ram.read32(v153_phys)==V156Ios::Reply&&
           ipc70_ram.read32(v153_phys+4u)==v153_fd&&
           ipc70_bus.services().queued_replies()==0u&&
           ipc70_bus.services().is_open(v153_fd,V156Ios::Device::File);
     const bool progress=ctx.inst_count>v156_first_inst&&
           ctx.gpr[13]==v147_first_r13;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     const bool ee=(ctx.msr&V156Bus::MSR_EE)!=0u;
     const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
     const bool coherent=ready==(ee&&ipc70_bus.external_irq_level());
     std::cout<<"V156_SC_AFTER_RESTORE irq="<<irq<<" reply="<<reply
              <<" progress="<<progress<<" text="<<text
              <<" coherent="<<coherent<<" ee="<<ee<<" ready="<<ready
              <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(irq&&reply&&progress&&text&&coherent,
           "V156 original SC scheduler restore did not advance with valid Y1/EE state");
     ++v156_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
NEXT_TRIAL='''       check(nwii::runtime::v156_next_seen==1u&&
             nwii::runtime::v155_next_seen==1u&&
             nwii::runtime::v154_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,
             "V156 original SC scheduler interrupt restore did not reach native successor");'''

def once(s: str,a: str,b: str)->str:
    n=s.count(a)
    if n!=1:raise ValueError(f"V156 original-free source anchor count={n}: {a[:72]}")
    return s.replace(a,b,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V156 predecessor restore-call stop is not unique")
    s=once(s,STATE,STATE+"\n static unsigned v156_next_seen=0;\n static uint64_t v156_first_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v156_next_seen=0u;\n     nwii::runtime::v156_first_inst=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,V146_ONCE,NEXT_OBSERVER+V146_ONCE)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
