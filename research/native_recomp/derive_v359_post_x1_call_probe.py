#!/usr/bin/env python3
"""V359: bounded native post-X1 call/IOS-state observer.

The authentic NAND PPCMSG and X1 submission are already proven. This
instrumentation records up to 16 subsequent original guest call entries
using a fixed, non-identifying 0-8 category. It never changes registers,
guest memory, translated code, service scheduling, ACK or IOS reply.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
PRIOR="V321_GUEST_ENTRY pc="
MARKER="V359_X1_CALL n="
CATEGORIES=(
    (0x80522af4,1),  # OSClearContext
    (0x805228cc,2),  # OSSetCurrentContext
    (0x805265d4,3),  # observed interrupt continuation helper
    (0x8052f830,4),  # SC status helper
    (0x8051906c,5),  # original IPC send helper
    (0x8054514c,6),  # verified AOT branch target
    (0x8051ad38,7),  # allocator tail
    (0x8051e150,8),  # NAND service target
)
INJECTION=(
    "\n  // V359: record only bounded public categories, never raw guest PC/LR.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    static bool v359_armed=false;\n"
    "    static unsigned v359_count=0u;\n"
    "    const bool pending=ipc70_bus.pending_native_ios_request();\n"
    "    if(pending||ipc70_bus.services().queued_replies()>0u)v359_armed=true;\n"
    "    if(v359_armed&&v359_count<16u){\n"
    "      unsigned kind=0u;\n"
    + "".join(f"      if(addr==0x{pc:08x}u)kind={kind}u;\n" for pc,kind in CATEGORIES)
    + "      ++v359_count;\n"
    '      std::cout<<"V359_X1_CALL n="<<v359_count<<" kind="<<kind\n'
    '               <<" pending="<<unsigned(pending)\n'
    '               <<" irq="<<unsigned(ipc70_bus.external_irq_level())\n'
    '               <<" ee="<<unsigned((ctx.msr&0x8000u)!=0u)\n'
    '               <<" replies="<<unsigned(ipc70_bus.services().queued_replies()>0u)\n'
    "               <<std::endl;\n"
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or MARKER in source or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2):
        raise ValueError("V359 original guest call seam missing or ambiguous")
    output=source.replace(HEAD,HEAD+INJECTION,1)
    if (output.count(MARKER)!=1 or output.count(HEAD)!=1 or
        output.replace(HEAD+INJECTION,HEAD,1)!=source):
        raise ValueError("V359 original-free call instrumentation geometry changed")
    return output

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    args=p.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError("output_exists")
        output=patch(args.input_harness.read_text(encoding="utf-8"))
        with args.output_harness.open("x",encoding="utf-8") as f:
            f.write(output)
    except (OSError,ValueError):
        print("V359_X1_PROBE installed=0",file=sys.stderr)
        return 1
    print("V359_X1_PROBE installed=1 max_calls=16 original_guest=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
