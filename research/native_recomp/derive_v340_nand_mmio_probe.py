#!/usr/bin/env python3
"""V340: read-only bounded NAND-phase Wii MMIO write classification.

Patch only the public owner-private harness and never mutate the guest state,
request contents, IOS bus, original PowerPC body or dispatch. No guest
address/value is printed; output is restricted to known MMIO categories.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEADER="void HW_Reg_Write32(uint32_t addr,uint32_t value){"
MARKER="V340_NAND_MMIO n="
INJECTION=(
    "\n  // V340: bounded diagnostic only; do not change MMIO routing.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    static unsigned v340_mmio_n=0u;\n"
    "    if(v340_mmio_n<16u){\n"
    "      using B=undercover::wii::IosBus;\n"
    "      using M=undercover::wii::IpcMailbox;\n"
    "      using H=undercover::wii::HollywoodIrq;\n"
    "      const bool msg=addr==B::IPC+M::PPCMSG||addr==B::MIRROR+M::PPCMSG;\n"
    "      const bool ctrl=addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL;\n"
    "      const bool mask=addr==B::PI_MASK||addr==B::IPC+H::PPC_MASK||\n"
    "                      addr==B::MIRROR+H::PPC_MASK;\n"
    "      const bool flag=addr==B::IPC+H::PPC_FLAG||addr==B::MIRROR+H::PPC_FLAG;\n"
    "      const unsigned kind=msg?1u:ctrl?2u:mask?3u:flag?4u:0u;\n"
    "      const bool readable=ipc70_bus.read32(addr).has_value();\n"
    "      ++v340_mmio_n;\n"
    '      std::cout<<"V340_NAND_MMIO n="<<v340_mmio_n<<" kind="<<kind\n'
    '               <<" ack="<<unsigned(irq76_ipc>0u)\n'
    '               <<" submit="<<unsigned(submit72_active)\n'
    '               <<" send="<<unsigned(post117_send>0u)\n'
    '               <<" readable="<<unsigned(readable)<<std::endl;\n'
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if source.count(HEADER)!=1 or MARKER in source or \
       source.count("v250_candidate_mode")<2 or \
       source.count("v250_nand_seen")<2 or \
       source.count("ACK_MMIO_OLD")!=0:
        raise ValueError("V340 source seam missing or already instrumented")
    result=source.replace(HEADER,HEADER+INJECTION,1)
    if result.count(MARKER)!=1 or \
       result.replace(HEADER+INJECTION,HEADER,1)!=source:
        raise ValueError("V340 owner-private write observer geometry changed")
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_harness",type=Path)
    parser.add_argument("output_harness",type=Path)
    args=parser.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError("output_exists")
        output=patch(args.input_harness.read_text(encoding="utf-8"))
        with args.output_harness.open("x",encoding="utf-8") as out:
            out.write(output)
    except (OSError,ValueError):
        print("V340_MMIO_PROBE installed=0",file=sys.stderr)
        return 1
    print("V340_MMIO_PROBE installed=1 bounded=16 original_guest=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
