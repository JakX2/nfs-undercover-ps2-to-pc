#!/usr/bin/env python3
"""Private native IPC-client -> first IOS_Open construction fixture."""
import argparse,struct
from pathlib import Path
from make_v624_ipc_geometry import geometry as ipc_geometry,render as ipc_render,exact_words,ROOT,CALL,RETURN
from make_v639_open_geometry import geometry as open_geometry,render as open_render
from prepare_v629_stm_open import paths_at
from make_v626_ipc_fixture import assemble,backward_polls
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from prepare_v625_ipc_client import audit_native,patch_return
SOURCE=0x805290a8;SUBMIT=0x805195ec;OPEN=0x80519944;RESUME=0x80519a1c
def build(dol,elf):
    ipc=ipc_geometry(dol,elf);rows,handler,hword,ret=ipc
    op=open_geometry(dol,elf);edges,extra,blocks=op
    sizes=parse_functions(elf)
    blocks=dict(blocks)
    for pc in {r[0] for r in rows}:
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3:raise ValueError('client extent')
        body=exact_words(dol,elf,pc,n//4)
        if pc in blocks and blocks[pc]!=body:raise ValueError('shared extent')
        blocks[pc]=body
    # Stop at the actual submission entry before its first instruction.
    blocks[SUBMIT]=exact_words(dol,elf,SUBMIT,1)
    vector=exact_words(dol,elf,SOURCE,7)
    raw=assemble({**blocks,SOURCE:vector},ROOT)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    restore=0x805265d4
    resume=[restore+4*(i+1) for i,w in enumerate(blocks[restore]) if w>>26==31 and (w>>1)&1023==146]
    if len(resume)!=1:raise ValueError('restore resume')
    words={pc+4*i:w for pc,ws in blocks.items() for i,w in enumerate(ws)}
    for pc,w in ((CALL,rows[0][2]),(RETURN,ret),(handler,hword),(0x8052b08c,edges[0][2])):
        if pc in words:raise ValueError('fixture overlap')
        words[pc]=w
    paths=paths_at(dol)
    if not {1,2}.issubset({k for a,k in paths}):raise ValueError('path coverage')
    f=lambda v:f'0x{v:08x}u'
    h=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v626 {\n'
       'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
       +','.join('Word{'+f(pc)+','+f(w)+'}' for pc,w in sorted(words.items()))+'};\n'
       'inline constexpr uint32_t restore_resume='+f(resume[0])+';\n'
       'inline constexpr std::array<uint32_t,'+str(len(polls:=backward_polls(blocks)))+'> backward_polls{'+','.join(map(f,polls))+'};\n'
       'inline constexpr std::array<uint8_t,28> vector{'+','.join(map(str,struct.pack('>7I',*vector)))+'};\n'
       'inline constexpr std::array<uint32_t,2> paths{'+','.join(f(next(a for a,k in paths if k==kind)) for kind in (1,2))+'};\n}\n')
    return raw,csv,ipc_render(*ipc),open_render(op),h,struct.pack('>7I',*vector)
def trace(dol,elf,root):
    _,extra,blocks=open_geometry(dol,elf)
    expected={pc+4*i:(pc,w) for pc,ws in blocks.items() for i,w in enumerate(ws)}
    shards=sorted(root.glob('output_*.cpp'))
    n=audit_native((p.read_text() for p in shards),(root/'main_output.cpp').read_text(),expected)
    hits=0
    for p in shards:
        s=p.read_text()
        if f'loc_{RESUME:X}: ;' in s:
            p.write_text(patch_return(s,extra[2],RESUME));hits+=1
    if hits!=1:raise ValueError('resume coverage')
    print(f'V651_OPEN_TRANSLATION verified=1 native_words={n}')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);p.add_argument('--trace',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        if a.trace:trace(d,e,a.out);return 0
        raw,csv,ipc,op,h,vector=build(d,e)
        a.out.mkdir(mode=0o700)
        for name,body in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v639_private_open_expectations.h',op),('v626_private_words.h',h)):
            (a.out/name).write_text(body)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'vector.bin').write_bytes(vector)
    except (OSError,ValueError,struct.error) as e:
        allowed={'client extent','shared extent','restore resume','fixture overlap','fixture range','fixture span','path coverage','resume coverage','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch'}
        why=str(e) if str(e) in allowed else 'geometry'
        print('V651_OPEN_FIXTURE accepted=0 reason='+why.replace(' ','_'));return 1
    print('V651_OPEN_FIXTURE accepted=1 exact_dol_elf=1 paths=2');return 0
if __name__=='__main__':raise SystemExit(main())
