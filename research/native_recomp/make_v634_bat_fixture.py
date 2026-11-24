#!/usr/bin/env python3
"""Private native BAT mapping fixture: original instructions, no replacement code."""
import argparse,hashlib,struct
from pathlib import Path
from make_v626_ipc_fixture import assemble,backward_polls
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,direct_bl
from audit_v584_bat_translation import MAPS,geometry
from prepare_v591_memory_init import MAP,ENTRIES,RESUMES,TRAMP
CALL=0x8052776c
RETURN=CALL+4
END=0x80527688
def build(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    geometry(dol,dd)
    if hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('identity')
    sizes=parse_functions(elf)
    if sizes.get(MAP)!=END-MAP:raise ValueError('mapper extent')
    blocks={lo:exact_words(dol,elf,lo,(hi-lo)//4) for lo,hi,_ in MAPS}
    body=exact_words(dol,elf,MAP,(END-MAP)//4)
    if body[-1]!=0x4e800020:raise ValueError('mapper return')
    calls=[(MAP+4*i,direct_bl(w,MAP+4*i)) for i,w in enumerate(body) if w>>26==18 and w&3==1]
    if calls!=list(TRAMP):raise ValueError('mapper calls')
    blocks[MAP]=body
    def edge(site,pc):
        w=exact_words(dol,elf,site,1)[0]
        if direct_bl(w,site)!=pc:raise ValueError('edge')
        return pc,site+4,w,exact_words(dol,elf,pc,1)[0]
    rows=[edge(CALL,MAP)]+[edge(*x) for x in TRAMP]
    ew=[exact_words(dol,elf,pc,1)[0] for pc in ENTRIES]
    rw=[exact_words(dol,elf,pc,1)[0] for pc in RESUMES]
    fmt=lambda x:f'0x{x:08x}u'
    arr=lambda x:'{'+','.join(map(fmt,x))+'}'
    edg=lambda x:'VectorEdge'+arr(x)
    words={pc+4*i:w for pc,ws in blocks.items() for i,w in enumerate(ws)}
    words[CALL]=rows[0][2]
    polls=backward_polls(blocks)
    h=('#pragma once\n#include "wii_bat_mapping_witness_v590.h"\nnamespace undercover::wii::v634 {\n'
       'inline constexpr BatMappingExpectations expected{'+edg(rows[0])+',{{'+','.join(map(edg,rows[1:]))+'}},'+arr(ew)+','+arr(rw)+'};\n'
       'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
       +','.join('Word'+arr((pc,w)) for pc,w in sorted(words.items()))+'};\n'
       'inline constexpr std::array<uint32_t,'+str(len(polls))+'> polls'+arr(polls)+';\n}\n')
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble(blocks,MAP),csv,h
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,c,h=build(a.dol.read_bytes(),a.elf.read_bytes());a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(d);(a.out/'symbols.csv').write_text(c);(a.out/'v634_private_bat.h').write_text(h)
    except (OSError,ValueError,struct.error) as e:
        allowed={'identity','mapper extent','mapper return','mapper calls','edge','size','mapper geometry','fixture geometry','fixture range','fixture span','fixture overlap','poll geometry'}
        print('V634_BAT_FIXTURE accepted=0 reason='+(str(e) if str(e) in allowed else 'input').replace(' ','_'));return 1
    print('V634_BAT_FIXTURE owner=1 accepted=1 roots=4');return 0
if __name__=='__main__':raise SystemExit(main())
