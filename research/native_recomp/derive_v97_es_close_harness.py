#!/usr/bin/env python3
"""V97 original ES close through shared synchronous IOS transport."""
import argparse
from pathlib import Path
from derive_v96_directory_return_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8054b4b4u",
    "POST_OWNER=0x80527b4cu"
  ],
  [
    " static unsigned post96_phase=0,post96_in_flush=0,post96_return=0;",
    " static unsigned post96_phase=0,post96_in_flush=0,post96_return=0;\n static unsigned post97_copy=0,post97_close=0,post97_return=0;\n static uint32_t post97_dst=0;"
  ],
  [
    "   if(post96_phase==2u&&addr==POST_OWNER&&ctx.lr==0x8051e8a0u){",
    "   if(post96_phase==2u&&addr==0x8054b4b4u&&ctx.lr==0x8051e8a0u){"
  ],
  [
    "     ++post96_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // before original subsequent string copy",
    "     check(ctx.gpr[3]&&ctx.gpr[4]&&open71_ram(ctx.gpr[3],POST96_DIRECTORY.size()+1u)&&\n           open71_ram(ctx.gpr[4],POST96_DIRECTORY.size()+1u),\"V97 original directory copy range\");\n     for(unsigned i=0;i<POST96_DIRECTORY.size();++i)\n       check(ctx.mmu.read8(ctx.gpr[4]+i)==uint8_t(POST96_DIRECTORY[i]),\"V97 original directory copy source differs\");\n     check(ctx.mmu.read8(ctx.gpr[4]+POST96_DIRECTORY.size())==0u,\"V97 unterminated directory copy\");\n     post97_dst=ctx.gpr[3];++post96_return;post96_phase=3u;return true; // execute original string copy"
  ],
  [
    "   if(post96_phase==1u&&addr==0x8051a62cu&&ctx.lr==0x804f0b5cu){",
    "   if(post96_phase==3u&&addr==0x804f063cu&&ctx.lr==0x8051e8a4u){\n     bool copied=post97_dst!=0u;\n     for(unsigned i=0;i<POST96_DIRECTORY.size();++i)copied&=ctx.mmu.read8(post97_dst+i)==uint8_t(POST96_DIRECTORY[i]);\n     copied&=ctx.mmu.read8(post97_dst+POST96_DIRECTORY.size())==0u;\n     std::cout<<\"V97_DIRECTORY_COPY copied=\"<<copied<<std::endl;\n     check(copied&&post97_copy==0u&&ctx.gpr[1]==post91_child_stack,\"V97 original NAND directory copy not preserved\");\n     ++post97_copy;return true;\n   }\n   if(post96_phase==3u&&addr==0x80519b24u&&ctx.lr==0x804f065cu){\n     using I=undercover::wii::StmIos;\n     check(post97_copy==1u&&post97_close==0u&&ctx.gpr[3]==3u&&ctx.msr==ipc69_msr&&\n           ipc70_bus.services().is_open(3u,I::Device::Es)&&ipc70_bus.services().event_pending()&&\n           open83_free_restore==1u&&resume82_stop==1u&&reply79_irq==1u,\"V97 original ES close ABI differs\");\n     ++post97_close;post96_phase=4u;open71_stack=ctx.gpr[1];\n     submit72_active=false;\n     open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n     open71_flush=open71_sc=open71_submit=0;\n     open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n     submit72_flush=submit72_sc=submit72_disable=0;\n     submit72_message=submit72_x1=submit72_ack=0;\n     submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n     sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=sleep73_select=0;\n     sched74_get=sched74_save=sched74_set=sched74_enable=0;\n     sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n     vector75_entry=vector75_handler=0;\n     irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n     ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n     reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n     wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n     wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n     resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n     resume82_sleep_frame=0;\n     resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n     open83_restore=open83_free=open83_free_disable=open83_free_restore=0;\n     return true;\n   }\n   if(post96_phase==4u&&addr==POST_OWNER&&ctx.lr==0x8051e8c0u){\n     using I=undercover::wii::StmIos;\n     const bool route=post97_return==0u&&post97_copy==1u&&post97_close==1u&&open71_submit==1u&&\n         submit72_ack==1u&&resume82_stop==1u&&open83_free_restore==1u;\n     const bool closed=!ipc70_bus.services().is_open(3u,I::Device::Es)&&ctx.mmu.read32(R13-16784u)==0xffffffffu;\n     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n          ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate)&&\n          ipc70_bus.services().event_pending()&&ipc70_ram.read32(async87_request)==post92_event_command&&\n          ipc70_ram.read32(async87_request+4u)==post92_event_result&&ipc70_ram.read32(async86_out)==post92_event_output&&\n          !ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u;\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack&&ctx.mmu.read16(THREAD+712u)==2u&&\n          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n     const bool callback=ctx.gpr[3]&&!(ctx.gpr[3]&3u)&&open71_ram(ctx.gpr[3],16u);\n     std::cout<<\"V97_ES_RETURN route=\"<<route<<\" closed=\"<<closed<<\" prior=\"<<prior<<\" abi=\"<<abi<<\" callback=\"<<callback<<std::endl;\n     check(route&&closed&&prior&&abi&&callback,\"V97 original ES close did not reach shutdown registration\");\n     ++post97_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{};\n   }\n   if(post96_phase==3u&&addr==REPORT&&ctx.lr==0x8051e8b8u)return true; // original logging sink\n   if(post96_phase==1u&&addr==0x8051a62cu&&ctx.lr==0x804f0b5cu){"
  ],
  [
    "   if(post95_active&&!submit72_active&&post94_query==1u){",
    "   if(post96_phase==4u&&!submit72_active){\n     using I=undercover::wii::StmIos;\n     if((addr==0x8051ad38u||addr==0x8051ab34u)&&ctx.lr==0x80519b60u){\n       if(addr==0x8051ad38u){check(open71_profile==0u,\"V97 duplicate close allocator wrapper\");++open71_profile;}\n       else{check(open71_alloc==0u&&ctx.gpr[4]>=64u&&ctx.gpr[4]<=0x1000u,\"V97 close allocator ABI\");++open71_alloc;}\n       return true;\n     }\n     if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u){\n       check(open71_alloc==1u&&open71_alloc_disable==0u&&(ctx.msr&0x8000u),\"V97 close allocator disable\");\n       ++open71_alloc_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u){\n       check(open71_alloc_disable==1u&&open71_alloc_restore==0u&&!(ctx.msr&0x8000u),\"V97 close allocator restore\");\n       ++open71_alloc_restore;return true;\n     }\n     if(addr==0x805195ecu&&ctx.lr==0x80519bacu){\n       unsigned matches=0;\n       for(unsigned reg=3;reg<=10u;++reg){\n         const auto p=ctx.gpr[reg]&0x3fffffffu;\n         if(!ctx.gpr[reg]||(p&31u)||!ipc70_ram.valid(p,64u))continue;\n         if(ipc70_ram.read32(p)==I::Close&&ipc70_ram.read32(p+8u)==3u)++matches;\n       }\n       check(matches>0u&&open71_alloc_restore==1u&&open71_submit==0u&&ctx.msr==ipc69_msr,\"V97 genuine close request preparation\");\n       ++open71_submit;submit72_active=true;return true;\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V97_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     check(false,\"V97 unexpected close preparation dependency\");\n   }\n   if(post95_active&&!submit72_active&&post94_query==1u){"
  ],
  [
    "     if(post95_active){\n       const bool wire=ipc70_ram.read32(request+8u)==3u",
    "     if(post96_phase==4u){\n       const bool wire=ipc70_ram.read32(request+8u)==3u&&request!=async87_request;\n       const uint32_t flush=submit72_base&0x3fffffffu;\n       check(wire&&flush<=request&&uint64_t(request)+32u<=uint64_t(flush)+submit72_len,\n             \"V97 actual close wire request or flush differs\");\n       check(ipc70_bus.tick()==IOS::Pump::Ack&&ipc70_bus.services().queued_replies()==1u&&\n             ipc70_bus.services().event_pending(),\"V97 native IOS close ACK differs\");\n       const bool closed=!ipc70_bus.services().is_open(3u,IOS::Device::Es);\n       std::cout<<\"V97_CLOSE_ACK wire=\"<<wire<<\" closed=\"<<closed<<std::endl;\n       check(closed,\"V97 native ES descriptor not closed\");\n     }else if(post95_active){\n       const bool wire=ipc70_ram.read32(request+8u)==3u"
  ],
  [
    "     nwii::runtime::post96_outlen=8u;",
    "     nwii::runtime::post96_outlen=8u;\n     nwii::runtime::post97_copy=nwii::runtime::post97_close=nwii::runtime::post97_return=nwii::runtime::post97_dst=0;"
  ],
  [
    "       check(nwii::runtime::post96_return==1u&&",
    "       check(nwii::runtime::post97_return==1u&&nwii::runtime::post96_return==1u&&"
  ],
  [
    "V96_TRIAL_PASS trial=",
    "V97_TRIAL_PASS trial="
  ],
  [
    "V96 recovered continuous original __start->ES directory query return assertions",
    "V97 recovered continuous original __start->ES close return assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V97 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    for typ,count in (("IOS",5),("I",5),("StmIos",1)):
        old=f"post95_active?{typ}::Ioctlv:{typ}::Open"
        if source.count(old)!=count:raise ValueError("V97 command guard count differs: "+typ)
        source=source.replace(old,f"post96_phase==4u?{typ}::Close:"+old)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as f:
        f.write(result)

if __name__=="__main__":
    main()
