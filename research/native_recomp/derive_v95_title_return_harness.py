#!/usr/bin/env python3
"""V95 original title query through real synchronous IPC."""
import argparse
from pathlib import Path
from derive_v94_es_open_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x8051a62cu",
    "POST_OWNER=0x804f0ad8u"
  ],
  [
    " static unsigned post94_return=0,post94_query=0;",
    " static unsigned post94_return=0,post94_query=0;\n static bool post95_active=false;\n static unsigned post95_prepare=0,post95_flush=0,post95_sc=0,post95_out_flush=0,post95_table_flush=0,post95_tail=0,post95_return=0,post95_invalidate=0;\n static uint32_t post95_table=0,post95_out=0,post95_stack=0,post95_flush_base=0,post95_flush_len=0;\n static uint64_t post95_flush_before=0;\n static constexpr uint64_t POST95_TITLE=0x0001000041424344ull;"
  ],
  [
    "   if(post94_active&&post94_return==1u&&addr==POST_OWNER&&ctx.lr==0x804f0bd8u){",
    "   if(post94_active&&post94_return==1u&&addr==0x8051a62cu&&ctx.lr==0x804f0bd8u){"
  ],
  [
    "     ++post94_query;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // actual query entry, no fabricated response",
    "     check(open83_free_restore==1u&&resume82_stop==1u&&reply79_irq==1u,\"V95 ES open cleanup missing\");\n     ++post94_query;post95_active=true;post95_table=table;\n     post95_out=ctx.mmu.read32(table);post95_stack=ctx.gpr[1];open71_stack=ctx.gpr[1];\n     submit72_active=false;\n     open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n     open71_flush=open71_sc=open71_submit=0;\n     open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n     submit72_flush=submit72_sc=submit72_disable=0;\n     submit72_message=submit72_x1=submit72_ack=0;\n     submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n     sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=sleep73_select=0;\n     sched74_get=sched74_save=sched74_set=sched74_enable=0;\n     sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n     vector75_entry=vector75_handler=0;\n     irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n     ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n     reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n     wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n     wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n     resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n     resume82_sleep_frame=0;\n     resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n     open83_restore=open83_free=open83_free_disable=open83_free_restore=0;\n     return true; // execute original IOS_Ioctlv"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post95_active&&addr==POST_OWNER&&ctx.lr==0x8051e884u){\n     using I=undercover::wii::StmIos;\n     const bool route=post95_tail==1u&&post95_return==0u&&open71_submit==1u&&submit72_ack==1u&&\n          resume82_stop==1u&&open83_restore==1u&&open83_free==1u&&open83_free_restore==1u;\n     const bool output=ctx.mmu.read32(post95_out)==uint32_t(POST95_TITLE>>32)&&\n          ctx.mmu.read32(post95_out+4u)==uint32_t(POST95_TITLE);\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack&&\n          ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&ipc70_bus.services().is_open(3u,I::Device::Es)&&\n          ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate)&&\n          ipc70_bus.services().event_pending()&&ipc70_ram.read32(async87_request)==post92_event_command&&\n          ipc70_ram.read32(async87_request+4u)==post92_event_result&&ipc70_ram.read32(async86_out)==post92_event_output&&\n          !ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u;\n     const bool vector=ctx.mmu.read32(post95_table)==post95_out&&ctx.mmu.read32(post95_table+4u)==8u&&post95_invalidate>0u;\n     std::cout<<\"V95_TITLE_RETURN route=\"<<route<<\" output=\"<<output<<\" abi=\"<<abi<<\" prior=\"<<prior<<\" vector=\"<<vector<<std::endl;\n     check(route&&output&&abi&&prior&&vector,\"V95 original title query did not return with vector and metadata restored\");\n     ++post95_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{};\n   }\n   if(post95_active&&addr==0x8054514cu&&ctx.lr==0x8051a6f8u){\n     check(open83_free_restore==1u&&resume82_stop==1u&&post95_tail==0u&&ctx.gpr[3]==0u&&ctx.msr==ipc69_msr,\n           \"V95 original vector wrapper epilogue failed\");\n     ++post95_tail;return true;\n   }\n   if(post95_active&&!submit72_active&&post94_query==1u){\n     using I=undercover::wii::StmIos;\n     if(addr==0x80545100u&&(ctx.lr==0x8051a640u||ctx.lr==0x8051a420u))return true;\n     if((addr==0x8051ad38u||addr==0x8051ab34u)&&ctx.lr==0x8051a678u){\n       if(addr==0x8051ad38u){check(open71_profile==0u,\"V95 duplicate allocator wrapper\");++open71_profile;}\n       else{check(open71_alloc==0u&&ctx.gpr[4]>=64u&&ctx.gpr[4]<=0x1000u,\"V95 vector request allocator ABI\");++open71_alloc;}\n       return true;\n     }\n     if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u){\n       check(open71_alloc==1u&&open71_alloc_disable==0u&&(ctx.msr&0x8000u),\"V95 vector allocator disable\");\n       ++open71_alloc_disable;return true;\n     }\n     if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u){\n       check(open71_alloc_disable==1u&&open71_alloc_restore==0u&&!(ctx.msr&0x8000u),\"V95 vector allocator restore\");\n       ++open71_alloc_restore;return true;\n     }\n     if(addr==0x8051a40cu&&ctx.lr==0x8051a6d0u){\n       check(open71_alloc_restore==1u&&post95_prepare==0u&&ctx.msr==ipc69_msr,\"V95 original vector preparation entry\");\n       ++post95_prepare;return true;\n     }\n     if(addr==0x805222c0u&&(ctx.lr==0x8051a474u||ctx.lr==0x8051a4ccu||ctx.lr==0x8051a514u)){\n       check(post95_prepare==1u&&post95_flush==post95_sc&&post95_flush<4u&&\n             ctx.gpr[4]>0u&&ctx.gpr[4]<=0x1000u&&open71_ram(ctx.gpr[3],ctx.gpr[4]),\"V95 original vector flush ABI\");\n       post95_flush_base=ctx.gpr[3];post95_flush_len=ctx.gpr[4];post95_flush_before=ctx.guest_flush_count;\n       const auto lo=post95_flush_base&0x3fffffffu;const uint64_t end=uint64_t(lo)+post95_flush_len;\n       if(lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+8u)++post95_out_flush;\n       if(lo<=(post95_table&0x3fffffffu)&&end>=uint64_t(post95_table&0x3fffffffu)+8u)++post95_table_flush;\n       ++post95_flush;return true;\n     }\n     if(addr==0x80000c00u&&(ctx.lr==0x8051a474u||ctx.lr==0x8051a4ccu||ctx.lr==0x8051a514u)){\n       check(post95_flush==post95_sc+1u&&ctx.srr0==0x805222ecu,\"V95 vector flush syscall route\");return true;\n     }\n     if(addr==0x8054514cu&&ctx.lr==0x8051a538u)return true;\n     if(addr==0x805195ecu&&ctx.lr==0x8051a6e8u){\n       unsigned matches=0;\n       for(unsigned reg=3;reg<=10u;++reg){\n         const auto p=ctx.gpr[reg]&0x3fffffffu;\n         if(!ctx.gpr[reg]||(p&31u)||!ipc70_ram.valid(p,64u))continue;\n         if(ipc70_ram.read32(p)==I::Ioctlv&&ipc70_ram.read32(p+8u)==3u&&\n            ipc70_ram.read32(p+12u)==I::EsGetTitleId&&ipc70_ram.read32(p+16u)==0u&&\n            ipc70_ram.read32(p+20u)==1u&&ipc70_ram.read32(p+24u)==(post95_table&0x3fffffffu))++matches;\n       }\n       const bool flush=post95_flush==post95_sc&&post95_out_flush>0u&&post95_table_flush>0u;\n       const bool wire=matches>0u&&ctx.mmu.read32(post95_table)==(post95_out&0x3fffffffu)&&ctx.mmu.read32(post95_table+4u)==8u;\n       std::cout<<\"V95_VECTOR_SUBMIT flush=\"<<flush<<\" wire=\"<<wire<<std::endl;\n       check(flush&&wire&&open71_alloc_restore==1u&&open71_submit==0u&&ctx.msr==ipc69_msr,\"V95 original title query request not prepared\");\n       ++open71_submit;submit72_active=true;return true;\n     }\n     if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n       std::cout<<\"V95_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec<<std::endl;\n     check(false,\"V95 unexpected original vector preparation dependency\");\n   }"
  ],
  [
    "     const uint32_t path=ipc70_ram.read32(request+12u),mode=ipc70_ram.read32(request+16u);",
    "     if(post95_active){\n       const bool wire=ipc70_ram.read32(request+8u)==3u&&ipc70_ram.read32(request+12u)==IOS::EsGetTitleId&&\n          ipc70_ram.read32(request+16u)==0u&&ipc70_ram.read32(request+20u)==1u&&\n          ipc70_ram.read32(request+24u)==(post95_table&0x3fffffffu)&&request!=async87_request;\n       const uint32_t flush=submit72_base&0x3fffffffu;\n       check(wire&&flush<=request&&uint64_t(request)+32u<=uint64_t(flush)+submit72_len,\n             \"V95 actual mailbox vector request or header flush differs\");\n       check(ipc70_bus.tick()==IOS::Pump::Ack&&ipc70_bus.services().queued_replies()==1u&&\n             ipc70_bus.services().event_pending(),\"V95 native IOS did not accept the actual title request\");\n       const bool output=ctx.mmu.read32(post95_out)==uint32_t(POST95_TITLE>>32)&&ctx.mmu.read32(post95_out+4u)==uint32_t(POST95_TITLE);\n       std::cout<<\"V95_TITLE_ACK wire=\"<<wire<<\" output=\"<<output<<std::endl;\n       check(output,\"V95 native title metadata output differs\");\n     }else{\n     const uint32_t path=ipc70_ram.read32(request+12u),mode=ipc70_ram.read32(request+16u);"
  ],
  [
    "     const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u);\n     check(!(ctrl&Mail::X1)",
    "     }\n     const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u);\n     check(!(ctrl&Mail::X1)"
  ],
  [
    "open84_first_device!=device;",
    "open84_first_device==(ipc70_bus.services().is_open(1u,IOS::Device::Immediate)?IOS::Device::Event:IOS::Device::Immediate);"
  ],
  [
    "const bool second=ipc70_bus.services().is_open(1u,device)&&",
    "const bool second=(ipc70_bus.services().is_open(1u,IOS::Device::Immediate)||ipc70_bus.services().is_open(1u,IOS::Device::Event))&&"
  ],
  [
    "ipc70_ram.read32(request+12u)==path;",
    "ipc70_ram.read32(request+12u)==(stm70_path&0x3fffffffu);"
  ],
  [
    "             if(lo<=submit72_phys&&end>=uint64_t(submit72_phys)+12u)++wake80_invalidate;",
    "             if(lo<=submit72_phys&&end>=uint64_t(submit72_phys)+12u)++wake80_invalidate;\n             if(post95_active&&lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+8u)++post95_invalidate;"
  ],
  [
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){",
    "  if(own&&post95_active&&ctx.pc==0x805222e8u&&(ctx.lr==0x8051a474u||ctx.lr==0x8051a4ccu||ctx.lr==0x8051a514u)){\n    check(post95_flush==post95_sc+1u,\"V95 vector cache syscall order\");\n    const uint64_t lines=((post95_flush_base&31u)+uint64_t(post95_flush_len)+31u)/32u;\n    check(ctx.guest_flush_count==post95_flush_before+lines,\"V95 vector cache line count differs\");\n    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;const auto gp=ctx.gpr;\n    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),[](auto& c){func_80000C00(c);});\n    check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\"V95 vector cache syscall changed state\");\n    for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)check(ctx.gpr[r]==gp[r],\"V95 vector cache syscall changed unrelated GPR\");\n    ++post95_sc;return true;\n  }\n  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){"
  ],
  [
    "     nwii::runtime::post94_active=false;nwii::runtime::post94_return=nwii::runtime::post94_query=0;",
    "     nwii::runtime::post94_active=false;nwii::runtime::post94_return=nwii::runtime::post94_query=0;\n     nwii::runtime::post95_active=false;\n     nwii::runtime::post95_prepare=nwii::runtime::post95_flush=nwii::runtime::post95_sc=nwii::runtime::post95_out_flush=nwii::runtime::post95_table_flush=0;\n     nwii::runtime::post95_tail=nwii::runtime::post95_return=nwii::runtime::post95_invalidate=0;\n     nwii::runtime::post95_table=nwii::runtime::post95_out=nwii::runtime::post95_stack=nwii::runtime::post95_flush_base=nwii::runtime::post95_flush_len=0;\n     nwii::runtime::post95_flush_before=0;"
  ],
  [
    "       check(nwii::runtime::post94_query==1u&&",
    "       check(nwii::runtime::post95_return==1u&&nwii::runtime::post94_query==1u&&"
  ],
  [
    "V94_TRIAL_PASS trial=",
    "V95_TRIAL_PASS trial="
  ],
  [
    "V94 recovered continuous original __start->ES open and title query assertions",
    "V95 recovered continuous original __start->ES title query return assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V95 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
    old="ipc70_ram.read32(submit72_phys+4u)==(post94_active?3u:post92_active?2u:open84_active?1u:0u)&&"
    if source.count(old)!=4:raise ValueError("V95 synchronous result guards differ")
    source=source.replace(old,"ipc70_ram.read32(submit72_phys+4u)==(post95_active?0u:post94_active?3u:post92_active?2u:open84_active?1u:0u)&&")
    for old,new,count in (
        ("==IOS::Open","==(post95_active?IOS::Ioctlv:IOS::Open)",4),
        ("==I::Open","==(post95_active?I::Ioctlv:I::Open)",5),
        ("reply79_irq?IOS::Reply:IOS::Open","reply79_irq?IOS::Reply:post95_active?IOS::Ioctlv:IOS::Open",1),
        ("==StmIos::Open","==(post95_active?StmIos::Ioctlv:StmIos::Open)",1)):
        if source.count(old)!=count:raise ValueError("V95 command guard count differs: "+old+str(source.count(old)))
        source=source.replace(old,new)
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
