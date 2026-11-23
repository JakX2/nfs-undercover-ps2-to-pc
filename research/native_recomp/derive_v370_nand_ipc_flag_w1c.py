#!/usr/bin/env python3
"""V370: forward an authentic Wii NAND PPC_FLAG write-one-to-clear to native IRQ.

Authenticated V367 owner-original output found one PPC_FLAG write and
zero mask writes before the old IPC69 "unexpected IPC mask" assertion.
The Hollywood native bus already implements W1C for PPC_FLAG. Forward
the untouched guest register/value only in the original NAND phase.
Do not synthesize exception entry, IOS ACK, Y1, reply or callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void HW_Reg_Write32(uint32_t addr,uint32_t value){"
PRIOR="V367_NAND_IRQ_MASK n="
MARKER="V370_NAND_FLAG_W1C n="
INJECTION=(
    "\n  // V370: actual original Broadway Hollywood IPC flag W1C.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    using B=undercover::wii::IosBus;\n"
    "    using H=undercover::wii::HollywoodIrq;\n"
    "    const bool flag=addr==B::IPC+H::PPC_FLAG||\n"
    "                    addr==B::MIRROR+H::PPC_FLAG;\n"
    "    if(flag){\n"
    "      const auto prior=ipc70_bus.read32(addr);\n"
    "      const bool before=prior.has_value()&&((*prior&H::IPC_PPC)!=0u);\n"
    "      const bool accepted=ipc70_bus.write32(addr,value);\n"
    '      check(accepted,"V370 native Hollywood rejected original NAND W1C");\n'
    "      const auto after=ipc70_bus.read32(addr);\n"
    "      const bool remaining=after.has_value()&&((*after&H::IPC_PPC)!=0u);\n"
    "      static unsigned v370_count=0u;\n"
    "      if(v370_count<16u){\n"
    "        ++v370_count;\n"
    '        std::cout<<"V370_NAND_FLAG_W1C n="<<v370_count\n'
    '                 <<" accepted="<<unsigned(accepted)\n'
    '                 <<" before="<<unsigned(before)\n'
    '                 <<" write_ipc="<<unsigned((value&H::IPC_PPC)!=0u)\n'
    '                 <<" remaining="<<unsigned(remaining)\n'
    '                 <<" irq="<<unsigned(ipc70_bus.external_irq_level())\n'
    '                 <<" queued="<<unsigned(ipc70_bus.services().queued_replies()>0u)\n'
    "                 <<std::endl;\n"
    "      }\n"
    "      mmio_writes.emplace_back(addr,value);\n"
    "      return;\n"
    "    }\n"
    "  }\n"
)

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or
        source.count("unexpected IPC mask MMIO write")!=1 or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        "ipc70_bus.write32" not in source or
        "mmio_writes.emplace_back" not in source or
        "ipc70_bus.services().queued_replies()" not in source or
        MARKER in source):
        raise ValueError("V370 original PPC_FLAG routing seam changed")
    output=source.replace(HEAD,HEAD+INJECTION,1)
    if output.count(MARKER)!=1 or \
       output.replace(HEAD+INJECTION,HEAD,1)!=source:
        raise ValueError("V370 independent original-free MMIO geometry changed")
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    a=p.parse_args()
    try:
        if a.output_harness.exists() or a.output_harness.is_symlink():
            raise ValueError("output_exists")
        with a.output_harness.open("x",encoding="utf-8") as out:
            out.write(patch(a.source_harness.read_text(encoding="utf-8")))
    except (OSError,ValueError):
        print("V370_FLAG_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V370_FLAG_ROUTE installed=1 original_guest=1 w1c=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
