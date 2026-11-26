#!/usr/bin/env python3
"""Prepare the post-ACK Open source seams without mutating the generated tree.

Keep the earlier STM/IPC edits and original boot SC owners intact. This
planner is deliberately separate from the opt-in live integration.
"""
import re
from pathlib import Path
from make_v639_open_geometry import geometry,render,OPEN,PROFILE,ALLOC
from apply_open_roots_v645 import irq_spans
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native,patch_return
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v1029_third_transfer import replace_body
from prepare_v1141_postalarm_handler import block_at
from prepare_v641_open_request import patch_sc,IOS_INC,IOS_HOOK
from apply_open_cache_trace_v649 import PAIRS
from apply_irq_bootstrap_v475 import rewrite
from prepare_v419_full_start import replace_exact
from prepare_v574_dsp_sc import expectations as vector_geometry

SC=0x805222e8
RESUME=0x80519a1c
SC_INCLUDE='#include "undercover/wii_post_ack_open_binding_v1246.h"'
SC_HOOK='  if (undercover::wii::v1246::try_sc(ctx)) return false;'

def patch_ios(s):
    # Require the previously authenticated arena and boot SC handlers.
    boot='  if (undercover::wii::v574::try_sc(ctx)) return false;'
    if s.count(boot)!=1 or s.count(IOS_HOOK)!=1 or SC_INCLUDE in s or SC_HOOK in s:
        raise ValueError('ACK Open IOS seam')
    if s.index(IOS_HOOK)>s.index(boot):
        raise ValueError('ACK Open IOS order')
    return replace_exact(replace_exact(s,IOS_INC,IOS_INC+'\n'+SC_INCLUDE),IOS_HOOK,SC_HOOK+'\n'+IOS_HOOK)

def verify_tail(body,word):
    block=block_at(body,PROFILE,word)
    # Pinned NWiiRecomp emits an unconditional external branch as a
    # PC assignment followed by return to the native dispatcher.
    # Do not accept local jumps or a fabricated link-register write.
    if len(re.findall(r'(?mi)^    ctx\.pc = 0x'+f'{ALLOC:X}'+r'; return;$',block))!=1 or \
       any(x in block for x in ('ctx.lr =','goto loc_','interpret_step','micro_interpret','handle_syscall')):
        raise ValueError('ACK Open allocator tail')

def plan_native(src,outer,edits,g):
    rows,extra,blocks=g
    expected={pc+4*i:(pc,w) for pc,ws in blocks.items() for i,w in enumerate(ws)}
    for target,_,_,w in rows:
        if target in blocks and blocks[target][0]!=w:raise ValueError('ACK Open root word')
        expected[target]=(target,w)
    if len(rows)!=6 or PROFILE not in blocks or len(blocks[PROFILE])!=1 or ALLOC not in blocks:
        raise ValueError('ACK Open geometry')
    if audit_native(src.values(),outer,expected)!=len(expected):
        raise ValueError('ACK Open coverage')
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:
            raise ValueError('ACK Open entry')
        return hits[0]
    for a in {r[0] for r in rows}|{ALLOC}:owner(a)
    for target,lr,w,_ in rows:
        site=lr-4
        # Exact original BL in the unique generated label, including the
        # STM call which is outside the Open spans.
        pat=re.compile(r'(?mi)^loc_'+f'{site:X}'+r': ;\n    // 0x'+f'{site:08X}: {w:08X}'+r'$')
        hits=[s for s in src.values() if pat.search(s)]
        if sum(len(pat.findall(s)) for s in hits)!=1:
            raise ValueError('ACK Open edge word')
        verify_direct(hits[0],site,target)
    verify_tail(exact_function(src[owner(PROFILE)],PROFILE),blocks[PROFILE][0])
    changes=dict(edits)
    for pc,fn in ((RESUME,lambda s:patch_return(s,extra[2],RESUME)),(SC,patch_sc)):
        paths=[p for p,s in src.items() if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s)]
        if len(paths)!=1:raise ValueError('ACK Open trace owner')
        p=paths[0];changes[p]=fn(changes.get(p,src[p]))
    return changes

def prepare(dol,elf,src,outer,edits,dest,host,ios_text,cpu_text,old):
    g=geometry(dol,elf)
    rows,extra,blocks=g
    blocks=dict(blocks)
    for pc,n in irq_spans(dol,elf):
        ws=exact_words(dol,elf,pc,n//4)
        if pc in blocks and blocks[pc]!=ws:raise ValueError('ACK Open shared extent')
        blocks[pc]=ws
    changes=plan_native(src,outer,edits,(rows,extra,blocks))
    # The existing V574 vector metadata must match the owner image.
    header,_,_=vector_geometry(dol)
    vector=dest/'v574_private_sc_expectations.h'
    if vector.is_symlink() or not vector.is_file() or vector.read_text()!=header:
        raise ValueError('ACK Open vector identity')
    if 'UNDERCOVER_V1246_PRIVATE_ACK_OPEN' in old or dest.is_symlink():
        raise ValueError('ACK Open destination')
    files={dest/'v1246_private_ack_open.h':render(g)+'\n#include "wii_post_ack_open_join_v1242.h"\n'}
    for name in ('wii_open_request_witness_v639.h','wii_open_sc_route_v637.h','open_cache_range_trace_v649.h','wii_post_ack_open_join_v1242.h','wii_post_ack_open_binding_v1246.h'):
        files[dest/name]=(host/name).read_text()
    for path,data in files.items():
        if path.is_symlink() or (path.exists() and (path.name=='v1246_private_ack_open.h' or not path.is_file() or path.read_text()!=data)):
            raise ValueError('ACK Open destination')
    files={p:s for p,s in files.items() if not p.exists()}
    return changes,files,patch_ios(ios_text),rewrite(cpu_text,PAIRS)
