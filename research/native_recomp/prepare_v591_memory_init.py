#!/usr/bin/env python3
"""Compose authenticated complete-image original memory initialization."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v581_dsp_return import install as install_dsp,expectations as dsp_geometry,CONTINUE
from prepare_v574_dsp_sc import diagnostic
from audit_v584_bat_translation import install as audit_bat,geometry as bat_geometry
from make_start_to_memory_protect_v65 import EDGES,STOP
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
import hashlib
BEGIN=0x805208d8
MAP=0x80527568
SITES=tuple(EDGES[:4])+tuple((0x80527724+12*i,0x805265f8) for i in range(5))+tuple(EDGES[4:7])
TRAMP=tuple(EDGES[7:9])
ENTRIES=(0x805270c4,0x80527144)
RESUMES=(0x805275d0,0x80527600)
INCLUDE='#include "v581_private_dsp_return_expectations.h"'
DECL='    static DspReturnWitness dsp_return(v581::expected_return);'
DECL_NEW=DECL+'''
    static MemoryInitWitness memory_init(v591::expected_memory);
    if(memory_init.stage()){
        const auto before=memory_init.stage();
        if(!memory_init.observe(addr,cpu)){std::cout<<"V591_MI_INVALID reason="<<memory_init.failure()<<" stage="<<memory_init.stage()<<std::endl;
            std::cout<<"V604_MI_EDGE stage="<<before<<" pc="<<std::hex<<addr<<" lr="<<cpu.lr<<std::dec<<" outer="<<memory_init.outer_visits()<<" metadata="<<memory_init.mapping_metadata(cpu)<<std::endl;std::_Exit(115);}
        if(memory_init.stage()!=before)std::cout<<"V591_MI_STAGE n="<<memory_init.stage()<<std::endl;
        if(memory_init.stage()==20u){
            std::cout<<"V591_MI_RESULT handlers=5 shutdown=1 bat=32 rfi_returns=2 mi_mask=16 returned=1 permissions=0 firmware_executed=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
END='''            std::cout<<"V581_DSP_RETURN_RESULT reset=2 dma=2 bytes=64 ack=2 mailbox=1 delay=1 restore=128 returned=1 firmware_executed=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
NEXT=END.replace('std::_Exit(0);','''const char* mode=std::getenv("UNDERCOVER_V591_MI");
            if(!mode||mode[0]!='1'||mode[1]!='\\0'||!memory_init.begin(cpu)){
                std::cout<<"V591_MI_INVALID reason=1 stage=0"<<std::endl;std::_Exit(115);}
            dsp_session.reset();
            std::cout<<"V591_MI_STAGE n=1"<<std::endl;''')
def expectations(data,elf,digest=OWNER_SHA,elf_digest=ORIGINAL_SHA256):
    dsp_geometry(data,digest);bat_geometry(data,digest)
    if hashlib.sha256(elf).hexdigest()!=elf_digest:raise ValueError('ELF identity')
    sizes=parse_functions(elf)
    rows=[edge(data,site) for site,_ in SITES];tramp=[edge(data,site) for site,_ in TRAMP]
    if len(rows)!=12 or [r[0] for r in rows]!=[p for _,p in SITES] or [r[0] for r in tramp]!=[p for _,p in TRAMP]:raise ValueError('MI call geometry')
    # Restrict nested call allowance to exact ELF-sized original functions
    # already known to participate in this MI initializer. No guest targets
    # outside these caller extents are accepted on mere address similarity.
    helper=[]
    for pc in (0x8052693c,0x805269bc,0x805266e0,0x80527b4c,0x805265f8):
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n%4:raise ValueError('MI helper extent')
        for i,w in enumerate(words_at(data,pc,n//4)):
            if w>>26==18 and w&3==1:helper.append(edge(data,pc+4*i))
    if len(helper)>64:raise ValueError('MI helper count')
    # The complete original initializer also owns calls omitted from the old
    # high-level witness (before mask and after unmask). Authenticate them
    # against BOTH private inputs; phase authorization is in the witness.
    memory=0x805276d4;extent=sizes.get(memory,0)
    if extent!=0x805277a0-memory:raise ValueError('MI outer extent')
    known={s for s,_ in SITES};outer=[]
    for i,w in enumerate(words_at(data,memory,extent//4)):
        site=memory+4*i
        if site not in known and w>>26==18 and w&3==1:
            row=edge(data,site)
            if tuple(read_words(elf,site,1))!=(w,) or tuple(read_words(elf,row[0],1))!=(row[3],):raise ValueError('MI outer identity')
            outer.append(row)
    if not 1<=len(outer)<=16:raise ValueError('MI outer calls')
    entry=words_at(data,BEGIN,1)[0];ret=words_at(data,STOP,1)[0]
    ew=[words_at(data,p,1)[0] for p in ENTRIES];rw=[words_at(data,p,1)[0] for p in RESUMES]
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    arr=lambda r:'{'+','.join(map(fmt,r))+'}'
    words=lambda r:'{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_memory_init_witness_v591.h"\nnamespace undercover::wii::v591 {\n'
        'inline const MemoryInitExpectations expected_memory{'+arr(rows)+',BatMappingExpectations{'+fmt(rows[10])+','+arr(tramp)+','+words(ew)+','+words(rw)+'},'
        +f'0x{entry:08x}u,0x{ret:08x}u,'+arr(helper)+','+arr(outer)+'};\n}\n')
    return header,sorted({r[0] for r in rows+tramp+outer}|set(ENTRIES)),dict(zip((*RESUMES,STOP),(*rw,ret)))
def patch_probe(source):
    return replace_exact(replace_exact(replace_exact(source,INCLUDE,INCLUDE+'\n#include "v591_private_mi_expectations.h"'),DECL,DECL_NEW),END,NEXT)
def patch_label(source,pc,word):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {word:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pat.findall(source))!=1:raise ValueError('MI return label')
    return pat.sub(lambda m:m[0]+f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V591 original MI return\n',source,count=1)
def install(data,elf,generated,host,digest=OWNER_SHA,elf_digest=ORIGINAL_SHA256):
    header,targets,labels=expectations(data,elf,digest,elf_digest)
    audit_bat(data,generated,digest)
    counts=dict.fromkeys(targets,0);owners={}
    for p in generated.glob('output_*.cpp'):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        for pc,word in labels.items():
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):
                if pc in owners:raise ValueError('MI duplicate return')
                patch_label(s,pc,word);owners[pc]=p
    if any(n!=1 for n in counts.values()) or set(owners)!=set(labels):raise ValueError('MI trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v591_private_mi_expectations.h':header}
    for name in ('wii_bat_mapping_witness_v590.h','wii_memory_init_witness_v591.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_dsp(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    for pc,path in owners.items():
        s=files[path] if path in files else path.read_text(encoding='utf-8')
        files[path]=patch_label(s,pc,labels[pc])
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as exc:
        print(diagnostic(exc));print('V591_MI_ROUTE installed=0');return 1
    print('V591_MI_ROUTE installed=1 physical_mapping=2 permissions=0');return 0
if __name__=='__main__':raise SystemExit(main())
