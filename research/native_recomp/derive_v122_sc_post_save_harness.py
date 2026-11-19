#!/usr/bin/env python3
"""V122 execute original IOS register save and observe next original call."""
from derive_v121_sc_after_restore_harness import derive as previous
from pathlib import Path
import argparse
EDITS=[
 (" static uint32_t post121_next_pc=0,post121_next_lr=0;",
  " static uint32_t post121_next_pc=0,post121_next_lr=0;\n static unsigned post122_next=0;\n static uint32_t post122_pc=0;"),
 ("""     ++post121_next;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};""",
  """     check(addr==0x80545150u&&ctx.lr==0x80519934u,
           "V122 original PPC register-save caller differs");
     ++post121_next;return; // execute the original function"""),
 ("   if(post119_control==1u&&post120_restore==0u&&post120_walk<16u){",
  """   if(post121_next==1u&&post122_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post121_next_pc==0x80545150u&&post121_next_lr==0x80519934u&&
          post120_restore==1u&&post119_control==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
          ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD&&
          ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V122_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V122 original next call after register-save differs");
     post122_pc=addr;++post122_next;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post119_control==1u&&post120_restore==0u&&post120_walk<16u){"""),
 ("nwii::runtime::post121_next_pc=nwii::runtime::post121_next_lr=0;",
  "nwii::runtime::post121_next_pc=nwii::runtime::post121_next_lr=0;\n     nwii::runtime::post122_next=nwii::runtime::post122_pc=0;"),
 ("check(nwii::runtime::post121_next==1u&&",
  "check(nwii::runtime::post122_next==1u&&nwii::runtime::post121_next==1u&&"),
 ("V121_TRIAL_PASS trial=","V122_TRIAL_PASS trial="),
 ("V121 recovered continuous original __start->SC IOS post-X1 continuation call assertions",
  "V122 recovered continuous original __start->SC IOS register-save and next call assertions"),
 ("nwii::runtime::post90_target==nwii::runtime::post121_next_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post122_pc&&")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:raise ValueError("V122 source anchor missing or ambiguous: "+a[:95]+" count="+str(n))
        s=s.replace(a,b,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
