#!/usr/bin/env python3
"""Independent original console-report selector census using native code.

Only the selection slice is installed. The native fixture enters at the
real console-query return with an explicitly supplied return value, then
stops before any OSReport instruction. No output backend is claimed.
"""
import argparse,struct
from pathlib import Path
from make_v594_boot_report_geometry import geometry,START,END,REPORT,TARGETS
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v453_debug_leaf import data_at
from make_v626_ipc_fixture import assemble
from make_private_elf_symbol_map import parse_functions
ENTRY=0x80520410
END_SLICE=0x8052055c
DATA=0x8060b7a8
CONSOLE=0x8051fd44
def build(dol,elf):
    bctr,table=geometry(dol,elf)
    words=exact_words(dol,elf,ENTRY,(END_SLICE-ENTRY)//4)
    sites=tuple(ENTRY+4*i+4 for i,w in enumerate(words) if w>>26==18 and w&3==1 and direct_bl(w,ENTRY+4*i)==REPORT)
    if not 7<=len(sites)<=24:raise ValueError('site count')
    # Include the genuine report epilogue instruction immediately after
    # the last possible print call as a label; never execute past Print.
    blocks={ENTRY:words,REPORT:(0x4e800020,)}
    sizes=parse_functions(elf);pending=[CONSOLE]
    while pending:
        pc=pending.pop()
        if pc in blocks:continue
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3 or len(blocks)>=16:raise ValueError('console closure')
        body=exact_words(dol,elf,pc,n//4);blocks[pc]=body
        for i,w in enumerate(body):
            if w>>26==18 and w&3==1:
                target=direct_bl(w,pc+4*i)
                if target not in blocks:pending.append(target)
    raw=bytearray(assemble(blocks,ENTRY))
    data=data_at(dol,DATA,600)
    for off,v in ((0x1c,len(raw)),(0x64,DATA),(0xac,len(data))):struct.pack_into('>I',raw,off,v)
    raw.extend(data)
    # V594's root-scoped analyzer is for the full report function. This
    # isolated selector uses its own exact entry and no arbitrary roots.
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    f=lambda n:f'0x{n:08x}u'
    h=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v642 {\n'
       'inline constexpr std::array<uint32_t,'+str(len(sites))+'> sites{'+','.join(map(f,sites))+'};\n'
       'inline constexpr std::array<uint8_t,600> data{'+','.join(map(str,data))+'};\n'
       'inline constexpr uint32_t bctr='+f(bctr)+';\n'
       'inline constexpr std::array<uint32_t,'+str(len(blocks)-2)+'> roots{'+','.join(f(pc) for pc in sorted(blocks) if pc not in (ENTRY,REPORT))+'};\n'
       'inline constexpr std::array<uint32_t,'+str(sum(len(ws) for pc,ws in blocks.items() if pc not in (ENTRY,REPORT)))+'> console_words{'+','.join(f(w) for pc,ws in sorted(blocks.items()) if pc not in (ENTRY,REPORT) for w in ws)+'};\n}\n')
    return raw,csv,h
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        raw,csv,h=build(a.dol.read_bytes(),a.elf.read_bytes());a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'symbols.csv').write_text(csv);(a.out/'v642_private_report.h').write_text(h)
    except (OSError,ValueError,struct.error) as e:
        print('V642_REPORT_FIXTURE accepted=0 reason='+('site_count' if str(e)=='site count' else 'geometry'));return 1
    print('V642_REPORT_FIXTURE accepted=1 exact_dol_elf=1 isolated=1');return 0
if __name__=='__main__':raise SystemExit(main())
