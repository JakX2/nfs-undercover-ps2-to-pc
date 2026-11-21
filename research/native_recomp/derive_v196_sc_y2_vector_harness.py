#!/usr/bin/env python3
"""V196 execute the genuine installed PowerPC external vector for second Y2.

V195 owner-authenticated exception-entry state: resume PC 0x8052F830,
exception vector 0x80000500, MSR.EE masked, one original IOS_Open
completion queued. No private guest opcode or original asset is published.
The test advances only authentic translated Wii vector/handler instructions.
"""
import argparse
from pathlib import Path
from derive_v195_sc_y2_irq_entry_harness import derive as previous,IRQ
from derive_v194_osrestore_next_harness import STATE,RESET,once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

OBSERVER='''  // Second, separately authenticated original Wii Y2 exception.
  // The first SC IRQ's V141+ observer is already completed at the V194
  // terminal guest checkpoint, and is phase-retired in the V196 trial.
  if(v196_live&&addr==0x80000500u){
    bool installed=true;
    for(size_t i=0;i<irq74_vector.size();++i)
      installed&=ctx.mmu.read8(addr+uint32_t(i))==irq74_vector[i];
    const bool vector=v196_vector_seen==0u&&v196_handler_seen==0u&&
          ctx.pc==addr&&ctx.srr0==v196_resume&&ctx.srr1==v196_srr1&&
          ctx.msr==v196_msr&&ctx.gpr==v196_gprs&&
          ctx.lr==v196_lr&&ctx.ctr==v196_ctr&&ctx.xer==v196_xer;
    check(vector&&installed,
          "V196 original second IOS Y2 installed vector entry differs");
    ++v196_vector_seen;
    return;
  }
  if(v196_live&&addr==0x80526ce0u){
    const uint32_t frame=ctx.gpr[4];
    const bool mapped=frame!=0u&&!(frame&7u)&&
          ctx.mmu.get_ptr(frame)!=nullptr&&
          ctx.mmu.get_ptr(frame+415u)!=nullptr;
    const bool handler=v196_vector_seen==1u&&v196_handler_seen==0u&&
          ctx.pc==addr&&ctx.gpr[3]==4u&&mapped;
    const bool saved=handler&&
          ctx.mmu.read32(frame+408u)==v196_resume&&
          ctx.mmu.read32(frame+412u)==v196_srr1&&
          ctx.mmu.read32(frame+12u)==v196_gprs[3]&&
          ctx.mmu.read32(frame+16u)==v196_gprs[4]&&
          ctx.mmu.read32(frame+20u)==v196_gprs[5]&&
          ctx.mmu.read32(frame+132u)==v196_lr&&
          ctx.mmu.read32(frame+136u)==v196_ctr&&
          ctx.mmu.read32(frame+140u)==v196_xer;
    const bool pending=ipc70_bus.services().queued_replies()==1u&&
          ipc70_bus.external_irq_level()&&
          !ipc70_bus.pending_native_ios_request();
    const bool progressed=ctx.inst_count>v196_start_inst;
    std::cout<<"V196_Y2_VECTOR vector="<<(v196_vector_seen==1u)
             <<" handler="<<handler<<" saved="<<saved
             <<" pending="<<pending<<" progressed="<<progressed
             <<" resume="<<std::hex<<v196_resume
             <<" pc="<<addr<<std::dec<<std::endl;
    check(handler&&saved&&pending&&progressed,
          "V196 original second IOS Y2 PowerPC vector did not save guest exception context");
    ++v196_handler_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_TRIAL='''    // V195 hardware entry already proved the exact interrupted Wii PC,
    // SRRs and pending second IOS Y2 state. Run the installed original
    // PowerPC vector to its next genuine OS exception-handler entry.
    if(owner){
      check(nwii::runtime::v194_next_seen==1u&&
            c.pc==0x80000500u&&c.srr0==0x8052f830u&&
            !c.dispatch_saved_ctx&&!c.is_running&&
            nwii::runtime::ipc70_bus.services().queued_replies()==1u,
            "V196 authenticated original second Y2 IRQ vector boundary differs");
      // The FIRST IRQ has completed its original V141+ observer sequence.
      // Scope those test-only observers to the first interrupt, without
      // touching the CPU, guest memory, original code or IOS reply queue.
      nwii::runtime::v141_live=false;
      nwii::runtime::v196_live=true;
      nwii::runtime::v196_resume=c.srr0;
      nwii::runtime::v196_srr1=c.srr1;
      nwii::runtime::v196_msr=c.msr;
      nwii::runtime::v196_lr=c.lr;
      nwii::runtime::v196_ctr=c.ctr;
      nwii::runtime::v196_xer=c.xer;
      nwii::runtime::v196_gprs=c.gpr;
      nwii::runtime::v196_start_inst=c.inst_count;
      c.is_running=true;
      bool stopped=false;
      try{run_game(c);}catch(const ExceptionStop&){stopped=true;}
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            !c.is_running&&c.pc==0x80526ce0u,
            "V196 second original IOS Y2 vector did not reach native OS exception handler");
    }
'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(IRQ)!=1:
        raise ValueError("V196 verified native second IOS exception entry changed")
    s=once(s,STATE,STATE+'''
 static bool v196_live=false;
 static unsigned v196_vector_seen=0u,v196_handler_seen=0u;
 static uint64_t v196_start_inst=0u;
 static uint32_t v196_resume=0u,v196_srr1=0u,v196_msr=0u;
 static uint32_t v196_lr=0u,v196_ctr=0u,v196_xer=0u;
 static std::array<uint32_t,32> v196_gprs{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v196_live=false;
     nwii::runtime::v196_vector_seen=nwii::runtime::v196_handler_seen=0u;
     nwii::runtime::v196_start_inst=0u;
     nwii::runtime::v196_resume=nwii::runtime::v196_srr1=nwii::runtime::v196_msr=0u;
     nwii::runtime::v196_lr=nwii::runtime::v196_ctr=nwii::runtime::v196_xer=0u;
     nwii::runtime::v196_gprs.fill(0u);''')
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,IRQ,IRQ+'\n'+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
