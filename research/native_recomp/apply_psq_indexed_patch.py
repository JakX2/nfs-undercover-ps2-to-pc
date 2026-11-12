#!/usr/bin/env python3
"""Idempotently add indexed paired-single instruction emission to NWiiRecomp.

Run against a PRIVATE, user-provided checkout of the upstream recompiler.
This small owner-authored patch does not include game code or assets.
"""
import argparse
from pathlib import Path

TARGET = Path('nWiiRecomp/src/recompiler.cpp')
ANCHOR = '''    if (xo == 21) {\n      out << "    ctx.ps_add(" << frD << ", " << frA << ", " << frB << ");\\n";\n'''
PATCH = '''    // The low six bits of the 10-bit XO select indexed paired-single\n    // memory operation. Bits 10 and 7..9 of the instruction encode W and I.\n    // Do not treat higher XO bits as separate opcodes: those bits carry GQR\n    // and single/pair selection, which caused Undercover translation traps.\n    const uint32_t psq_xo = xo_10 & 0x3F;\n    if (psq_xo == 6 || psq_xo == 7 || psq_xo == 38 || psq_xo == 39) {\n      const uint32_t rA = ppc_inst.ra();\n      const uint32_t rB = ppc_inst.rb();\n      const uint32_t W = (inst.opcode >> 10) & 1;\n      const uint32_t I = (inst.opcode >> 7) & 7;\n      const bool update = psq_xo == 38 || psq_xo == 39;\n      const bool store = psq_xo == 7 || psq_xo == 39;\n      if (update && rA == 0) {\n        out << "    std::cerr << \\\"Invalid psq_*ux rA=0\\\\n\\\"; std::exit(1);\\n";\n      } else {\n        out << "    { uint32_t ea = ";\n        if (rA != 0) out << "ctx.gpr[" << rA << "] + ";\n        out << "ctx.gpr[" << rB << "];\\n";\n        out << (store ? "      ctx.psq_store(" : "      ctx.psq_load(")\n            << frD << ", ea, " << W << ", " << I << ");\\n";
        if (update) out << "      ctx.gpr[" << rA << "] = ea;\\n";
        out << "    } // indexed paired single memory\\n";
      }
'''

def apply(path: Path) -> str:
    source = path.read_text(encoding='utf-8')
    if 'const uint32_t psq_xo = xo_10 & 0x3F;' in source:
        return 'already patched'
    if source.count(ANCHOR) != 1:
        raise RuntimeError('unrecognized upstream layout, refusing to patch')
    source = source.replace(ANCHOR, PATCH + '    } else ' + ANCHOR.lstrip(' '), 1)
    path.write_text(source, encoding='utf-8')
    return 'applied'

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream_root', type=Path)
    args = ap.parse_args()
    print(apply(args.upstream_root/TARGET))
