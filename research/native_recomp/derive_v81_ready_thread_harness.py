#!/usr/bin/env python3
"""V81: original wake transition; no host thread-state writes."""
import argparse
from pathlib import Path
from derive_v80_reply_wake_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x8052a51cu",
    "POST_OWNER=0x80529718u"
  ],
  [
    " static uint64_t wake80_invalidate_before=0;",
    " static uint64_t wake80_invalidate_before=0;\n static unsigned ready81_disable=0,ready81_enter=0;"
  ],
  [
    "         const bool enable_helper=ack77_reply==1u&&reply79_irq==0u&&",
    "         const bool wake_helper=reply79_irq==1u&&wake80_enter==1u&&ready81_disable==0u&&\n                                   addr==INT_DISABLE&&ctx.lr==0x8052a538u;\n         if(wake_helper){\n           check(!(ctx.msr&0x8000u),\"V81 wake nested disable entered with interrupts enabled\");\n           ++ready81_disable;return true;\n         }\n         const bool enable_helper=ack77_reply==1u&&reply79_irq==0u&&"
  ],
  [
    "           if(addr==POST_OWNER){\n             using I=undercover::wii::StmIos;",
    "           if(addr==0x8052a51cu){\n             using I=undercover::wii::StmIos;"
  ],
  [
    "             ++wake80_enter;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before original OSWakeupThread",
    "             ++wake80_enter;return true; // execute genuine wake routine\n           }\n           if(addr==POST_OWNER&&wake80_enter==1u){\n             const auto queue=ctx.mmu.read32(THREAD+732u);\n             const bool route=ctx.lr==0x8052a5f0u&&ctx.gpr[3]==0u&&\n                  ready81_disable==1u&&ready81_enter==0u&&!(ctx.msr&0x8000u);\n             const bool drained=ctx.mmu.read32(sleep73_queue)==0u&&\n                  ctx.mmu.read32(sleep73_queue+4u)==0u;\n             const bool ready=ctx.mmu.read16(THREAD+712u)==1u;\n             const bool enrolled=queue!=sleep73_queue&&queue!=0u&&!(queue&3u)&&\n                  open71_ram(queue,8u)&&ctx.mmu.read32(queue)==THREAD&&\n                  ctx.mmu.read32(queue+4u)==THREAD&&\n                  ctx.mmu.read32(THREAD+736u)==0u&&ctx.mmu.read32(THREAD+740u)==0u;\n             const bool still_idle=ctx.mmu.read32(0x800000d4u)==IDLE_CONTEXT;\n             std::cout<<\"V81_READY_STATE route=\"<<route<<\" drained=\"<<drained\n                      <<\" ready=\"<<ready<<\" enrolled=\"<<enrolled<<\" idle=\"<<still_idle<<std::endl;\n             check(route&&drained&&ready&&enrolled&&still_idle,\n                   \"V81 original wake did not transfer the waiting thread to ready queue\");\n             ++ready81_enter;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before scheduler selection"
  ],
  [
    "     nwii::runtime::wake80_invalidate_before=0;",
    "     nwii::runtime::wake80_invalidate_before=0;\n     nwii::runtime::ready81_disable=nwii::runtime::ready81_enter=0;"
  ],
  [
    "       check(nwii::runtime::wake80_enter==1u&&nwii::runtime::wake80_armmsg>0u&&",
    "       check(nwii::runtime::ready81_enter==1u&&nwii::runtime::ready81_disable==1u&&\n             nwii::runtime::wake80_enter==1u&&nwii::runtime::wake80_armmsg>0u&&"
  ],
  [
    "V80_TRIAL_PASS trial=",
    "V81_TRIAL_PASS trial="
  ],
  [
    "V80 recovered continuous original __start->reply wake entry assertions",
    "V81 recovered continuous original __start->ready thread scheduler entry assertions"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V81 source anchor missing or ambiguous")
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
