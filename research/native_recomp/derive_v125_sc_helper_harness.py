#!/usr/bin/env python3
"""V125 advance original SC routine at 0x8051E5BC after verified X1 delivery."""
from pathlib import Path
from derive_v124_sc_second_save_harness import derive as previous
import argparse
EDITS=[
 (" static uint32_t post124_pc=0,post124_lr=0;",
  " static uint32_t post124_pc=0,post124_lr=0;\n static unsigned post125_next=0;\n static uint32_t post125_pc=0,post125_lr=0;\n static uint64_t post125_enter_inst=0;"),
 ("""     post124_pc=addr;post124_lr=ctx.lr;++post124_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     check(addr==0x8051e5bcu&&ctx.lr==0x8051e054u,
           "V125 original SC helper callsite differs");
     post124_pc=addr;post124_lr=ctx.lr;++post124_next;post125_enter_inst=ctx.inst_count;return;
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
  "nwii::runtime::post124_next=nwii::runtime::post124_pc=nwii::runtime::post124_lr=0;\n     nwii::runtime::post125_next=nwii::runtime::post125_pc=nwii::runtime::post125_lr=0;\n     nwii::runtime::post125_enter_inst=0;"),
 ("check(nwii::runtime::post124_next==1u&&nwii::runtime::post123_next==1u&&",
  "check(nwii::runtime::post125_next==1u&&nwii::runtime::post124_next==1u&&nwii::runtime::post123_next==1u&&"),
 ("V124_TRIAL_PASS trial=","V125_TRIAL_PASS trial="),
 ("V124 recovered continuous original __start->SC IOS second register-save call and successor",
  "V125 recovered continuous original __start->SC IOS SC helper continuation"),
 ("nwii::runtime::post90_target==nwii::runtime::post124_pc&&",
  "nwii::runtime::post90_target==nwii::runtime::post125_pc&&"),
 ("static uint64_t post125_enter_inst=0;",
  "static uint64_t post125_enter_inst=0;\n static unsigned post125_trace_count=0;"),
 ("void trace_call(uint32_t addr, CPUContext&ctx){",
  "void trace_call(uint32_t addr, CPUContext&ctx){\n"
  "   if((post124_next==1u||(post123_next==1u&&addr==0x8051e5bcu&&ctx.lr==0x8051e054u))&&post125_next==0u&&post125_trace_count<8u){\n"
  "     ++post125_trace_count;\n"
  "     std::cout<<\"V125_TRACE_CALL seq=\"<<post125_trace_count<<\" pc=\"<<std::hex<<addr\n"
  "              <<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n"
  "     if(post125_trace_count==1u){\n"
  "       const uint32_t a=ctx.mmu.read32(addr),b=ctx.mmu.read32(addr+4u);\n"
  "       const unsigned op0=a>>26,op1=b>>26;\n"
  "       const bool b0=op0==16u||op0==18u||op0==19u;\n"
  "       const bool b1=op1==16u||op1==18u||op1==19u;\n"
  "       const bool m0=op0>=32u&&op0<=55u;\n"
  "       const bool m1=op1>=32u&&op1<=55u;\n"
  "       std::cout<<\"V125_OPCODE_CLASS first_branch=\"<<b0<<\" first_mem=\"<<m0\n"
  "                <<\" second_branch=\"<<b1<<\" second_mem=\"<<m1<<std::endl;\n"
  "       std::cout<<\"V125_OPCODE_DETAIL major0=\"<<op0<<\" major1=\"<<op1\n"
  "                <<\" xo0=\"<<((a>>1u)&1023u)<<\" zero0=\"<<(a==0u)\n"
  "                <<\" zero1=\"<<(b==0u)<<std::endl;\n"
  "     }\n"
  "   }"),
 ("nwii::runtime::post125_enter_inst=0;",
  "nwii::runtime::post125_enter_inst=0;\n     nwii::runtime::post125_trace_count=0;"),
 ("try{run_game(c);}catch(const ExceptionStop&){exception_stop=true;}",
  "try{run_game(c);}catch(const ExceptionStop&){exception_stop=true;}\n"
  "      catch(const std::exception& e){\n"
  "        std::cout<<\"V125_EXCEPTION_SITE pc=\"<<std::hex<<c.pc<<\" lr=\"<<c.lr<<std::dec\n"
  "                 <<\" phase=\"<<(nwii::runtime::post124_next==1u)\n"
  "                 <<\" kind=\"<<(dynamic_cast<const std::runtime_error*>(&e)!=nullptr)<<std::endl;\n"
  "        std::cout<<\"V125_EXCEPTION_STEPS delta=\"<<(c.inst_count>=nwii::runtime::post125_enter_inst ?\n"
  "                   std::min<uint64_t>(c.inst_count-nwii::runtime::post125_enter_inst,999999u) : 0u)<<std::endl;\n"
  "        throw;\n"
  "      }")
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
