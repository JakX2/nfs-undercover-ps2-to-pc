#!/usr/bin/env python3
"""V116 execute original IOS submit IRQ-disable and reach the real IPC queue helper."""
import argparse
from pathlib import Path
from derive_v115_sc_irq_disable_harness import derive as previous

EDITS = [
 ("POST_OWNER=0x805265acu", "POST_OWNER=0x8051afe0u"),
 (" static bool post115_vector_active=false;",
  " static bool post115_vector_active=false;\n static unsigned post116_queue=0;"),
 ("if(post115_sc==1u&&addr==POST_OWNER&&ctx.lr==0x80519640u){",
  "if(post115_sc==1u&&addr==INT_DISABLE&&ctx.lr==0x80519640u){"),
 ("""     ++post115_disable;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;
     throw ExceptionStop{}; // stop before executing original IRQ-disable function
   }""",
  """     ++post115_disable;return; // execute original IRQ-disable function
   }
   if(post115_disable==1u&&addr==POST_OWNER&&ctx.lr==0x805196d4u){
     using I=undercover::wii::StmIos;
     const bool route=post116_queue==0u&&post115_sc==1u&&
          post115_vector==1u&&post114_syscall==1u&&post112_submit==1u;
     const bool pointer=ctx.gpr[3]!=0u&&!(ctx.gpr[3]&3u)&&
          open71_ram(ctx.gpr[3],8u);
     const bool abi=!(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD;
     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().event_pending()&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
     std::cout<<"V116_QUEUE_HELPER route="<<route<<" pointer="<<pointer
              <<" abi="<<abi<<" prior="<<prior<<std::endl;
     check(route&&pointer&&abi&&prior,
           "V116 original IOS request queue-helper boundary differs");
     ++post116_queue;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("nwii::runtime::post115_vector_active=false;",
  "nwii::runtime::post115_vector_active=false;\n     nwii::runtime::post116_queue=0;"),
 ("check(nwii::runtime::post115_disable==1u&&",
  "check(nwii::runtime::post116_queue==1u&&nwii::runtime::post115_disable==1u&&"),
 ("V115_TRIAL_PASS trial=", "V116_TRIAL_PASS trial="),
 ("V115 recovered continuous original __start->SC IOS request cache syscall return and IRQ-disable entry assertions",
  "V116 recovered continuous original __start->SC IOS IRQ-disable return and queue-helper entry assertions"),
]

def derive(source):
    result=previous(source)
    for old,new in EDITS:
        n=result.count(old)
        if n!=1:
            raise ValueError("V116 original-free anchor missing/ambiguous: "+old[:95]+" count="+str(n))
        result=result.replace(old,new,1)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
