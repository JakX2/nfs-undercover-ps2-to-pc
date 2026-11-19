#!/usr/bin/env python3
"""V124 execute original asynchronous continuation's second register-save call."""
from pathlib import Path
import argparse
from derive_v123_sc_post_leaf_harness import derive as previous
EDITS=[
 (" static uint32_t post123_pc=0,post123_lr=0;",
  " static uint32_t post123_pc=0,post123_lr=0;\n static unsigned post124_next=0;\n static uint32_t post124_pc=0,post124_lr=0;"),
 ("""     post123_pc=addr;post123_lr=ctx.lr;++post123_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x80545150u&&ctx.lr==0x8051de54u,
           "V124 original second register-save callsite differs");
     post123_pc=addr;post123_lr=ctx.lr;++post123_next;return;
   }
   if(post123_next==1u&&post124_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post122_next==1u&&post122_pc==0x8054514cu&&
          post123_pc==0x80545150u&&post123_lr==0x8051de54u&&
          post120_restore==1u&&post119_control==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
          ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD&&
          ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V124_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V124 second original register-save successor differs");
     post124_pc=addr;post124_lr=ctx.lr;++post124_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("nwii::runtime::post123_next=nwii::runtime::post123_pc=nwii::runtime::post123_lr=0;",
  "nwii::runtime::post123_next=nwii::runtime::post123_pc=nwii::runtime::post123_lr=0;\n     nwii::runtime::post124_next=nwii::runtime::post124_pc=nwii::runtime::post124_lr=0;"),
 ("check(nwii::runtime::post123_next==1u&&nwii::runtime::post122_next==1u&&",
  "check(nwii::runtime::post124_next==1u&&nwii::runtime::post123_next==1u&&nwii::runtime::post122_next==1u&&"),
 ("V123_TRIAL_PASS trial=","V124_TRIAL_PASS trial="),
 ("V123 recovered continuous original __start->SC IOS second helper and next call assertions",
  "V124 recovered continuous original __start->SC IOS second register-save call and successor"),
 ("nwii::runtime::post90_target==nwii::runtime::post123_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post124_pc&&")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:raise ValueError("V124 source anchor missing or ambiguous: "+a[:95]+" count="+str(n))
        s=s.replace(a,b,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
