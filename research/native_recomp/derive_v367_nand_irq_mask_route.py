#!/usr/bin/env python3
"""V367: route authenticated original Wii NAND IRQ mask writes to native IOS.

V366 reached the IPC69 initial-startup mask oracle after a real NAND IOS
ACK. Route only the three already implemented Broadway mask MMIO addresses
using the *unchanged* original write value. Unsupported writes still enter
the old assertion. No guest register/memory edits, Starlet scheduling,
invented IOS results or exception entry is permitted.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEADER="void HW_Reg_Write32(uint32_t addr,uint32_t value){"
PRIOR="V352_NAND_BUS kind="
MARKER="V367_NAND_IRQ_MASK n="
INJECTION=(
    "\n  // V367: original NAND-era interrupt mask registers, native hardware.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    using B=undercover::wii::IosBus;\n"
    "    using H=undercover::wii::HollywoodIrq;\n"
    "    const bool pi=addr==B::PI_MASK;\n"
    "    const bool ppc=addr==B::IPC+H::PPC_MASK||\n"
    "                   addr==B::MIRROR+H::PPC_MASK;\n"
    "    if(pi||ppc){\n"
    "      // The original early IPC69 assertion tests its first init stage,\n"
    "      // not later NAND writes after the authentic Starlet ACK.\n"
    "      const bool accepted=ipc70_bus.write32(addr,value);\n"
    '      check(accepted,"V367 original NAND native IRQ mask write rejected");\n'
    "      static unsigned v367_count=0u;\n"
    "      if(v367_count<16u){\n"
    "        ++v367_count;\n"
    '        std::cout<<"V367_NAND_IRQ_MASK n="<<v367_count\n'
    '                 <<" kind="<<(pi?1u:2u)\n'
    '                 <<" accepted="<<unsigned(accepted)\n'
    '                 <<" irq="<<unsigned(ipc70_bus.external_irq_level())\n'
    "                 <<std::endl;\n"
    "      }\n"
    "      mmio_writes.emplace_back(addr,value);\n"
    "      return;\n"
    "    }\n"
    "  }\n"
)

def patch(source:str)->str:
    if (source.count(HEADER)!=1 or source.count(PRIOR)!=2 or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        source.count("unexpected IPC mask MMIO write")!=1 or
        "ipc70_bus.write32" not in source or
        "mmio_writes.emplace_back" not in source or
        MARKER in source):
        raise ValueError("V367 native IRQ mask routing seam changed")
    result=source.replace(HEADER,HEADER+INJECTION,1)
    if (result.count(MARKER)!=1 or
        result.replace(HEADER+INJECTION,HEADER,1)!=source):
        raise ValueError("V367 original-free mask route geometry changed")
    return result

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    a=p.parse_args()
    try:
        if a.output_harness.exists() or a.output_harness.is_symlink():
            raise ValueError("output_exists")
        source=a.source_harness.read_text(encoding="utf-8")
        with a.output_harness.open("x",encoding="utf-8") as out:
            out.write(patch(source))
    except (OSError,ValueError):
        print("V367_MASK_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V367_MASK_ROUTE installed=1 original_guest=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
