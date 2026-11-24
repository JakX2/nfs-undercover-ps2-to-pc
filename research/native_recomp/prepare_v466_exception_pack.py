#!/usr/bin/env python3
"""Compose authenticated complete-image vector loop and syscall overlay observer."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v457_exception_vector import geometry as vector_geometry,install as install_vector,ENTRY,STOP,SOURCE,REQUIRED
from prepare_v453_debug_leaf import VECTORS,data_at
from make_osinit_systemcall_v45 import SOURCE as SYS_SOURCE,ENTRY as SYS_ENTRY,END as SYS_END
EXC_END=0x80520e74
ALARM=0x805210cc
BRIDGE=((0x805208ac,SYS_ENTRY),(0x805208b0,ALARM))
SYS_REQUIRED={SYS_ENTRY+0x2c:0x80004338,SYS_ENTRY+0x38:0x80522320,SYS_ENTRY+0x48:0x80522378}
def edge(data,site):
    w=words_at(data,site,1)[0];pc=direct_bl(w,site)
    return pc,site+4,w,words_at(data,pc,1)[0]
def edges(data,start,end,required):
    found={}
    for i,w in enumerate(words_at(data,start,(end-start)//4)):
        site=start+i*4
        if w>>26==18 and w&3==1:found[site]=edge(data,site)
    if not 0<len(found)<=32 or any(site not in found or found[site][0]!=pc for site,pc in required.items()):
        raise ValueError('call coverage')
    return list(found.values())
def expectations(data,digest=OWNER_SHA):
    vector_geometry(data,digest)
    offsets=struct.unpack('>15I',data_at(data,VECTORS,60))
    if offsets.count(0xc00)!=1:raise ValueError('syscall slot')
    handler=struct.pack('>38I',*words_at(data,SOURCE,38))
    syscall=struct.pack('>7I',*words_at(data,SYS_SOURCE,7))
    exc=edges(data,ENTRY,EXC_END,{**REQUIRED,0x80520e58:0x804e50b8,0x80520e60:0x80545134})
    sys=edges(data,SYS_ENTRY,SYS_END,SYS_REQUIRED)
    bridge=[edge(data,site) for site,_ in BRIDGE]
    if [e[0] for e in bridge]!=[pc for _,pc in BRIDGE]:raise ValueError('bridge')
    if any(words_at(data,end-4,1)[0]!=0x4e800020 for end in (EXC_END,SYS_END)):raise ValueError('return')
    fmt=lambda vals:'{'+','.join(f'0x{v:x}u' for v in vals)+'}'
    rows=lambda vals:'{'+','.join('VectorEdge'+fmt(e) for e in vals)+'}'
    header=('#pragma once\n#include "wii_exception_pack_route_v466.h"\nnamespace undercover::wii::v466 {\n'
            'inline constexpr ExceptionPackRouteExpectations expected_pack{'
            'ExceptionPackExpectations{'+fmt(offsets)+','+fmt(handler)+','+fmt(syscall)+'},'
            +rows(exc)+','+rows(sys)+f',{len(exc)}u,{len(sys)}u,'
            +'VectorEdge'+fmt(bridge[0])+',VectorEdge'+fmt(bridge[1])+f',0x{words_at(data,STOP,1)[0]:08x}u'+'};\n}\n')
    return header,sorted({e[0] for e in exc+sys+bridge})
PRELUDE='    static FirstVectorWitness first_vector(v457::expected_vector);'
ROUTE='''    static ExceptionPackRoute pack(v466::expected_pack);
    static FirstVectorWitness first_vector(v457::expected_vector);
    if(first_vector.stage()==4u){
        const unsigned before=pack.phase(),vectors=pack.vectors();
        if(!pack.observe(addr,cpu)){std::cout<<"V466_PACK_INVALID reason="<<pack.failure()<<" phase="<<pack.phase()<<std::endl;std::_Exit(92);}
        if(pack.vectors()!=vectors)std::cout<<"V466_PACK_VECTOR n="<<pack.vectors()<<std::endl;
        if(pack.phase()!=before)std::cout<<"V466_PACK_PHASE n="<<pack.phase()<<std::endl;
        if(pack.phase()==4u){std::cout<<"V466_PACK_RESULT vectors=15 syscall=1 alarm_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }'''
BEGIN='            std::cout<<"V457_VECTOR_BEGIN debug_needed="<<unsigned(first_vector.debug_needed())<<std::endl;'
FIRST='        if(first_vector.stage()==0u){std::cout<<"V457_VECTOR_PRELUDE n="<<first_vector.prelude()<<std::endl;return;}'
END='        if(first_vector.stage()==4u){std::cout<<"V457_VECTOR_RESULT copied=152 flush=5 invalidate=5 sync=2 isync=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
def patch_probe(source):
    source=replace_exact(source,'#include "v457_private_vector_expectations.h"','#include "v457_private_vector_expectations.h"\n#include "v466_private_pack_expectations.h"')
    source=replace_exact(source,PRELUDE,ROUTE)
    source=replace_exact(source,BEGIN,BEGIN+'''
            if(!pack.begin(cpu)){std::cout<<"V466_PACK_INVALID reason="<<pack.failure()<<" phase="<<pack.phase()<<std::endl;std::_Exit(92);}''')
    source=replace_exact(source,FIRST,FIRST+'''
        const bool pack_ok=first_vector.stage()==1u?pack.first_copy(cpu):pack.first_vector_event(addr,cpu,first_vector.stage());
        if(!pack_ok){std::cout<<"V466_PACK_INVALID reason="<<pack.failure()<<" phase="<<pack.phase()<<std::endl;std::_Exit(92);}''')
    return replace_exact(source,END,END.replace('std::_Exit(0);','')+'\n        if(first_vector.stage()==4u)std::cout<<"V466_PACK_VECTOR n=1"<<std::endl;')
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest)
    counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v466_private_pack_expectations.h':header}
    for name in ('wii_exception_pack_v462.h','wii_exception_pack_route_v466.h'):files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_vector(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V466_PACK_ROUTE installed=0');return 1
    print('V466_PACK_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
