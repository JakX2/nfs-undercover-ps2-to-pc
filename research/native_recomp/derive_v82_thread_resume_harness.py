#!/usr/bin/env python3
"""V82: verify original scheduler-driven sleeping-thread resume."""
import argparse
from pathlib import Path
from derive_v81_ready_thread_harness import derive as previous

EDITS = [
  [
    "POST_OWNER=0x80529718u",
    "POST_OWNER=0x805265d4u"
  ],
  [
    " static unsigned ready81_disable=0,ready81_enter=0;",
    " static unsigned ready81_disable=0,ready81_enter=0;\n static unsigned resume82_wake_return=0,resume82_enable=0,resume82_select=0,resume82_load=0,resume82_stop=0;\n static uint32_t resume82_sleep_frame=0;"
  ],
  [
    "         const bool wake_helper=reply79_irq==1u&&wake80_enter==1u&&ready81_disable==0u&&",
    "         if(reply79_irq==1u&&ready81_enter==1u){\n           if(addr==INT_RESTORE&&ctx.lr==0x8052a5f8u){\n             check(resume82_wake_return==0u&&ctx.gpr[3]==0u&&\n                   ctx.mmu.read16(THREAD+712u)==1u&&\n                   ctx.mmu.read32(0x800000d4u)==IDLE_CONTEXT&&!(ctx.msr&0x8000u),\n                   \"V82 original nested scheduler did not preserve disabled wake state\");\n             ++resume82_wake_return;return true;\n           }\n           if(resume82_enable==1u&&\n              ((addr==INT_DISABLE&&ctx.lr==0x80529448u)||\n               (addr==INT_RESTORE&&ctx.lr==0x80529458u)))return true;\n           if(addr==POST_OWNER&&ctx.lr==0x8052a504u){\n             const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n                   ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n             const bool stack=ctx.gpr[1]==resume82_sleep_frame&&resume82_sleep_frame<sleep73_sp;\n             const bool queue=ctx.mmu.read32(sleep73_queue)==0u&&ctx.mmu.read32(sleep73_queue+4u)==0u;\n             const bool route=resume82_load==1u&&resume82_stop==0u&&ctx.gpr[3]==0u&&!(ctx.msr&0x8000u);\n             std::cout<<\"V82_RESUME_STATE running=\"<<running<<\" stack=\"<<stack\n                      <<\" queue=\"<<queue<<\" route=\"<<route<<std::endl;\n             check(running&&stack&&queue&&route,\"V82 original sleeping thread did not resume its saved stack\");\n             ++resume82_stop;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before restoring nested interrupt state\n           }\n         }\n         const bool wake_helper=reply79_irq==1u&&wake80_enter==1u&&ready81_disable==0u&&"
  ],
  [
    "           if(addr==POST_OWNER&&wake80_enter==1u){",
    "           if(addr==0x80529718u&&wake80_enter==1u&&ready81_enter==0u){"
  ],
  [
    "             ++ready81_enter;observed_stop_pc=ctx.pc;++post_stops;ctx.is_running=false;\n             throw ExceptionStop{}; // before scheduler selection",
    "             ++ready81_enter;return true; // allow genuine nested scheduler\n           }\n           if(ready81_enter==1u){\n             if(addr==0x80529434u&&ctx.lr==0x80526cb0u){\n               using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;\n               using H=undercover::wii::HollywoodIrq;\n               const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL).value_or(~0u);\n               const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG).value_or(~0u);\n               const bool clear=!(ctrl&(M::Y1|M::Y2))&&!(flags&H::IPC_PPC)&&\n                        !ipc70_bus.external_irq_level();\n               const bool ready=ctx.mmu.read16(THREAD+712u)==1u&&\n                        ctx.mmu.read32(sleep73_queue)==0u&&ctx.mmu.read32(sleep73_queue+4u)==0u;\n               const bool route=resume82_wake_return==1u&&resume82_enable==0u&&\n                        wake80_ctrl>0u&&wake80_flag>0u&&!(ctx.msr&0x8000u);\n               std::cout<<\"V82_REPLY_RETURN clear=\"<<clear<<\" ready=\"<<ready<<\" route=\"<<route<<std::endl;\n               check(clear&&ready&&route,\"V82 original reply IRQ did not finish after wake\");\n               ++resume82_enable;return true;\n             }\n             if(addr==0x80529940u){\n               check(resume82_enable==1u&&ctx.lr==0x80526cb4u&&!(ctx.msr&0x8000u),\n                     \"V82 second IRQ reschedule ABI differs\");\n               return true;\n             }\n             if(addr==0x80529718u){\n               check(resume82_enable==1u&&resume82_select==0u&&ctx.gpr[3]==0u&&!(ctx.msr&0x8000u),\n                     \"V82 second IRQ scheduler ABI differs\");\n               ++resume82_select;return true;\n             }\n             if(addr==0x80522928u){\n               check(ctx.lr==0x80529748u&&!(ctx.msr&0x8000u),\n                     \"V82 scheduler get-context ABI differs\");\n               return true;\n             }\n             if(addr==0x80529128u){\n               check(resume82_select==1u&&ctx.ctr==addr&&ctx.lr>=0x80529718u&&ctx.lr<0x80529940u,\n                     \"V82 original scheduler switch callback ABI differs\");\n               return true;\n             }\n             if(addr==0x805228ccu&&ctx.lr==0x8052991cu){\n               check(resume82_select==1u&&ctx.gpr[3]==THREAD&&!(ctx.msr&0x8000u),\n                     \"V82 scheduler did not set default thread context\");\n               return true;\n             }\n             if(addr==0x805229b4u){\n               const bool selected=resume82_select==1u&&ctx.lr==0x80529924u&&ctx.gpr[3]==THREAD;\n               const bool running=ctx.mmu.read16(THREAD+712u)==2u&&\n                    ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(0x800000e4u)==THREAD;\n               const bool saved=ctx.mmu.read32(THREAD+408u)==0x80529818u&&\n                    ctx.mmu.read32(THREAD+4u)<resume82_sleep_frame;\n               std::cout<<\"V82_LOAD_CONTEXT selected=\"<<selected<<\" running=\"<<running<<\" saved=\"<<saved<<std::endl;\n               check(selected&&running&&saved&&resume82_load==0u&&!(ctx.msr&0x8000u),\n                     \"V82 scheduler did not load the original saved sleeping context\");\n               ++resume82_load;return true;\n             }"
  ],
  [
    "     nwii::runtime::ready81_disable=nwii::runtime::ready81_enter=0;",
    "     nwii::runtime::ready81_disable=nwii::runtime::ready81_enter=0;\n     nwii::runtime::resume82_wake_return=nwii::runtime::resume82_enable=nwii::runtime::resume82_select=0;\n     nwii::runtime::resume82_load=nwii::runtime::resume82_stop=0;\n     nwii::runtime::resume82_sleep_frame=0;"
  ],
  [
    "       check(nwii::runtime::ready81_enter==1u&&nwii::runtime::ready81_disable==1u&&",
    "       check(nwii::runtime::resume82_wake_return==1u&&nwii::runtime::resume82_enable==1u&&\n             nwii::runtime::resume82_select==1u&&nwii::runtime::resume82_load==1u&&nwii::runtime::resume82_stop==1u&&\n             nwii::runtime::ready81_enter==1u&&nwii::runtime::ready81_disable==1u&&"
  ],
  [
    "V81_TRIAL_PASS trial=",
    "V82_TRIAL_PASS trial="
  ],
  [
    "V81 recovered continuous original __start->ready thread scheduler entry assertions",
    "V82 recovered continuous original __start->sleeping thread resumed assertions"
  ],
  [
    "     ++sleep73_select;return true;",
    "     resume82_sleep_frame=ctx.gpr[1];++sleep73_select;return true;"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V82 source anchor missing or ambiguous")
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
