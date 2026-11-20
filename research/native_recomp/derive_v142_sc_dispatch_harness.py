#!/usr/bin/env python3
"""V142 execute the original SC exception handler up to IRQ dispatcher entry.

The already-verified V141 vector and handler are allowed to run natively.
Only the original dispatcher-entry callback adds a test stop and register/frame
observations; no game instruction, device response or status byte is patched.
"""
import argparse
from pathlib import Path
from derive_v141_sc_vector_harness import derive as previous

STATE="static unsigned v141_vector_seen=0,v141_handler_seen=0;"
RESET="nwii::runtime::v141_vector_seen=nwii::runtime::v141_handler_seen=0u;"
HANDLER='''     ++v141_handler_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&!c.is_running,
             "V141 original SC external vector/handler was not executed");'''
NEXT='''     ++v141_handler_seen;return;
   }
   if(v141_live && addr==0x80526a3cu){
     const uint32_t frame=ctx.gpr[4];
     const bool mapped=frame!=0u&&!(frame&7u)&&
          ctx.mmu.get_ptr(frame)!=nullptr&&ctx.mmu.get_ptr(frame+415u)!=nullptr;
     const bool route=v141_vector_seen==1u&&v141_handler_seen==1u&&
          v142_dispatch_seen==0u&&ctx.pc==addr&&ctx.gpr[3]==4u&&mapped;
     bool registers=route;
     if(route){
       for(unsigned i=6u;i<32u;++i)
         registers&=ctx.mmu.read32(frame+4u*i)==v141_gprs[i];
     }
     const bool status=route&&ctx.mmu.read32(frame+408u)==v141_resume&&
           ctx.mmu.read32(frame+412u)==v141_srr1&&
           ctx.mmu.read32(frame+132u)==v141_lr&&
           ctx.mmu.read32(frame+136u)==v141_ctr&&
           ctx.mmu.read32(frame+140u)==v141_xer;
     const bool pending=ipc70_bus.services().queued_replies()==1u&&
                        ipc70_bus.external_irq_level();
     std::cout<<"V142_SC_DISPATCH route="<<route
              <<" regs="<<registers<<" status="<<status
              <<" pending="<<pending<<std::endl;
     check(route&&registers&&status&&pending,
           "V142 original SC handler did not enter native IRQ dispatcher with saved context");
     ++v142_dispatch_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL_NEXT='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&!c.is_running,
             "V142 original SC external vector did not enter authentic IRQ dispatcher");'''

def one(s:str,old:str,new:str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V142 source anchor expected once, got {count}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source:str)->str:
    s=previous(source)
    s=one(s,STATE,STATE+"\n static unsigned v142_dispatch_seen=0;")
    s=one(s,RESET,RESET+"\n     nwii::runtime::v142_dispatch_seen=0u;")
    s=one(s,HANDLER,NEXT)
    s=one(s,TRIAL,TRIAL_NEXT)
    return s

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    a=parser.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
