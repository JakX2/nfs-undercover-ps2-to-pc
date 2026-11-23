#!/usr/bin/env python3
"""V365: read-only original Wii IRQ readiness following genuine NAND IOS ACK.

Do not enter an interrupt, tick IOS, change CPU state or manufacture a reply.
Record up to 16 samples of pending IRQ, MSR.EE, safe guest dispatch boundary,
and byte-verified installed exception vector. Original owner bytes remain
private; only fixed booleans are emitted from the native trial.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
PRIOR="V361_NAND_IOS_YIELD n="
MARKER="V365_IRQ_READY n="
INJECTION=(
    "\n  // V365: only classify the existing Starlet IRQ and original vector.\n"
    "  if(v250_candidate_mode&&v250_nand_seen==1u&&\n"
    "     ipc70_bus.external_irq_level()){\n"
    "    static unsigned v365_count=0u;\n"
    "    if(v365_count<16u){\n"
    "      ++v365_count;\n"
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
    '      std::cout<<"V365_IRQ_READY n="<<v365_count\n'
    '               <<" eligible="<<unsigned(eligible)\n'
    '               <<" safe="<<unsigned(safe)\n'
    '               <<" installed="<<unsigned(installed)\n'
    '               <<" ready="<<unsigned(eligible&&safe&&installed)\n'
    "               <<std::endl;\n"
    "    }\n"
    "  }\n"
)

def patch(source: str)->str:
    if (source.count(HEAD)!=1 or source.count(PRIOR)!=1 or MARKER in source or
        source.count("v250_candidate_mode")<2 or
        source.count("v250_nand_seen")<2 or
        "irq74_vector" not in source or
        "native_external_irq.h" not in source):
        raise ValueError("V365 native IRQ vector observation seam changed")
    result=source.replace(HEAD,HEAD+INJECTION,1)
    if result.count(MARKER)!=1 or \
       result.replace(HEAD+INJECTION,HEAD,1)!=source:
        raise ValueError("V365 owner-only source mutation geometry changed")
    return result

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_harness",type=Path)
    p.add_argument("output_harness",type=Path)
    a=p.parse_args()
    try:
        if a.output_harness.exists() or a.output_harness.is_symlink():
            raise ValueError("output_exists")
        derived=patch(a.input_harness.read_text(encoding="utf-8"))
        with a.output_harness.open("x",encoding="utf-8") as out:
            out.write(derived)
    except (ValueError,OSError):
        print("V365_IRQ_PROBE installed=0",file=sys.stderr)
        return 1
    print("V365_IRQ_PROBE installed=1 bounded=16 read_only=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
