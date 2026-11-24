#!/usr/bin/env python3
"""Continue the authenticated complete Wii image through original IRQ return."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v476_irq_mmio import expectations as mmio_geometry,install as install_mmio
from apply_irq_banks_v481 import apply as install_banks
from apply_irq_mask_trace_v482 import apply as install_trace
CALLS=((0x80526674,0x805265ac),(0x805266a0,0x805266e0),
       (0x805266b0,0x805265d4),(0x805266c0,0x80520e9c),(0x805208bc,0x80522eb8))
RETURNS=(0x80526708,0x80526778,0x805267b8,0x805267e4,
         0x80526828,0x8052686c,0x805268a0,0x80526938,0x805266dc,0x805265f4)
def expectations(data,digest=OWNER_SHA):
    mmio_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS]:raise ValueError('IRQ return edges')
    if any(words_at(data,pc,1)[0]!=0x4e800020 for pc in RETURNS):raise ValueError('IRQ return instructions')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_irq_return_witness_v482.h"\nnamespace undercover::wii::v483 {\n'
            'inline constexpr IrqReturnExpectations expected_return{{'+','.join(map(fmt,rows))+'}};\n}\n')
    return header,sorted({r[0] for r in rows})
MMIO_END='        if(mmio.stage()==2u){std::cout<<"V476_MMIO_RESULT pi=1 hollywood=1 aliases=1 writes=2 disable_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
MMIO_NEXT=MMIO_END.replace('std::_Exit(0);','if(!irq_return.begin(cpu)){std::cout<<"V483_IRQ_RETURN_INVALID reason="<<irq_return.failure()<<" stage="<<irq_return.stage()<<std::endl;std::_Exit(96);}std::cout<<"V483_IRQ_RETURN_STAGE n=1"<<std::endl;')
RETURN_PROBE='''    static IrqReturnWitness irq_return(v483::expected_return);
    if(irq_return.stage()){
        if(!irq_return.observe(addr,cpu)){std::cout<<"V483_IRQ_RETURN_INVALID reason="<<irq_return.failure()<<" stage="<<irq_return.stage()<<std::endl;std::_Exit(96);}
        std::cout<<"V483_IRQ_RETURN_STAGE n="<<irq_return.stage()<<std::endl;
        if(irq_return.stage()==11u){std::cout<<"V483_IRQ_RETURN_RESULT banks=7 restore=1 handler=1 context_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v476_private_mmio_expectations.h"','#include "v476_private_mmio_expectations.h"\n#include "v483_private_irq_return_expectations.h"')
    seam='    static IrqMmioWitness mmio(v476::start_word,v476::disable_edge);'
    return replace_exact(replace_exact(source,seam,RETURN_PROBE+seam),MMIO_END,MMIO_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('IRQ return trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';out=dest/'v483_private_irq_return_expectations.h'
    if dest.is_symlink() or out.exists() or out.is_symlink():raise ValueError('destination')
    install_mmio(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    install_banks(generated,host);install_trace(generated,host)
    out.write_text(header,encoding='utf-8');probe.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V483_IRQ_RETURN_ROUTE installed=0');return 1
    print('V483_IRQ_RETURN_ROUTE installed=1 banks=7 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
