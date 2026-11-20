#!/usr/bin/env python3
"""V154 execute original SC interrupt scheduler helper after native IOS reply.

V153's deterministic native IOS step has published the original SYSCONF
IOS_Open reply at authenticated function entry 0x80529434 (LR 0x80526CB0).
Now run that original function, retaining the new Y1 IRQ and response buffer,
and observe the next genuine translated PPC function entry. No forced return,
SC status update, IRQ entry or callback is added.
"""
import argparse
from pathlib import Path
from derive_v153_sc_reply_handoff_harness import (
    derive as previous, STATE, RESET, NEXT_OBSERVER, NEXT_TRIAL as TRIAL,
)
from derive_v150_sc_irq_flag_harness import V146_ONCE

STOP='''     v153_phys=*req;v153_fd=uint32_t(result);
     ++v152_next_seen;++v153_bridge_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     v153_phys=*req;v153_fd=uint32_t(result);
     ++v152_next_seen;++v153_bridge_seen;
     v154_start_inst=ctx.inst_count;return; // run the original scheduler helper
   }'''
OBSERVER='''   if(v141_live&&v153_bridge_seen==1u&&v154_next_seen==0u&&ctx.pc==addr){
     using V154Bus=undercover::wii::IosBus;
     using V154Mail=undercover::wii::IpcMailbox;
     using V154Irq=undercover::wii::HollywoodIrq;
     using V154Ios=undercover::wii::StmIos;
     const auto control=ipc70_bus.read32(V154Bus::IPC+V154Mail::PPCCTRL);
     const auto flags=ipc70_bus.read32(V154Bus::IPC+V154Irq::PPC_FLAG);
     const auto arm=ipc70_bus.read32(V154Bus::IPC+V154Mail::ARMMSG);
     const bool signal=control.has_value()&&flags.has_value()&&arm.has_value()&&
           ((*control&V154Mail::Y1)!=0u)&&((*control&V154Mail::Y2)==0u)&&
           ((*flags&V154Irq::IPC_PPC)!=0u)&&*arm==v153_phys&&
           ipc70_bus.external_irq_level();
     const bool reply=ipc70_ram.valid(v153_phys,64u)&&
           ipc70_ram.read32(v153_phys)==V154Ios::Reply&&
           ipc70_ram.read32(v153_phys+4u)==v153_fd&&
           ipc70_bus.services().queued_replies()==0u&&
           ipc70_bus.services().is_open(v153_fd,V154Ios::Device::File);
     const bool guest=ctx.inst_count>v154_start_inst&&
           ctx.gpr[13]==v147_first_r13&&
           !(ctx.msr&V154Bus::MSR_EE);
     const bool target=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V154_SC_SCHED_NEXT signal="<<signal<<" reply="<<reply
              <<" guest="<<guest<<" target="<<target
              <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(signal&&reply&&guest&&target,
           "V154 SC reply IRQ or guest scheduler helper continuation differs");
     ++v154_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
V153_CHECK='''             c.pc==0x80529434u&&c.lr==0x80526cb0u&&!c.is_running;'''
V154_CHECK='''             nwii::runtime::v154_next_seen==1u&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&!c.is_running;'''
TRIAL_NEXT='''       check(nwii::runtime::v154_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&
             nwii::runtime::v152_next_seen==1u&&!c.is_running,
             "V154 did not execute SC post-IRQ original scheduler helper");'''

def once(source: str, old: str, new: str)->str:
    count=source.count(old)
    if count!=1:
        raise ValueError(f"V154 original-free source anchor count={count}: {old[:64]}")
    return source.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if NEXT_OBSERVER.count(STOP)!=1 or TRIAL.count(V153_CHECK)!=1:
        raise ValueError("V154 inherited SC IOS reply boundary diverged")
    s=once(s,STATE,STATE+"\n static unsigned v154_next_seen=0;\n static uint64_t v154_start_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v154_next_seen=0u;\n     nwii::runtime::v154_start_inst=0u;")
    s=once(s,STOP,CONTINUE)
    s=once(s,V146_ONCE,OBSERVER+V146_ONCE)
    s=once(s,TRIAL,TRIAL.replace(V153_CHECK,V154_CHECK,1)+"\n"+TRIAL_NEXT)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
