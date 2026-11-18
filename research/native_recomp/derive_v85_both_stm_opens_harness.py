#!/usr/bin/env python3
"""V85: complete both original STM opens in one guest startup."""
import argparse
from pathlib import Path
from derive_v84_second_ack_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x8052a430u",
    "POST_OWNER=0x805265acu"
  ],
  [
    " static unsigned open84_ack=0;",
    " static unsigned open84_ack=0;\n static unsigned open85_complete=0;"
  ],
  [
    "   if(resume82_stop==1u&&!open84_active){",
    "   if(resume82_stop==1u&&(!open84_active||open84_ack==1u)){"
  ],
  [
    "     if(addr==0x80519944u&&ctx.lr==0x8052b0b8u){",
    "     if(open84_active&&addr==POST_OWNER&&ctx.lr==0x8052b0d4u){\n       using M=undercover::wii::IpcMailbox;using B=undercover::wii::IosBus;\n       using H=undercover::wii::HollywoodIrq;\n       const auto other=open84_first_device==I::Device::Immediate?I::Device::Event:I::Device::Immediate;\n       const bool descriptors=ipc70_bus.services().is_open(0u,open84_first_device)&&\n                             ipc70_bus.services().is_open(1u,other);\n       const bool idle=ipc70_bus.services().queued_replies()==0u&&!ipc70_bus.services().event_pending()&&\n            !ipc70_bus.external_irq_level()&&\n            (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u)&(M::X1|M::Y1|M::Y2))==0u&&\n            (ipc70_bus.read32(B::IPC+H::PPC_FLAG).value_or(~0u)&H::IPC_PPC)==0u;\n       const bool cleanup=open83_restore==1u&&open83_free==1u&&open83_free_disable==1u&&\n                          open83_free_restore==1u&&open84_ack==1u&&open83_second==1u&&resume82_stop==1u;\n       const bool abi=ctx.gpr[1]==open71_stack&&ctx.msr==ipc69_msr&&\n                      ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD&&\n                      ctx.mmu.read16(THREAD+712u)==2u;\n       const bool route=ctx.pc==POST_OWNER&&open85_complete==0u&&stm70_open==2u;\n       std::cout<<\"V85_STM_OPENS descriptors=\"<<descriptors<<\" idle=\"<<idle<<\" cleanup=\"<<cleanup\n                <<\" abi=\"<<abi<<\" route=\"<<route<<std::endl;\n       check(descriptors&&idle&&cleanup&&abi&&route,\"V85 both original STM opens did not return to initialized STM\");\n       ++open85_complete;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before original STM post-open interrupt disable\n     }\n     if(!open84_active&&addr==0x80519944u&&ctx.lr==0x8052b0b8u){"
  ],
  [
    "   if(addr==INT_DISABLE&&(!irq76_dispatch||open84_active)){",
    "   if(addr==INT_DISABLE&&(!irq76_dispatch||(open84_active&&open84_ack==0u))){"
  ],
  [
    "   if((!irq76_dispatch||open84_active)&&(addr==0x8051906cu||addr==0x8051905cu)){",
    "   if((!irq76_dispatch||(open84_active&&open84_ack==0u))&&(addr==0x8051906cu||addr==0x8051905cu)){"
  ],
  [
    "       const bool route=ctx.pc==POST_OWNER&&ctx.lr==0x805197d8u&&open84_ack==0u&&",
    "       const bool route=ctx.pc==0x8052a430u&&ctx.lr==0x805197d8u&&open84_ack==0u&&"
  ],
  [
    "       ++open84_ack;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n       throw ExceptionStop{}; // before second original thread sleep body",
    "       check(open83_restore==1u&&open83_free==1u&&open83_free_disable==1u&&open83_free_restore==1u&&\n             resume82_load==1u&&resume82_stop==1u&&reply79_irq==1u&&ack77_reply==1u&&\n             wake80_enter==1u&&ready81_enter==1u&&sched74_irq==1u,\n             \"V85 first transaction evidence missing before second sleep\");\n       ++open84_ack;\n       // Reset observers for the next transaction, not CPU, RAM, services,\n       // interrupt latches, descriptor table or guest scheduler state.\n       sleep73_select=0;\n       sched74_get=sched74_save=sched74_set=sched74_enable=0;\n       sched74_callback=sched74_irq=sched74_msr=sched74_resume=0;\n       vector75_entry=vector75_handler=0;\n       irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n       ack77_ctrl=ack77_flag=ack77_read=ack77_reply=0;\n       reply79_enable=reply79_resched=reply79_load=reply79_irq=reply79_entry=0;\n       wake80_armmsg=wake80_invalidate=wake80_ctrl=wake80_flag=wake80_enter=0;\n       wake80_invalidate_before=0;ready81_disable=ready81_enter=0;\n       resume82_wake_return=resume82_enable=resume82_select=resume82_load=resume82_stop=0;\n       resume82_sleep_frame=0;\n       resume82_idle_load=resume82_idle_rfi=resume82_idle_disable=resume82_idle_clear=0;\n       open83_restore=open83_free=open83_free_disable=open83_free_restore=0;"
  ],
  [
    "     if(!open84_active&&reply79_irq==1u&&irq76_ipc&&",
    "     if((!open84_active||open84_ack==1u)&&reply79_irq==1u&&irq76_ipc&&"
  ],
  [
    "     if(!open84_active&&irq76_ipc&&((addr==undercover::wii::IosBus::IPC+4u)",
    "     if((!open84_active||open84_ack==1u)&&irq76_ipc&&((addr==undercover::wii::IosBus::IPC+4u)"
  ],
  [
    "     if(irq76_dispatch&&!open84_active){",
    "     if(irq76_dispatch&&(!open84_active||open84_ack==1u)){"
  ],
  [
    "   if(irq76_ipc&&!open84_active){",
    "   if(irq76_ipc&&(!open84_active||open84_ack==1u)){"
  ],
  [
    "     nwii::runtime::open84_active=false;nwii::runtime::open84_ack=0;",
    "     nwii::runtime::open84_active=false;nwii::runtime::open84_ack=0;nwii::runtime::open85_complete=0;"
  ],
  [
    "       check(nwii::runtime::open84_active&&nwii::runtime::open84_ack==1u&&",
    "       check(nwii::runtime::open85_complete==1u&&nwii::runtime::open84_active&&nwii::runtime::open84_ack==1u&&"
  ],
  [
    "V84_TRIAL_PASS trial=",
    "V85_TRIAL_PASS trial="
  ],
  [
    "V84 recovered continuous original __start->second STM ACK assertions",
    "V85 recovered continuous original __start->both STM opens completed assertions"
  ]
]

def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:
            raise ValueError("V85 source anchor missing or ambiguous")
        source=source.replace(old,new,1)
    old="ipc70_ram.read32(submit72_phys+4u)==0u&&"
    if source.count(old)!=4:
        raise ValueError("V85 original reply result guard count differs")
    return source.replace(old,"ipc70_ram.read32(submit72_phys+4u)==(open84_active?1u:0u)&&")

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
