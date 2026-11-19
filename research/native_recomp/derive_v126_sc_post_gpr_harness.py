#!/usr/bin/env python3
"""V126 execute authentic PPC register-save at 0x80545150 on the SC path."""
import argparse
from pathlib import Path
from derive_v125_sc_helper_harness import derive as previous

EDITS=[
 (" static uint32_t post125_pc=0,post125_lr=0;",
  " static uint32_t post125_pc=0,post125_lr=0;\n static unsigned post126_next=0;\n static uint32_t post126_pc=0,post126_lr=0;"),
 ("""     post125_pc=addr;post125_lr=ctx.lr;++post125_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x80545150u&&ctx.lr==0x8051e05cu,
           "V126 original GPR-save callsite after SC helper differs");
     post125_pc=addr;post125_lr=ctx.lr;++post125_next;return;
   }
   if(post125_next==1u&&post126_next==0u){
     using B=undercover::wii::IosBus;
     using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
     const bool route=post124_next==1u&&post124_pc==0x8051e5bcu&&
          post124_lr==0x8051e054u&&post125_pc==0x80545150u&&
          post125_lr==0x8051e05cu&&post120_restore==1u&&
          post119_control==1u&&post118_x1==1u;
     const bool wire=post118_phys!=0u&&msg.has_value()&&
          *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&
          ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;
     const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD&&
          ctx.mmu.read16(THREAD+712u)==2u;
     const bool text=addr>=0x80400000u&&addr<0x80600000u&&
          ctx.lr>=0x80400000u&&ctx.lr<0x80600000u;
     std::cout<<"V126_NEXT_CALL pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec
              <<" route="<<route<<" wire="<<wire<<" abi="<<abi
              <<" text="<<text<<std::endl;
     check(route&&wire&&abi&&text,"V126 original post-SC GPR-save successor differs");
     post126_pc=addr;post126_lr=ctx.lr;++post126_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""),
 ("bool handle_syscall(CPUContext&ctx){",
  "bool handle_syscall(CPUContext&ctx){\n"
  " if(post125_next==1u&&post126_next==0u&&ctx.pc==0x8052096cu){\n"
  "   using B=undercover::wii::IosBus;\n"
  "   using M=undercover::wii::IpcMailbox;\n"
  "   using I=undercover::wii::StmIos;\n"
  "   const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);\n"
  "   const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);\n"
  "   const bool route=post124_next==1u&&post124_pc==0x8051e5bcu&&\n"
  "       post124_lr==0x8051e054u&&post125_pc==0x80545150u&&\n"
  "       post125_lr==0x8051e05cu&&ctx.lr==0x8052096cu&&\n"
  "       post120_restore==1u&&post118_x1==1u;\n"
  "   const bool wire=post118_phys!=0u&&msg.has_value()&&\n"
  "       *msg==post118_phys&&ctrl.has_value()&&(*ctrl&M::X1)!=0u&&\n"
  "       ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open;\n"
  "   const bool abi=ctx.gpr[1]!=0u&&!(ctx.gpr[1]&7u)&&\n"
  "       ctx.mmu.read32(0x800000d4u)==THREAD&&\n"
  "       ctx.mmu.read32(0x800000e4u)==THREAD&&\n"
  "       ctx.mmu.read16(THREAD+712u)==2u;\n"
  "   const bool stop=ctx.mmu.read32(ctx.pc)==0x44000002u;\n"
  "   std::cout<<\"V126_OSINIT_RETURN pc=\"<<std::hex<<ctx.pc<<\" lr=\"<<ctx.lr<<std::dec\n"
  "            <<\" route=\"<<route<<\" wire=\"<<wire<<\" abi=\"<<abi\n"
  "            <<\" stop=\"<<stop<<std::endl;\n"
  "   check(route&&wire&&abi&&stop,\"V126 original OSInit return state differs\");\n"
  "   post126_pc=ctx.pc;post126_lr=ctx.lr;++post126_next;\n"
  "   post90_target=ctx.pc;observed_stop_pc=ctx.pc;++post_stops;\n"
  "   ctx.is_running=false;throw ExceptionStop{};\n"
  " }\n"
  ),
 ("nwii::runtime::post125_next=nwii::runtime::post125_pc=nwii::runtime::post125_lr=0;",
  "nwii::runtime::post125_next=nwii::runtime::post125_pc=nwii::runtime::post125_lr=0;\n     nwii::runtime::post126_next=nwii::runtime::post126_pc=nwii::runtime::post126_lr=0;"),
 ("check(nwii::runtime::post125_next==1u&&nwii::runtime::post124_next==1u&&",
  "check(nwii::runtime::post126_next==1u&&nwii::runtime::post125_next==1u&&nwii::runtime::post124_next==1u&&"),
 ("V125_TRIAL_PASS trial=","V126_TRIAL_PASS trial="),
 ("V125 recovered continuous original __start->SC IOS SC helper continuation",
  "V126 recovered continuous original __start->SC IOS post-helper GPR-save and OSInit return"),
 ("nwii::runtime::post90_target==nwii::runtime::post125_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post126_pc&&")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        count=s.count(a)
        if count!=1:
            raise ValueError("V126 original-free anchor missing or ambiguous: "+a[:90]+" count="+str(count))
        s=s.replace(a,b,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
