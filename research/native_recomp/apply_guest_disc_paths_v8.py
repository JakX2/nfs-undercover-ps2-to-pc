#!/usr/bin/env python3
"""Apply an original-free Wii host-disc filename bridge to NWiiRecomp DVDOpen.

The bridge is not a DI/FST emulator. Run against a private upstream runtime
checkout, alongside the V4-V7 recompiler fixes. No original game code included.
"""
import argparse
from pathlib import Path

TARGET = Path('nWiiRuntime/src/hle/dvd.cpp')
HEADER = Path('nWiiRuntime/include/runtime/guest_disc_paths.h')
ANCHOR_INCLUDE = '#include "runtime/config.h"\n'
INCLUDE = '#include "runtime/config.h"\n#include "runtime/guest_disc_paths.h"\n'
ANCHOR = '''    std::filesystem::path full_path = std::filesystem::path(Config::get().game_dir) / filename;
    auto stream = std::make_shared<std::ifstream>(full_path, std::ios::binary);
'''
ANCHOR_READ = '''    std::string filename;
    uint32_t addr = filename_addr;
    while (true) {
        char c = (char)ctx.mmu.read8(addr++);
        if (c == '\\0') break;
        filename += c;
    }
'''
REPLACEMENT_READ = '''    std::string filename;
    uint32_t addr = filename_addr;
    // Avoid unbounded guest-memory scanning on corrupt/nonterminated names.
    for (size_t i = 0; i < 4096; ++i) {
        char c = (char)ctx.mmu.read8(addr++);
        if (c == '\\0') break;
        filename += c;
    }
    if (filename.size() >= 4096) {
        ctx.gpr[3] = 0;
        return;
    }
'''
REPLACEMENT = '''    // Wii disc paths may be rooted and use backslashes or case differences.
    // Resolve only within the user-provided extracted-disc root.
    const auto resolved = resolve_guest_disc_path(Config::get().game_dir, filename);
    if (!resolved) {
        ctx.gpr[3] = 0;
        return;
    }
    auto stream = std::make_shared<std::ifstream>(*resolved, std::ios::binary);
'''

def apply(root: Path, source: Path):
    target = root / TARGET
    header = root / HEADER
    initial = target.read_text(encoding='utf-8')
    include_done = INCLUDE in initial
    path_done = REPLACEMENT in initial
    bounded_read_done = REPLACEMENT_READ in initial
    if not include_done and initial.count(ANCHOR_INCLUDE) != 1:
        raise ValueError('unexpected upstream DVD include, no change made')
    if not path_done and initial.count(ANCHOR) != 1:
        raise ValueError('unexpected upstream DVDOpen file code, no change made')
    if not bounded_read_done and initial.count(ANCHOR_READ) != 1:
        raise ValueError('unexpected DVDOpen guest-string scanning code, no change made')
    new = initial
    if not bounded_read_done: new = new.replace(ANCHOR_READ, REPLACEMENT_READ, 1)
    if not include_done: new = new.replace(ANCHOR_INCLUDE, INCLUDE, 1)
    if not path_done: new = new.replace(ANCHOR, REPLACEMENT, 1)
    reference = source.read_bytes()
    if header.exists() and header.read_bytes() != reference:
        raise ValueError('existing DVD path header differs, refusing overwrite')
    # All validation occurs before writing either file.
    if not header.exists():
        header.parent.mkdir(parents=True, exist_ok=True)
        header.write_bytes(reference)
    if new != initial: target.write_text(new, encoding='utf-8')
    return new != initial

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('upstream_root', type=Path)
    ap.add_argument('--header',type=Path,default=Path(__file__).with_name('guest_disc_paths_v8.h'))
    args=ap.parse_args()
    print('DVDOpen source changed:',apply(args.upstream_root,args.header))
