#!/usr/bin/env python3
"""Attach an opt-in native external entry route after the V616 arena observer."""
import argparse,hashlib,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from audit_v662_external_overlay import expected,audit
from prepare_v616_irq_enable import DECL,CONT,expectations
TRAMP=0x80526ce0
DISPATCH=0x80526a3c
HEADER='#include "v616_private_irq_expectations.h"'
PROBE='    static IrqEnableWitness irq_enable(v616::expected_irq);'
START='''            if(!irq_enabled||!irq_enable.begin(cpu,irq_cause,irq_mask)){'''
CALLBACK='bool process_pending_callbacks(CPUContext &ctx) {'
IOS_INCLUDE='#include "undercover/wii_boot_sc_binding_v574.h"'
def patch_probe(s):
    s=replace_exact(s,HEADER,HEADER+'\n#include "wii_external_entry_binding_v663.h"')
    s=replace_exact(s,PROBE,PROBE+'''
    if(v663::route.stage()){
        v663::observe(addr,cpu);
        return;
    }''')
    return replace_exact(s,START,'''            if(v663::enabled()){
                if(!irq_enabled) v663::reject(9);
                v663::begin(cpu,irq_cause,irq_mask);
                return;
            }
'''+START)
def patch_ios(s):
    s=replace_exact(s,IOS_INCLUDE,IOS_INCLUDE+'\n#include "undercover/wii_external_entry_binding_v663.h"')
    return replace_exact(s,CALLBACK,CALLBACK+'''
  if (undercover::wii::v663::route.stage())
    return undercover::wii::v663::poll(ctx);''')
def verify_dispatch_tick(s):
    a='        process_pending_callbacks(ctx);'
    b='        uint32_t target = ctx.pc;'
    pattern=r'(?m)^        if \(\(\+\+ctx\.inst_count % 100000\) == 0\) std::cout << "Dispatcher PC: 0x" << std::hex << target << std::endl;$'
    hits=list(re.finditer(pattern,s))
    if s.count(a)!=1 or s.count(b)!=1 or len(hits)!=1 or not s.index(a)<s.index(b)<hits[0].start():raise ValueError('external dispatch tick geometry')
    end=s.index('        switch (target) {',hits[0].end())
    if '++ctx.inst_count' in s[s.index(a):hits[0].start()] or '++ctx.inst_count' in s[hits[0].end():end]:raise ValueError('external dispatch tick geometry')
def install(dol,elf,root,host):
    if hashlib.sha256(dol).hexdigest()!=OWNER_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
    expectations(dol,elf)
    words=expected(dol)
    if audit(root,words)!=38:raise ValueError('vector coverage')
    sizes=parse_functions(elf)
    shards=sorted(root.glob('output_*.cpp'))
    main=(root/'main_output.cpp').read_text(encoding='utf-8')
    verify_dispatch_tick(main)
    targets=(0x80000500,TRAMP,DISPATCH)
    counts=dict.fromkeys(targets,0)
    for shard in shards:
        s=shard.read_text(encoding='utf-8')
        for pc in targets:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('trace coverage')
    target_words=[]
    for pc in (TRAMP,DISPATCH):
        if not sizes.get(pc):raise ValueError('root')
        w=words_at(dol,pc,1)[0]
        if tuple(read_words(elf,pc,1))!=(w,):raise ValueError('identity')
        if len(re.findall(r'(?m)^\s*case 0x'+f'{pc:X}'+r': (?:fn|func)_'+f'{pc:X}'+r'\(ctx\); break;\s*$',main))!=1:raise ValueError('dispatch')
        target_words.append(w)
    dest=root/'nWiiRuntime/include/undercover'
    private=dest/'v663_private_external_expectations.h'
    probe=dest/'wii_full_start_probe_v419.h'
    ios=root/'nWiiRuntime/src/hle/ios.cpp'
    shared=dest/'native_external_irq.h'
    if shared.is_symlink() or not shared.is_file() or shared.read_bytes()!=(host/shared.name).read_bytes():raise ValueError('shared IRQ header identity')
    names=('wii_cold_external_entry_v663.h','wii_external_entry_binding_v663.h')
    files={dest/name:(host/name).read_text(encoding='utf-8') for name in names}
    raw=struct.pack('>38I',*words)
    files[private]=('#pragma once\n#include "v616_private_irq_expectations.h"\n#include "wii_cold_external_entry_v663.h"\n'
        'namespace undercover::wii::v663 {\ninline constexpr ColdExternalExpectations expected{v616::expected_irq,{'
        +','.join(map(str,raw))+'},'+','.join(f'0x{w:08x}u' for w in target_words)+'};\n}\n')
    if dest.is_symlink() or any(x.exists() or x.is_symlink() for x in files) or any(x.is_symlink() for x in (probe,ios)):raise ValueError('destination')
    files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    files[ios]=patch_ios(ios.read_text(encoding='utf-8'))
    for x,s in files.items():x.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        from prepare_v574_dsp_sc import diagnostic
        print(diagnostic(e));print('V663_EXTERNAL_ROUTE installed=0');return 1
    print('V663_EXTERNAL_ROUTE installed=1 native_vector=38 bounded_dispatcher=1 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
