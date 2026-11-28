#!/usr/bin/env python3
"""Opt-in original Wii scheduler/OSLoadContext/RFI Windows native continuation.

Reuse the Linux V922 original-function, direct-edge and exact-label owner
audits, the real V751 pre-exception capture/V921 same-CPU saved-context join,
and the existing V932 pending-SI RFI/second-vector witness. This adapter does
NOT synthesize guest registers, interrupt state, a loader return, or RFI.
It is an installer: native execution needs a separate owner-original launch.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v767_live_epilogue import geometry
from prepare_v616_irq_enable import ENTRY
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_v922_irq_return import patch_label,patch_entry


def patch_return(s:str)->str:
    """RFI route is selected only at the already-authenticated V920 return."""
    if type(s) is not str or 'windows_rfi_enabled' in s:
        raise ValueError('Windows RFI return duplicate')
    s=replace_exact(s,'#include "wii_saved_context_join_v921.h"',
        '#include "wii_saved_context_join_v921.h"\n'
        '#include "wii_live_irq_return_binding_v922.h"')
    start='template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){'
    helper='''inline bool windows_rfi_enabled(){
    const char* v=std::getenv("UNDERCOVER_V926_WINDOWS_RFI");
    return v&&v[0]=='1'&&v[1]=='\\0';
}
'''
    s=replace_exact(s,start,helper+start)
    # This marker is emitted by the genuine V921 join, not this adapter.
    # Place the branch after the join and before the original V922 (Windows)
    # scheduler stage so the default-disabled older lanes remain unchanged.
    evidence='    std::cout<<"WINDOWS_RFI_CONTEXT_JOIN original_snapshot=1 original_handler_return=1 saved_gprs=32 special=6 same_cpu=1 rfi=0 boot_verified=0"<<std::endl;'
    if s.count(evidence)!=1:
        raise ValueError('Windows RFI captured-frame contract')
    anchor='    if(scheduler_enabled()){scheduler_start(c,pc,w);return;}'
    s=replace_exact(s,anchor,'''    if(windows_rfi_enabled()){
        if(!windows_context_bridge_enabled()||
           !v921::join.captured()||v921::join.stage()!=2u)reject(6);
        v922::begin(c,pc,w);
        return;
    }
'''+anchor)
    if s.index(evidence)>s.index('    if(windows_rfi_enabled()){'):
        raise ValueError('Windows RFI join order')
    return s


def install(dol:bytes,elf:bytes,root:Path,host:Path)->int:
    if type(dol) is not bytes or type(elf) is not bytes or not isinstance(root,Path):
        raise ValueError('Windows RFI input contract')
    if len(dol)>MAX_DOL or len(elf)>64*1024*1024:
        raise ValueError('Windows RFI input size')
    expected,j,resume,header,edges,entries=geometry(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if (len(paths)<20 or not main.is_file() or main.is_symlink() or
        any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths)):
        raise ValueError('Windows RFI native tree')
    outer=main.read_text(encoding='utf-8')
    verify_resume_dispatch(outer,ENTRY,resume)
    sources={p:p.read_text(encoding='utf-8') for p in paths}
    if audit_native(sources.values(),outer,expected)!=len(expected):
        raise ValueError('Windows RFI native coverage')
    for owner,links in edges:
        bodies=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(bodies)!=1:
            raise ValueError('Windows RFI direct-edge owner')
        for site,dst in links:
            verify_direct(bodies[0],site,dst)
    if any(sum(entry_count(s,a) for s in sources.values())!=1 for a in entries):
        raise ValueError('Windows RFI entry coverage')

    changes={};seen=set()
    for path,old in sources.items():
        new=old
        for pc,(owner,w) in expected.items():
            if pc==j or f'loc_{pc:X}: ;' not in new:
                continue
            if pc in seen:
                raise ValueError('Windows RFI label duplicate')
            new=patch_label(new,pc,w,pc==resume,1 if owner==DISABLE else 3 if owner==RESTORE else 0)
            seen.add(pc)
        if new!=old:
            inc='#include "undercover/wii_live_irq_return_binding_v922.h"'
            if inc not in new:
                new=replace_exact(new,'#include "runtime/cpu_context.h"',
                                  '#include "runtime/cpu_context.h"\n'+inc)
            changes[path]=new
    if seen!=set(expected)-{j}:
        raise ValueError('Windows RFI hook coverage')

    dest=root/'nWiiRuntime/include/undercover'
    external=dest/'wii_external_entry_binding_v663.h'
    handler=dest/'wii_handler_suffix_binding_v868.h'
    if (dest.is_symlink() or not dest.is_dir() or
        any(p.is_symlink() or not p.is_file() for p in (external,handler))):
        raise ValueError('Windows RFI destination')
    for name in ('wii_external_return_v706.h','wii_cold_return_capture_v741.h',
                 'wii_saved_context_join_v921.h'):
        p=dest/name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Windows RFI missing context bridge')
        ref=host/name
        if p.read_bytes()!=ref.read_bytes():
            raise ValueError('Windows RFI context identity')
    headers=('wii_live_epilogue_v762.h',
             'wii_live_irq_return_binding_v922.h',
             'wii_pending_external_reentry_v932.h')
    for name in headers:
        p=dest/name
        if p.exists() or p.is_symlink():
            raise ValueError('Windows RFI destination')
        changes[p]=(host/name).read_text(encoding='utf-8')
    private=dest/'v922_private_irq_return.h'
    if private.exists() or private.is_symlink():
        raise ValueError('Windows RFI destination')
    changes[private]=header.replace('::v767','::v922')
    changes[external]=patch_entry(external.read_text(encoding='utf-8'))
    changes[handler]=patch_return(handler.read_text(encoding='utf-8'))
    for p,s in changes.items():p.write_text(s,encoding='utf-8')
    return len(expected)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path)
    p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        labels=install(a.dol.read_bytes(),a.elf.read_bytes(),
                       a.generated,Path(__file__).resolve().parent)
    except (OSError,ValueError,UnicodeError,IndexError,KeyError,struct.error):
        print('V926_WINDOWS_NATIVE_RFI_ROUTE installed=0');return 1
    print(f'V926_WINDOWS_NATIVE_RFI_ROUTE installed=1 authenticated_labels={labels}'
          ' original_scheduler=1 original_loader=1 saved_context=1'
          ' pending_second_vector=1 original_rfi_executed=0 boot_verified=0')
    return 0


if __name__=='__main__':raise SystemExit(main())
