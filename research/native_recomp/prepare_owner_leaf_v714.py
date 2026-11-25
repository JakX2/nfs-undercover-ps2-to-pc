#!/usr/bin/env python3
"""Authenticate original leaves and generate a private scratch-only fixture."""
import argparse,re,shutil
from pathlib import Path
from audit_os_leaf_v703 import plan
from prepare_v419_full_start import MAX_DOL
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root,entry_count,validate_coverage
HOST=Path(__file__).resolve().parent
H=0x80004000
def bl(a,b):
    if not -(1<<25)<=b-a<(1<<25) or (a|b)&3:raise ValueError('branch span')
    return 0x48000001|((b-a)&0x03fffffc)
def fixture(dol,elf):
    rows=plan(dol,elf);D,T,R=[row[1] for row in rows]
    sites=(H,H+4,H+12)
    caller=[bl(H,D),bl(H+4,T),0x38600000,bl(H+12,R),0x60000000,0x4e800020]
    private=[(site,r[1],r[2],bl(site,r[1]),r[4],r[5],r[6]) for site,r in zip(sites,rows)]
    return {H:caller,**{r[1]:r[5] for r in rows}},private
def header(dol,elf,out):
    roots,rows=fixture(dol,elf)
    D,T,R=[r[1] for r in rows]
    code=roots[T]
    tb=lambda w,xo:w>>26==31 and (w>>1)&1023==xo and (((w>>11)&31)*32+((w>>16)&31)) in (268,269)
    print(f'V715_OWNER_LEAF_SHAPE mftb={sum(tb(w,371) for w in code)} mfspr_tb={sum(tb(w,339) for w in code)}')
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{H:08x}u,D=0x{D:08x}u,T=0x{T:08x}u,R=0x{R:08x}u;\n'
    for name,pc in zip(('caller','disable_words','time_words','restore_words'),(H,D,T,R)):
        words=roots[pc];s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    out.write_text(s)
def install(dol,elf,root,inc):
    roots,rows=fixture(dol,elf)
    paths=list(root.glob('*.cpp'));original={p:p.read_text() for p in paths}
    main=(root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')).read_text()
    outer=main[main.index('extern "C" void run_game('):]
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    if audit_native(original.values(),outer,expected)!=26:raise ValueError('owner leaf label audit')
    seen=set();calls=0;entries={r[1]:0 for r in rows}
    for p,s in original.items():
        if owns_root(s,H):
            for site,dst,*_ in rows:verify_direct(exact_function(s,H),site,dst);calls+=1
        for row in rows:entries[row[1]]+=entry_count(s,row[1])
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('owner leaf hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    leaf_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=original[p]:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('include')
            p.write_text(s.replace(anchor,anchor+'\n#include "leaf_test.h"'))
    if seen!=set(expected):raise ValueError('owner leaf hook coverage')
    validate_coverage(calls,entries,{pc for pc in seen if pc not in range(H,H+24,4)},rows)
    dest=inc/'undercover';dest.mkdir(parents=True)
    shutil.copyfile(HOST/'wii_postack_os_leaf_v703.h',dest/'wii_postack_os_leaf_v703.h')
    shutil.copyfile(HOST/'leaf_test_v705.h',inc/'leaf_test.h')
    print('V714_PRIVATE_LEAF_ROUTE native_labels=20 caller_labels=6 direct_edges=3')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('--include',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        if a.include:install(d,e,a.output,a.include)
        else:header(d,e,a.output)
    except (OSError,ValueError,UnicodeError):print('V714_PRIVATE_LEAF_PREP verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
