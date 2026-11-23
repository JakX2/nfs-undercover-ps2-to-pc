#!/usr/bin/env python3
"""V361: experimentally yield native IOS at a genuine NAND OSRestoreInterrupts call.

The original Wii guest has submitted PPCMSG/PPCCTRL.X1 at this point.
Run one real IosYieldScheduler step only if a pending, validated original
request exists. This is host Starlet scheduling, not a fake guest reply,
forced PPC branch, manufactured interrupt, or injected success code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
PRIOR="V359_X1_CALL n="
MARKER="V361_NAND_IOS_YIELD n="
INJECTION=(
    "\n  // V361: native Starlet service at original OSRestoreInterrupts entry.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u&&\n"
    "     addr==0x805265d4u&&ipc70_bus.pending_native_ios_request()){\n"
    "    using B=undercover::wii::IosBus;\n"
    "    using M=undercover::wii::IpcMailbox;\n"
    "    const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);\n"
    "    const bool mapped=msg.has_value()&&*msg!=0u&&\n"
    "                      (*msg&31u)==0u&&ipc70_ram.valid(*msg,64u);\n"
    '    check(mapped,"V361 original NAND IOS request buffer became invalid");\n'
    "    undercover::wii::IosYieldScheduler scheduler(ipc70_bus);\n"
    "    const auto state=scheduler.service_one(ctx.msr);\n"
    "    static unsigned v361_logged=0u;\n"
    "    if(v361_logged<16u){\n"
    "      ++v361_logged;\n"
    '      std::cout<<"V361_NAND_IOS_YIELD n="<<v361_logged\n'
    '               <<" mapped="<<unsigned(mapped)\n'
    '               <<" pump="<<unsigned(state.progress)\n'
    '               <<" pending="<<unsigned(ipc70_bus.pending_native_ios_request())\n'
    '               <<" irq="<<unsigned(state.broadway_irq_level)\n'
    '               <<" eligible="<<unsigned(state.guest_exception_ready)\n'
    '               <<" replies="<<unsigned(ipc70_bus.services().queued_replies()>0u)\n'
    "               <<std::endl;\n"
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        "wii_ios_yield_scheduler.h" not in source or
        MARKER in source):
        raise ValueError("V361 authenticated IOS yield seam changed")
    output=source.replace(HEAD,HEAD+INJECTION,1)
    if (output.count(MARKER)!=1 or
        output.replace(HEAD+INJECTION,HEAD,1)!=source):
        raise ValueError("V361 original AOT-yield instrumentation changed")
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    args=p.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError("output_exists")
        output=patch(args.input_harness.read_text(encoding="utf-8"))
        with args.output_harness.open("x",encoding="utf-8") as out:
            out.write(output)
    except (OSError,ValueError):
        print("V361_IOS_YIELD_PROBE installed=0",file=sys.stderr)
        return 1
    print("V361_IOS_YIELD_PROBE installed=1 original_guest=1 no_fake_reply=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
