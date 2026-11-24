#!/usr/bin/env python3
"""Opt-in native IRQ-enable continuation after the complete original arena lane."""
import argparse,hashlib,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from make_v613_irq_fixture import geometry,ENTRY,CALL
from prepare_v609_arena_clear import install as install_arena
from prepare_v574_dsp_sc import diagnostic
RETURN=CALL+4
INCLUDE='#include "v609_private_arena_expectations.h"'
DECL='    static ArenaClearWitness arena_clear(v609::expected_arena);'
NEXT=DECL+'''
    static IrqEnableWitness irq_enable(v616::expected_irq);
    if(irq_enable.stage()){
        using namespace nwii::runtime::hw;
        if(!irq_enable.observe(addr,cpu,pi_intsr.load(),pi_intmr.load())){
            std::cout<<"V616_IRQ_INVALID reason="<<irq_enable.failure()<<" stage="<<irq_enable.stage()<<std::endl;std::_Exit(119);
        }
        std::cout<<"V616_IRQ_STAGE n="<<irq_enable.stage()<<std::endl;
        if(irq_enable.stage()==4u){
            std::cout<<"V616_IRQ_RESULT returned=1 ee=1 previous=0 ticks=5 pending=0 actual_irq=0 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);
        }
        return;
    }'''
END='''            std::cout<<"V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros="<<arena_clear.lines()<<" flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
CONT=END.replace('std::_Exit(0);','''const char* irq=std::getenv("UNDERCOVER_V616_IRQ");
            using namespace nwii::runtime::hw;
            const auto irq_cause=pi_intsr.load(),irq_mask=pi_intmr.load();
            const bool irq_enabled=irq&&irq[0]=='1'&&irq[1]=='\\0';
            if(!irq_enabled||!irq_enable.begin(cpu,irq_cause,irq_mask)){
                std::cout<<"V616_IRQ_INVALID reason=1 stage=0"<<std::endl;
                std::cout<<"V661_IRQ_BEGIN refusal="<<(irq_enabled?irq_enable.entry_refusal():1024u)<<" pending="<<(irq_cause&irq_mask)<<std::endl;
                std::_Exit(119);}
            std::cout<<"V616_IRQ_STAGE n=1"<<std::endl;''')
def expectations(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    if hashlib.sha256(dol).hexdigest()!=dd or hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('identity')
    if parse_functions(elf).get(ENTRY)!=20:raise ValueError('IRQ leaf extent')
    ws=words_at(dol,ENTRY,5);resume=geometry(ws)
    def word(pc):
        w=words_at(dol,pc,1)[0]
        if tuple(read_words(elf,pc,1))!=(w,):raise ValueError('IRQ instruction identity')
        return w
    if direct_bl(word(CALL),CALL)!=ENTRY or tuple(read_words(elf,ENTRY,5))!=ws:raise ValueError('IRQ edge')
    labels={resume:word(resume),RETURN:word(RETURN)}
    h=('#pragma once\n#include "wii_irq_enable_witness_v615.h"\nnamespace undercover::wii::v616 {\n'
       'inline constexpr IrqEnableExpectations expected_irq{'+','.join(f'0x{x:08x}u' for x in (word(CALL),word(ENTRY),resume,labels[resume],labels[RETURN]))+'};\n}\n')
    return h,resume,labels
def patch_probe(s):
    return replace_exact(replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n#include "v616_private_irq_expectations.h"'),DECL,NEXT),END,CONT)
def patch_label(s,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pat.findall(s))!=1:raise ValueError('IRQ label coverage')
    return pat.sub(lambda m:m[0]+f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V616 native IRQ resume\n',s,count=1)
def native_dispatch(main,resume,owner):
    if not re.fullmatch(r'(?:fn|func)_805265[Cc]0',owner):raise ValueError('IRQ root identity')
    for pc in (ENTRY,resume):
        rows=re.findall(r'(?mi)^[ \t]*case[ \t]+0x'+f'{pc:X}'+r'[ \t]*:[ \t]*([^\r\n]*)',main)
        if len(rows)!=1 or not re.fullmatch(re.escape(owner)+r'\(ctx\);[ \t]*break;[ \t]*',rows[0]):raise ValueError('IRQ dispatcher')
def native_leaf(shards,main,resume,words):
    expected={ENTRY+4*i:w for i,w in enumerate(words)}
    seen=dict.fromkeys(expected,0);owner=None
    pat=re.compile(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n')
    defs=re.compile(r'(?m)^void ((?:fn|func)_[0-9A-Fa-f]+)\(CPUContext& ctx\) \{')
    for s in shards:
        fs=list(defs.finditer(s))
        for i,f in enumerate(fs):
            body=s[f.end():fs[i+1].start() if i+1<len(fs) else len(s)]
            labels=list(pat.finditer(body))
            for j,l in enumerate(labels):
                pc=int(l[1],16)
                if pc not in seen:continue
                seen[pc]+=1
                if int(f[1].split('_')[1],16)!=ENTRY or int(l[2],16)!=pc or int(l[3],16)!=expected[pc]:
                    raise ValueError('IRQ label ownership')
                if owner is not None and owner!=f[1]:raise ValueError('IRQ root identity')
                owner=f[1]
                block=body[l.end():labels[j+1].start() if j+1<len(labels) else len(body)].split('\n}',1)[0]
                if block.count('++ctx.inst_count;')!=1 or 'interpret_step' in block or 'micro_interpret' in block:
                    raise ValueError('IRQ native tick')
    if not owner or any(n!=1 for n in seen.values()):raise ValueError('IRQ unique leaf coverage')
    native_dispatch(main,resume,owner)
    return owner
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    h,resume,labels=expectations(dol,elf,dd,ed)
    main=(generated/'main_output.cpp').read_text(encoding='utf-8')
    shards=sorted(generated.glob('output_*.cpp'))
    if len(shards)<20 or any(p.is_symlink() or p.stat().st_size>64*1024*1024 for p in shards):raise ValueError('IRQ full image')
    native_leaf((p.read_text(encoding='utf-8') for p in shards),main,resume,words_at(dol,ENTRY,5))
    owners={};entries=0
    for p in sorted(generated.glob('output_*.cpp')):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        entries+=s.count('if (nwii::runtime::g_trace_calls && ctx.pc == 0x805265C0) nwii::runtime::trace_call(0x805265C0, ctx);')
        for pc,w in labels.items():
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):
                if pc in owners:raise ValueError('duplicate IRQ label')
                patch_label(s,pc,w);owners[pc]=p
    if entries!=1 or set(owners)!=set(labels):raise ValueError('IRQ trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v616_private_irq_expectations.h':h,dest/'wii_irq_enable_witness_v615.h':(host/'wii_irq_enable_witness_v615.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_arena(dol,elf,generated,host,dd,ed)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    for pc,p in owners.items():
        files[p]=patch_label(files[p] if p in files else p.read_text(encoding='utf-8'),pc,labels[pc])
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as exc:
        print(diagnostic(exc));print('V616_IRQ_ROUTE installed=0');return 1
    print('V616_IRQ_ROUTE installed=1 native_resume=1 ticks=5 root_identity=1 actual_irq=0');return 0
if __name__=='__main__':raise SystemExit(main())
