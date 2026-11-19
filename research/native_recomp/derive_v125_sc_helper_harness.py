#!/usr/bin/env python3
"""V125 advance original SC routine at 0x8051E5BC after verified X1 delivery."""
from pathlib import Path
from derive_v124_sc_second_save_harness import derive as previous
import argparse
EDITS=[
 (" static uint32_t post124_pc=0,post124_lr=0;",
  " static uint32_t post124_pc=0,post124_lr=0;\n static unsigned post125_next=0;\n static uint32_t post125_pc=0,post125_lr=0;"),
 ("""     post124_pc=addr;post124_lr=ctx.lr;++post124_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x8051e5bcu&&ctx.lr==0x8051e054u,
           "V125 original SC helper callsite differs");
     post124_pc=addr;post124_lr=ctx.lr;++post124_next;return;
   }
   if(post124_next==1u&&post125_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post123_next==1u&&post123_pc==0x80545150u&&
          post123_lr==0x8051de54u&&post124_pc==0x8051e5bcu&&
          post124_lr==0x8051e054u&&post120_restore==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
          ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD&&
          ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V125_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V125 original post-X1 SC helper continuation differs");
     post125_pc=addr;post125_lr=ctx.lr;++post125_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("nwii::runtime::post124_next=nwii::runtime::post124_pc=nwii::runtime::post124_lr=0;",
  "nwii::runtime::post124_next=nwii::runtime::post124_pc=nwii::runtime::post124_lr=0;\n     nwii::runtime::post125_next=nwii::runtime::post125_pc=nwii::runtime::post125_lr=0;"),
 ("check(nwii::runtime::post124_next==1u&&nwii::runtime::post123_next==1u&&",
  "check(nwii::runtime::post125_next==1u&&nwii::runtime::post124_next==1u&&nwii::runtime::post123_next==1u&&"),
 ("V124_TRIAL_PASS trial=","V125_TRIAL_PASS trial="),
 ("V124 recovered continuous original __start->SC IOS second register-save call and successor",
  "V125 recovered continuous original __start->SC IOS SC helper continuation"),
 ("nwii::runtime::post90_target==nwii::runtime::post124_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post125_pc&&")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:raise ValueError("V125 original-free anchor missing/ambiguous: "+a[:90]+" count="+str(n))
        s=s.replace(a,b,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
