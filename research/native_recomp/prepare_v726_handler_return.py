#!/usr/bin/env python3
"""Opt-in native SI handler return observer; original code remains private."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import geometry,DISPATCH,HANDLER,exact
from prepare_v668_si_ack import geometry as handler_geometry
from si_second_geometry_v688 import second_plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root

def render(root,end,second,resume,word):
    return '#pragma once\n#include "wii_si_handler_return_v725.h"\nnamespace undercover::wii::v726 {inline constexpr SiHandlerReturnExpectation expected{'+','.join(f'0x{x:08x}u' for x in (root,end,second,resume,word))+'};}\n'

def patch_ack(s):
    pairs=(
        ('#include "wii_si_second_binding_v688.h"','#include "wii_si_second_binding_v688.h"\n#include "wii_si_handler_return_binding_v726.h"'),
        ('    std::cout<<"V672_SI_ACK_STAGE n=1"','    v726::capture(c);\n    std::cout<<"V672_SI_ACK_STAGE n=1"'),
        ('    if(!si_completion_ack_trace.before(pc,word))reject(3);','    if(!si_completion_ack_trace.before(pc,word))reject(3);\n    if(v726::active()){v726::before(c,pc,word,ordinal,kind);return;}'),
        ('    postack_refusal(c,c.pc,1);','    if(v726::active())return v726::poll(c);\n    postack_refusal(c,c.pc,1);'))
    for a,b in pairs:s=replace_exact(s,a,b)
    return s

def patch_second(s):
    a='''            std::cout<<"V699_POSTACK_RESULT second_return=1 abi=1 original_ack=1 rfi_return=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
    s=replace_exact(s,'#include "v688_private_si_second_expectations.h"','#include "v688_private_si_second_expectations.h"\n#include "wii_si_handler_return_binding_v726.h"')
    return replace_exact(s,a,a.replace('std::_Exit(0);','if(v726::start(c,pc))return;\n            std::_Exit(0);'))

def patch_resume(s,owner,pc,w):
    body=exact_function(s,owner)
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    if len(pat.findall(body))!=1:raise ValueError('resume label identity')
    out=pat.sub(lambda m:m[0]+f'    undercover::wii::v726::resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n',body,count=1)
    s=replace_exact(s,body,out)
    return replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n#include "undercover/wii_si_handler_return_binding_v726.h"')

def verify_resume_dispatch(main,owner,pc):
    rows=re.findall(r'(?mi)^[ \t]*case[ \t]+0x'+f'{pc:X}'+r'[ \t]*:[ \t]*([^\r\n]*)',main)
    if len(rows)!=1 or not re.fullmatch(r'(?:fn|func)_'+f'{owner:X}'+r'\(ctx\);[ \t]*break;[ \t]*',rows[0],re.I):
        raise ValueError('resume dispatcher identity')

def install(dol,elf,root,host):
    _,(site,_),_,_,_=geometry(dol,elf)
    n,*_=handler_geometry(dol,elf);second,*_=second_plan(dol,elf)
    resume=site+4;w=exact(dol,elf,resume,1)[0]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('private tree')
    outer=main.read_text();verify_resume_dispatch(outer,DISPATCH,resume)
    # Audit original native return label ownership and exact native dispatch.
    audit_native((p.read_text() for p in paths),outer,{resume:(DISPATCH,w)})
    changes={}
    for p in paths:
        s=p.read_text()
        if owns_root(s,DISPATCH):changes[p]=patch_resume(s,DISPATCH,resume,w)
    if len(changes)!=1:raise ValueError('resume coverage')
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_si_handler_return_v725.h','wii_si_handler_return_binding_v726.h')}
    files[dest/'v726_private_handler_return_expectations.h']=render(HANDLER,HANDLER+n*4,second+4,resume,w)
    a=dest/'wii_si_ack_binding_v672.h';b=dest/'wii_si_second_binding_v688.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() for p in (a,b)):raise ValueError('destination')
    files[a]=patch_ack(a.read_text());files[b]=patch_second(b.read_text())
    for p,s in {**files,**changes}.items():p.write_text(s)
    print('V726_HANDLER_ROUTE installed=1 resume_label=1 indirect_return=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error) as e:
        allowed=('resume label identity','resume dispatcher identity','resume coverage','private tree','destination','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch')
        print('V726_HANDLER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
