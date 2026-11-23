#!/usr/bin/env python3
"""V373: read-only timeline of original Wii NAND IPC IRQ eligibility.

V365 sampled 16 calls only while the Hollywood IRQ level was asserted.
After the authenticated NAND X1->Y2 ACK and genuine PPC_FLAG W1C,
also observe the otherwise invisible masked/disabled-EE interval.
This probe never pumps Starlet, dispatches an IRQ, modifies guest state,
or prints guest pointers, addresses, register values or proprietary code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

HEAD = "void trace_call(uint32_t addr, CPUContext&ctx){"
PRIOR = "V365_IRQ_READY n="
FLAG_ROUTE = "V370_NAND_FLAG_W1C n="
MARKER = "V373_NAND_IRQ_TIMELINE n="
MAX_SAMPLES = 96
INJECTION = (
    "\n  // V373: observe outstanding native replies at guest call boundaries.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u&&\n"
    "     ipc70_bus.services().queued_replies()>0u&&\n"
    "     !ipc70_bus.pending_native_ios_request()){\n"
    "    static unsigned v373_count=0u;\n"
    "    if(v373_count<96u){\n"
    "      using B=undercover::wii::IosBus;\n"
    "      using M=undercover::wii::IpcMailbox;\n"
    "      using H=undercover::wii::HollywoodIrq;\n"
    "      ++v373_count;\n"
    "      const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);\n"
    "      const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);\n"
    "      const bool y1=ctrl.has_value()&&((*ctrl&M::Y1)!=0u);\n"
    "      const bool y2=ctrl.has_value()&&((*ctrl&M::Y2)!=0u);\n"
    "      const bool pending_flag=flag.has_value()&&((*flag&H::IPC_PPC)!=0u);\n"
    "      const bool ee=(ctx.msr&B::MSR_EE)!=0u;\n"
    "      const bool irq=ipc70_bus.external_irq_level();\n"
    "      const bool eligible=ipc70_bus.external_exception_pending(ctx.msr);\n"
    "      const bool safe=!ctx.dispatch_saved_ctx&&ctx.pc!=0u&&\n"
    "                      (ctx.pc&3u)==0u&&\n"
    "                      !(ctx.msr&undercover::wii::ExternalUnsupportedMsr);\n"
    "      bool installed=true;\n"
    "      for(size_t i=0u;i<irq74_vector.size();++i){\n"
    "        const uint32_t at=undercover::wii::ExternalVector+uint32_t(i);\n"
    "        if(ctx.mmu.get_ptr(at)==nullptr||ctx.mmu.read8(at)!=irq74_vector[i]){\n"
    "          installed=false;break;\n"
    "        }\n"
    "      }\n"
    '      std::cout<<"V373_NAND_IRQ_TIMELINE n="<<v373_count\n'
    '               <<" ee="<<unsigned(ee)\n'
    '               <<" irq="<<unsigned(irq)\n'
    '               <<" eligible="<<unsigned(eligible)\n'
    '               <<" safe="<<unsigned(safe)\n'
    '               <<" installed="<<unsigned(installed)\n'
    '               <<" ready="<<unsigned(eligible&&safe&&installed)\n'
    '               <<" y1="<<unsigned(y1)\n'
    '               <<" y2="<<unsigned(y2)\n'
    '               <<" flag="<<unsigned(pending_flag)\n'
    '               <<" queued="<<unsigned(ipc70_bus.services().queued_replies()>0u)\n'
    '               <<std::endl;\n'
    "    }\n"
    "  }\n"
)

def patch(source: str) -> str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or
        source.count(FLAG_ROUTE)!=1 or MARKER in source or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        'irq74_vector' not in source or
        'native_external_irq.h' not in source or
        'ipc70_bus.services().queued_replies()' not in source):
        raise ValueError("V373 read-only guest call seam changed")
    result = source.replace(HEAD, HEAD+INJECTION, 1)
    if result.count(MARKER)!=1 or result.replace(HEAD+INJECTION,HEAD,1)!=source:
        raise ValueError("V373 code injection not exactly reversible")
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_harness",type=Path)
    parser.add_argument("output_harness",type=Path)
    args=parser.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError("output_exists")
        with args.output_harness.open("x",encoding="utf-8") as dest:
            dest.write(patch(args.source_harness.read_text(encoding="utf-8")))
    except (ValueError,OSError):
        print("V373_IRQ_TIMELINE installed=0",file=sys.stderr)
        return 1
    print("V373_IRQ_TIMELINE installed=1 original_guest=1 bounded=96 read_only=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
