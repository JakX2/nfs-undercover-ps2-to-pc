#!/usr/bin/env python3
"""Authenticate original cold EXI poll loop and observe actual native controller reads."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v488_os_cache_reuse import expectations as reuse_geometry,install as install_reuse
from apply_exi_controller_v490 import apply as install_exi
from apply_irq_bootstrap_v475 import rewrite
from make_start_to_exi_poll_v52 import verify_prefix,EXI,STOP
CALLS=((0x805208c4,EXI),(STOP,0x8052693c))
def expectations(data,digest=OWNER_SHA):
    reuse_geometry(data,digest)
    prefix=words_at(data,EXI,(STOP-EXI)//4)
    verify_prefix(struct.pack('>'+str(len(prefix))+'I',*prefix))
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS]:raise ValueError('EXI call graph')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_exi_poll_witness_v491.h"\nnamespace undercover::wii::v491 {\n'
            'inline constexpr ExiColdPollExpectations expected_poll{{'+','.join(map(fmt,rows))+'}};\n}\n')
    return header,sorted({r[0] for r in rows})
REUSE_END='        if(reuse.stage()==9u){std::cout<<"V488_REUSE_RESULT l1=1 l2=1 handler=1 exi_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
REUSE_NEXT=REUSE_END.replace('std::_Exit(0);','if(!exi_poll.begin(cpu,IrqBankBinding::exi_enabled())){std::cout<<"V491_EXI_POLL_INVALID reason="<<exi_poll.failure()<<" stage="<<exi_poll.stage()<<std::endl;std::_Exit(99);}std::cout<<"V491_EXI_POLL_STAGE n=1"<<std::endl;')
POLL_PROBE='''    static ExiColdPollWitness exi_poll(v491::expected_poll);
    if(exi_poll.stage()){
        if(!exi_poll.observe(addr,cpu)){std::cout<<"V491_EXI_POLL_INVALID reason="<<exi_poll.failure()<<" stage="<<exi_poll.stage()<<std::endl;std::_Exit(99);}
        std::cout<<"V491_EXI_POLL_STAGE n="<<exi_poll.stage()<<std::endl;
        if(exi_poll.stage()==2u){std::cout<<"V491_EXI_POLL_RESULT channels=3 idle=1 mask_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
BIND_PAIRS=(('#include "wii_exi_controller_v489.h"','#include "wii_exi_controller_v489.h"\n#include "wii_exi_poll_witness_v491.h"'),
('    static bool active()noexcept{return active_!=nullptr;}',
 '    static bool active()noexcept{return active_!=nullptr;}\n    static bool exi_enabled()noexcept{return active_&&active_->exi_;}'),
('            case Reg::ExiFull:{const auto off=exi_offset(a);return active_->exi_->read(off/20u,off%20u);}',
 '            case Reg::ExiFull:{const auto off=exi_offset(a);const auto v=active_->exi_->read(off/20u,off%20u);exi_cold_poll_trace.record(false,off,v);return v;}'),
('            case Reg::ExiFull:{const auto off=exi_offset(a);active_->exi_->write(off/20u,off%20u,value);return true;}',
 '            case Reg::ExiFull:{const auto off=exi_offset(a);active_->exi_->write(off/20u,off%20u,value);exi_cold_poll_trace.record(true,off,value);return true;}'))
def patch_probe(source):
    source=replace_exact(source,'#include "v488_private_reuse_expectations.h"','#include "v488_private_reuse_expectations.h"\n#include "v491_private_exi_poll_expectations.h"')
    seam='    static OsCacheReuseWitness reuse(v488::expected_cache);'
    return replace_exact(replace_exact(source,seam,POLL_PROBE+seam),REUSE_END,REUSE_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('EXI poll trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v491_private_exi_poll_expectations.h':header,
        dest/'wii_exi_poll_witness_v491.h':(host/'wii_exi_poll_witness_v491.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_reuse(data,generated,host,digest);install_exi(generated,host)
    probe=dest/'wii_full_start_probe_v419.h';binding=dest/'wii_irq_bank_binding_v481.h'
    new=patch_probe(probe.read_text(encoding='utf-8'))
    bound=rewrite(binding.read_text(encoding='utf-8'),BIND_PAIRS)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8');binding.write_text(bound,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V491_EXI_POLL_ROUTE installed=0');return 1
    print('V491_EXI_POLL_ROUTE installed=1 native_controller=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
