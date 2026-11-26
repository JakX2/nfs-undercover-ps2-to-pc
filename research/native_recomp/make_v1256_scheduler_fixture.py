#!/usr/bin/env python3
"""Private native SelectThread continuation to the original interrupt enable."""
import argparse,re,struct
from pathlib import Path
from make_v1245_open_fixture import build as prior
from make_v1252_sleep_fixture import geometry as sleep_geometry,extend as sleep_extend,render as sleep_render,SLEEP,SELECT,SIZE
from make_v651_open_fixture import SOURCE
from make_v624_ipc_geometry import ROOT,exact_words
from make_v626_ipc_fixture import assemble,backward_polls
from make_start_to_select_thread_v74 import SPANS,EDGES
from make_start_to_thread_return_v61 import CALLBACK,CALLBACK_PTR
from prepare_v453_debug_leaf import data_at
from prepare_v419_full_start import words_at,direct_bl,MAX_DOL
from make_private_elf_symbol_map import parse_functions
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_bat_roots_v586 import ROOT as ANALYZE_ROOT,READ
from apply_irq_bootstrap_v475 import rewrite
BLR=0x4e800020
GET=0x80522928;SAVE=0x80522934;SET=0x805228cc;ENABLE=0x805265c0
FORBIDDEN=(0x805229b4,0x80522af4)
ALLOWED=(SELECT,GET,SAVE,SET,ENABLE,CALLBACK)

def geometry(dol,elf):
    sizes=parse_functions(elf);native={}
    expect={**dict(SPANS),SET:0x5c,CALLBACK:4}
    for pc in ALLOWED:
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n%4 or (pc in expect and n!=expect[pc]) or (pc==ENABLE and n>20):
            raise ValueError('scheduler extent')
        body=exact_words(dol,elf,pc,n//4)
        if body[-1]!=BLR:raise ValueError('scheduler return')
        native[pc]=body
    if struct.unpack('>I',data_at(dol,CALLBACK_PTR,4))[0]!=CALLBACK:raise ValueError('scheduler callback pointer')
    edges=[];indirect=[]
    for i,w in enumerate(native[SELECT]):
        site=SELECT+4*i
        if w>>26==18 and w&3==1:
            target=direct_bl(w,site)
            if (site,target) not in EDGES:raise ValueError('scheduler direct edge')
            edges.append((target,site+4,w,exact_words(dol,elf,target,1)[0]))
        elif w>>26==19 and (w>>1)&1023==528 and w&1:
            indirect.append((CALLBACK,site+4,w,native[CALLBACK][0]))
    if {(lr-4,t) for t,lr,_,_ in edges}!=set(EDGES) or not 1<=len(indirect)<=4:
        raise ValueError('scheduler edge coverage')
    mt=[(ENABLE+4*(i+1),w) for i,w in enumerate(native[ENABLE]) if w>>26==31 and (w>>1)&1023==146]
    if len(mt)!=1:raise ValueError('scheduler enable seam')
    stops={pc:exact_words(dol,elf,pc,1) for pc in FORBIDDEN}
    return native,stops,tuple(edges),tuple(indirect),mt[0]

def extend(raw,csv,native,stops):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if not re.fullmatch(r'func_[0-9A-F]{8}',name) or not size or size%4 or pc in blocks:raise ValueError('scheduler symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if SELECT not in blocks or blocks[SELECT]!=(native[SELECT][0],BLR) or set(stops)&set(blocks) or SOURCE in blocks:
        raise ValueError('scheduler predecessor')
    for pc,ws in native.items():
        if pc!=SELECT and pc in blocks and blocks[pc]!=ws:raise ValueError('scheduler shared extent')
        blocks[pc]=ws
    blocks.update({pc:ws+(BLR,) for pc,ws in stops.items()})
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble({**blocks,SOURCE:words_at(raw,SOURCE,7)},ROOT,max_roots=48),csv

def render(native,stops,edges,indirect,mt):
    words={pc+4*i:w for pc,ws in {**native,**stops}.items() for i,w in enumerate(ws)}
    f=lambda n:f'0x{n:08x}u'
    def rows(name,items):
        return ('inline constexpr std::array<undercover::wii::VectorEdge,'+str(len(items))+'> '+name+'{'
          +','.join('undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in items)+'};\n')
    resumes=sorted({pc+4*(i+1) for pc,ws in native.items() for i,w in enumerate(ws[:-1]) if w>>26==31 and (w>>1)&1023==146}|set(backward_polls(native)))
    return ('#pragma once\n#include "wii_post_ack_scheduler_join_v1256.h"\nnamespace v1256 {\n'
      +rows('edges',edges)+rows('indirect',indirect)
      +'inline constexpr uint32_t resume='+f(mt[0])+',resume_word='+f(mt[1])+';\n'
      'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'
      +','.join('Word{'+f(a)+','+f(w)+'}' for a,w in sorted(words.items()))+'};\n'
      'inline constexpr std::array<uint32_t,'+str(len(resumes))+'> polls{'+','.join(map(f,resumes))+'};\n}\n')

def analyzer(source,native,stops):
    spans=tuple(sorted([(pc,len(ws)*4) for pc,ws in native.items()]+[(pc,8) for pc in stops]))
    if set(native)!=set(ALLOWED) or set(stops)!=set(FORBIDDEN):raise ValueError('scheduler ownership')
    roots=(ANALYZE_ROOT+'\n    const auto sched_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+
        '      return 0;\n    };\n    if(sched_owner(func_start)&&sched_owner(func_start)!=func_start)continue;')
    read='        const auto sched_root=sched_owner(current_pc);\n        if((sched_root&&sched_root!=func_start)||(sched_owner(func_start)&&sched_root!=func_start))break;\n'+READ
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc,_ in spans)+')func.hle_hook_name.clear();'
    return rewrite(source,((ANALYZE_ROOT,roots),(READ,read),(SCANNER,scanner)))

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--analyzer',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        native,stops,edges,indirect,mt=geometry(d,e)
        if a.analyzer:
            if a.analyzer.is_symlink():raise ValueError('scheduler analyzer')
            a.analyzer.write_text(analyzer(a.analyzer.read_text(),native,stops))
            print('V1256_SCHED_ANALYZER installed=1 scoped=1');return 0
        raw,csv,ipc,op,header,vector,stm,data=prior(d,e)
        body,rows,entry=sleep_geometry(d,e);raw,csv=sleep_extend(raw,csv,body,entry)
        raw,csv=extend(raw,csv,native,stops)
        a.out.mkdir(mode=0o700)
        for n,s in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v639_private_open_expectations.h',op),
                    ('v626_private_words.h',header),('v629_private_stm_expectations.h',stm),('v1243_private_stm_data.h',data),
                    ('v1252_private_sleep.h',sleep_render(body,rows,entry)),('v1256_private_scheduler.h',render(native,stops,edges,indirect,mt))):
            (a.out/n).write_text(s)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'vector.bin').write_bytes(vector)
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1256_SCHED_FIXTURE accepted=0');return 1
    print('V1256_SCHED_FIXTURE accepted=1 native_roots=6 forbidden_roots=2 enable_seam=1');return 0
if __name__=='__main__':raise SystemExit(main())
