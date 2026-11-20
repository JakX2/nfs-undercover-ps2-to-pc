#!/usr/bin/env python3
"""V129 execute original Wii interrupt-disable routine after V128 helper."""
import argparse
from pathlib import Path
from derive_v128_next_function_harness import derive as previous
EDITS=[
 (" static uint32_t post128_pc=0,post128_lr=0;",
  " static uint32_t post128_pc=0,post128_lr=0;\n static unsigned post129_next=0;\n static uint32_t post129_pc=0,post129_lr=0;"),
 ("""     post128_pc=addr;post128_lr=ctx.lr;++post128_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x805265acu&&ctx.lr==0x8052f84cu,
           "V129 original interrupt-disable callsite differs");
     post128_pc=addr;post128_lr=ctx.lr;++post128_next;return;
   }
   if(post128_next==1u&&post129_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post127_pc==0x8052f830u&&post127_lr==0x80520970u&&
           post128_pc==0x805265acu&&post128_lr==0x8052f84cu&&
           post120_restore==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
           *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
           ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
           ctx.mmu.read32(0x800000d4u)==THREAD&&
           ctx.mmu.read32(0x800000e4u)==THREAD&&ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
           ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V129_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V129 original interrupt-disable successor differs");
     post129_pc=addr;post129_lr=ctx.lr;++post129_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("nwii::runtime::post128_next=nwii::runtime::post128_pc=nwii::runtime::post128_lr=0;",
  "nwii::runtime::post128_next=nwii::runtime::post128_pc=nwii::runtime::post128_lr=0;\n     nwii::runtime::post129_next=nwii::runtime::post129_pc=nwii::runtime::post129_lr=0;"),
 ("check(nwii::runtime::post128_next==1u&&nwii::runtime::post127_next==1u&&",
  "check(nwii::runtime::post129_next==1u&&nwii::runtime::post128_next==1u&&nwii::runtime::post127_next==1u&&"),
 ("V128_TRIAL_PASS trial=","V129_TRIAL_PASS trial="),
 ("nwii::runtime::post90_target==nwii::runtime::post128_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post129_pc&&")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:raise ValueError("V129 original-free harness anchor differs: "+a[:90]+" count="+str(n))
        s=s.replace(a,b,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
