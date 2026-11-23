#!/usr/bin/env python3
"""V352: route authentic NAND PPCMSG/PPCCTRL writes to the existing IOS bus.

The early V69 hardware-initialization MMIO observer is still active after its
own request. Route only these two supported original guest mailbox registers
in authenticated NAND mode, without altering the value, guest RAM, original
AOT, IOS service, scheduler, ACK or reply. Invalid pointers fail closed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEADER="void HW_Reg_Write32(uint32_t addr,uint32_t value){"
MARKER="V352_NAND_BUS kind="
INJECTION=(
    "\n  // V352: real NAND MMIO transport, not a synthetic IOS reply.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    using B=undercover::wii::IosBus;\n"
    "    using M=undercover::wii::IpcMailbox;\n"
    "    const bool message=addr==B::IPC+M::PPCMSG||addr==B::MIRROR+M::PPCMSG;\n"
    "    const bool control=addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL;\n"
    "    if(message||control){\n"
    "      const bool mapped=!message||(value!=0u&&(value&31u)==0u&&\n"
    "                                  ipc70_ram.valid(value,64u));\n"
    "      if(!mapped){\n"
    '        std::cout<<"V352_NAND_BUS kind=1 mapped=0 accepted=0 queued=0"\n'
    "                 <<std::endl;\n"
    '        check(false,"V352 authentic NAND IPC message pointer invalid");\n'
    "      }\n"
    "      const bool accepted=ipc70_bus.write32(addr,value);\n"
    '      std::cout<<"V352_NAND_BUS kind="<<(message?1u:2u)\n'
    '               <<" mapped=1 accepted="<<unsigned(accepted)\n'
    '               <<" queued="<<unsigned(ipc70_bus.pending_native_ios_request())\n'
    "               <<std::endl;\n"
    '      check(accepted,"V352 native IOS bus rejected authentic NAND write");\n'
    "      mmio_writes.emplace_back(addr,value);\n"
    "      return;\n"
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if (source.count(HEADER)!=1 or MARKER in source or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        "ipc70_bus.write32" not in source or
        "ipc70_ram.valid" not in source or
        "mmio_writes.emplace_back" not in source):
        raise ValueError("V352 authenticated native IPC transport seam changed")
    result=source.replace(HEADER,HEADER+INJECTION,1)
    if (result.count(MARKER)!=2 or
        result.replace(HEADER+INJECTION,HEADER,1)!=source):
        raise ValueError("V352 original-free mailbox route geometry changed")
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    args=p.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError("output_exists")
        generated=patch(args.source_harness.read_text(encoding="utf-8"))
        with args.output_harness.open("x",encoding="utf-8") as out:
            out.write(generated)
    except (ValueError,OSError):
        print("V352_NAND_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V352_NAND_ROUTE installed=1 original_guest=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
