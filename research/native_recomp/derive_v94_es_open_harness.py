#!/usr/bin/env python3
"""V94 authentic ES open through next original title query."""
import argparse
from pathlib import Path
from derive_v93_isfs_return_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x80519944u",
    "POST_OWNER=0x8051a62cu"
  ],
  [
    " static unsigned post92_complete=0;",
    " static unsigned post92_complete=0;\n static bool post94_active=false;\n static unsigned post94_return=0,post94_query=0;"
  ],
  [
    "   if(post92_complete==1u){",
    "   if(post92_complete==1u&&!post94_active){"
  ],
  [
    "     if(addr==POST_OWNER&&ctx.lr==0x804f0614u){",
    "     if(addr==0x80519944u&&ctx.lr==0x804f0614u){"
  ],
  [
    "       ++post93_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before real ES open, never simulate a successful return",
    "       check(!post94_active&&open83_free_restore==1u&&resume82_stop==1u&&reply79_irq==1u,\n             \"V94 prior original filesystem request cleanup missing\");\n       ++post93_open;post94_active=true;\n       post92_mode=ctx.gpr[4];stm70_path=ctx.gpr[3];\n       open71_path_len=uint32_t(pathname.size()+1u);open71_stack=ctx.gpr[1];\n       submit72_active=false;\n       open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n       open71_flush=open71_sc=open71_submit=0;\n       open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n       submit72_flush=submit72_sc=submit72_disable=0;\n       submit72_message=submit72_x1=submit72_ack=0;\n       submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n       sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=sleep73_select=0;\n       sched74_get=sched74_save=sched74_set=sched74_enable=0;\n       sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n       vector75_entry=vector75_handler=0;\n       irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n       ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n       reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n       wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n       wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n       resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n       resume82_sleep_frame=0;\n       resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n       open83_restore=open83_free=open83_free_disable=open83_free_restore=0;\n       return true; // execute authentic fourth original IOS_Open"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post92_active&&addr==0x8051908cu",
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post94_active&&addr==0x804f0b70u&&ctx.lr==0x8051e864u){\n     using I=undercover::wii::StmIos;\n     const bool route=post94_return==0u&&post93_open==1u&&open71_submit==1u&&submit72_ack==1u&&\n           resume82_stop==1u&&open83_restore==1u&&open83_free==1u&&open83_free_restore==1u;\n     const bool result=ctx.mmu.read32(R13-16784u)==3u&&ipc70_bus.services().is_open(3u,I::Device::Es);\n     const bool prior=ctx.mmu.read32(R13-16768u)==2u&&ipc70_bus.services().is_open(2u,I::Device::Fs)&&\n          ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n     const bool deferred=ipc70_bus.services().event_pending()&&\n          ipc70_ram.read32(async87_request)==post92_event_command&&\n          ipc70_ram.read32(async87_request+4u)==post92_event_result&&\n          ipc70_ram.read32(async86_out)==post92_event_output&&submit72_phys!=async87_request&&\n          !ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u;\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==post91_child_stack&&\n          ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n     std::cout<<\"V94_ES_RETURN route=\"<<route<<\" result=\"<<result<<\" prior=\"<<prior\n              <<\" deferred=\"<<deferred<<\" abi=\"<<abi<<std::endl;\n     check(route&&result&&prior&&deferred&&abi,\"V94 original ES open did not return to NANDInit\");\n     ++post94_return;return true; // execute the genuine title-query wrapper\n   }\n   if(post94_active&&post94_return==1u&&addr==POST_OWNER&&ctx.lr==0x804f0bd8u){\n     using I=undercover::wii::StmIos;\n     const bool route=post94_query==0u&&ctx.pc==addr&&ctx.msr==ipc69_msr&&ctx.gpr[1]<post91_child_stack;\n     const bool api=ctx.gpr[3]==3u&&ctx.gpr[4]==I::EsGetTitleId&&ctx.gpr[5]==0u&&ctx.gpr[6]==1u;\n     const uint32_t table=ctx.gpr[7];\n     bool vector=table&&!(table&3u)&&open71_ram(table,8u);\n     if(vector){\n       const uint32_t out=ctx.mmu.read32(table),size=ctx.mmu.read32(table+4u);\n       vector=out&&size==8u&&open71_ram(out,size);\n     }\n     const bool prior=ipc70_bus.services().is_open(2u,I::Device::Fs)&&ipc70_bus.services().is_open(3u,I::Device::Es)&&\n          ipc70_bus.services().event_pending()&&!ipc70_bus.external_irq_level()&&\n          ipc70_ram.read32(async87_request)==post92_event_command&&ipc70_ram.read32(async86_out)==post92_event_output;\n     std::cout<<\"V94_TITLE_REQUEST route=\"<<route<<\" api=\"<<api<<\" vector=\"<<vector<<\" prior=\"<<prior<<std::endl;\n     check(route&&api&&vector&&prior,\"V94 original first title query vector ABI differs\");\n     ++post94_query;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // actual query entry, no fabricated response\n   }\n   if(post92_active&&addr==0x8051908cu"
  ],
  [
    "     const auto device=post92_active?IOS::Device::Fs:name==\"/dev/stm/immediate\"?IOS::Device::Immediate:IOS::Device::Event;",
    "     const auto device=post94_active?IOS::Device::Es:post92_active?IOS::Device::Fs:name==\"/dev/stm/immediate\"?IOS::Device::Immediate:IOS::Device::Event;"
  ],
  [
    "     check(post92_active?name==\"/dev/fs\":(name==\"/dev/stm/immediate\"||name==\"/dev/stm/eventhook\"),",
    "     check(post94_active?name==\"/dev/es\":post92_active?name==\"/dev/fs\":(name==\"/dev/stm/immediate\"||name==\"/dev/stm/eventhook\"),"
  ],
  [
    "ipc70_bus.services().is_open(post92_active?2u:open84_active?1u:0u,device)",
    "ipc70_bus.services().is_open(post94_active?3u:post92_active?2u:open84_active?1u:0u,device)"
  ],
  [
    "            ipc70_bus.services().is_open(1u-async86_fd,IOS::Device::Immediate);",
    "            ipc70_bus.services().is_open(1u-async86_fd,IOS::Device::Immediate)&&\n            (!post94_active||ipc70_bus.services().is_open(2u,IOS::Device::Fs));"
  ],
  [
    "       std::cout<<\"V92_FS_ACK prior=\"<<prior<<\" event=\"<<event<<std::endl;",
    "       std::cout<<(post94_active?\"V94_ES_ACK prior=\":\"V92_FS_ACK prior=\")<<prior<<\" event=\"<<event<<std::endl;"
  ],
  [
    "     nwii::runtime::post92_active=false;nwii::runtime::post92_complete=0;",
    "     check(nwii::runtime::ipc70_bus.services().mount_title_metadata(0x0001000041424344ull),\n           \"V94 explicit synthetic title metadata fixture rejected\");\n     nwii::runtime::post94_active=false;nwii::runtime::post94_return=nwii::runtime::post94_query=0;\n     nwii::runtime::post92_active=false;nwii::runtime::post92_complete=0;"
  ],
  [
    "       check(nwii::runtime::post93_open==1u&&",
    "       check(nwii::runtime::post94_query==1u&&nwii::runtime::post94_return==1u&&nwii::runtime::post93_open==1u&&"
  ],
  [
    "V93_TRIAL_PASS trial=",
    "V94_TRIAL_PASS trial="
  ],
  [
    "V93 recovered continuous original __start->filesystem init and next service open assertions",
    "V94 recovered continuous original __start->ES open and title query assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V94 source anchor missing or ambiguous")
        source=source.replace(old,new,1)
    old="ipc70_ram.read32(submit72_phys+4u)==(post92_active?2u:open84_active?1u:0u)&&"
    if source.count(old)!=4:
        raise ValueError("V94 prior synchronous result guard count differs")
    return source.replace(old,"ipc70_ram.read32(submit72_phys+4u)==(post94_active?3u:post92_active?2u:open84_active?1u:0u)&&")

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
