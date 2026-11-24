#!/usr/bin/env python3
"""Compose the complete original two-arena lane after V603 report return."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v603_boot_report import install as install_report,expectations as report_geometry
from prepare_v574_dsp_sc import diagnostic,HOOK_NEW
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from make_start_to_arena_clear_v67 import RANGES,EDGES,STOP
from apply_arena_cache_trace_v596 import apply as install_cache
from apply_arena_reset_v606 import apply as install_reset
BEGIN=0x80520908
LANES=(
 ((0x8052093c,0x8051ffc8),(0x8051ffdc,0x805285d0),(0x8051ffe8,0x80521d28),
  (0x8051fff0,0x80521d40),(0x8051fff8,0x80521d40),(0x8052001c,0x8052234c),(0x80520028,0x805222c0)),
 ((0x80520940,0x805201a4),(0x805201b8,0x805285d0),(0x805201c4,0x80521d20),
  (0x805201cc,0x80521d38),(0x805201d4,0x80521d38),(0x805201f8,0x8052234c),(0x80520204,0x805222c0)))
INCLUDE='#include "v603_private_report_expectations.h"'
DECL='    static BootReportWitness boot_report(v603::expected_report);'
NEXT=DECL+'''
    static ArenaClearWitness arena_clear(v609::expected_arena);
    if(arena_clear.stage()){
        if(v609::vector_trace(addr,cpu))return;
        if(!arena_clear.observe(addr,cpu,v609::reset,v609::pair)){
            std::cout<<"V609_ARENA_INVALID reason="<<arena_clear.failure()<<" stage="<<arena_clear.stage()<<std::endl;std::_Exit(117);
        }
        std::cout<<"V609_ARENA_STAGE n="<<arena_clear.stage()<<std::endl;
        if(arena_clear.stage()==20u){
            std::cout<<"V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros="<<arena_clear.lines()<<" flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
END='''            std::cout<<"V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed="<<unsigned(boot_report.computed())<<" returned=1 output_backend=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
CONT=END.replace('std::_Exit(0);','''if(!arena_clear.begin(cpu)||!v609::enable()){
                std::cout<<"V609_ARENA_INVALID reason=1 stage=0"<<std::endl;std::_Exit(117);}
            std::cout<<"V609_ARENA_STAGE n=1"<<std::endl;''')
IOS_INCLUDE='#include "undercover/wii_boot_sc_binding_v574.h"'
def expectations(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    report_geometry(dol,elf,dd,ed)
    sizes=parse_functions(elf)
    def word(pc):
        w=words_at(dol,pc,1)[0]
        if tuple(read_words(elf,pc,1))!=(w,):raise ValueError('arena word identity')
        return w
    for lo,hi in RANGES:
        ws=words_at(dol,lo,(hi-lo)//4)
        if tuple(read_words(elf,lo,len(ws)))!=ws or ws[-1]!=0x4e800020:raise ValueError('arena extent')
    rows=[[edge(dol,s) for s,_ in lane] for lane in LANES]
    for lane,edges in zip(LANES,rows):
        if [x[0] for x in edges]!=[p for _,p in lane]:raise ValueError('arena edge')
        for p,lr,b,e in edges:
            if word(p)!=e or word(lr-4)!=b or p not in sizes:raise ValueError('arena edge identity')
    for s,p in EDGES:
        if edge(dol,s)[0]!=p:raise ValueError('arena original route')
    zero=0x8052234c
    if sizes.get(zero)!=0x2c:raise ValueError('zero extent')
    z=[(zero+4*i,w) for i,w in enumerate(words_at(dol,zero,11)) if w>>26==31 and (w>>1)&1023==1014]
    if len(z)!=1:raise ValueError('zero opcode geometry')
    labels={r[-1][1]:word(r[-1][1]) for r in rows};labels[STOP]=word(STOP)
    fmt=lambda r:'ArenaClearEdge{'+','.join(f'0x{x:08x}u' for x in r)+'}'
    arr=lambda r:'{'+','.join(map(fmt,r))+'}'
    h=('#pragma once\n#include "wii_arena_clear_witness_v607.h"\nnamespace undercover::wii::v609 {\n'
        'inline const ArenaClearExpectations expected_arena{{'+','.join(map(arr,rows))+'},'
        '{'+','.join(f'0x{labels[r[-1][1]]:08x}u' for r in rows)+'},'
        f'0x{word(BEGIN):08x}u,0x{word(STOP):08x}u'+'};\n}\n')
    return h,sorted({r[0] for lane in rows for r in lane}),labels,z[0]
def patch_probe(s):
    return replace_exact(replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n#include "v609_private_arena_expectations.h"\n#include "wii_arena_binding_v609.h"'),DECL,NEXT),END,CONT)
def patch_ios(s):
    return replace_exact(replace_exact(s,IOS_INCLUDE,IOS_INCLUDE+'\n#include "undercover/wii_arena_binding_v609.h"'),HOOK_NEW,
        HOOK_NEW.replace('  if (undercover::wii::v574::try_sc(ctx))','  if (undercover::wii::v609::try_sc(ctx)) return false;\n  if (undercover::wii::v574::try_sc(ctx))'))
def label_pattern(pc,w):
    return re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
def patch_label(s,pc,w):
    pat=label_pattern(pc,w)
    line=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V609 original arena return\n'
    if len(pat.findall(s))!=1 or line in s:raise ValueError('arena return label')
    return pat.sub(lambda m:m[0]+line,s,count=1)
def native_zero(s,pc,w):
    pat=label_pattern(pc,w);hits=list(pat.finditer(s))
    if len(hits)!=1:raise ValueError('zero label')
    rest=s[hits[0].end():]
    block=re.split(r'(?m)^loc_[0-9A-Fa-f]+: ;$',rest,maxsplit=1)[0]
    if block.count('ctx.guest_dcbz(')!=1 or 'interpret_step' in block or 'micro_interpret' in block:raise ValueError('native zero body')
    return True
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    h,targets,labels,z=expectations(dol,elf,dd,ed)
    counts=dict.fromkeys(targets,0);owners={};zeros=0
    for p in sorted(generated.glob('output_*.cpp')):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        for pc,w in labels.items():
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):
                if pc in owners:raise ValueError('duplicate arena label')
                patch_label(s,pc,w);owners[pc]=p
        if re.search(r'(?mi)^loc_'+f'{z[0]:X}'+r': ;$',s):native_zero(s,*z);zeros+=1
    if any(n!=1 for n in counts.values()) or set(owners)!=set(labels) or zeros!=1:raise ValueError('arena native coverage')
    rt=generated/'nWiiRuntime';dest=rt/'include/undercover'
    files={dest/'v609_private_arena_expectations.h':h}
    for name in ('wii_arena_clear_witness_v607.h','wii_arena_sc_pair_v598.h','wii_arena_binding_v609.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_report(dol,elf,generated,host,dd,ed)
    install_cache(generated,host);install_reset(generated,host)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    ios=rt/'src/hle/ios.cpp';files[ios]=patch_ios(ios.read_text(encoding='utf-8'))
    for pc,p in owners.items():
        s=files[p] if p in files else p.read_text(encoding='utf-8')
        files[p]=patch_label(s,pc,labels[pc])
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as exc:
        print(diagnostic(exc));print('V609_ARENA_ROUTE installed=0');return 1
    print('V609_ARENA_ROUTE installed=1 edges=14 native_zero=1 reset_profile=1 sc_routes=2');return 0
if __name__=='__main__':raise SystemExit(main())
