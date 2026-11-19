#!/usr/bin/env python3
"""V120 execute original asynchronous IPC X1 register write into original thread-sleep call."""
import argparse
from pathlib import Path
from derive_v119_sc_control_write_harness import derive as previous

EDITS = [
 ("POST_OWNER=0x8051906cu", "POST_OWNER=0x8052a430u"),
 (" static unsigned post119_control=0;",
  " static unsigned post119_control=0;\n static unsigned post120_sleep=0,post120_walk=0;"),
 ("if(post118_sleep==1u&&post117_send==1u&&addr==POST_OWNER&&ctx.lr==0x805197c8u){",
  "if(post118_sleep==1u&&post117_send==1u&&addr==0x8051906cu&&ctx.lr==0x805197c8u){"),
 ("""     ++post119_control;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post117_send==1u&&post118_sleep==0u&&post118_walk<16u){""",
  """     ++post119_control;return; // execute original IPC X1 control-register writer
   }
   if(post119_control==1u&&addr==POST_OWNER&&ctx.lr==0x805197d8u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const bool route=post120_sleep==0u&&post117_send==1u&&
          post118_sleep==1u&&post118_reads>0u&&post119_control==1u;
     const bool sent=post118_msg==1u&&post118_x1==1u;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
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
     std::cout<<"V120_X1_SLEEP_ENTRY route="<<route<<" sent="<<sent
              <<" wire="<<wire<<" abi="<<abi<<" prior="<<prior<<std::endl;
     check(route&&sent&&wire&&abi&&prior,
           "V120 original IOS X1 submission did not reach genuine sleep call");
     ++post120_sleep;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post119_control==1u&&post120_sleep==0u&&post120_walk<16u){
     ++post120_walk;
     std::cout<<"V120_WALK seq="<<post120_walk<<" pc="<<std::hex<<addr
              <<" lr="<<ctx.lr<<std::dec<<" x1="<<post118_x1<<std::endl;
   }
   if(post117_send==1u&&post118_sleep==0u&&post118_walk<16u){"""),
 ("nwii::runtime::post119_control=0;",
  "nwii::runtime::post119_control=0;\n     nwii::runtime::post120_sleep=nwii::runtime::post120_walk=0;"),
 ("check(nwii::runtime::post119_control==1u&&",
  "check(nwii::runtime::post120_sleep==1u&&nwii::runtime::post119_control==1u&&"),
 ("V119_TRIAL_PASS trial=","V120_TRIAL_PASS trial="),
 ("V119 recovered continuous original __start->SC IOS control-register read return and write-helper entry assertions",
  "V120 recovered continuous original __start->SC IOS X1 submission and thread-sleep call entry assertions")
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V120 source anchor missing or ambiguous: "+old[:96]+" count="+str(count))
        s=s.replace(old,new,1)
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
