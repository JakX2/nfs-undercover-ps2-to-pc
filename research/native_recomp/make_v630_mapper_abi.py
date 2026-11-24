#!/usr/bin/env python3
"""Export only a private, DOL/ELF-identical mapper prefix for liveness proof."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,direct_bl
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from make_v624_ipc_geometry import exact_words
MAP=0x80527568
CALL=0x8052776c
def prefix(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    if hashlib.sha256(dol).hexdigest()!=dd or hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('identity')
    size=parse_functions(elf).get(MAP,0)
    if not 64<=size<=4096 or size%4:raise ValueError('extent')
    if direct_bl(exact_words(dol,elf,CALL,1)[0],CALL)!=MAP:raise ValueError('edge')
    return exact_words(dol,elf,MAP,16)
def render(words):
    if len(words)!=16:raise ValueError('prefix')
    return ('#pragma once\n#include <array>\n#include <cstdint>\nnamespace undercover::wii::v630 {\n'
            'inline constexpr std::array<uint32_t,16> owner_prefix{'+','.join(f'0x{w:08x}u' for w in words)+'};\n}\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024 or a.out.is_symlink():raise ValueError('identity')
        words=prefix(a.dol.read_bytes(),a.elf.read_bytes())
        with a.out.open('x',encoding='utf-8') as f:f.write(render(words))
    except (OSError,ValueError,struct.error):
        print('V630_MAPPER_GEOMETRY accepted=0');return 1
    print('V630_MAPPER_GEOMETRY accepted=1 words=16 exact_dol_elf=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
