#!/usr/bin/env python3
"""Opt-in second callback prologue on the authenticated full native image."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_callback_prefix_v797 import plan
from prepare_v807_callback_prefix import render,SI
from prepare_v789_alarm_suffix import expectations
from prepare_v850_callback_return import BLOCK_END
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v667_si_dispatch import HANDLER
from prepare_v625_ipc_client import audit_native

def patch_label(body,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('second callback label')
    start=hits[0].end();stop=BLOCK_END.search(body,start);end=stop.start() if stop else len(body)
    block=body[start:end]
    old=f'    undercover::wii::v807::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    current=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n'
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or block.count(old)!=1 or not block.index('++ctx.inst_count;')<block.index(SI)<block.index(old):
        raise ValueError('second callback order')
    if 'v958::before(' in block:
        if block.count(current)!=1 or block.index(current)<block.index(SI):raise ValueError('second callback shared hook')
    else:
        i=block.index(SI)+len(SI)
        block=block[:i]+'    if(undercover::wii::v958::callback_active()) '+current.lstrip()+block[i:]
    # The first transfer witness is still alive in this process. Do not
    # route a shared compiler save to its retired device transaction.
    legacy=re.compile(r'(?m)^    ([^\n]*undercover::wii::(?:v680::before|v768::save_before)\(ctx,[^\n]+;\n)')
    if len(legacy.findall(block))>1:raise ValueError('second callback shared hook')
    block=legacy.sub(lambda m:'    if(!undercover::wii::v958::callback_active()) '+m[1],block)
    return body[:start]+block+body[end:]

def install(dol,elf,root,host):
    roots,C,S,site,_,_=plan(dol,elf);candidate,words,sites=expectations(dol,elf)
    prefix=roots[C][:-1];save=roots[S]
    if candidate!=C or tuple(prefix)!=words[:len(prefix)] or len(prefix)!=6 or len(save)!=7:raise ValueError('second callback geometry')
    dest=root/'nWiiRuntime/include/undercover'
    old=dest/'v807_private_callback_prefix.h';private=dest/'v958_private_second_ack.h';header=dest/'wii_callback_prefix_v800.h'
    if dest.is_symlink() or any(p.is_symlink() or not p.is_file() for p in (old,private,header)):raise ValueError('second callback destination')
    if old.read_text()!=render(C,S,prefix,save) or header.read_text()!=(host/header.name).read_text():raise ValueError('second callback identity')
    text=private.read_text()
    if '#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n' not in text or 'UNDERCOVER_V1009_PRIVATE_CALLBACK' in text:raise ValueError('second callback mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('second callback tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    def owner(a):
        found=[p for p,s in src.items() if owns_root(s,a)]
        if len(found)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('second callback owner')
        return found[0]
    verify_indirect(exact_function(src[owner(HANDLER)],HANDLER),sites[0])
    verify_direct(exact_function(src[owner(C)],C),site,S)
    for a,ws in ((C,prefix),(S,save)):
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        expected={a+4*i:(a,w) for i,w in enumerate(ws)}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('second callback coverage')
        for i,w in enumerate(ws):out=patch_label(out,a+4*i,w)
        s=replace_exact(s,body,out);inc='#include "undercover/wii_second_ack_live_v958.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    text=replace_exact(text,'#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n','#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n#define UNDERCOVER_V1009_PRIVATE_CALLBACK 1\n')
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    text+='namespace undercover::wii::v958 {\n'+f'inline constexpr uint32_t second_callback_save_root=0x{S:08x}u;\n'
    for name,ws in (('second_callback_prefix',prefix),('second_callback_save',save)):
        text+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n'
    changes[private]=text+'}\n'
    for p,s in changes.items():p.write_text(s)
    print('V1009_CALLBACK_ROUTE installed=1 original_prefix=6 original_save=7 shared_device=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('second callback label','second callback order','second callback shared hook','second callback geometry','second callback destination','second callback identity','second callback mode','second callback tree','second callback owner','second callback coverage','source seam')
        print('V1009_CALLBACK_PREP installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
