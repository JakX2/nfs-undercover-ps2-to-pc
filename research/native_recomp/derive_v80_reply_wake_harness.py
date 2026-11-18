#!/usr/bin/env python3
"""V80 candidate: continue the original IOS reply processor to OSWakeupThread.

Reuses the V77 authenticated fixture and V79 two-interrupt path. This is an
original-free harness transformation, not guest code or an IOS wakeup hook.
"""
import argparse
from pathlib import Path
from derive_v79_reply_harness import derive as derive_v79

EDITS = [
  [
    "POST_OWNER=0x805190c0u",
    "POST_OWNER=0x8052a51cu"
  ],
  [
    "static unsigned reply79_enable=0,reply79_resched=0,reply79_load=0,reply79_irq=0,reply79_entry=0;",
    "static unsigned reply79_enable=0,reply79_resched=0,reply79_load=0,reply79_irq=0,reply79_entry=0;\n static unsigned wake80_armmsg=0,wake80_invalidate=0,wake80_ctrl=0,wake80_flag=0,wake80_enter=0;\n static uint64_t wake80_invalidate_before=0;"
  ],
  [
    "           check(ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&!(ctx.msr&0x8000u),",
    "           const bool main_call=ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u;\n           const bool reply_call=reply79_entry==1u&&ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u;\n           check((main_call||reply_call)&&!(ctx.msr&0x8000u),"
  ],
  [
    "         if(addr==POST_OWNER){\n           using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;",
    "         if(addr==0x805190c0u){\n           using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;"
  ],
  [
    "           ++reply79_entry;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n           throw ExceptionStop{}; // before original reply processing body",
    "           ++reply79_entry;wake80_invalidate_before=ctx.guest_data_invalidate_count;\n           return true; // execute original reply processor, not an HLE response\n         }\n         if(reply79_entry==1u&&reply79_irq==1u){\n           if(addr==0x80522294u){\n             check(ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&!(ctx.msr&0x8000u)&&\n                   open71_ram(ctx.gpr[3],ctx.gpr[4])&&ctx.gpr[4]<=0x100000u,\n                   \"V80 original reply cache invalidation call ABI differs\");\n             // Track the real invalidate operation on the originating reply\n             // header, without fabricating a cache result or changing RAM.\n             const uint32_t lo=ctx.gpr[3]&0x3fffffffu;\n             const uint64_t end=uint64_t(lo)+ctx.gpr[4];\n             if(lo<=submit72_phys&&end>=uint64_t(submit72_phys)+12u)++wake80_invalidate;\n             return true;\n           }\n           if(addr==POST_OWNER){\n             using I=undercover::wii::StmIos;\n             const bool route=ctx.lr==0x805192d4u&&ctx.gpr[3]==sleep73_queue&&wake80_enter==0u&&!(ctx.msr&0x8000u);\n             const bool waiting=ctx.mmu.read16(THREAD+712u)==4u&&\n                 ctx.mmu.read32(sleep73_queue)==THREAD&&ctx.mmu.read32(sleep73_queue+4u)==THREAD&&\n                 ctx.mmu.read32(THREAD+732u)==sleep73_queue;\n             const bool wire=ipc70_ram.read32(submit72_phys)==I::Reply&&\n                 ipc70_ram.read32(submit72_phys+4u)==0u&&ipc70_ram.read32(submit72_phys+8u)==I::Open;\n             const bool consumed=wake80_armmsg>0u&&wake80_invalidate>0u&&\n                 ctx.guest_data_invalidate_count>wake80_invalidate_before;\n             std::cout<<\"V80_WAKE_ENTRY route=\"<<route<<\" waiting=\"<<waiting\n                      <<\" wire=\"<<wire<<\" consumed=\"<<consumed<<std::endl;\n             check(route&&waiting&&wire&&consumed,\"V80 original reply did not reach the authentic waiting queue wakeup\");\n             ++wake80_enter;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before original OSWakeupThread\n           }\n           // Source-authenticated helper dependencies within the reply body.\n           // Preserve the original calls and fail closed on other functions.\n           if(addr==0x80522af4u||addr==0x805228ccu||addr==0x8051ad3cu||addr==0x8051b070u){\n             check(ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&!(ctx.msr&0x8000u),\n                   \"V80 reply helper callsite differs\");\n             return true;\n           }"
  ],
  [
    "     const auto result=ipc70_bus.read32(addr);\n     if(irq76_ipc&&",
    "     const auto result=ipc70_bus.read32(addr);\n     if(reply79_irq==1u&&irq76_ipc&&\n        (addr==undercover::wii::IosBus::IPC+undercover::wii::IpcMailbox::ARMMSG||\n         addr==undercover::wii::IosBus::MIRROR+undercover::wii::IpcMailbox::ARMMSG)){\n       check(result&&*result==submit72_phys,\"V80 original ARMMSG read selected a different request\");\n       ++wake80_armmsg;\n     }\n     if(irq76_ipc&&"
  ],
  [
    "       if(value&M::Y2)++ack77_ctrl;",
    "       if(reply79_irq==1u){\n         if(value&M::Y1)++wake80_ctrl;\n       }else if(value&M::Y2)++ack77_ctrl;"
  ],
  [
    "       check(value&H::IPC_PPC,\"original ACK flag write lacked IPC W1C bit\");++ack77_flag;",
    "       check(value&H::IPC_PPC,\"original IRQ flag write lacked IPC W1C bit\");\n       if(reply79_irq==1u)++wake80_flag;else ++ack77_flag;"
  ],
  [
    "     nwii::runtime::reply79_irq=nwii::runtime::reply79_entry=0;",
    "     nwii::runtime::reply79_irq=nwii::runtime::reply79_entry=0;\n     nwii::runtime::wake80_armmsg=nwii::runtime::wake80_invalidate=nwii::runtime::wake80_ctrl=0;\n     nwii::runtime::wake80_flag=nwii::runtime::wake80_enter=0;\n     nwii::runtime::wake80_invalidate_before=0;"
  ],
  [
    "       check(nwii::runtime::reply79_enable==1u&&nwii::runtime::reply79_resched==1u&&",
    "       check(nwii::runtime::wake80_enter==1u&&nwii::runtime::wake80_armmsg>0u&&\n             nwii::runtime::wake80_invalidate>0u&&\n             nwii::runtime::reply79_enable==1u&&nwii::runtime::reply79_resched==1u&&"
  ],
  [
    "V79_TRIAL_PASS trial=",
    "V80_TRIAL_PASS trial="
  ],
  [
    "V79 recovered continuous original __start->reply processor entry assertions",
    "V80 recovered continuous original __start->reply wake entry assertions"
  ]
]

def derive(source):
    source = derive_v79(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V80 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x", encoding="utf-8") as f:
        f.write(result)

if __name__ == "__main__":
    main()
