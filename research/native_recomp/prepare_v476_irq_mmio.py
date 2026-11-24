#!/usr/bin/env python3
"""Private complete-image continuation through actual PI and Hollywood writes."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v473_module_irq import expectations as irq_geometry,install as install_irq,STOP
from apply_irq_bootstrap_v475 import apply as install_runtime
from make_start_to_interrupt_mmio_v46 import is_stw
DISABLE=0x805265ac
CALL=0x80526674
STORES=((0x8052666c,5,4,0x3004),(0x80526670,0,3,0x34))
def expectations(data,digest=OWNER_SHA):
    irq_geometry(data,digest)
    start=words_at(data,STOP,1)[0]
    rows=words_at(data,STOP,(CALL-STOP)//4)
    for pc,src,base,disp in STORES:
        if not is_stw(rows[(pc-STOP)//4],src,base,disp):raise ValueError('IRQ MMIO store geometry')
    e=edge(data,CALL)
    if e[0]!=DISABLE:raise ValueError('IRQ disable branch')
    fmt=lambda row:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in row)+'}'
    header=('#pragma once\n#include "wii_irq_bootstrap_v475.h"\nnamespace undercover::wii::v476 {\n'
            f'inline constexpr uint32_t start_word=0x{start:08x}u;\n'
            'inline constexpr VectorEdge disable_edge='+fmt(e)+';\n}\n')
    return header,DISABLE
IRQ_END='        if(irq.stage()==5u){std::cout<<"V473_IRQ_RESULT module=1 table=128 pointer=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
IRQ_NEXT=IRQ_END.replace('std::_Exit(0);','if(!mmio.begin(cpu)){std::cout<<"V476_MMIO_INVALID reason="<<mmio.failure()<<" stage="<<mmio.stage()<<std::endl;std::_Exit(95);}std::cout<<"V476_MMIO_STAGE n=1"<<std::endl;')
MMIO_PROBE='''    static IrqMmioWitness mmio(v476::start_word,v476::disable_edge);
    if(mmio.stage()){
        if(!mmio.observe(addr,cpu)){std::cout<<"V476_MMIO_INVALID reason="<<mmio.failure()<<" stage="<<mmio.stage()<<std::endl;std::_Exit(95);}
        std::cout<<"V476_MMIO_STAGE n="<<mmio.stage()<<std::endl;
        if(mmio.stage()==2u){std::cout<<"V476_MMIO_RESULT pi=1 hollywood=1 aliases=1 writes=2 disable_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v473_private_irq_expectations.h"','#include "v473_private_irq_expectations.h"\n#include "v476_private_mmio_expectations.h"')
    seam='    static ModuleIrqWitness irq(v473::expected_irq);'
    return replace_exact(replace_exact(source,seam,MMIO_PROBE+seam),IRQ_END,IRQ_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,target=expectations(data,digest)
    trace=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);'
    count=0
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        count+=shard.read_text(encoding='utf-8').count(trace)
    if count!=1:raise ValueError('IRQ disable trace')
    dest=generated/'nWiiRuntime/include/undercover'
    out=dest/'v476_private_mmio_expectations.h'
    if dest.is_symlink() or out.exists() or out.is_symlink():raise ValueError('destination')
    install_irq(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h'
    new=patch_probe(probe.read_text(encoding='utf-8'))
    install_runtime(generated,host)
    out.write_text(header,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V476_MMIO_ROUTE installed=0');return 1
    print('V476_MMIO_ROUTE installed=1 native_mask=1 ios_scheduler=0');return 0
if __name__=='__main__':raise SystemExit(main())
