#!/usr/bin/env python3
"""Private installed-vector metadata for the post-scheduler owner test."""
import argparse,hashlib,struct
from pathlib import Path
from audit_v662_external_overlay import expected,SOURCE
from make_private_elf_symbol_map import ORIGINAL_SHA256
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
def render(words):
    if len(words)!=38:raise ValueError('vector extent')
    data=struct.pack('>38I',*words)
    return ('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v1259 {\n'
        'inline constexpr std::array<uint8_t,152> vector{'+','.join(str(b) for b in data)+'};\n}\n')
def prepare(dol,elf):
    if hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
    installed=expected(dol)
    source=list(exact_words(dol,elf,SOURCE,38))
    source[22]=0x60000000;source[26]|=4
    if source!=installed:raise ValueError('installed vector identity')
    return render(installed)
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        content=prepare(a.dol.read_bytes(),a.elf.read_bytes())
        with a.out.open('x') as f:f.write(content)
    except (OSError,ValueError,struct.error,IndexError):
        print('V1259_VECTOR_METADATA verified=0');return 1
    print('V1259_VECTOR_METADATA verified=1 bytes=152 seeded=1');return 0
if __name__=='__main__':raise SystemExit(main())
