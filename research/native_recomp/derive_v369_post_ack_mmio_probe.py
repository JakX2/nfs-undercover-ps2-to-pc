#!/usr/bin/env python3
"""V369: bounded read-only original Wii MMIO census after the genuine IOS ACK.

Unlike the older V340 first-writes census, arm only after a real native
queued IOS completion exists and Broadway X1 has been consumed. Report
known public register classes, never the original address or write value.
No MMIO write, native IOS tick, guest mutation or IRQ entry is added.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void HW_Reg_Write32(uint32_t addr,uint32_t value){"
PRIOR="V367_NAND_IRQ_MASK n="
MARKER="V369_POST_ACK_MMIO n="
INJECTION=(
    "\n  // V369: privacy-safe bounded post-ACK MMIO register census.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u&&\n"
    "     ipc70_bus.services().queued_replies()>0u&&\n"
    "     !ipc70_bus.pending_native_ios_request()){\n"
    "    static unsigned v369_count=0u;\n"
    "    if(v369_count<32u){\n"
    "      using B=undercover::wii::IosBus;\n"
    "      using M=undercover::wii::IpcMailbox;\n"
    "      using H=undercover::wii::HollywoodIrq;\n"
    "      const bool pi=addr==B::PI_MASK;\n"
    "      const bool mask=addr==B::IPC+H::PPC_MASK||addr==B::MIRROR+H::PPC_MASK;\n"
    "      const bool flag=addr==B::IPC+H::PPC_FLAG||addr==B::MIRROR+H::PPC_FLAG;\n"
    "      const bool ctrl=addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL;\n"
    "      const bool msg=addr==B::IPC+M::PPCMSG||addr==B::MIRROR+M::PPCMSG;\n"
    "      const unsigned kind=pi?1u:mask?2u:flag?3u:ctrl?4u:msg?5u:0u;\n"
    "      ++v369_count;\n"
    '      std::cout<<"V369_POST_ACK_MMIO n="<<v369_count\n'
    '               <<" kind="<<kind\n'
    '               <<" legacy="<<unsigned(ipc69_active)\n'
    '               <<" readable="<<unsigned(ipc70_bus.read32(addr).has_value())\n'
    '               <<" irq="<<unsigned(ipc70_bus.external_irq_level())\n'
    "               <<std::endl;\n"
    "    }\n"
    "  }\n"
)

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        "unexpected IPC mask MMIO write" not in source or
        "ipc69_active" not in source or
        "ipc70_bus.services().queued_replies()" not in source or
        MARKER in source):
        raise ValueError("V369 post-ACK original MMIO observation seam changed")
    out=source.replace(HEAD,HEAD+INJECTION,1)
    if out.count(MARKER)!=1 or \
       out.replace(HEAD+INJECTION,HEAD,1)!=source:
        raise ValueError("V369 original-free observer geometry changed")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    a=p.parse_args()
    try:
        if a.output_harness.exists() or a.output_harness.is_symlink():
            raise ValueError("output_exists")
        new=patch(a.source_harness.read_text(encoding="utf-8"))
        with a.output_harness.open("x",encoding="utf-8") as out:
            out.write(new)
    except (OSError,ValueError):
        print("V369_MMIO_PROBE installed=0",file=sys.stderr)
        return 1
    print("V369_MMIO_PROBE installed=1 bounded=32 read_only=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
