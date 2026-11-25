#!/usr/bin/env python3
"""Private original context loader and original IRQ-enable suffix."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v616_irq_enable import expectations,ENTRY
from prepare_v667_si_dispatch import exact
from prepare_owner_context_v720 import plan as loader_plan,L
from prepare_v625_ipc_client import audit_native

B=0x80004000
CALLER=[0x44000002,0x4e800020]
def extract_shape(w):
    return w>>26==21 and not(w&1) and (w>>16)&31==3 and (w>>11)&31==17 and (w>>6)&31==31 and (w>>1)&31==31

def plan(dol,elf):
    _,resume,labels=expectations(dol,elf)
    leaf=exact(dol,elf,resume,2)
    if resume!=ENTRY+12 or leaf[-1]!=0x4e800020 or not extract_shape(leaf[0]):
        raise ValueError('IRQ leaf shape')
    code,gqr=loader_plan(dol,elf)
    return resume,leaf,code,gqr

def header(p,out):
    h,leaf,code,gqr=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{h:08x}u,B=0x{B:08x}u,L=0x{L:08x}u,GqrMask={gqr}u;\n'
    for name,words in (('resume_words',leaf),('loader_words',code),('caller_words',CALLER)):
        s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    with out.open('x') as f:f.write(s)

def install(p,root):
    h,leaf,code,gqr=p
    paths=sorted(root.glob('*.cpp'))
    if not paths or any(f.is_symlink() for f in paths):raise ValueError('private output')
    sources={f:f.read_text() for f in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={a+4*i:(a,w) for a,ws in ((B,CALLER),(h,leaf),(L,code)) for i,w in enumerate(ws)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    hooks={pc:w for pc,(a,w) in expected.items() if a!=B or pc==B}
    seen=set();changes={}
    for f,old in sources.items():
        s=old
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            matches=list(pat.finditer(s))
            if not matches:continue
            if len(matches)!=1 or pc in seen:raise ValueError('label identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('include')
            changes[f]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for f,s in changes.items():f.write_text(s)
    print('V927_NATIVE_ROUTE loader_labels=54 original_resume_labels=2 synthetic_caller=1 fallback=0 execution=0')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);a.add_argument('--install',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        else:header(p,x.output);print('V927_GEOMETRY original_loader=54 original_resume=2 synthetic_caller=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('IRQ leaf shape','private output','native coverage','label identity','include','hook coverage')
        print('V927_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
