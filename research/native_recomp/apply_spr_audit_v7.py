#!/usr/bin/env python3
"""V7: stop silently discarding unknown Broadway SPR writes.

This adds an intentionally NON-FUNCTIONAL (for MMU side effects) shadow register
ledger for diagnostics. It is NOT a BAT/MMU implementation. The optional strict
mode rejects writes until those semantics are implemented and differential-tested.
No game bytes or symbols are embedded in this source-only patch.
"""
from pathlib import Path
import argparse

RECOMPILER = Path('nWiiRecomp/src/recompiler.cpp')
CONTEXT = Path('nWiiRuntime/include/runtime/cpu_context.h')


def replace_exact(src: str, old: str, new: str, label: str) -> str:
    if new in src:
        return src
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one upstream anchor, got {count}')
    return src.replace(old, new, 1)


def patch_translator(src: str) -> str:
    src = replace_exact(src,
        '''    } else if (spr >= 920 && spr <= 924) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr HID " << spr << "\\n";
    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr HID0 (stub)\\n";
''',
        '''    } else if (spr >= 920 && spr <= 924) {
      out << "    ctx.gpr[" << rD << "] = ctx.read_unmodeled_spr(" << spr
          << "); // mfspr HID shadow (not full hardware)\\n";
    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = ctx.read_unmodeled_spr(1008); // HID0 shadow\\n";
''', 'HID reads')
    src = replace_exact(src,
        '''    } else if (spr == 1017) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr L2CR\\n";
    } else {
      out << "    std::cerr << \\"[WARN] mfspr r\\" << " << rD
          << " << \\" spr=\\" << " << spr << " << \\" (stub=0)\\\\n\\";\\n";
      out << "    ctx.gpr[" << rD << "] = 0; // unknown spr stub\\n";
''',
        '''    } else if (spr == 1017) {
      out << "    ctx.gpr[" << rD << "] = ctx.read_unmodeled_spr(1017); // L2CR shadow\\n";
    } else {
      out << "    ctx.gpr[" << rD << "] = ctx.read_unmodeled_spr(" << spr
          << "); // unknown SPR shadow, no hardware effects\\n";
''', 'other SPR reads')
    src = replace_exact(src,
        '''    } else {
      out << "    // unhandled mtspr " << spr
          << "\\n"; 
    }
''',
        '''    } else {
      out << "    ctx.write_unmodeled_spr(" << spr << ", ctx.gpr[" << rS
          << "]); // original mtspr, effects not modeled\\n";
    }
''', 'unknown SPR writes')
    return src


def patch_context(src: str) -> str:
    src = replace_exact(src, '#include <iostream>\n',
                        '#include <iostream>\n#include <stdexcept>\n#include <cstdlib>\n', 'header include')
    old = '''  std::array<uint32_t, 8> gqr;
  std::array<uint32_t, 4> sprg; 

  struct BackupState {
'''
    new = '''  std::array<uint32_t, 8> gqr;
  std::array<uint32_t, 4> sprg; 

  // Shadow-only diagnostics for otherwise-ignored guest SPRs. This does not
  // implement BAT translation, cache invalidation, timebase or exception effects.
  std::array<uint32_t, 1024> unmodeled_spr_values{};
  std::array<uint8_t, 1024> unmodeled_spr_written{};
  uint64_t unmodeled_spr_write_count = 0;
  bool strict_unmodeled_sprs = std::getenv("NWII_SPR_STRICT") != nullptr;

  static constexpr bool needs_hardware_spr_effect(uint32_t spr) {
    return (spr >= 528 && spr <= 543) ||  // IBAT0-3 / DBAT0-3
           (spr >= 560 && spr <= 575) ||  // additional BATs
           spr == 25 ||                   // SDR1
           spr == 18 || spr == 19 ||      // exception status/address
           spr == 284 || spr == 285 ||    // timebase
           (spr >= 1008 && spr <= 1023) ||
           (spr >= 920 && spr <= 923);    // HID2 / WPAR etc.
  }

  void write_unmodeled_spr(uint32_t spr, uint32_t value) {
    if (spr >= 1024) throw std::out_of_range("invalid PowerPC SPR number");
    if (strict_unmodeled_sprs && needs_hardware_spr_effect(spr))
      throw std::runtime_error("unimplemented Wii SPR hardware side effects: " + std::to_string(spr));
    if (!unmodeled_spr_written[spr])
      std::cerr << "[SPR AUDIT] shadow-only SPR " << spr
                << " (hardware effects not implemented)\\n";
    unmodeled_spr_values[spr] = value;
    unmodeled_spr_written[spr] = 1;
    ++unmodeled_spr_write_count;
    if (std::getenv("NWII_SPR_TRACE"))
      std::cerr << "[SPR WRITE] pc=0x" << std::hex << pc << " SPR=" << std::dec
                << spr << " value=0x" << std::hex << value << std::dec << "\\n";
  }

  uint32_t read_unmodeled_spr(uint32_t spr) const {
    if (spr >= 1024) throw std::out_of_range("invalid PowerPC SPR number");
    return unmodeled_spr_values[spr];
  }

  struct BackupState {
'''
    src = replace_exact(src, old, new, 'CPUContext SPR shadow')
    # The upstream constructor leaves SPRG uninitialized despite exposing
    # mfsprg reads. Initialize the register bank deterministically.
    src = replace_exact(src,
        'srr1(0), gqr{0}, exception_pc(0)',
        'srr1(0), gqr{0}, sprg{0}, exception_pc(0)', 'SPRG initialization')
    return src


def apply(root: Path) -> None:
    rp, cp = root / RECOMPILER, root / CONTEXT
    old_r, old_c = rp.read_text(), cp.read_text()
    # Determine both transformations before making either write.
    new_r, new_c = patch_translator(old_r), patch_context(old_c)
    if new_r != old_r: rp.write_text(new_r)
    if new_c != old_c: cp.write_text(new_c)
    print(f'V7 SPR audit patch: translator={new_r != old_r} CPUContext={new_c != old_c}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('upstream_root', type=Path)
    a = p.parse_args()
    apply(a.upstream_root)
