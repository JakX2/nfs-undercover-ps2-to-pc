#!/usr/bin/env python3
"""V155 execute original OSDI from authenticated V154 SC scheduler call.

V154 observed the original scheduler calling interrupt-disable function
0x805265AC with LR 0x80529448 while the SYSCONF IOS_Open reply is published
and Y1/IPC IRQ remain asserted. The V79 harness's legacy STM observer would
reject this later authentic SC call, since its phase is scoped to the earlier
STM reply. Release only this one already-confirmed function call and observe
the next translated guest function. No replacement guest code, return-value
stubs, new IOS steps or forged SC-ready byte.
"""
import argparse
from pathlib import Path
from derive_v154_sc_scheduler_next_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRIAL as PREVIOUS_TRIAL, V146_ONCE
)

STOP='''     ++v154_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x805265acu&&ctx.lr==0x80529448u,
           "V155 inherited V154 original OSDI caller differs");
     v155_first_inst=ctx.inst_count;
     ++v154_next_seen;
     return; // execute original interrupt-disable guest function
   }'''

NEXT_OBSERVER='''   if(v141_live&&v154_next_seen==1u&&v155_next_seen==0u&&ctx.pc==addr){
     using V155Bus=undercover::wii::IosBus;
     using V155Mail=undercover::wii::IpcMailbox;
     using V155Irq=undercover::wii::HollywoodIrq;
     using V155Ios=undercover::wii::StmIos;
     const auto ctrl=ipc70_bus.read32(V155Bus::IPC+V155Mail::PPCCTRL);
     const auto flags=ipc70_bus.read32(V155Bus::IPC+V155Irq::PPC_FLAG);
     const auto msg=ipc70_bus.read32(V155Bus::IPC+V155Mail::ARMMSG);
     const bool y1=ctrl.has_value()&&flags.has_value()&&msg.has_value()&&
           ((*ctrl&V155Mail::Y1)!=0u)&&((*ctrl&V155Mail::Y2)==0u)&&
           ((*flags&V155Irq::IPC_PPC)!=0u)&&*msg==v153_phys&&
           ipc70_bus.external_irq_level();
     const bool reply=ipc70_ram.valid(v153_phys,64u)&&
           ipc70_ram.read32(v153_phys)==V155Ios::Reply&&
           ipc70_ram.read32(v153_phys+4u)==v153_fd&&
           ipc70_bus.services().queued_replies()==0u&&
           ipc70_bus.services().is_open(v153_fd,V155Ios::Device::File);
     const bool progressed=ctx.inst_count>v155_first_inst&&
           ctx.gpr[13]==v147_first_r13&&
           !(ctx.msr&V155Bus::MSR_EE);
     const bool call=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V155_SC_AFTER_DISABLE y1="<<y1<<" reply="<<reply
              <<" progressed="<<progressed<<" call="<<call
              <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
     check(y1&&reply&&progressed&&call,
           "V155 original SC scheduler interrupt disable did not reach real successor");
     ++v155_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
'''
NEXT_TRIAL='''       check(nwii::runtime::v155_next_seen==1u&&
             nwii::runtime::v154_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,
             "V155 original SC interrupt-disable helper did not advance");'''

def once(s: str,a: str,b: str)->str:
    n=s.count(a)
    if n!=1:raise ValueError(f"V155 source anchor count={n}: {a[:75]}")
    return s.replace(a,b,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V155 predecessor original helper stop differs")
    s=once(s,STATE,STATE+"\n static unsigned v155_next_seen=0;\n static uint64_t v155_first_inst=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v155_next_seen=0u;\n     nwii::runtime::v155_first_inst=0u;")
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
