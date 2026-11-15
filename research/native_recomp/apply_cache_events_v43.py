#!/usr/bin/env python3
"""Original-free NWiiRecomp cache-operation observability and host-order patch.

The guest cache controls are represented only by bounded line traces and host
memory fences. They do NOT emulate Wii hardware cache state or invalidate
statically recompiled host code. Fail closed on unknown upstream revisions.
"""
import argparse
from pathlib import Path

CONTEXT = Path('nWiiRuntime/include/runtime/cpu_context.h')
EMITTER = Path('nWiiRecomp/src/recompiler.cpp')
CTX_BEFORE = '  uint32_t hid4 = 0;\n\n  struct BackupState {'
CTX_AFTER = '''  uint32_t hid4 = 0;

  // Diagnostic guest cache-line ordering: not a hardware cache model.
  std::array<uint32_t, 32> guest_flush_lines{};
  std::array<uint32_t, 32> guest_invalidate_lines{};
  uint32_t guest_flush_count = 0;
  uint32_t guest_invalidate_count = 0;
  uint32_t guest_sync_count = 0;
  uint32_t guest_isync_count = 0;
  uint32_t guest_last_flush = 0;
  uint32_t guest_last_invalidate = 0;

  void guest_dcbf(uint32_t effective_address) {
    const uint32_t line = effective_address & ~31u;
    if (guest_flush_count < guest_flush_lines.size())
      guest_flush_lines[guest_flush_count] = line;
    ++guest_flush_count;
    guest_last_flush = line;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }
  void guest_icbi(uint32_t effective_address) {
    const uint32_t line = effective_address & ~31u;
    if (guest_invalidate_count < guest_invalidate_lines.size())
      guest_invalidate_lines[guest_invalidate_count] = line;
    ++guest_invalidate_count;
    guest_last_invalidate = line;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }
  void guest_sync() {
    ++guest_sync_count;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }
  void guest_isync() {
    ++guest_isync_count;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }

  struct BackupState {'''
EMIT_BEFORE = '''    if (xo == 598 || xo == 854 || xo == 982 || xo == 54 || xo == 86 ||
        xo == 278 || xo == 246 || xo == 470) {
      
      out << "    // sync/cache instruction\\n";
    } else if (xo == 0) {'''
EMIT_AFTER = '''    if (xo == 86 || xo == 982) {
      // PPC cache-line address uses zero when RA is r0.
      const std::string base = (rA == 0) ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx." << (xo == 86 ? "guest_dcbf" : "guest_icbi")
          << "(" << base << " + ctx.gpr[" << rB << "]);\\n";
    } else if (xo == 598) {
      out << "    ctx.guest_sync(); // guest sync ordering\\n";
    } else if (xo == 854 || xo == 54 || xo == 278 || xo == 246 || xo == 470) {
      out << "    // unimplemented guest cache instruction\\n";
    } else if (xo == 0) {'''
ISYNC_BEFORE = '''    if (xo == 150) { 
      out << "    // isync\\n";
    } else if (xo == 50) { '''
ISYNC_AFTER = '''    if (xo == 150) {
      out << "    ctx.guest_isync(); // guest isync ordering\\n";
    } else if (xo == 50) { '''


def transform(content, pairs):
    output = content
    for old, new in pairs:
        if output.count(new) == 1 and old not in output:
            continue
        if output.count(old) != 1 or new in output:
            raise ValueError('unknown or conflicting upstream Wii cache emitter/state revision')
        output = output.replace(old, new, 1)
    return output


def apply(root: Path):
    cpath, epath = root / CONTEXT, root / EMITTER
    before_ctx = cpath.read_text(encoding='utf-8')
    before_emitter = epath.read_text(encoding='utf-8')
    def state(source, old, new):
        if source.count(old) == 1 and new not in source:
            return 'old'
        if source.count(new) == 1 and old not in source:
            return 'new'
        raise ValueError('unknown or ambiguous Wii cache source revision')
    states = (state(before_ctx, CTX_BEFORE, CTX_AFTER),
              state(before_emitter, EMIT_BEFORE, EMIT_AFTER),
              state(before_emitter, ISYNC_BEFORE, ISYNC_AFTER))
    if len(set(states)) != 1:
        raise ValueError('partially patched cache runtime/emitter; refusing unsafe mixed state')
    if states[0] == 'new':
        return False
    after_ctx = transform(before_ctx, [(CTX_BEFORE, CTX_AFTER)])
    after_emitter = transform(before_emitter,
                              [(EMIT_BEFORE, EMIT_AFTER), (ISYNC_BEFORE, ISYNC_AFTER)])
    # Validate every anchor before writing either file.
    cpath.write_text(after_ctx, encoding='utf-8')
    epath.write_text(after_emitter, encoding='utf-8')
    return True


if __name__ == '__main__':
    arg = argparse.ArgumentParser()
    arg.add_argument('nwiirecomp_root', type=Path)
    a=arg.parse_args()
    print('V43 original-free cache event patch:', 'installed' if apply(a.nwiirecomp_root) else 'already applied')
