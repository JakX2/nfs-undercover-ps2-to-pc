#!/usr/bin/env python3
"""Apply V5 source-only NWiiRecomp PS estimate, signed GQR and SPRG fixes.

This patch must be applied to a private V4-indexed-PSQ NWiiRecomp tree.
Only tool/runtime implementations are changed; no original game code is included.
Fail closed on upstream layout changes. The estimate implementation is numerical
fallback only, not Broadway bit-exact approximation or FPSCR emulation.
"""
import argparse
from pathlib import Path


def substitute_exact(data: str, before: str, after: str, title: str) -> str:
    if after in data:
        return data
    if data.count(before) != 1:
        raise RuntimeError(f'{title}: expected exactly one unpatched anchor, found {data.count(before)}')
    return data.replace(before, after, 1)


def patch_translator(original: str) -> str:
    result = original
    # These are exact 10-bit opcode selections; avoid a broad XO5 predicate
    # that can capture other paired-single forms.
    before = '''    } else if (xo_10 == 1014) {
      out << "    // dcbz_l (no-op)\\n";
    } else {
'''
    after = '''    } else if (xo_10 == 24) {
      out << "    ctx.ps_res(" << frD << ", " << frB << "); // ps_res (approximate)\\n";
    } else if (xo_10 == 26) {
      out << "    ctx.ps_rsqrte(" << frD << ", " << frB << "); // ps_rsqrte (approximate)\\n";
    } else if (xo_10 == 1014) {
      out << "    // dcbz_l (no-op)\\n";
    } else {
'''
    result = substitute_exact(result, before, after, 'ps estimates')
    before = '''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gpr[" << rD << "] = ctx.gqr[" << (spr - 912)
          << "]; // mfgqr" << (spr - 912) << " r" << rD << "\\n";
    } else if (spr == 1) {
'''
    after = '''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gpr[" << rD << "] = ctx.gqr[" << (spr - 912)
          << "]; // mfgqr" << (spr - 912) << " r" << rD << "\\n";
    } else if (spr >= 272 && spr <= 275) {
      out << "    ctx.gpr[" << rD << "] = ctx.sprg[" << (spr - 272)
          << "]; // mfsprg" << (spr - 272) << "\\n";
    } else if (spr == 1) {
'''
    result = substitute_exact(result, before, after, 'SPRG reads')
    before = '''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gqr[" << (spr - 912) << "] = ctx.gpr[" << rS
          << "]; // mtgqr" << (spr - 912) << " r" << rS << "\\n";
    } else if (spr == 1) {
'''
    after = '''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gqr[" << (spr - 912) << "] = ctx.gpr[" << rS
          << "]; // mtgqr" << (spr - 912) << " r" << rS << "\\n";
    } else if (spr >= 272 && spr <= 275) {
      out << "    ctx.sprg[" << (spr - 272) << "] = ctx.gpr[" << rS
          << "]; // mtsprg" << (spr - 272) << "\\n";
    } else if (spr == 1) {
'''
    result = substitute_exact(result, before, after, 'SPRG writes')
    return result


def patch_context(original: str) -> str:
    result = original
    before = '''  void psq_load(uint32_t frD, uint32_t addr, uint32_t W, uint32_t I) {
'''
    after = '''  // GQR scale is a signed six-bit quantity, not unsigned (WiiBrew/YAGCD).
  static constexpr int32_t signed_gqr_scale6(uint32_t bits) {
    const int32_t raw = static_cast<int32_t>(bits & 0x3Fu);
    return raw >= 32 ? raw - 64 : raw;
  }

  // Approximate fallbacks only: Broadway-specific estimate lookup tables,
  // rounding, status flags and special-value behavior still need validation.
  void ps_res(uint32_t dst, uint32_t src) {
    const float first = static_cast<float>(fpr[src]);
    const float second = static_cast<float>(ps1[src]);
    fpr[dst] = static_cast<double>(1.0f / first);
    ps1[dst] = static_cast<double>(1.0f / second);
  }

  void ps_rsqrte(uint32_t dst, uint32_t src) {
    const float first = static_cast<float>(fpr[src]);
    const float second = static_cast<float>(ps1[src]);
    fpr[dst] = static_cast<double>(1.0f / std::sqrt(first));
    ps1[dst] = static_cast<double>(1.0f / std::sqrt(second));
  }

  void psq_load(uint32_t frD, uint32_t addr, uint32_t W, uint32_t I) {
'''
    result = substitute_exact(result, before, after, 'estimate helpers')
    result = substitute_exact(
        result,
        '''    uint32_t ld_scale = (gqr_val >> 24) & 0x3F;
    float scale = std::pow(2.0f, -((int)ld_scale));''',
        '''    const int32_t ld_scale = signed_gqr_scale6(gqr_val >> 24);
    const float scale = std::ldexp(1.0f, -ld_scale);''',
        'signed load scale')
    result = substitute_exact(
        result,
        '''    uint32_t st_scale = (gqr_val >> 8) & 0x3F;
    float scale = std::pow(2.0f, (int)st_scale);''',
        '''    const int32_t st_scale = signed_gqr_scale6(gqr_val >> 8);
    const float scale = std::ldexp(1.0f, st_scale);''',
        'signed store scale')
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream_root', type=Path)
    args = ap.parse_args()
    src = args.upstream_root / 'nWiiRecomp/src/recompiler.cpp'
    ctx = args.upstream_root / 'nWiiRuntime/include/runtime/cpu_context.h'
    old_src = src.read_text(encoding='utf-8')
    old_ctx = ctx.read_text(encoding='utf-8')
    new_src = patch_translator(old_src)
    new_ctx = patch_context(old_ctx)
    # Both validations finish before writing either file.
    if new_src != old_src:
        src.write_text(new_src, encoding='utf-8')
    if new_ctx != old_ctx:
        ctx.write_text(new_ctx, encoding='utf-8')
    print('translator:', 'patched' if new_src != old_src else 'already patched')
    print('runtime:', 'patched' if new_ctx != old_ctx else 'already patched')

if __name__ == '__main__':
    main()
