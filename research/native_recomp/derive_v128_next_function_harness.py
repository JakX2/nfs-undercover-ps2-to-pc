#!/usr/bin/env python3
"""V128 continue native execution into original 71-instruction post-OSInit helper."""
import argparse
from pathlib import Path
from derive_v127_osinit_first_bl_harness import derive as previous
EDITS=[
 (" static uint32_t post127_pc=0,post127_lr=0;",
  " static uint32_t post127_pc=0,post127_lr=0;\n static unsigned post128_next=0;\n static uint32_t post128_pc=0,post128_lr=0;"),
 ("""     post127_pc=addr;post127_lr=ctx.lr;++post127_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x8052f830u&&ctx.lr==0x80520970u,
           "V128 original function callsite differs");
     post127_pc=addr;post127_lr=ctx.lr;++post127_next;return;
   }
   if(post127_next==1u&&post128_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post124_next==1u&&post124_pc==0x8051e5bcu&&
           post125_pc==0x80545150u&&post127_pc==0x8052f830u&&
           post127_lr==0x80520970u&&post120_restore==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
           *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
           ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
           ctx.mmu.read32(0x800000d4u)==THREAD&&
           ctx.mmu.read32(0x800000e4u)==THREAD&&ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V128_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V128 post-OSInit helper successor differs");
     post128_pc=addr;post128_lr=ctx.lr;++post128_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("nwii::runtime::post127_next=nwii::runtime::post127_pc=nwii::runtime::post127_lr=0;",
  "nwii::runtime::post127_next=nwii::runtime::post127_pc=nwii::runtime::post127_lr=0;\n     nwii::runtime::post128_next=nwii::runtime::post128_pc=nwii::runtime::post128_lr=0;"),
 ("check(nwii::runtime::post127_next==1u&&nwii::runtime::post125_next==1u&&",
  "check(nwii::runtime::post128_next==1u&&nwii::runtime::post127_next==1u&&nwii::runtime::post125_next==1u&&"),
 ("V127_TRIAL_PASS trial=","V128_TRIAL_PASS trial="),
 ("V127 recovered original OSInit first authenticated BL after post-SC GPR save",
  "V128 recovered original 71-instruction OSInit next function and successor"),
 ("nwii::runtime::post90_target==nwii::runtime::post127_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post128_pc&&")
]
def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V128 original-free harness anchor ambiguous: "+old[:90]+" count="+str(count))
        s=s.replace(old,new,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
