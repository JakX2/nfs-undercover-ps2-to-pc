#!/usr/bin/env python3
"""V321: one-shot, owner-private guest AOT function-entry instrumentation.

Apply only to the already V298/V320-scoped public C++ harness. The
instrumentation records a bounded positive observation when generated
AOT reaches a known guest function entry. It never edits guest CPU
registers, memory, control flow, original binary, or IOS responses.
No private C++ or guest instruction bytes are printed or committed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

HEAD = "void trace_call(uint32_t addr, CPUContext&ctx){"
GUARD71 = ("if((!v250_candidate_mode||v250_nand_seen==0u)&&"
           "open71_trace(addr,ctx))return;")
GUARD112 = "if(post111_open==1u&&post110_chosen==2u&&"
TARGETS = (
    0x804F2064, # restored first NAND helper
    0x80519BCC, # restored 64-word descendant
    0x8051D20C, # early NAND service
    0x8051E150, # later NAND service
    0x8052FCA4, # original SYSCONF writer
    0x8051AD38, # allocator tail
    0x80545100, # branch/interrupt target
    0x8054514C, # branch/interrupt target
)
MARKER = "V321_GUEST_ENTRY pc="
INJECTION = (
    "\n  // V321: owner-private, once-per-function positive AOT entry evidence.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u){\n"
    "    static unsigned v321_entry_mask=0u;\n"
    "    static constexpr uint32_t v321_targets[]={\n"
    "      "+", ".join(f"0x{pc:08x}u" for pc in TARGETS)+"\n"
    "    };\n"
    "    for(unsigned i=0u;i<8u;++i){\n"
    "      const unsigned bit=1u<<i;\n"
    "      if(addr==v321_targets[i]&&!(v321_entry_mask&bit)){\n"
    "        v321_entry_mask|=bit;\n"
    '        std::cout<<"V321_GUEST_ENTRY pc="<<std::hex<<addr<<std::dec<<std::endl;\n'
    "      }\n"
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if (source.count(HEAD)!=1 or source.count(GUARD71)!=1 or
        source.count(GUARD112)!=1 or MARKER in source or
        source.count("v250_nand_seen")<2):
        raise ValueError("guest_entry_source_guard")
    output=source.replace(HEAD,HEAD+INJECTION,1)
    if (output.count(MARKER)!=1 or output.count(HEAD)!=1 or
        output.replace(HEAD+INJECTION,HEAD,1)!=source):
        raise ValueError("guest_entry_insert_guard")
    return output

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_v320_harness",type=Path)
    p.add_argument("private_v321_harness",type=Path)
    a=p.parse_args()
    try:
        if a.private_v321_harness.exists() or a.private_v321_harness.is_symlink():
            raise ValueError("output_exists")
        modified=patch(a.private_v320_harness.read_text(encoding="utf-8"))
        with a.private_v321_harness.open("x",encoding="utf-8") as output:
            output.write(modified)
    except (OSError,ValueError):
        print("V321_ENTRY_PROBE installed=0",file=sys.stderr)
        return 1
    print("V321_ENTRY_PROBE installed=1 targets=8 bounded=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
