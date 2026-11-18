#!/usr/bin/env python3
"""V96 original directory query return through shared native IOS transport."""
import argparse
from pathlib import Path
from derive_v95_title_return_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x804f0ad8u",
    "POST_OWNER=0x8054b4b4u"
  ],
  [
    " static constexpr uint64_t POST95_TITLE=0x0001000041424344ull;",
    " static constexpr uint64_t POST95_TITLE=0x0001000041424344ull;\n static unsigned post96_phase=0,post96_in_flush=0,post96_return=0;\n static uint32_t post96_input=0,post96_outlen=8u;\n static constexpr std::string_view POST96_DIRECTORY=\"/title/00010000/41424344/data\";"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){",
    " static bool post96_result(CPUContext&ctx){\n   if(post96_phase!=2u)return ctx.mmu.read32(post95_out)==uint32_t(POST95_TITLE>>32)&&\n                                    ctx.mmu.read32(post95_out+4u)==uint32_t(POST95_TITLE);\n   for(unsigned i=0;i<POST96_DIRECTORY.size();++i)\n     if(ctx.mmu.read8(post95_out+i)!=uint8_t(POST96_DIRECTORY[i]))return false;\n   return ctx.mmu.read8(post95_out+POST96_DIRECTORY.size())==0u;\n }\n static bool post96_vector(CPUContext&ctx,bool physical){\n   const uint32_t mask=physical?0x3fffffffu:0xffffffffu;\n   if(post96_phase!=2u)return ctx.mmu.read32(post95_table)==(post95_out&mask)&&ctx.mmu.read32(post95_table+4u)==8u;\n   return ctx.mmu.read32(post95_table)==(post96_input&mask)&&ctx.mmu.read32(post95_table+4u)==8u&&\n          ctx.mmu.read32(post95_table+8u)==(post95_out&mask)&&ctx.mmu.read32(post95_table+12u)==post96_outlen;\n }\n static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post96_phase==2u&&addr==POST_OWNER&&ctx.lr==0x8051e8a0u){\n     using I=undercover::wii::StmIos;\n     const bool route=post96_return==0u&&post95_return==1u&&post95_tail==1u&&open71_submit==1u&&submit72_ack==1u&&\n          resume82_stop==1u&&open83_restore==1u&&open83_free==1u&&open83_free_restore==1u;\n     const bool data=post96_result(ctx)&&ctx.mmu.read32(post96_input)==uint32_t(POST95_TITLE>>32)&&\n          ctx.mmu.read32(post96_input+4u)==uint32_t(POST95_TITLE);\n     const bool vector=post96_vector(ctx,false)&&post95_invalidate>0u&&post96_in_flush>0u;\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack&&ctx.mmu.read16(THREAD+712u)==2u&&\n          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&ipc70_bus.services().is_open(3u,I::Device::Es)&&\n          ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate)&&\n          ipc70_bus.services().event_pending()&&ipc70_ram.read32(async87_request)==post92_event_command&&\n          ipc70_ram.read32(async87_request+4u)==post92_event_result&&ipc70_ram.read32(async86_out)==post92_event_output&&\n          !ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u;\n     std::cout<<\"V96_DIRECTORY_RETURN route=\"<<route<<\" data=\"<<data<<\" vector=\"<<vector<<\" abi=\"<<abi<<\" prior=\"<<prior<<std::endl;\n     check(route&&data&&vector&&abi&&prior,\"V96 original directory query did not return to NANDInit\");\n     ++post96_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // before original subsequent string copy\n   }\n   if(post96_phase==1u&&addr==0x8051a62cu&&ctx.lr==0x804f0b5cu){\n     using I=undercover::wii::StmIos;\n     const bool api=ctx.gpr[3]==3u&&ctx.gpr[4]==I::EsGetDataDir&&ctx.gpr[5]==1u&&ctx.gpr[6]==1u&&\n          ctx.msr==ipc69_msr&&ctx.gpr[1]<post91_child_stack;\n     const uint32_t table=ctx.gpr[7];\n     check(api&&table&&!(table&3u)&&open71_ram(table,16u),\"V96 actual directory request vector table invalid\");\n     const uint32_t in=ctx.mmu.read32(table),out=ctx.mmu.read32(table+8u),len=ctx.mmu.read32(table+12u);\n     const bool vector=in&&out&&ctx.mmu.read32(table+4u)==8u&&len>=POST96_DIRECTORY.size()+1u&&len<=0x1000u&&\n         open71_ram(in,8u)&&open71_ram(out,len);\n     const bool title=vector&&ctx.mmu.read32(in)==uint32_t(POST95_TITLE>>32)&&ctx.mmu.read32(in+4u)==uint32_t(POST95_TITLE);\n     std::cout<<\"V96_DIRECTORY_REQUEST api=\"<<api<<\" vector=\"<<vector<<\" title=\"<<title<<std::endl;\n     check(api&&vector&&title,\"V96 original directory query did not use previous returned title ID\");\n     post96_phase=2u;post96_input=in;post96_outlen=len;post95_table=table;post95_out=out;\n     post95_stack=ctx.gpr[1];open71_stack=ctx.gpr[1];\n     post95_prepare=post95_flush=post95_sc=post95_out_flush=post95_table_flush=post95_tail=post95_invalidate=0;\n     post95_flush_base=post95_flush_len=0;post95_flush_before=0;\n     submit72_active=false;\n     open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n     open71_flush=open71_sc=open71_submit=0;\n     open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n     submit72_flush=submit72_sc=submit72_disable=0;\n     submit72_message=submit72_x1=submit72_ack=0;\n     submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n     sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=sleep73_select=0;\n     sched74_get=sched74_save=sched74_set=sched74_enable=0;\n     sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n     vector75_entry=vector75_handler=0;\n     irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n     ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n     reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n     wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n     wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n     resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n     resume82_sleep_frame=0;\n     resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n     open83_restore=open83_free=open83_free_disable=open83_free_restore=0;\n     return true;\n   }"
  ],
  [
    "   if(post95_active&&addr==POST_OWNER&&ctx.lr==0x8051e884u){",
    "   if(post95_active&&addr==0x804f0ad8u&&ctx.lr==0x8051e884u){"
  ],
  [
    "     ++post95_return;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{};",
    "     ++post95_return;post96_phase=1u;return true; // original next directory query wrapper"
  ],
  [
    "       if(lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+8u)++post95_out_flush;\n       if(lo<=(post95_table&0x3fffffffu)&&end>=uint64_t(post95_table&0x3fffffffu)+8u)++post95_table_flush;",
    "       if(lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+post96_outlen)++post95_out_flush;\n       if(lo<=(post95_table&0x3fffffffu)&&end>=uint64_t(post95_table&0x3fffffffu)+(post96_phase==2u?16u:8u))++post95_table_flush;\n       if(post96_phase==2u&&lo<=(post96_input&0x3fffffffu)&&end>=uint64_t(post96_input&0x3fffffffu)+8u)++post96_in_flush;"
  ],
  [
    "ipc70_ram.read32(p+12u)==I::EsGetTitleId&&ipc70_ram.read32(p+16u)==0u&&",
    "ipc70_ram.read32(p+12u)==(post96_phase==2u?I::EsGetDataDir:I::EsGetTitleId)&&ipc70_ram.read32(p+16u)==(post96_phase==2u?1u:0u)&&"
  ],
  [
    "       const bool flush=post95_flush==post95_sc&&post95_out_flush>0u&&post95_table_flush>0u;\n       const bool wire=matches>0u&&ctx.mmu.read32(post95_table)==(post95_out&0x3fffffffu)&&ctx.mmu.read32(post95_table+4u)==8u;",
    "       const bool flush=post95_flush==post95_sc&&post95_out_flush>0u&&post95_table_flush>0u&&(post96_phase!=2u||post96_in_flush>0u);\n       const bool wire=matches>0u&&post96_vector(ctx,true);"
  ],
  [
    "       std::cout<<\"V95_VECTOR_SUBMIT flush=\"<<flush<<\" wire=\"<<wire<<std::endl;",
    "       std::cout<<(post96_phase==2u?\"V96_VECTOR_SUBMIT flush=\":\"V95_VECTOR_SUBMIT flush=\")<<flush<<\" wire=\"<<wire<<std::endl;"
  ],
  [
    "ipc70_ram.read32(request+12u)==IOS::EsGetTitleId&&\n          ipc70_ram.read32(request+16u)==0u&&ipc70_ram.read32(request+20u)==1u&&",
    "ipc70_ram.read32(request+12u)==(post96_phase==2u?IOS::EsGetDataDir:IOS::EsGetTitleId)&&\n          ipc70_ram.read32(request+16u)==(post96_phase==2u?1u:0u)&&ipc70_ram.read32(request+20u)==1u&&"
  ],
  [
    "       const bool output=ctx.mmu.read32(post95_out)==uint32_t(POST95_TITLE>>32)&&ctx.mmu.read32(post95_out+4u)==uint32_t(POST95_TITLE);\n       std::cout<<\"V95_TITLE_ACK wire=\"<<wire<<\" output=\"<<output<<std::endl;",
    "       const bool output=post96_result(ctx);\n       std::cout<<(post96_phase==2u?\"V96_DIRECTORY_ACK wire=\":\"V95_TITLE_ACK wire=\")<<wire<<\" output=\"<<output<<std::endl;"
  ],
  [
    "if(post95_active&&lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+8u)++post95_invalidate;",
    "if(post95_active&&lo<=(post95_out&0x3fffffffu)&&end>=uint64_t(post95_out&0x3fffffffu)+post96_outlen)++post95_invalidate;"
  ],
  [
    "     nwii::runtime::post95_active=false;",
    "     nwii::runtime::post95_active=false;\n     nwii::runtime::post96_phase=nwii::runtime::post96_in_flush=nwii::runtime::post96_return=nwii::runtime::post96_input=0;\n     nwii::runtime::post96_outlen=8u;"
  ],
  [
    "       check(nwii::runtime::post95_return==1u&&",
    "       check(nwii::runtime::post96_return==1u&&nwii::runtime::post95_return==1u&&"
  ],
  [
    "V95_TRIAL_PASS trial=",
    "V96_TRIAL_PASS trial="
  ],
  [
    "V95 recovered continuous original __start->ES title query return assertions",
    "V96 recovered continuous original __start->ES directory query return assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V96 source anchor missing or ambiguous: "+old[:80])
        source=source.replace(old,new,1)
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
