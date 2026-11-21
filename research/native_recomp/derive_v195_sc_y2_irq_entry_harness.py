#!/usr/bin/env python3
"""V195 hardware external IRQ entry after 16-trial owner-original V194.

Only after original owner DOL executes and all original guest/CPU/memory
assertions pass, admit pending Hollywood Y2 IRQ at the stopped original Wii
OSInit retry instruction boundary. Requires original installed vector;
preserves GPR/LR/CTR/XER, saves PC/MSR to SRR0/SRR1, changes only hardware
exception state. Does not execute guest handler yet or create IOS reply.
"""
import argparse
from pathlib import Path
from derive_v194_osrestore_next_harness import derive as previous

TAIL='''      check(c.mmu.read32(0x80036004u)==0xDEADBEEFu,"synthetic store overran neighboring word");
    }
  }
  check(nwii::runtime::unknown_calls==0&&nwii::runtime::interpreter_calls==0,"unexpected syscall/interpreter fallback");'''
IRQ='''    // Bounded hardware exception after all authenticated guest state checks.
    // No guest instruction, IRQ latch acknowledgment or IOS service is faked.
    if(owner){
      using Bus=undercover::wii::IosBus;
      using Mail=undercover::wii::IpcMailbox;
      using Irq=undercover::wii::HollywoodIrq;
      const uint32_t oldpc=c.pc,oldmsr=c.msr,oldlr=c.lr;
      const uint32_t oldctr=c.ctr,oldxer=c.xer;
      const auto oldgprs=c.gpr;
      const bool pending=nwii::runtime::ipc70_bus.external_exception_pending(c.msr);
      const bool safe=!c.dispatch_saved_ctx&&!c.is_running;
      const auto result=undercover::wii::enter_external_irq(
          c,nwii::runtime::ipc70_bus,nwii::runtime::irq74_vector,safe);
      const bool entered=result==undercover::wii::ExternalEntry::Entered&&
          c.pc==undercover::wii::ExternalVector;
      const bool saved=c.srr0==oldpc&&
          c.srr1==(oldmsr&undercover::wii::ExternalSrr1Mask)&&
          c.msr==(oldmsr&~undercover::wii::ExternalMsrClear);
      const bool regs=c.gpr==oldgprs&&c.lr==oldlr&&
          c.ctr==oldctr&&c.xer==oldxer;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
      const auto flags=nwii::runtime::ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
      const bool mail=ctrl.has_value()&&flags.has_value()&&
          ((*ctrl&Mail::Y2)!=0u)&&((*flags&Irq::IPC_PPC)!=0u)&&
          nwii::runtime::ipc70_bus.external_irq_level()&&
          nwii::runtime::ipc70_bus.services().queued_replies()==1u&&
          !nwii::runtime::ipc70_bus.pending_native_ios_request();
      const bool masked=!nwii::runtime::ipc70_bus.external_exception_pending(c.msr)&&
          (c.msr&Bus::MSR_EE)==0u;
      std::cout<<"V195_SC_Y2_VECTOR pending="<<pending<<" safe="<<safe
               <<" entered="<<entered<<" saved="<<saved
               <<" regs="<<regs<<" mail="<<mail<<" masked="<<masked
               <<" resume="<<std::hex<<oldpc<<" pc="<<c.pc<<std::dec<<std::endl;
      check(nwii::runtime::v194_next_seen==1u&&
            oldpc==0x8052f830u&&oldlr==0x80520970u&&
            (oldmsr&Bus::MSR_EE)!=0u&&
            pending&&safe&&entered&&saved&&regs&&mail&&masked,
            "V195 real second IOS Y2 failed authentic external exception entry");
    }
'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(TAIL)!=1 or s.count("V194_RESTORE_STATE guest=")!=1:
        raise ValueError("V195 original-free authenticated trial tail changed")
    insertion='  }\n  check(nwii::runtime::unknown_calls'
    if TAIL.count(insertion)!=1:
        raise ValueError("V195 end of trial is not unique")
    return s.replace(TAIL,TAIL.replace(insertion,IRQ+insertion,1),1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
