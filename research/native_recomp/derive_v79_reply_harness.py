#!/usr/bin/env python3
"""Derive V79's original-free harness from V77 with exact, fail-closed anchors.

The owner DOL, fixture, AOT generation and geometry checks remain V77's.
No original PPC or translated code is embedded here.
"""
import argparse
from pathlib import Path

EDITS = [
  [
    "POST_OWNER=0x80529434u",
    "POST_OWNER=0x805190c0u"
  ],
  [
    "static unsigned ack77_ctrl=0,ack77_flag=0,ack77_read=0,ack77_reply=0;",
    "static unsigned ack77_ctrl=0,ack77_flag=0,ack77_read=0,ack77_reply=0;\n static unsigned reply79_enable=0,reply79_resched=0,reply79_load=0,reply79_irq=0,reply79_entry=0;"
  ],
  [
    "         check(irq76_disable==1u&&ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u,",
    "         const bool disable_helper=ctx.lr>=0x805293f8u&&ctx.lr<0x80529434u;\n         const bool enable_helper=ack77_reply==1u&&reply79_irq==0u&&\n                                  (ctx.lr==0x80529448u||ctx.lr==0x80529458u);\n         check(irq76_disable==1u&&(disable_helper||enable_helper),"
  ],
  [
    "         const bool active=ipc70_bus.external_irq_level()&&ipc70_ram.read32(submit72_phys)==IOS::Open&&\n             (ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u)&Mail::Y2);",
    "         const auto control=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u);\n         const bool active=ipc70_bus.external_irq_level()&&\n             ipc70_ram.read32(submit72_phys)==(reply79_irq?IOS::Reply:IOS::Open)&&\n             (control&(Mail::Y1|Mail::Y2))==(reply79_irq?Mail::Y1:Mail::Y2);"
  ],
  [
    "         if(addr==POST_OWNER){",
    "         if(addr==POST_OWNER){\n           using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n           using I=undercover::wii::StmIos;\n           const bool route=reply79_irq==1u&&reply79_entry==0u&&irq76_ipc==1u&&ctx.lr==0x80519354u;\n           const bool wire=ipc70_bus.read32(B::IPC+M::ARMMSG)==submit72_phys&&\n                 ipc70_ram.read32(submit72_phys)==I::Reply&&ipc70_ram.read32(submit72_phys+4u)==0u&&\n                 ipc70_ram.read32(submit72_phys+8u)==I::Open;\n           const bool waiting=ctx.mmu.read16(THREAD+712u)==4u&&ctx.mmu.read32(sleep73_queue)==THREAD;\n           const bool pending=ipc70_bus.external_irq_level()&&\n                 (ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(0u)&(M::Y1|M::Y2))==M::Y1&&!(ctx.msr&0x8000u);\n           std::cout<<\"V79_REPLY_ENTRY route=\"<<route<<\" wire=\"<<wire<<\" waiting=\"<<waiting<<\" pending=\"<<pending<<std::endl;\n           check(route&&wire&&waiting&&pending,\"V79 original IPC handler did not enter reply processor\");\n           ++reply79_entry;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n           throw ExceptionStop{}; // before original reply processing body\n         }\n         if(addr==0x80529434u){"
  ],
  [
    "           ++ack77_reply;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n           throw ExceptionStop{}; // stop before scheduler enable / original interrupt return",
    "           ++ack77_reply;++reply79_enable;return true; // execute original scheduler enable\n         }\n         if(ack77_reply==1u&&reply79_irq==0u){\n           if(addr==0x80529940u){\n             check(reply79_enable==1u&&reply79_resched==0u&&ctx.lr==0x80526cb4u&&!(ctx.msr&0x8000u),\n                   \"V79 original reschedule entry differs\");\n             ++reply79_resched;return true;\n           }\n           if(addr==0x80529718u){\n             check(reply79_resched==1u&&reply79_load==0u&&ctx.gpr[3]==0u&&\n                   !(ctx.msr&0x8000u),\n                   \"V79 reschedule selected unexpected scheduler state\");\n             return true;\n           }\n           if(addr==0x80522928u){\n             check(reply79_resched==1u&&ctx.lr==0x80529748u&&!(ctx.msr&0x8000u),\n                   \"V79 scheduler context getter call differs\");\n             return true;\n           }\n           if(addr==0x805229b4u){\n             check(reply79_resched==1u&&reply79_load==0u&&ctx.gpr[3]==IDLE_CONTEXT&&\n                   (ctx.lr==0x80526cbcu||ctx.lr==0x80526cc4u)&&!(ctx.msr&0x8000u),\n                   \"V79 original interrupt context-load ABI differs\");\n             ++reply79_load;return true;\n           }"
  ],
  [
    "bool process_pending_callbacks(CPUContext& ctx){\n  if(!sched74_enable||sched74_irq)return false;",
    "bool process_pending_callbacks(CPUContext& ctx){\n  if(ack77_reply==1u&&reply79_irq==0u){\n    using namespace undercover::wii;\n    if(!ipc70_bus.external_exception_pending(ctx.msr))return false;\n    const bool resume=reply79_load==1u&&ctx.pc==sched74_resume&&ctx.msr==vector75_srr1;\n    const bool regs=ctx.gpr==vector75_gprs&&ctx.lr==vector75_lr&&ctx.ctr==vector75_ctr&&ctx.xer==vector75_xer;\n    const bool waiting=ctx.mmu.read16(THREAD+712u)==4u&&ctx.mmu.read32(sleep73_queue)==THREAD;\n    std::cout<<\"V79_RFI_STATE resume=\"<<resume<<\" regs=\"<<regs<<\" waiting=\"<<waiting<<std::endl;\n    check(resume&&regs&&waiting,\"V79 original context return did not restore interrupted idle CPU state\");\n    check(enter_external_irq(ctx,ipc70_bus,irq74_vector,true)==ExternalEntry::Entered,\n          \"V79 pending IOS reply did not enter installed external exception\");\n    check(ctx.pc==0x80000500u&&ctx.srr0==sched74_resume&&ctx.srr1==vector75_srr1,\n          \"V79 second exception entry lost exact resumed PC or status\");\n    ++reply79_irq;\n    // Reset only per-interrupt observation counters, never guest/device state.\n    vector75_entry=vector75_handler=0;\n    irq76_dispatch=irq76_ipc=irq76_time=irq76_disable=irq76_pi_cause=irq76_pi_mask=0;\n    return true;\n  }\n  if(!sched74_enable||sched74_irq)return false;"
  ],
  [
    "     nwii::runtime::ack77_ctrl=nwii::runtime::ack77_flag=nwii::runtime::ack77_read=nwii::runtime::ack77_reply=0;",
    "     nwii::runtime::ack77_ctrl=nwii::runtime::ack77_flag=nwii::runtime::ack77_read=nwii::runtime::ack77_reply=0;\n     nwii::runtime::reply79_enable=nwii::runtime::reply79_resched=nwii::runtime::reply79_load=0;\n     nwii::runtime::reply79_irq=nwii::runtime::reply79_entry=0;"
  ],
  [
    "       check(nwii::runtime::ack77_reply==1u&&nwii::runtime::irq76_ipc==1u&&",
    "       check(nwii::runtime::reply79_enable==1u&&nwii::runtime::reply79_resched==1u&&\n             nwii::runtime::reply79_load==1u&&nwii::runtime::reply79_irq==1u&&nwii::runtime::reply79_entry==1u&&\n             nwii::runtime::ack77_reply==1u&&nwii::runtime::irq76_ipc==1u&&"
  ],
  [
    "V77_TRIAL_PASS trial=",
    "V79_TRIAL_PASS trial="
  ],
  [
    "V77 recovered continuous original __start->ACK return and IOS reply assertions",
    "V79 recovered continuous original __start->reply processor entry assertions"
  ],
  [
    "         check(false,\"unexpected original IPC ACK-only path dependency\");",
    "         if(addr>=0x80400000u&&addr<0x80600000u&&ctx.lr>=0x80400000u&&ctx.lr<0x80600000u)\n           std::cout<<\"V79_DEPENDENCY pc=\"<<std::hex<<addr<<\" lr=\"<<ctx.lr<<std::dec\n                    <<\" phase=\"<<reply79_irq<<\" enable=\"<<reply79_enable<<\" resched=\"<<reply79_resched<<\" load=\"<<reply79_load<<std::endl;\n         check(false,\"unexpected original IPC ACK-only path dependency\");"
  ]
]

def derive(source):
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V79 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
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
