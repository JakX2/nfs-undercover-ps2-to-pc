#!/usr/bin/env python3
"""Private focused original IPC ACK handler, after the original Open/submit lane."""
import argparse,re,struct
from pathlib import Path
from make_v1245_open_fixture import build as prior
from make_v651_open_fixture import SOURCE
from make_v624_ipc_geometry import ROOT,exact_words,geometry as ipc_geometry
from make_v626_ipc_fixture import assemble,backward_polls
from make_start_to_ipc_ack_v77 import IPC,SPANS,EDGES
from prepare_v419_full_start import words_at,direct_bl,MAX_DOL
from make_private_elf_symbol_map import parse_functions
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_bat_roots_v586 import ROOT as ANALYZE_ROOT,READ
from apply_irq_bootstrap_v475 import rewrite
BLR=0x4e800020
DISPATCH_RETURN=0x80526cac

# The reply processor and wake function are forbidden on ACK-only entry.
FORBIDDEN=(0x805190c0,0x8052a51c)
ALLOWED=(IPC,0x8051b060,0x8051905c,0x8051906c)

def geometry(dol,elf):
    sizes=parse_functions(elf)
    _,handler,_,_=ipc_geometry(dol,elf)
    if handler!=IPC:raise ValueError('ACK registered handler')
    spans=dict(SPANS)
    native={}
    for pc in ALLOWED:
        size=sizes.get(pc,0)
        if not 4<=size<=4096 or size%4 or (pc in spans and size!=spans[pc]):
            raise ValueError('ACK extent')
        body=exact_words(dol,elf,pc,size//4)
        if body[-1]!=BLR:raise ValueError('ACK return')
        native[pc]=body
    # Authenticate all direct BLs in the actual admitted handler, not only
    # the branches taken during the first ACK trial.
    edges=[]
    for i,w in enumerate(native[IPC]):
        if w>>26!=18 or w&3!=1:continue
        site=IPC+4*i;target=direct_bl(w,site)
        if (site,target) not in EDGES or target not in (*ALLOWED,*FORBIDDEN):
            raise ValueError('ACK call closure')
        edges.append((target,site+4,w,exact_words(dol,elf,target,1)[0]))
    if {(lr-4,t) for t,lr,_,_ in edges}!={(s,t) for s,t in EDGES if IPC<=s<IPC+4*len(native[IPC])}:
        raise ValueError('ACK edge coverage')
    # Prior V77 dispatch evidence: actual indirect call and return site.
    word=exact_words(dol,elf,DISPATCH_RETURN-4,1)[0]
    if word!=0x4e800421:raise ValueError('ACK indirect call')
    stop={pc:exact_words(dol,elf,pc,1) for pc in FORBIDDEN}
    return native,stop,tuple(edges),word

def extend(raw,csv,native,stop):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if not re.fullmatch(r'func_[0-9A-F]{8}',name) or not size or size%4 or pc in blocks:raise ValueError('ACK symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if IPC in blocks or set(stop)&set(blocks) or SOURCE in blocks:raise ValueError('ACK predecessor')
    for pc,ws in native.items():
        if pc in blocks and blocks[pc]!=ws:raise ValueError('ACK shared extent')
        blocks[pc]=ws
    # Authentic entry, synthetic unreachable BLR: the observer refuses
    # these roots before any instruction executes.
    blocks.update({pc:ws+(BLR,) for pc,ws in stop.items()})
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble({**blocks,SOURCE:words_at(raw,SOURCE,7)},ROOT),csv

def render(native,stop,edges,word):
    words={pc+4*i:w for pc,ws in {**native,**stop}.items() for i,w in enumerate(ws)}
    words[DISPATCH_RETURN-4]=word
    f=lambda n:f'0x{n:08x}u'
    return ('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v1255 {\n'
      'inline constexpr uint32_t handler='+f(IPC)+',returned='+f(DISPATCH_RETURN)+';\n'
      'inline constexpr std::array<undercover::wii::VectorEdge,'+str(len(edges))+'> edges{'
      +','.join('undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in edges)+'};\n'
      'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
      +','.join('Word{'+f(a)+','+f(w)+'}' for a,w in sorted(words.items()))+'};\n'
      'inline constexpr std::array<uint32_t,'+str(len(polls:=backward_polls(native)))+'> polls{'+','.join(map(f,polls))+'};\n}\n')

def analyzer(source,native,stop):
    spans=tuple(sorted((pc,len(ws)*4) for pc,ws in native.items()))+tuple(sorted((pc,8) for pc in stop))
    if set(native)!=set(ALLOWED) or set(stop)!=set(FORBIDDEN):raise ValueError('ACK ownership')
    roots=(ANALYZE_ROOT+'\n    const auto ack_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+
        '      return 0;\n    };\n    if(ack_owner(func_start)&&ack_owner(func_start)!=func_start)continue;')
    read='        const auto ack_root=ack_owner(current_pc);\n        if((ack_root&&ack_root!=func_start)||(ack_owner(func_start)&&ack_root!=func_start))break;\n'+READ
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc,_ in spans)+')func.hle_hook_name.clear();'
    return rewrite(source,((ANALYZE_ROOT,roots),(READ,read),(SCANNER,scanner)))

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--analyzer',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        native,stop,edges,word=geometry(d,e)
        if a.analyzer:
            if a.analyzer.is_symlink():raise ValueError('ACK analyzer')
            a.analyzer.write_text(analyzer(a.analyzer.read_text(),native,stop))
            print('V1255_ACK_ANALYZER installed=1 scoped=1');return 0
        raw,csv,ipc,op,header,vector,stm,data=prior(d,e)
        raw,csv=extend(raw,csv,native,stop)
        a.out.mkdir(mode=0o700)
        for n,s in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v639_private_open_expectations.h',op),
                    ('v626_private_words.h',header),('v629_private_stm_expectations.h',stm),('v1243_private_stm_data.h',data),
                    ('v1255_private_ack.h',render(native,stop,edges,word))):
            (a.out/n).write_text(s)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'vector.bin').write_bytes(vector)
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1255_ACK_FIXTURE accepted=0');return 1
    print('V1255_ACK_FIXTURE accepted=1 native_roots=4 forbidden_roots=2 modeled_dispatch=1');return 0
if __name__=='__main__':raise SystemExit(main())
