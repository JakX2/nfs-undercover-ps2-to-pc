#!/usr/bin/env python3
"""Private native post-wireless callback suffix, without executing either callee."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_callback_after_setter_v842 import plan
from prepare_owner_callback_frontier_v820 import plan as frontier_plan
from prepare_v831_callback_frontier import render as render_frontier
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v1097_after_alarm import patch_label,fmt
from prepare_v1106_postalarm_time import verify_resume
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v1029_third_transfer import replace_body,include_once

def render(C,resume,words,stops):
    h='#pragma once\n#include "wii_callback_suffix_v841.h"\nnamespace undercover::wii::v1123 {\n'
    h+=f'inline constexpr std::array<CallbackSuffixWord,{len(words)}> rows{{{{'+','.join(
        'CallbackSuffixWord{'+fmt((pc,w))+'}' for pc,w in sorted(words.items()))+'}};\n'
    h+='inline constexpr CallbackSuffixExpectation expected{'+fmt((C,C+688,resume))+',rows,{{'
    h+=','.join('CallbackSuffixEdge{'+fmt((pc,dst or 0))+f',{i}u'+'}' for pc,(i,k,dst) in sorted(stops.items()))+'}}};\n'
    return h+'}\n'

def install(dol,elf,root,host):
    joined,C,resume,seen,stops=plan(dol,elf,True)
    q,prior,frontier,A,B=frontier_plan(dol,elf)
    base,T,D,U,R,ts,leaves=q;_,candidate,_,_,_,_=base
    original=exact(dol,elf,C,172);cb,words,_=expectations(dol,elf)
    if C!=candidate or C!=cb or len(original)!=172 or tuple(original)!=tuple(words) or \
       len(seen)!=21 or len(set(seen))!=21 or resume not in seen or len(prior)!=27 or \
       sorted((i,k) for i,k,_ in stops.values())!=[(4,2),(13,1)] or \
       sorted(o for o,_ in frontier.values())!=[3,5] or \
       {pc+4 for pc,(i,dst) in frontier.items() if i==3}!={resume} or \
       not set(stops).issubset(seen) or any(pc&3 or not C<=pc<C+688 for pc in seen):
        raise ValueError('postalarm suffix geometry')
    rows={pc:original[(pc-C)//4] for pc in seen}
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    frontier_header=dest/'v831_private_callback_frontier.h';suffix_header=dest/'v1123_private_postalarm_suffix.h'
    witnesses=('wii_callback_suffix_v841.h','wii_third_alarm_suffix_v1047.h')
    if dest.is_symlink() or suffix_header.exists() or suffix_header.is_symlink() or \
       any(p.is_symlink() or not p.is_file() for p in (private,frontier_header,*[dest/n for n in witnesses])):
        raise ValueError('postalarm suffix destination')
    if frontier_header.read_text()!=render_frontier(C,ts+4,{pc:(C,original[(pc-C)//4]) for pc in prior},frontier) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('postalarm suffix identity')
    old=private.read_text();macro='#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1\n'
    newmacro='#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX' in old:
        raise ValueError('postalarm suffix mode')
    row=f'inline constexpr std::array<uint32_t,{len(words)}> third_postalarm_words{{'+fmt(words)+'};\n'
    if old.count(row)!=1 or len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm suffix metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('postalarm suffix tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    owners=[p for p,s in src.items() if owns_root(s,C)]
    if len(owners)!=1 or sum(entry_count(s,C) for s in src.values())!=1:
        raise ValueError('postalarm suffix owner')
    path=owners[0];source=src[path];body=exact_function(source,C);out=body
    for pc,(i,k,dst) in sorted(stops.items()):
        if k==1:verify_direct(body,pc,dst)
        else:verify_indirect(body,pc)
    if audit_native([body],outer,{pc:(C,w) for pc,w in rows.items()})!=len(rows):
        raise ValueError('postalarm suffix coverage')
    reuse=set(seen)&(set(prior)|{pc+4 for pc in frontier})
    if resume not in reuse:raise ValueError('postalarm suffix resume')
    for pc,w in sorted(rows.items()):
        if pc in reuse:verify_resume(out,pc,w)
        else:out=patch_label(out,pc,w)
    updated=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    path.write_text(updated);private.write_text(old.replace(macro,macro+newmacro,1))
    suffix_header.write_text(render(C,resume,rows,stops))
    print(f'V1124_POSTALARM_SUFFIX_ROUTE installed=1 labels=21 reused={len(reuse)} direct_edges=1 indirect_edges=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('postalarm suffix geometry','postalarm suffix destination','postalarm suffix identity',
              'postalarm suffix mode','postalarm suffix metadata','postalarm suffix tree','postalarm suffix owner',
              'postalarm suffix coverage','postalarm suffix resume','postalarm time resume',
              'postalarm label','postalarm tick','postalarm duplicate','postalarm hook','helper call label',
              'helper direct native call','helper native return edge','native IPC label identity','native IPC label body',
              'native IPC coverage','native IPC dispatch','indirect label','indirect LR','indirect dispatch','indirect fallback')
        print('V1124_POSTALARM_SUFFIX_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
