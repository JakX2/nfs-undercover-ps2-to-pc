#!/usr/bin/env python3
"""Private original __OSContextInit continuation to cache initializer entry."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v483_irq_return import expectations as irq_geometry,install as install_irq
CONTEXT=0x80522eb8
CALLS=((0x805208bc,CONTEXT),(CONTEXT+0x18,0x80520e9c),
       (CONTEXT+0x34,0x804e50b8),(0x805208c0,0x80522540))
RET=CONTEXT+0x44
def expectations(data,digest=OWNER_SHA):
    irq_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS] or words_at(data,RET,1)[0]!=0x4e800020:
        raise ValueError('context call graph')
    # Extract only the stack-frame geometry from the original prologue.
    frames=[0x10000-(w&0xffff) for w in words_at(data,CONTEXT,6)
            if w>>26==37 and (w>>21)&31==1 and (w>>16)&31==1 and w&0x8000]
    if len(frames)!=1 or not 8<=frames[0]<=256 or frames[0]&7:raise ValueError('context stack frame')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_context_startup_witness_v486.h"\nnamespace undercover::wii::v486 {\n'
            'inline constexpr ContextStartupExpectations expected_context{{'+','.join(map(fmt,rows))+'},'+str(frames[0])+'u};\n}\n')
    return header,sorted({r[0] for r in rows})
IRQ_END='        if(irq_return.stage()==11u){std::cout<<"V483_IRQ_RETURN_RESULT banks=7 restore=1 handler=1 context_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
IRQ_NEXT=IRQ_END.replace('std::_Exit(0);','if(!context.begin(cpu)){std::cout<<"V486_CONTEXT_INVALID reason="<<context.failure()<<" stage="<<context.stage()<<std::endl;std::_Exit(97);}std::cout<<"V486_CONTEXT_STAGE n=1"<<std::endl;')
CONTEXT_PROBE='''    static ContextStartupWitness context(v486::expected_context);
    if(context.stage()){
        if(!context.observe(addr,cpu)){std::cout<<"V486_CONTEXT_INVALID reason="<<context.failure()<<" stage="<<context.stage()<<std::endl;std::_Exit(97);}
        std::cout<<"V486_CONTEXT_STAGE n="<<context.stage()<<std::endl;
        if(context.stage()==4u){std::cout<<"V486_CONTEXT_RESULT handler=1 current_context=1 cache_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v483_private_irq_return_expectations.h"','#include "v483_private_irq_return_expectations.h"\n#include "v486_private_context_expectations.h"')
    seam='    static IrqReturnWitness irq_return(v483::expected_return);'
    return replace_exact(replace_exact(source,seam,CONTEXT_PROBE+seam),IRQ_END,IRQ_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('context trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v486_private_context_expectations.h':header,
        dest/'wii_context_startup_witness_v486.h':(host/'wii_context_startup_witness_v486.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_irq(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V486_CONTEXT_ROUTE installed=0');return 1
    print('V486_CONTEXT_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
