#!/usr/bin/env python3
"""Extend the focused private Open image with authentic OSSleepThread."""
import argparse,re,struct
from pathlib import Path
from make_v1245_open_fixture import build as prior
from make_v651_open_fixture import SOURCE
from make_v624_ipc_geometry import ROOT,exact_words
from make_v626_ipc_fixture import assemble,backward_polls
from make_start_to_ipc_sleep_v73 import SLEEP,STOP as SELECT,SIZE,EDGES
from prepare_v419_full_start import words_at,direct_bl,MAX_DOL
from make_private_elf_symbol_map import parse_functions
BLR=0x4e800020

def geometry(dol,elf):
    sizes=parse_functions(elf)
    if sizes.get(SLEEP)!=SIZE or not sizes.get(SELECT):raise ValueError('sleep extent')
    body=exact_words(dol,elf,SLEEP,SIZE//4)
    if body[-1]!=BLR:raise ValueError('sleep return')
    rows=[]
    for site,target in EDGES:
        w=exact_words(dol,elf,site,1)[0]
        if direct_bl(w,site)!=target or not sizes.get(target):raise ValueError('sleep edge')
        rows.append((target,site+4,w,exact_words(dol,elf,target,1)[0]))
    return body,tuple(rows),exact_words(dol,elf,SELECT,1)[0]

def extend(raw,csv,body,entry):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if not re.fullmatch(r'func_[0-9A-F]{8}',name) or not size or size%4 or pc in blocks:raise ValueError('sleep symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if SLEEP not in blocks or len(blocks[SLEEP])!=1 or blocks[SLEEP][0]!=body[0] or SELECT in blocks or SOURCE in blocks:
        raise ValueError('sleep predecessor')
    if len(body)!=SIZE//4 or body[-1]!=BLR:raise ValueError('sleep extent')
    blocks[SLEEP]=body
    blocks[SELECT]=(entry,BLR) # synthetic unreachable tail, stop at actual entry
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble({**blocks,SOURCE:words_at(raw,SOURCE,7)},ROOT),csv

def render(body,rows,entry):
    words={SLEEP+4*i:w for i,w in enumerate(body)};words[SELECT]=entry
    f=lambda n:f'0x{n:08x}u'
    return ('#pragma once\n#include "wii_post_ack_sleep_join_v1252.h"\nnamespace v1252 {\n'
      'inline constexpr std::array<undercover::wii::VectorEdge,3> edges{'
      +','.join('undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in rows)+'};\n'
      'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
      +','.join('Word{'+f(a)+','+f(w)+'}' for a,w in sorted(words.items()))+'};\n'
      'inline constexpr std::array<uint32_t,'+str(len(polls:=backward_polls({SLEEP:body})))+'> polls{'+','.join(map(f,polls))+'};\n}\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        raw,csv,ipc,op,header,vector,stm,data=prior(d,e)
        body,rows,entry=geometry(d,e);raw,csv=extend(raw,csv,body,entry)
        a.out.mkdir(mode=0o700)
        for n,s in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v639_private_open_expectations.h',op),
                    ('v626_private_words.h',header),('v629_private_stm_expectations.h',stm),('v1243_private_stm_data.h',data),
                    ('v1252_private_sleep.h',render(body,rows,entry))):
            (a.out/n).write_text(s)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'vector.bin').write_bytes(vector)
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1252_SLEEP_FIXTURE accepted=0');return 1
    print('V1252_SLEEP_FIXTURE accepted=1 original_sleep_words=59 select_entry=1 synthetic_select_tail=1');return 0
if __name__=='__main__':raise SystemExit(main())
