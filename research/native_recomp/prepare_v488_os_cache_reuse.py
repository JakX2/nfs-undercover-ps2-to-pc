#!/usr/bin/env python3
"""Complete-image second cache initialization and original EXI entry."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v486_context_startup import expectations as context_geometry,install as install_context
CALLS=((0x805208c0,0x80522540),(0x8052255c,0x804b7920),(0x80522578,0x804b7920),
       (0x80522594,0x804b7930),(0x80522650,0x805230b8),(0x805230dc,0x805265ac),
       (0x80523318,0x805265d4),(0x8052265c,0x804e50b8),(0x805208c4,0x804ef9bc))
RETURNS=(0x80522674,0x8052333c,0x804b7924,0x804b7934)
def expectations(data,digest=OWNER_SHA):
    context_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS] or any(words_at(data,pc,1)[0]!=0x4e800020 for pc in RETURNS):
        raise ValueError('cache reuse call/return geometry')
    # Authentic branch after original mfl2cr must skip disabled-L2 sequence.
    w=words_at(data,0x8052259c,1)[0]
    disp=w&0xfffc
    if disp&0x8000:disp-=0x10000
    if w>>26!=16 or w&3 or 0x8052259c+disp!=0x80522644:raise ValueError('L2 enabled branch')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_os_cache_reuse_v488.h"\nnamespace undercover::wii::v488 {\n'
            'inline constexpr OsCacheReuseExpectations expected_cache{{'+','.join(map(fmt,rows))+'}};\n}\n')
    return header,sorted({r[0] for r in rows})
CONTEXT_END='        if(context.stage()==4u){std::cout<<"V486_CONTEXT_RESULT handler=1 current_context=1 cache_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
CONTEXT_NEXT=CONTEXT_END.replace('std::_Exit(0);','if(!reuse.begin(cpu)){std::cout<<"V488_REUSE_INVALID reason="<<reuse.failure()<<" stage="<<reuse.stage()<<std::endl;std::_Exit(98);}std::cout<<"V488_REUSE_STAGE n=1"<<std::endl;')
REUSE_PROBE='''    static OsCacheReuseWitness reuse(v488::expected_cache);
    if(reuse.stage()){
        if(!reuse.observe(addr,cpu)){std::cout<<"V488_REUSE_INVALID reason="<<reuse.failure()<<" stage="<<reuse.stage()<<std::endl;std::_Exit(98);}
        std::cout<<"V488_REUSE_STAGE n="<<reuse.stage()<<std::endl;
        if(reuse.stage()==9u){std::cout<<"V488_REUSE_RESULT l1=1 l2=1 handler=1 exi_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v486_private_context_expectations.h"','#include "v486_private_context_expectations.h"\n#include "v488_private_reuse_expectations.h"')
    seam='    static ContextStartupWitness context(v486::expected_context);'
    return replace_exact(replace_exact(source,seam,REUSE_PROBE+seam),CONTEXT_END,CONTEXT_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('cache reuse trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v488_private_reuse_expectations.h':header,
        dest/'wii_os_cache_reuse_v488.h':(host/'wii_os_cache_reuse_v488.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_context(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V488_REUSE_ROUTE installed=0');return 1
    print('V488_REUSE_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
