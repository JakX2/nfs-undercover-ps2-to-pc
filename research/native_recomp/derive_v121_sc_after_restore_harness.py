#!/usr/bin/env python3
"""V121 discover the first original call after asynchronous IPC X1 restore."""
import argparse
from pathlib import Path
from derive_v120_sc_x1_sleep_harness import derive as previous

EDITS=[
 (" static unsigned post120_restore=0,post120_walk=0;",
  " static unsigned post120_restore=0,post120_walk=0;\n static unsigned post121_next=0;\n static uint32_t post121_next_pc=0,post121_next_lr=0;"),
 ("""     ++post120_restore;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post119_control==1u&&post120_restore==0u&&post120_walk<16u){""",
  """     ++post120_restore;return; // execute original OSRestoreInterrupts
   }
   if(post120_restore==1u&&post121_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post118_msg==1u&&post118_x1==1u&&
          post119_control==1u&&post117_send==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
          ipc70_ram.valid(post118_phys,64u)&&
          ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD&&
          ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V121_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,
           "V121 original post-X1 continuation call state differs");
     post121_next_pc=addr;post121_next_lr=ctx.lr;
     ++post121_next;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post119_control==1u&&post120_restore==0u&&post120_walk<16u){"""),
 ("nwii::runtime::post120_restore=nwii::runtime::post120_walk=0;",
  "nwii::runtime::post120_restore=nwii::runtime::post120_walk=0;\n     nwii::runtime::post121_next=0;\n     nwii::runtime::post121_next_pc=nwii::runtime::post121_next_lr=0;"),
 ("check(nwii::runtime::post120_restore==1u&&",
  "check(nwii::runtime::post121_next==1u&&nwii::runtime::post120_restore==1u&&"),
 ("V120_TRIAL_PASS trial=","V121_TRIAL_PASS trial="),
 ("V120 recovered continuous original __start->SC IOS X1 submission and interrupt-restore call entry assertions",
  "V121 recovered continuous original __start->SC IOS post-X1 continuation call assertions"),

]

def derive(source):
    result=previous(source)
    for a,b in EDITS:
        n=result.count(a)
        if n!=1:
            raise ValueError("V121 source anchor missing/ambiguous: "+a[:90]+" count="+str(n))
        result=result.replace(a,b,1)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
