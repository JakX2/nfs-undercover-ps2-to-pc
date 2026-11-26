#!/usr/bin/env python3
"""Non-mutating private planner for original first IOS submission."""
import re
from pathlib import Path
from make_v651_open_fixture import submit_geometry,SUBMIT,SLEEP
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native,patch_return
from prepare_v680_si_helper import verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v641_open_request import NEW_SC
from apply_native_ios_mmio_v418 import BIND
from prepare_v419_full_start import replace_exact

RESUME=0x8051963c
SC=0x805222e8
INCLUDE='#include "undercover/wii_native_ios_binding.h"'
WRITE='  if ('+BIND+'::write32(addr, val)) return;'
SUBMIT_INCLUDE='#include "undercover/wii_post_ack_submit_binding_v1257.h"'
SUBMIT_WRITE='  if (undercover::wii::v1257::try_write(addr, val)) return;'
SC_ROUTE='  if (undercover::wii::v1246::try_sc(ctx)) return false;'

def patch_mmio(s):
    # Run ahead of native binding, but after any previous SI ownership gate.
    # The eventual submit binding must decline outside its own active route.
    if s.count(INCLUDE)!=1 or s.count(WRITE)!=1 or SUBMIT_INCLUDE in s or SUBMIT_WRITE in s:
        raise ValueError('submit MMIO seam')
    return replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n'+SUBMIT_INCLUDE),WRITE,SUBMIT_WRITE+'\n'+WRITE)

def plan(src,outer,edits,blocks,edges,resume_word,ios,mmio):
    if len(edges)!=14 or SUBMIT not in blocks or len(blocks.get(SLEEP,()))!=1:
        raise ValueError('submit geometry')
    expected={pc+4*i:(pc,w) for pc,ws in blocks.items() for i,w in enumerate(ws)}
    for target,lr,branch,word in edges:
        if target in blocks and blocks[target][0]!=word:raise ValueError('submit target word')
        expected[target]=(target,word)
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('submit coverage')
    for target in {t for t,_,_,_ in edges}|{SUBMIT}:
        hits=[s for s in src.values() if owns_root(s,target)]
        if len(hits)!=1 or sum(entry_count(s,target) for s in src.values())!=1:raise ValueError('submit root trace')
    for target,lr,branch,_ in edges:
        site=lr-4
        pat=re.compile(r'(?mi)^loc_'+f'{site:X}'+r': ;\n    // 0x'+f'{site:08X}: {branch:08X}'+r'$')
        hits=[s for s in src.values() if pat.search(s)]
        if sum(len(pat.findall(s)) for s in hits)!=1:raise ValueError('submit call word')
        verify_direct(hits[0],site,target)
    # Reuse the previously installed native SC route, including its exact
    # pre-instruction PC checkpoint. Never patch the same SC twice.
    current={p:edits.get(p,s) for p,s in src.items()}
    sc=[s for s in current.values() if f'loc_{SC:X}: ;' in s]
    if len(sc)!=1 or sc[0].count(NEW_SC)!=1 or ios.count(SC_ROUTE)!=1:
        raise ValueError('submit SC predecessor')
    paths=[p for p,s in src.items() if re.search(r'(?mi)^loc_'+f'{RESUME:X}'+r': ;$',s)]
    if len(paths)!=1:raise ValueError('submit resume owner')
    changes=dict(edits);path=paths[0]
    changes[path]=patch_return(current[path],resume_word,RESUME)
    return changes,patch_mmio(mmio)

def render(edges):
    fmt=lambda row:'VectorEdge{'+','.join(f'0x{x:08x}u' for x in row)+'}'
    return ('#pragma once\n#include "wii_post_ack_submit_join_v1251.h"\n'
            'namespace undercover::wii::v1257 {\n'
            'inline constexpr std::array<VectorEdge,14> expected_submit{'+','.join(map(fmt,edges))+'};\n}\n')

def prepare(dol,elf,src,outer,edits,dest,host,ios,mmio):
    blocks,edges=submit_geometry(dol,elf)
    changes,new_mmio=plan(src,outer,edits,blocks,edges,exact_words(dol,elf,RESUME,1)[0],ios,mmio)
    if dest.is_symlink():raise ValueError('submit destination')
    files={dest/'v1257_private_submit.h':render(edges),
           dest/'wii_post_ack_submit_join_v1251.h':(host/'wii_post_ack_submit_join_v1251.h').read_text()}
    for p,s in files.items():
        if p.is_symlink() or (p.exists() and (p.name=='v1257_private_submit.h' or not p.is_file() or p.read_text()!=s)):
            raise ValueError('submit destination')
    # Return a plan only; do not install the MMIO interception until the
    # live binding header and CPU-context ownership have been integrated.
    return changes,{p:s for p,s in files.items() if not p.exists()},new_mmio
