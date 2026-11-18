#!/usr/bin/env python3
"""V92: original filesystem open, synchronous IRQs and return to initializer."""
import argparse
from pathlib import Path
from derive_v91_resource_open_harness import derive as previous
EDITS = [
  [
    "POST_OWNER=0x80519944u",
    "POST_OWNER=0x8051908cu"
  ],
  [
    " static bool open84_active=false;",
    " static bool open84_active=false;\n static bool post92_active=false;\n static unsigned post92_complete=0;\n static uint32_t post92_mode=0,post92_event_command=0,post92_event_result=0,post92_event_output=0;"
  ],
  [
    "ctx.mmu.read32(cached+16u)==0u;",
    "ctx.mmu.read32(cached+16u)==(post92_active?post92_mode:0u);"
  ],
  [
    "     if(addr==POST_OWNER&&ctx.lr==0x804f0d68u){",
    "     if(addr==0x80519944u&&ctx.lr==0x804f0d68u){"
  ],
  [
    "       ++post91_open;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original next IOS_Open",
    "       check(device==1u&&!post92_active&&open85_complete==1u&&async88_rfi==1u&&\n             open83_free_restore==1u&&resume82_stop==1u&&reply79_irq==1u,\n             \"V92 first filesystem open did not inherit completed STM transactions\");\n       // The device backend has been explicitly mounted at trial start.\n       // Neither the original CPU nor RAM nor device state is reset here.\n       post92_mode=ctx.gpr[4];post92_active=true;++post91_open;\n       post92_event_command=ipc70_ram.read32(async87_request);\n       post92_event_result=ipc70_ram.read32(async87_request+4u);\n       post92_event_output=ipc70_ram.read32(async86_out);\n       stm70_path=ctx.gpr[3];open71_path_len=uint32_t(path.size()+1u);open71_stack=ctx.gpr[1];\n       submit72_active=false;\n       open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n       open71_flush=open71_sc=open71_submit=0;\n       open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n       submit72_flush=submit72_sc=submit72_disable=0;\n       submit72_message=submit72_x1=submit72_ack=0;\n       submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n       sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=sleep73_select=0;\n       sched74_get=sched74_save=sched74_set=sched74_enable=0;\n       sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n       vector75_entry=vector75_handler=0;\n       irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n       ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n       reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n       wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n       wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n       resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n       resume82_sleep_frame=0;\n       resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n       open83_restore=open83_free=open83_free_disable=open83_free_restore=0;\n       return true; // execute genuine third IOS_Open"
  ],
  [
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(async88_rfi==1u)return post89_trace(addr,ctx);\n   if(async87_deferred==1u)return async88_trace(addr,ctx);",
    " static bool submit72_trace(uint32_t addr,CPUContext&ctx){\n   if(post92_active&&addr==POST_OWNER&&ctx.lr==0x804f0dc4u){\n     using I=undercover::wii::StmIos;using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n     const bool route=post92_complete==0u&&open71_submit==1u&&submit72_ack==1u&&\n          resume82_stop==1u&&open83_restore==1u&&open83_free==1u&&open83_free_restore==1u;\n     const bool result=ctx.mmu.read32(R13-16768u)==2u&&ipc70_bus.services().is_open(2u,I::Device::Fs);\n     const bool descriptors=ipc70_bus.services().is_open(async86_fd,I::Device::Event)&&\n                            ipc70_bus.services().is_open(1u-async86_fd,I::Device::Immediate);\n     const bool deferred=ipc70_bus.services().event_pending()&&\n         ipc70_ram.read32(async87_request)==post92_event_command&&\n         ipc70_ram.read32(async87_request+4u)==post92_event_result&&\n         ipc70_ram.read32(async86_out)==post92_event_output&&submit72_phys!=async87_request;\n     const bool abi=ctx.msr==ipc69_msr&&ctx.gpr[1]==open71_stack&&ctx.gpr[2]==ipc69_gprs[2]&&\n         ctx.gpr[13]==ipc69_gprs[13]&&ctx.mmu.read16(THREAD+712u)==2u&&\n         ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n     const bool idle=!ipc70_bus.external_irq_level()&&ipc70_bus.services().queued_replies()==0u&&\n         (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u)&(M::X1|M::Y1|M::Y2))==0u;\n     const bool bounds=ctx.gpr[3]>=post91_buffer_lo&&ctx.gpr[3]<=post91_buffer_hi;\n     std::cout<<\"V92_FS_RETURN route=\"<<route<<\" result=\"<<result<<\" descriptors=\"<<descriptors\n              <<\" deferred=\"<<deferred<<\" abi=\"<<abi<<\" idle=\"<<idle<<\" bounds=\"<<bounds<<std::endl;\n     check(route&&result&&descriptors&&deferred&&abi&&idle&&bounds,\"V92 native filesystem open did not return to original resource initializer\");\n     ++post92_complete;post90_target=addr;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n     throw ExceptionStop{}; // before original next buffer reservation\n   }\n   if(post92_active&&!submit72_active){\n     check(open71_trace(addr,ctx),\"V92 unexpected filesystem open wrapper dependency\");return true;\n   }\n   if(async88_rfi==1u&&!post92_active)return post89_trace(addr,ctx);\n   if(async87_deferred==1u&&!post92_active)return async88_trace(addr,ctx);"
  ],
  [
    "   if(open85_complete==1u){",
    "   if(open85_complete==1u&&!post92_active){"
  ],
  [
    "     check(path==(stm70_path&0x3fffffffu)&&mode==0u&&ipc70_ram.valid(path,open71_path_len),",
    "     check(path==(stm70_path&0x3fffffffu)&&mode==(post92_active?post92_mode:0u)&&ipc70_ram.valid(path,open71_path_len),"
  ],
  [
    "     const auto device=name==\"/dev/stm/immediate\"?IOS::Device::Immediate:IOS::Device::Event;\n     check(name==\"/dev/stm/immediate\"||name==\"/dev/stm/eventhook\",\"actual wire pathname not a documented STM device\");\n     check(ipc70_bus.tick()==IOS::Pump::Ack&&ipc70_bus.services().queued_replies()==1u&&\n           ipc70_bus.services().is_open(open84_active?1u:0u,device),\"native IOS did not accept the actual original device open\");",
    "     const auto device=post92_active?IOS::Device::Fs:name==\"/dev/stm/immediate\"?IOS::Device::Immediate:IOS::Device::Event;\n     check(post92_active?name==\"/dev/fs\":(name==\"/dev/stm/immediate\"||name==\"/dev/stm/eventhook\"),\n           \"actual wire pathname not the expected documented IOS device\");\n     check(ipc70_bus.tick()==IOS::Pump::Ack&&ipc70_bus.services().queued_replies()==1u&&\n           ipc70_bus.services().is_open(post92_active?2u:open84_active?1u:0u,device),\"native IOS did not accept the actual original device open\");\n     if(post92_active){\n       const bool prior=ipc70_bus.services().is_open(async86_fd,IOS::Device::Event)&&\n            ipc70_bus.services().is_open(1u-async86_fd,IOS::Device::Immediate);\n       const bool event=ipc70_bus.services().event_pending()&&request!=async87_request&&\n            ipc70_ram.read32(async87_request)==post92_event_command&&\n            ipc70_ram.read32(async86_out)==post92_event_output;\n       std::cout<<\"V92_FS_ACK prior=\"<<prior<<\" event=\"<<event<<std::endl;\n       check(prior&&event,\"V92 filesystem ACK damaged the outstanding STM event\");\n     }"
  ],
  [
    "     if(open84_active){\n       const bool first=ipc70_bus.services().is_open(0u,open84_first_device)&&",
    "     if(open84_active&&!post92_active){\n       const bool first=ipc70_bus.services().is_open(0u,open84_first_device)&&"
  ],
  [
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu&&async86_submit==1u){",
    "  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu&&async86_submit==1u&&!post92_active){"
  ],
  [
    "  if(async87_deferred==1u){\n    using namespace undercover::wii;",
    "  if(async87_deferred==1u&&!post92_active){\n    using namespace undercover::wii;"
  ],
  [
    "uint32_t HW_Reg_Read32(uint32_t addr){\n   if(async87_deferred==1u){",
    "uint32_t HW_Reg_Read32(uint32_t addr){\n   if(async87_deferred==1u&&!post92_active){"
  ],
  [
    "   if(async86_submit==1u){\n     const auto value=ipc70_bus.read32(addr);",
    "   if(async86_submit==1u&&!post92_active){\n     const auto value=ipc70_bus.read32(addr);"
  ],
  [
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(async87_deferred==1u){",
    "void HW_Reg_Write32(uint32_t addr,uint32_t value){\n   if(async87_deferred==1u&&!post92_active){"
  ],
  [
    "   if(async86_submit==1u){\n     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n     const bool msg=",
    "   if(async86_submit==1u&&!post92_active){\n     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n     const bool msg="
  ],
  [
    "     nwii::runtime::ipc70_ram.cpu=&c;nwii::runtime::ipc70_bus.reset();",
    "     nwii::runtime::ipc70_ram.cpu=&c;nwii::runtime::ipc70_bus.reset();\n     check(nwii::runtime::ipc70_bus.services().mount_filesystem(std::make_shared<undercover::wii::GuestFiles>()),\n           \"V92 explicit empty native guest filesystem mount rejected\");\n     nwii::runtime::post92_active=false;nwii::runtime::post92_complete=0;\n     nwii::runtime::post92_mode=nwii::runtime::post92_event_command=nwii::runtime::post92_event_result=nwii::runtime::post92_event_output=0;"
  ],
  [
    "       check(nwii::runtime::post91_open==1u&&",
    "       check(nwii::runtime::post92_complete==1u&&nwii::runtime::post91_open==1u&&"
  ],
  [
    "V91_TRIAL_PASS trial=",
    "V92_TRIAL_PASS trial="
  ],
  [
    "V91 recovered continuous original __start->next IOS resource open assertions",
    "V92 recovered continuous original __start->filesystem open return assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V92 source anchor missing or ambiguous")
        source=source.replace(old,new,1)
    old="ipc70_ram.read32(submit72_phys+4u)==(open84_active?1u:0u)&&"
    if source.count(old)!=4:
        raise ValueError("V92 prior synchronous result guard count differs")
    return source.replace(old,"ipc70_ram.read32(submit72_phys+4u)==(post92_active?2u:open84_active?1u:0u)&&")

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
