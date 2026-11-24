#!/usr/bin/env python3
"""Install read-only boot-report witness after the original MI continuation."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v591_memory_init import install as install_mi
from prepare_v574_dsp_sc import diagnostic
from prepare_v453_debug_leaf import data_at
from make_v594_boot_report_geometry import START,END,TARGETS,REPORT,geometry
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from audit_v594_report_translation import check
from make_start_to_boot_report_v66 import DATA,EDGES,STOP
LRS=(0x805203ec,0x80520400,0x8052040c,0x8052047c,0x8052055c,0x805205ac,0x805205f8,0x80520618,0x80520638,0x80520658,STOP)+tuple(t+12 for t in TARGETS[:-1])
INCLUDE='#include "v591_private_mi_expectations.h"'
DECL='    static MemoryInitWitness memory_init(v591::expected_memory);'
NEXT=DECL+'''
    static BootReportWitness boot_report(v603::expected_report);
    if(boot_report.stage()){
        const auto before=boot_report.reports(),getters=boot_report.getters();
        if(!boot_report.observe(addr,cpu)){
            std::cout<<"V603_REPORT_INVALID reason="<<boot_report.failure()<<" stage="<<boot_report.stage()<<" reports="<<boot_report.reports()<<" getters="<<boot_report.getters()<<std::endl;
            if(boot_report.failure()==8u)std::cout<<"V643_REPORT_DIAG mask="<<boot_report.print_refusal()<<" class="<<boot_report.console_class()<<" call_offset="<<boot_report.call_offset()<<" format_offset="<<boot_report.format_offset()<<std::endl;
            std::_Exit(116);
        }
        if(boot_report.getters()!=getters)std::cout<<"V603_REPORT_GETTER n="<<boot_report.getters()<<std::endl;
        if(boot_report.reports()!=before)std::cout<<"V603_REPORT_CALL n="<<boot_report.reports()<<std::endl;
        if(boot_report.stage()==3u){
            std::cout<<"V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed="<<unsigned(boot_report.computed())<<" returned=1 output_backend=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
MI_END='''            std::cout<<"V591_MI_RESULT handlers=5 shutdown=1 bat=32 rfi_returns=2 mi_mask=16 returned=1 permissions=0 firmware_executed=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
MI_NEXT=MI_END.replace('std::_Exit(0);','''const char* mode=std::getenv("UNDERCOVER_V603_REPORT");
            if(!mode||mode[0]!='1'||mode[1]!='\\0'||!boot_report.begin(cpu)){
                std::cout<<"V603_REPORT_INVALID reason=1 stage=0 reports=0 getters=0"<<std::endl;std::_Exit(116);}
            std::cout<<"V603_REPORT_BEGIN native=1"<<std::endl;''')
def expectations(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    bctr,table=geometry(dol,elf,dd,ed)
    sizes=parse_functions(elf)
    def word(pc):
        w=words_at(dol,pc,1)[0]
        if tuple(read_words(elf,pc,1))!=(w,):raise ValueError('report word identity')
        return w
    roots=[edge(dol,s) for s,_ in EDGES]
    if [r[0] for r in roots]!=[p for _,p in EDGES]:raise ValueError('report edges')
    main,console,mem2=roots[0],roots[2],roots[3]
    getters=roots[4:]
    calls=[]
    for lr in LRS:
        w=word(lr-4)
        if direct_bl(w,lr-4)!=REPORT:raise ValueError('report call geometry')
        calls.append((lr,w,word(lr)))
    if len(set(LRS))!=len(LRS) or len(getters)!=6:raise ValueError('report counts')
    helpers=[]
    known={lr-4 for lr in LRS}|{s for s,_ in EDGES}
    for pc in (START,0x8051fd44):
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n%4:raise ValueError('report helper extent')
        for i,w in enumerate(words_at(dol,pc,n//4)):
            s=pc+i*4
            if s not in known and w>>26==18 and w&3==1:
                if word(s)!=w:raise ValueError('helper identity')
                helpers.append(edge(dol,s))
    if len(helpers)>32:raise ValueError('helper count')
    for r in [*roots,*helpers]:
        if word(r[0])!=r[3] or word(r[1]-4)!=r[2]:raise ValueError('edge identity')
    labels={lr:w for lr,_,w in calls}
    labels[console[1]]=word(console[1]);labels[bctr]=word(bctr)
    labels.update((p,word(p)) for p in TARGETS)
    fmt=lambda r,ty:'%s{%s}'%(ty,','.join(f'0x{v:08x}u' for v in r))
    arr=lambda r:'{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    edges=lambda r:'{'+','.join(fmt(x,'BootReportEdge') for x in r)+'}'
    raw=lambda r:'{'+','.join(map(str,r))+'}'
    h=('#pragma once\n#include "wii_boot_report_witness_v600.h"\nnamespace undercover::wii::v603 {\n'
       'inline const BootReportExpectations expected_report{'+','.join(fmt(x,'BootReportEdge') for x in (main,console,mem2))+','+
       edges(getters)+',{'+','.join(fmt(x,'BootReportSite') for x in calls)+'},'+edges(helpers)+','+
       ','.join(f'0x{x:08x}u' for x in (bctr,word(bctr),word(console[1]),word(STOP),word(EDGES[0][0])))+','+
       arr(table)+','+arr(word(p) for p in TARGETS)+','+raw(data_at(dol,*DATA[0]))+','+raw(data_at(dol,*DATA[1]))+'};\n}\n')
    return h,sorted({r[0] for r in roots+helpers}),labels,bctr
def patch_probe(source):
    return replace_exact(replace_exact(replace_exact(source,INCLUDE,INCLUDE+'\n#include "v603_private_report_expectations.h"'),DECL,NEXT),MI_END,MI_NEXT)
def patch_label(source,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pat.findall(source))!=1:raise ValueError('report trace label')
    line=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V603 original report label\n'
    if line in source:raise ValueError('duplicate report trace')
    return pat.sub(lambda m:m[0]+line,source,count=1)
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    h,targets,labels,bctr=expectations(dol,elf,dd,ed)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() for p in [*shards,main]):raise ValueError('full image')
    check((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),bctr,
          {p:labels[p] for p in (bctr,*TARGETS)})
    counts=dict.fromkeys(targets,0);owners={}
    for p in shards:
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        for pc,w in labels.items():
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):
                if pc in owners:raise ValueError('duplicate report label')
                patch_label(s,pc,w);owners[pc]=p
    if any(n!=1 for n in counts.values()) or set(owners)!=set(labels):raise ValueError('report trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v603_private_report_expectations.h':h,
           dest/'wii_boot_report_witness_v600.h':(host/'wii_boot_report_witness_v600.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_mi(dol,elf,generated,host,dd,ed)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
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
        print(diagnostic(exc));print('V603_REPORT_ROUTE installed=0');return 1
    print('V603_REPORT_ROUTE installed=1 callsites=17 computed_targets=7 output_backend=0');return 0
if __name__=='__main__':raise SystemExit(main())
