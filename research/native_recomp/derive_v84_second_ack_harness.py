#!/usr/bin/env python3
"""V84: second original STM request ACK, persistent native IOS state."""
import argparse
from pathlib import Path
from derive_v83_second_open_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x80519944u",
    "POST_OWNER=0x8052a430u"
  ],
  [
    " static unsigned open83_restore=0,open83_free=0,open83_free_disable=0,open83_free_restore=0,open83_second=0;",
    " static unsigned open83_restore=0,open83_free=0,open83_free_disable=0,open83_free_restore=0,open83_second=0;\n static bool open84_active=false;\n static unsigned open84_ack=0;\n static uint32_t open84_first_phys=0;\n static undercover::wii::StmIos::Device open84_first_device=undercover::wii::StmIos::Device::None;"
  ],
  [
    "   check(stm70_entered&&stm70_open==0u&&ctx.lr==0x8052b090u&&ctx.gpr[4]==0u,",
    "   check(stm70_entered&&stm70_open==(open84_active?1u:0u)&&\n         ctx.lr==(open84_active?0x8052b0b8u:0x8052b090u)&&ctx.gpr[4]==0u,"
  ],
  [
    "   if(resume82_stop==1u){",
    "   if(resume82_stop==1u&&!open84_active){"
  ],
  [
    "     if(addr==POST_OWNER&&ctx.lr==0x8052b0b8u){",
    "     if(addr==0x80519944u&&ctx.lr==0x8052b0b8u){"
  ],
  [
    "       ++open83_second;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before executing the second original IOS_Open",
    "       ++open83_second;\n       open84_first_phys=submit72_phys;\n       open84_first_device=ipc70_bus.services().is_open(0u,I::Device::Immediate)?\n                            I::Device::Immediate:I::Device::Event;\n       check(!ipc70_bus.services().is_open(1u,I::Device::Immediate)&&\n             !ipc70_bus.services().is_open(1u,I::Device::Event)&&\n             ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.services().event_pending(),\n             \"V84 first IOS completion left unexpected descriptor or queued reply\");\n       // Only request-specific observation counters are reset.\n       // Preserve guest RAM, CPU, IOS bus and first scheduler evidence.\n       open84_active=true;submit72_active=false;\n       open71_profile=open71_alloc=open71_alloc_disable=open71_alloc_restore=0;\n       open71_flush=open71_sc=open71_submit=0;\n       open71_path_len=open71_flush_base=open71_flush_len=0;open71_flush_before=0;\n       submit72_flush=submit72_sc=submit72_disable=0;\n       submit72_message=submit72_x1=submit72_ack=0;\n       submit72_base=submit72_len=submit72_phys=0;submit72_flush_before=0;\n       sleep73_queue=sleep73_sp=0;sleep73_init=sleep73_entry=sleep73_disable=0;\n       stm70_open_entry(ctx);return true; // execute second original Open body"
  ],
  [
    "   if(addr==INT_DISABLE&&!irq76_dispatch){",
    "   if(addr==INT_DISABLE&&(!irq76_dispatch||open84_active)){"
  ],
  [
    "   if(!irq76_dispatch&&(addr==0x8051906cu||addr==0x8051905cu)){",
    "   if((!irq76_dispatch||open84_active)&&(addr==0x8051906cu||addr==0x8051905cu)){"
  ],
  [
    "           ipc70_bus.services().is_open(0u,device),\"native IOS did not accept the actual original device open\");",
    "           ipc70_bus.services().is_open(open84_active?1u:0u,device),\"native IOS did not accept the actual original device open\");"
  ],
  [
    "     sleep73_sp=ctx.gpr[1];++sleep73_entry;return true;",
    "     sleep73_sp=ctx.gpr[1];++sleep73_entry;\n     if(open84_active){\n       const bool first=ipc70_bus.services().is_open(0u,open84_first_device)&&\n                        open84_first_device!=device;\n       const bool second=ipc70_bus.services().is_open(1u,device)&&\n                         stm70_open==2u&&open71_submit==1u&&open71_alloc==1u;\n       const bool wire=submit72_phys==request&&ipc70_ram.read32(request)==IOS::Open&&\n                       ipc70_ram.read32(request+12u)==path;\n       const bool pending=ipc70_bus.services().queued_replies()==1u&&ipc70_bus.external_irq_level()&&\n                          !ipc70_bus.external_exception_pending(ctx.msr)&&!(ctrl&Mail::Y1);\n       const bool route=ctx.pc==POST_OWNER&&ctx.lr==0x805197d8u&&open84_ack==0u&&\n                         open83_second==1u&&resume82_stop==1u&&open84_first_phys!=0u;\n       std::cout<<\"V84_SECOND_ACK first=\"<<first<<\" second=\"<<second<<\" wire=\"<<wire\n                <<\" pending=\"<<pending<<\" route=\"<<route<<std::endl;\n       check(first&&second&&wire&&pending&&route,\"V84 second original IOS request ACK did not preserve first transaction\");\n       ++open84_ack;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before second original thread sleep body\n     }\n     return true;"
  ],
  [
    "     if(reply79_irq==1u&&irq76_ipc&&",
    "     if(!open84_active&&reply79_irq==1u&&irq76_ipc&&"
  ],
  [
    "     if(irq76_ipc&&((addr==undercover::wii::IosBus::IPC+4u)",
    "     if(!open84_active&&irq76_ipc&&((addr==undercover::wii::IosBus::IPC+4u)"
  ],
  [
    "     if(irq76_dispatch){\n       if(addr==undercover::wii::IosBus::PI_CAUSE)",
    "     if(irq76_dispatch&&!open84_active){\n       if(addr==undercover::wii::IosBus::PI_CAUSE)"
  ],
  [
    "   if(irq76_ipc){\n     using B=undercover::wii::IosBus;",
    "   if(irq76_ipc&&!open84_active){\n     using B=undercover::wii::IosBus;"
  ],
  [
    "     nwii::runtime::open83_free_restore=nwii::runtime::open83_second=0;",
    "     nwii::runtime::open83_free_restore=nwii::runtime::open83_second=0;\n     nwii::runtime::open84_active=false;nwii::runtime::open84_ack=0;\n     nwii::runtime::open84_first_phys=0;\n     nwii::runtime::open84_first_device=undercover::wii::StmIos::Device::None;"
  ],
  [
    "       check(nwii::runtime::open83_second==1u&&nwii::runtime::open83_free_restore==1u&&",
    "       check(nwii::runtime::open84_active&&nwii::runtime::open84_ack==1u&&\n             nwii::runtime::submit72_ack==1u&&nwii::runtime::stm70_open==2u&&\n             nwii::runtime::open83_second==1u&&nwii::runtime::open83_free_restore==1u&&"
  ],
  [
    "V83_TRIAL_PASS trial=",
    "V84_TRIAL_PASS trial="
  ],
  [
    "V83 recovered continuous original __start->second STM open assertions",
    "V84 recovered continuous original __start->second STM ACK assertions"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V84 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as out:
        out.write(result)

if __name__=="__main__":
    main()
