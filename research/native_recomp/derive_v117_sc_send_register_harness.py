#!/usr/bin/env python3
"""V117 continue original IOS queue-helper code to its first IPC register write."""
import argparse
from pathlib import Path
from derive_v116_sc_queue_helper_harness import derive as previous

EDITS = [
 ("POST_OWNER=0x8051afe0u","POST_OWNER=0x8051906cu"),
 (" static unsigned post116_queue=0;",
  " static unsigned post116_queue=0;\n static unsigned post117_send=0,post117_walk=0;"),
 ("if(post115_disable==1u&&addr==POST_OWNER&&ctx.lr==0x805196d4u){",
  "if(post115_disable==1u&&addr==0x8051afe0u&&ctx.lr==0x805196d4u){"),
 ("""     ++post116_queue;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     ++post116_queue;return; // execute authentic original queue helper
   }
   if(post116_queue==1u&&addr==POST_OWNER&&ctx.lr==0x80519780u){
     using I=undercover::wii::StmIos;
     const bool route=post117_send==0u&&post115_disable==1u&&
          post115_sc==1u&&post115_vector==1u&&
          post114_syscall==1u&&post112_submit==1u;
     const bool abi=!(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD;
     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().event_pending()&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
     std::cout<<"V117_SEND_REG route="<<route<<" abi="<<abi
              <<" prior="<<prior<<std::endl;
     check(route&&abi&&prior,"V117 original IPC send register call ABI differs");
     ++post117_send;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post116_queue==1u&&post117_send==0u&&post117_walk<12u){
     ++post117_walk;
     std::cout<<"V117_WALK seq="<<post117_walk<<" pc="<<std::hex<<addr
              <<" lr="<<ctx.lr<<std::dec<<std::endl;
   }"""),
 ("nwii::runtime::post116_queue=0;",
  "nwii::runtime::post116_queue=0;\n     nwii::runtime::post117_send=nwii::runtime::post117_walk=0;"),
 ("check(nwii::runtime::post116_queue==1u&&",
  "check(nwii::runtime::post117_send==1u&&nwii::runtime::post116_queue==1u&&"),
 ("V116_TRIAL_PASS trial=","V117_TRIAL_PASS trial="),
 ("V116 recovered continuous original __start->SC IOS IRQ-disable return and queue-helper entry assertions",
  "V117 recovered continuous original __start->SC IOS queue-helper return and IPC send-register entry assertions"),
]

def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:
            raise ValueError("V117 source anchor missing or ambiguous: "+a[:96]+" count="+str(n))
        s=s.replace(a,b,1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
