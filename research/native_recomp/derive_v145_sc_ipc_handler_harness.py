#!/usr/bin/env python3
"""V145 continue original SC interrupt dispatcher to registered IPC IRQ handler.

V144's authentic scheduler-disable helper executes and returns. A read-only
observer requires the original dispatcher to select IRQ slot 27 and enter its
installed native IPC handler; the IOS request/reply and guest code are untouched.
"""
import argparse
from pathlib import Path
from derive_v144_sc_irq_disable_harness import derive as previous

STATE="static unsigned v144_disable_seen=0;"
RESET="nwii::runtime::v144_disable_seen=0u;"
STOP='''     ++v144_disable_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
NEXT='''     ++v144_disable_seen;v145_disable_inst=ctx.inst_count;return;
   }
   if(v141_live&&v144_disable_seen==1u&&addr==0x80519318u){
     const uint32_t frame=ctx.gpr[4];
     const bool mapped=frame!=0u&&!(frame&7u)&&ctx.mmu.get_ptr(frame)!=nullptr&&
           ctx.mmu.get_ptr(frame+415u)!=nullptr;
     const bool dispatch=ctx.pc==addr&&ctx.ctr==addr&&
           ctx.lr>=0x80526c98u&&ctx.lr<=0x80526cacu&&
           ctx.gpr[3]==27u&&v145_ipc_seen==0u&&
           ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr;
     const bool context=mapped&&ctx.mmu.read32(frame+408u)==v141_resume&&
           ctx.mmu.read32(frame+412u)==v141_srr1;
     const bool masked=(ctx.msr&0x8000u)==0u;
     const bool pending=ipc70_bus.services().queued_replies()==1u&&
                        ipc70_bus.external_irq_level();
     const bool progressed=ctx.inst_count>v145_disable_inst;
     std::cout<<"V145_SC_IPC dispatch="<<dispatch<<" context="<<context
              <<" masked="<<masked<<" pending="<<pending
              <<" progressed="<<progressed<<std::endl;
     check(dispatch&&context&&masked&&pending&&progressed,
           "V145 original SC IRQ dispatcher did not select its native IPC handler");
     ++v145_ipc_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&!c.is_running,
             "V144 original SC dispatcher did not reach scheduler interrupt-disable helper");'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&!c.is_running,
             "V145 original SC dispatcher did not enter registered IPC interrupt handler");'''

def one(s,old,new):
    n=s.count(old)
    if n!=1:raise ValueError(f"V145 native harness source anchor expected once, got {n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source):
    s=previous(source)
    s=one(s,STATE,STATE+"\n static unsigned v145_ipc_seen=0;\n static uint64_t v145_disable_inst=0;")
    s=one(s,RESET,RESET+"\n     nwii::runtime::v145_ipc_seen=0u;\n     nwii::runtime::v145_disable_inst=0u;")
    s=one(s,STOP,NEXT)
    s=one(s,"   if(v141_live&&v144_disable_seen==1u&&addr==0x80519318u){","   // V98's NAND registration observer is still active in the inherited\n   // test harness. The later SC interrupt reuses the original interrupt\n   // helpers, but is not part of NAND registration or the second SC retry.\n   // Let the verified native guest helper execute without applying the old\n   // V98 \"IOS must be idle\" assertion at this different IRQ phase.\n   if(v141_live&&v144_disable_seen==1u&&\n      (addr==INT_DISABLE||addr==INT_RESTORE)&&\n      ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u){\n     const bool masked=(ctx.msr&0x8000u)==0u;\n     const bool pending=ipc70_bus.services().queued_replies()==1u&&\n                        ipc70_bus.external_irq_level();\n     check(masked&&pending,\n           \"V145 original SC dispatcher nested IRQ helper lost pending IOS state\");\n     return;\n   }\n   if(v141_live&&v144_disable_seen==1u&&addr==0x80519318u){")
    s=one(s,TRIAL,NEXT_TRIAL)
    # V136's two callsite observers belong only to its second SC retry.
    # A later external IRQ legitimately calls the same interrupt helpers;
    # preserve the original V136 checks before the third SC entry, then
    # relinquish the helper addresses to the subsequent IRQ instrumentation.
    for addr in ("0x805265acu", "0x805265d4u"):
        before=f"if(post130_next==1u&&addr=={addr})"
        after=f"if(post130_next==1u&&post136_seen==0u&&addr=={addr})"
        s=one(s,before,after)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
