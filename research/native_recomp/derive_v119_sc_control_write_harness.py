#!/usr/bin/env python3
"""V119 continue original async IPC control read to its genuine control-write helper."""
import argparse
from pathlib import Path
from derive_v118_sc_async_mailbox_harness import derive as previous

EDITS = [
 ("POST_OWNER=0x8051905cu","POST_OWNER=0x8051906cu"),
 (" static uint32_t post118_phys=0;",
  " static uint32_t post118_phys=0;\n static unsigned post119_control=0;"),
 ("if(post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197b8u){",
  "if(post117_send==1u&&addr==0x8051905cu&&ctx.lr==0x805197b8u){"),
 ("""     ++post118_sleep;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post117_send==1u&&post118_sleep==0u&&post118_walk<16u){""",
  """     ++post118_sleep;return; // execute original PPCCTRL read helper
   }
   if(post118_sleep==1u&&post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197c8u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const bool route=post119_control==0u&&post118_msg==1u&&
          post118_x1==0u&&post116_queue==1u&&post115_sc==1u;
     const bool reads=post118_reads>0u&&post118_reads<=64u;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const bool wire=post118_phys!=0u&&msg.has_value()&&*msg==post118_phys&&
          ipc70_ram.valid(post118_phys,64u)&&
          ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=!(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD;
     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().event_pending()&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
     std::cout<<"V119_CTRL_WRITE_ENTRY route="<<route<<" reads="<<reads
              <<" wire="<<wire<<" abi="<<abi<<" prior="<<prior<<std::endl;
     check(route&&reads&&wire&&abi&&prior,
           "V119 original IPC control-write helper did not follow genuine read");
     ++post119_control;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post117_send==1u&&post118_sleep==0u&&post118_walk<16u){"""),
 ("nwii::runtime::post118_phys=0;",
  "nwii::runtime::post118_phys=0;\n     nwii::runtime::post119_control=0;"),
 ("check(nwii::runtime::post118_sleep==1u&&",
  "check(nwii::runtime::post119_control==1u&&nwii::runtime::post118_sleep==1u&&"),
 ("V118_TRIAL_PASS trial=","V119_TRIAL_PASS trial="),
 ("V118 recovered continuous original __start->SC IOS control-register read entry assertions",
  "V119 recovered continuous original __start->SC IOS control-register read return and write-helper entry assertions")
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V119 source anchor missing or ambiguous: "+old[:95]+" count="+str(count))
        s=s.replace(old,new,1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as output:
        output.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
