#!/usr/bin/env python3
"""V118 submit a genuine second Wii IOS Open request via original PPCMSG/X1 MMIO, stop at sleep."""
import argparse
from pathlib import Path
from derive_v117_sc_send_register_harness import derive as previous

EDITS = [
 ("POST_OWNER=0x8051906cu","POST_OWNER=0x8052a430u"),
 (" static unsigned post117_send=0,post117_walk=0;",
  " static unsigned post117_send=0,post117_walk=0;\n static unsigned post118_msg=0,post118_x1=0,post118_reads=0,post118_sleep=0,post118_walk=0;\n static uint32_t post118_phys=0;"),
 ("if(post116_queue==1u&&addr==POST_OWNER&&ctx.lr==0x80519780u){",
  "if(post116_queue==1u&&addr==0x8051906cu&&ctx.lr==0x80519780u){"),
 ("""     ++post117_send;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }""",
  """     ++post117_send;return; // execute original register writer and MMIO
   }
   if(post117_send==1u&&post118_x1==1u&&addr==POST_OWNER&&ctx.lr==0x805197d8u){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const bool route=post118_sleep==0u&&post118_msg==1u&&post118_x1==1u&&
          post117_send==1u&&post116_queue==1u&&post115_disable==1u;
     const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(0u);
     const bool wire=post118_phys!=0u&&!(post118_phys&31u)&&
          ipc70_ram.valid(post118_phys,64u)&&ipc70_ram.read32(post118_phys)==I::Open&&
          (ctrl&M::X1);
     const bool abi=!(ctx.msr&0x8000u)&&ctx.gpr[1]<post98_root_stack&&
          ctx.mmu.read16(THREAD+712u)==2u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&
          ctx.mmu.read32(0x800000e4u)==THREAD;
     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&
          !ipc70_bus.services().is_open(3u,I::Device::Es)&&
          ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.external_irq_level();
     std::cout<<"V118_SLEEP_ENTRY route="<<route<<" wire="<<wire
              <<" abi="<<abi<<" prior="<<prior<<std::endl;
     check(route&&wire&&abi&&prior,
           "V118 original IOS async request did not reach sleep after PPCMSG and X1");
     ++post118_sleep;post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }
   if(post117_send==1u&&post118_sleep==0u&&post118_walk<16u){
     ++post118_walk;
     std::cout<<"V118_WALK seq="<<post118_walk<<" pc="<<std::hex<<addr
              <<" lr="<<ctx.lr<<std::dec<<" msg="<<post118_msg
              <<" x1="<<post118_x1<<std::endl;
   }"""),
 ("void HW_Reg_Write32(uint32_t addr,uint32_t value){",
  """void HW_Reg_Write32(uint32_t addr,uint32_t value){
   if(post117_send==1u){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;
     const bool msg=addr==B::IPC+M::PPCMSG||addr==B::MIRROR+M::PPCMSG;
     const bool ctrl=addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL;
     if(msg){
       const uint32_t p=value&0x3fffffffu;
       const bool wire=post118_msg==0u&&post118_x1==0u&&
            value!=0u&&!(p&31u)&&ipc70_ram.valid(p,64u)&&
            ipc70_ram.read32(p)==I::Open&&
            ipc70_ram.read32(p+16u)==post112_mode;
       const uint32_t path=wire?(ipc70_ram.read32(p+12u)&0x3fffffffu):0u;
       bool copied=wire&&!post112_path.empty()&&post112_path.size()<=256u&&
            path!=0u&&ipc70_ram.valid(path,uint32_t(post112_path.size()));
       if(copied)for(unsigned k=0;k<post112_path.size();++k)
         copied&=ipc70_ram.read8(path+k)==post112_path[k];
       std::cout<<"V118_PPCMSG wire="<<wire<<" path="<<copied<<std::endl;
       check(wire&&copied,"V118 original IPC PPCMSG request wire differs");
       check(ipc70_bus.write32(addr,value),"V118 native IOS bus rejected PPCMSG");
       post118_phys=p;++post118_msg;mmio_writes.emplace_back(addr,value);return;
     }
     if(ctrl){
       const bool route=post118_msg==1u&&post118_x1==0u&&(value&M::X1);
       const bool request=post118_phys!=0u&&
            ipc70_bus.read32(B::IPC+M::PPCMSG).value_or(0u)==post118_phys;
       std::cout<<"V118_PPCCTRL route="<<route<<" request="<<request<<std::endl;
       check(route&&request,"V118 original IPC X1 submission differs");
       check(ipc70_bus.write32(addr,value),"V118 native IOS bus rejected X1");
       ++post118_x1;mmio_writes.emplace_back(addr,value);return;
     }
   }"""),
 ("uint32_t HW_Reg_Read32(uint32_t addr){",
  """uint32_t HW_Reg_Read32(uint32_t addr){
   if(post117_send==1u&&post118_msg==1u&&post118_x1==0u){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     if(addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL){
       const auto v=ipc70_bus.read32(addr);
       check(v.has_value()&&++post118_reads<=64u,
             "V118 IPC request control read unsupported or unbounded");
       mmio_reads.emplace_back(addr,*v);return *v;
     }
   }"""),
 ("nwii::runtime::post117_send=nwii::runtime::post117_walk=0;",
  "nwii::runtime::post117_send=nwii::runtime::post117_walk=0;\n     nwii::runtime::post118_msg=nwii::runtime::post118_x1=nwii::runtime::post118_reads=nwii::runtime::post118_sleep=nwii::runtime::post118_walk=0;\n     nwii::runtime::post118_phys=0;"),
 ("check(nwii::runtime::post117_send==1u&&",
  "check(nwii::runtime::post118_sleep==1u&&nwii::runtime::post118_msg==1u&&nwii::runtime::post118_x1==1u&&nwii::runtime::post117_send==1u&&"),
 ("V117_TRIAL_PASS trial=","V118_TRIAL_PASS trial="),
 ("V117 recovered continuous original __start->SC IOS queue-helper return and IPC send-register entry assertions",
  "V118 recovered continuous original __start->SC IOS async PPCMSG and X1 to sleeping thread assertions")
]

def derive(source):
    s=previous(source)
    for a,b in EDITS:
        n=s.count(a)
        if n!=1:
            raise ValueError("V118 source anchor missing or ambiguous: "+a[:96]+" count="+str(n))
        s=s.replace(a,b,1)
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
