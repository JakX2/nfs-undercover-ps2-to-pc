#!/usr/bin/env python3
"""Strict, idempotent FPSCR field-write modeling patch for NWiiRecomp.

The modifier implements only mtfsf field-mask writes through a host bit-copy.
Full PowerPC FP exception, rounding and W/L semantics are NOT implemented.
"""
from pathlib import Path
import argparse

CONTEXT = 'nWiiRuntime/include/runtime/cpu_context.h'
RECOMPILER = 'nWiiRecomp/src/recompiler.cpp'
CTX_BEFORE = '  CPUContext() : gpr{0}, fpr{0.0}, ps1{0.0}, cr{}, pc(0), lr(0), ctr(0), xer(0), '
CTX_AFTER = '''  // v19: FPSCR field-select write from lower 32 bits of a 64-bit FPR image.
  // Does not yet emulate FPSCR exception side effects / Rc / W/L forms.
  void mtfsf(uint32_t fields, uint32_t src) {
    uint32_t mask = 0;
    for (unsigned i = 0; i < 8; ++i) {
      if (fields & (0x80u >> i)) mask |= 0xFu << (28 - 4 * i);
    }
    uint64_t bits = 0;
    std::memcpy(&bits, &fpr.at(src), sizeof(bits));
    const uint32_t low_word = static_cast<uint32_t>(bits);
    fpscr = (fpscr & ~mask) | (low_word & mask);
  }

  CPUContext() : gpr{0}, fpr{0.0}, ps1{0.0}, cr{}, pc(0), lr(0), ctr(0), xer(0), '''
EMIT_BEFORE = '''    } else if (xo == 711) { 
      out << "    // mtfsf stub (ignore FPSCR write)\\n";
    } else if ((xo & 0x1F) == 26) { '''
EMIT_AFTER = '''    } else if (xo == 711) {
      const uint32_t fm = (ppc_inst.value() >> 17) & 0xFFu;
      out << "    ctx.mtfsf(" << fm << ", " << fB
          << "); // mtfsf FPSCR selected fields\\n";
    } else if ((xo & 0x1F) == 26) { '''


def rewrite(content, old, new):
    if content.count(new) == 1:
        return content
    if content.count(new) or content.count(old) != 1:
        raise ValueError('unknown or incompatible upstream FPSCR source revision')
    return content.replace(old, new, 1)


def apply(root: Path):
    ctx, rec = root / CONTEXT, root / RECOMPILER
    a, b = ctx.read_text(), rec.read_text()
    next_a = rewrite(a, CTX_BEFORE, CTX_AFTER)
    next_b = rewrite(b, EMIT_BEFORE, EMIT_AFTER)
    # All checks are complete before first filesystem mutation.
    if a != next_a:
        ctx.write_text(next_a)
    if b != next_b:
        rec.write_text(next_b)
    return a != next_a or b != next_b


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwiirecomp_root', type=Path)
    args = parser.parse_args()
    print('Applied V19 FPSCR field-mask runtime/emitter patch:', apply(args.nwiirecomp_root))
