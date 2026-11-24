#!/usr/bin/env python3
"""Private isolated original IPC client test, using only authenticated function spans."""
import argparse,struct
from pathlib import Path
from make_v624_ipc_geometry import geometry,render,exact_words,ROOT,CALL,RETURN,SPANS
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL,direct_bl
NOP=0x60000000
def assemble(blocks,entry):
    if not blocks or len(blocks)>32 or entry not in blocks:raise ValueError('fixture geometry')
    lo=min(blocks);hi=max(pc+4*len(ws) for pc,ws in blocks.items())
    if lo&3 or hi-lo>0x40000 or lo<0x80004000 or hi>0x81800000:raise ValueError('fixture range')
    raw=bytearray(struct.pack('>I',NOP)*((hi-lo)//4));occupied=set()
    for pc,ws in sorted(blocks.items()):
        if pc&3 or not ws or len(ws)>1024:raise ValueError('fixture span')
        for i,w in enumerate(ws):
            at=pc+4*i
            if at in occupied:raise ValueError('fixture overlap')
            occupied.add(at);struct.pack_into('>I',raw,at-lo,w)
    h=bytearray(256)
    for off,v in ((0,256),(0x48,lo),(0x90,len(raw)),(0xe0,entry)):struct.pack_into('>I',h,off,v)
    return bytes(h)+raw
def build(dol,elf):
    g=geometry(dol,elf);rows,handler,hword,ret=g;sizes=parse_functions(elf)
    roots={r[0] for r in rows}
    if len(roots)!=15 or not {pc for pc,_ in SPANS}.issubset(roots):raise ValueError('root count')
    blocks={}
    for pc in sorted(roots):
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3:raise ValueError('fixture span')
        ws=exact_words(dol,elf,pc,n//4)
        if ws[-1]!=0x4e800020:raise ValueError('fixture return')
        for i,w in enumerate(ws):
            if w>>26==18 and w&3==1 and direct_bl(w,pc+4*i) not in roots:raise ValueError('fixture call closure')
        blocks[pc]=ws
    restore=0x805265d4
    resume=[restore+4*(i+1) for i,w in enumerate(blocks[restore]) if w>>26==31 and (w>>1)&1023==146]
    if len(resume)!=1:raise ValueError('restore resume')
    words={pc+4*i:w for pc,ws in blocks.items() for i,w in enumerate(ws)}
    for pc,w in ((CALL,rows[0][2]),(RETURN,ret),(handler,hword)):
        if pc in words:raise ValueError('fixture overlap')
        words[pc]=w
    fmt=lambda v:f'0x{v:08x}u'
    image=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v626 {\n'
           'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
           +','.join('Word{'+fmt(pc)+','+fmt(w)+'}' for pc,w in sorted(words.items()))+'};\n'
           'inline constexpr uint32_t restore_resume='+fmt(resume[0])+';\n}\n')
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in blocks.items())
    return assemble(blocks,ROOT),csv,render(*g),image
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        raw,csv,expect,image=build(a.dol.read_bytes(),a.elf.read_bytes())
        a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'symbols.csv').write_text(csv)
        (a.out/'v624_private_ipc_expectations.h').write_text(expect)
        (a.out/'v626_private_words.h').write_text(image)
    except (OSError,ValueError,struct.error) as e:
        allow={'root count','fixture geometry','fixture range','fixture span','fixture overlap','fixture return','fixture call closure','restore resume','size'}
        reason=str(e) if str(e) in allow else 'identity_or_io'
        print('V626_IPC_FIXTURE accepted=0 reason='+reason.replace(' ','_'));return 1
    print('V626_IPC_FIXTURE owner=1 accepted=1 native_roots=15')
    return 0
if __name__=='__main__':raise SystemExit(main())
