#!/usr/bin/env python3
"""Authenticate original EXI version tail, return to OSInit, and SI cold setup."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v510_exi_absent import expectations as absent_geometry,install as install_absent
from make_start_to_si_sampling_v58 import data_at,EDGES
from make_start_to_exi_return_v57 import version_data
from apply_si_binding_v512 import apply as install_si
from apply_si_tick_v515 import apply as install_tick
from apply_si_profile_v518 import apply as install_profile
CALLS=((0x804efb5c,0x80521018),(0x805208c8,0x80532080),
       (0x8053209c,0x80521018),(0x805320d0,0x80532d6c))
TAIL=0x80521024
def expectations(data,digest=OWNER_SHA):
    absent_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS] or any(edge(data,s)[0]!=t for s,t in EDGES):
        raise ValueError('SI call graph')
    w=words_at(data,TAIL,1)[0];disp=w&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    if w>>26!=18 or w&3 or TAIL+disp!=0x80522f00:raise ValueError('version tail')
    exi=struct.unpack('>I',version_data(data))[0]
    si=struct.unpack('>I',data_at(data,0x8070aa70,4))[0]
    if not 0x80000000<=si<0x81800000:raise ValueError('SI version pointer')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_si_entry_witness_v520.h"\nnamespace undercover::wii::v520 {\n'
            'inline constexpr SiEntryExpectations expected_si_entry{'+','.join(map(fmt,rows))+','
            +f'0x{w:08x}u,0x{exi:08x}u,0x{si:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),w
ABSENT_END='        if(exi_absent.stage()==8u){std::cout<<"V510_EXI_ABSENT_RESULT cards=2 absent=1 extra_transfers=0 version_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
ABSENT_NEXT=ABSENT_END.replace('std::_Exit(0);','if(!si_entry.begin(cpu)){std::cout<<"V520_SI_ENTRY_INVALID reason="<<si_entry.failure()<<" stage="<<si_entry.stage()<<std::endl;std::_Exit(104);}std::cout<<"V520_SI_ENTRY_STAGE n=1"<<std::endl;')
PROBE='''    static SiEntryWitness si_entry(v520::expected_si_entry);
    if(si_entry.stage()){
        const auto before=si_entry.stage();
        if(!si_entry.observe(addr,cpu)){std::cout<<"V520_SI_ENTRY_INVALID reason="<<si_entry.failure()<<" stage="<<si_entry.stage()<<std::endl;std::_Exit(104);}
        if(si_entry.stage()!=before)std::cout<<"V520_SI_ENTRY_STAGE n="<<si_entry.stage()<<std::endl;
        if(si_entry.stage()==6u){std::cout<<"V520_SI_ENTRY_RESULT exi_return=1 version_tails=2 slots=4 rate_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v510_private_exi_absent_expectations.h"','#include "v510_private_exi_absent_expectations.h"\n#include "v520_private_si_entry_expectations.h"')
    seam='    static ExiAbsentWitness exi_absent(v510::expected_absent);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),ABSENT_END,ABSENT_NEXT)
def patch_label(source,word):
    pattern=re.compile(r'(?mi)^loc_80521024: ;\n    // 0x80521024: '+f'{word:08X}'+r'\n')
    if len(pattern.findall(source))!=1 or 'V520 original version tail' in source:raise ValueError('version label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80521024, ctx); // V520 original version tail\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80521024: ;$',source):patch_label(source,word);labels.append(shard)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('SI entry trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v520_private_si_entry_expectations.h':header,
        dest/'wii_si_entry_witness_v520.h':(host/'wii_si_entry_witness_v520.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_absent(data,generated,host,digest)
    install_si(generated,host);install_tick(generated,'runtime',host);install_profile(generated,host)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')
    shard=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8'),word),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V520_SI_ENTRY_ROUTE installed=0');return 1
    print('V520_SI_ENTRY_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
