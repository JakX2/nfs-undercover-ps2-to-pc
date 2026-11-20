#!/usr/bin/env python3
"""V141 resume V140's native SC exception into the original installed PPC vector.

The first run is the complete V140 owner-original test. After its assertions,
a second run dispatches the already-selected external vector and stops exactly
at the original exception handler entry. No replacement game instructions,
forced SC status, or synthetic successful IOS reply are introduced.
"""
import argparse
from pathlib import Path
from derive_v140_sc_irq_entry_harness import derive as previous

STATE = " static unsigned post136_disable=0,post136_restore=0,post136_seen=0;"
RESET = ("nwii::runtime::post136_disable=nwii::runtime::post136_restore="
         "nwii::runtime::post136_seen=0;")
INJECT = "     // Record the original callable stop, not the newly selected vector."
TRACE = "void trace_call(uint32_t addr, CPUContext&ctx){"
TRIAL = '       std::cout<<"V130_TRIAL_PASS trial="'

VARS = """ 
 static bool v141_live=false;
 static unsigned v141_vector_seen=0,v141_handler_seen=0;
 static uint32_t v141_resume=0,v141_srr1=0,v141_msr_after=0;
 static uint32_t v141_lr=0,v141_ctr=0,v141_xer=0;
 static std::array<uint32_t,32> v141_gprs{};
"""

BEFORE_STOP = """     v141_resume=v140_resume;
     v141_srr1=ctx.srr1;v141_msr_after=ctx.msr;
     v141_lr=v140_lr;v141_ctr=v140_ctr;v141_xer=v140_xer;
     v141_gprs=v140_gprs;v141_live=true;
"""

ENTRY_OBSERVER = """void trace_call(uint32_t addr, CPUContext&ctx){
   if(v141_live && addr==0x80000500u){
     const bool state=v141_vector_seen==0u&&v141_handler_seen==0u&&
           ctx.pc==addr&&ctx.srr0==v141_resume&&ctx.srr1==v141_srr1&&
           ctx.msr==v141_msr_after&&ctx.gpr==v141_gprs&&
           ctx.lr==v141_lr&&ctx.ctr==v141_ctr&&ctx.xer==v141_xer;
     bool installed=true;
     for(size_t i=0;i<irq74_vector.size();++i)
       installed&=ctx.mmu.read8(addr+uint32_t(i))==irq74_vector[i];
     check(state&&installed,"V141 authentic SC external vector dispatch state differs");
     ++v141_vector_seen;return;
   }
   if(v141_live && addr==0x80526ce0u){
     const uint32_t frame=ctx.gpr[4];
     const bool mapped=frame!=0u&&!(frame&7u)&&
           ctx.mmu.get_ptr(frame)!=nullptr&&
           ctx.mmu.get_ptr(frame+415u)!=nullptr;
     const bool state=v141_vector_seen==1u&&v141_handler_seen==0u&&
           ctx.pc==addr&&ctx.gpr[3]==4u&&mapped;
     const bool saved=state&&ctx.mmu.read32(frame+408u)==v141_resume&&
           ctx.mmu.read32(frame+412u)==v141_srr1&&
           ctx.mmu.read32(frame+12u)==v141_gprs[3]&&
           ctx.mmu.read32(frame+16u)==v141_gprs[4]&&
           ctx.mmu.read32(frame+20u)==v141_gprs[5]&&
           ctx.mmu.read32(frame+132u)==v141_lr&&
           ctx.mmu.read32(frame+136u)==v141_ctr&&
           ctx.mmu.read32(frame+140u)==v141_xer;
     const bool queued=ipc70_bus.services().queued_replies()==1u&&
                       ipc70_bus.external_irq_level();
     std::cout<<"V141_SC_VECTOR vector="<<(v141_vector_seen==1u)
              <<" handler="<<state<<" saved="<<saved<<" queued="<<queued<<std::endl;
     check(state&&saved&&queued,"V141 original SC vector did not save interrupted guest context");
     ++v141_handler_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }
"""

RESET_EXTRA = """ 
     nwii::runtime::v141_live=false;
     nwii::runtime::v141_vector_seen=nwii::runtime::v141_handler_seen=0u;
     nwii::runtime::v141_resume=nwii::runtime::v141_srr1=
       nwii::runtime::v141_msr_after=0u;
     nwii::runtime::v141_lr=nwii::runtime::v141_ctr=
       nwii::runtime::v141_xer=0u;
     nwii::runtime::v141_gprs.fill(0u);"""

TRIAL_EXTRA = """       // Validate the complete inherited V140 native owner path first.
       // Then resume only the already-armed original PowerPC vector.
       check(nwii::runtime::v141_live&&c.pc==0x80000500u&&
             nwii::runtime::v141_vector_seen==0u,
             "V141 original SC IRQ vector was not armed after V140 stop");
       c.is_running=true;
       bool v141_stopped=false;
       try{run_game(c);}catch(const ExceptionStop&){v141_stopped=true;}
       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&!c.is_running,
             "V141 original SC external vector/handler was not executed");
"""

def once(s: str, old: str, new: str) -> str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V141 source anchor expected once, got {count}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str) -> str:
    s=previous(source)
    s=once(s,STATE,STATE+VARS)
    s=once(s,INJECT,BEFORE_STOP+INJECT)
    s=once(s,TRACE,ENTRY_OBSERVER)
    s=once(s,RESET,RESET+RESET_EXTRA)
    s=once(s,TRIAL,TRIAL_EXTRA+TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
