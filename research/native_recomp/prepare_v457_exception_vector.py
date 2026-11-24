#!/usr/bin/env python3
"""Prepare private complete-image first exception vector observer (V460 full-image scope)."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v446_full_os_ipc import expectations as ipc_expectations,install as install_ipc
from prepare_v453_debug_leaf import VECTORS,data_at,vector_geometry
from prepare_v439_full_os_hardware import PreparationError as PriorHardwareError
from prepare_v446_full_os_ipc import IpcPreparationError

class VectorPreparationError(ValueError):
    def __init__(self,stage,ordinal=0):
        self.stage=stage;self.ordinal=ordinal
        super().__init__('first-vector preparation failed')

ENTRY=0x80520bf4
STOP=0x80520db8
SOURCE=0x80520ec0
REQUIRED={ENTRY+16:0x805450e8,0x80520c44:0x804e50b8,0x80520cc4:0x804e50a0,
          0x80520cf0:0x804e50a0,0x80520d98:0x80004338,0x80520da4:0x80522320,
          0x80520db4:0x80522378}

def geometry(data,digest=OWNER_SHA):
    try:ipc_expectations(data,digest)
    except (PriorHardwareError,IpcPreparationError):raise
    except (ValueError,struct.error):raise VectorPreparationError('prior_ipc') from None
    if not vector_geometry(data)[0]:raise VectorPreparationError('vector_table')
    offsets=struct.unpack('>15I',data_at(data,VECTORS,60))
    handler=struct.pack('>38I',*words_at(data,SOURCE,38))
    body=words_at(data,ENTRY,(STOP-ENTRY)//4);edges={}
    for i,w in enumerate(body):
        pc=ENTRY+4*i
        if w>>26==18 and w&3==1:
            dest=direct_bl(w,pc)
            edges[pc]=(dest,pc+4,w,words_at(data,dest,1)[0])
    if not 0<len(edges)<=32 or any(pc not in edges or edges[pc][0]!=dest for pc,dest in REQUIRED.items()):
        raise VectorPreparationError('edge_coverage')
    stop=words_at(data,STOP,1)[0]
    fmt=lambda vals:'{'+','.join(f'0x{v:x}u' for v in vals)+'}'
    rows=','.join('VectorEdge'+fmt(e) for e in edges.values())
    header=('#pragma once\n#include "wii_exception_vector_witness_v457.h"\nnamespace undercover::wii::v457 {\n'
            'inline constexpr VectorExpectations expected_vector{{'+rows+'},'+str(len(edges))+','+fmt(offsets)+','+fmt(handler)+f',0x{stop:08x}u'+'};\n}\n')
    return header,stop,set(e[0] for e in edges.values())

OLD='        if(os_ipc.stage()==4u){std::cout<<"V446_IPC_RESULT mem2_stores=2 ipc_stores=2 exception_entry=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
NEW='''        if(os_ipc.stage()==4u){
            std::cout<<"V446_IPC_RESULT mem2_stores=2 ipc_stores=2 exception_entry=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;
            if(!first_vector.begin(cpu)){std::cout<<"V457_VECTOR_INVALID reason="<<first_vector.failure()<<" stage="<<first_vector.stage()<<std::endl;std::_Exit(91);}
            std::cout<<"V457_VECTOR_BEGIN debug_needed="<<unsigned(first_vector.debug_needed())<<std::endl;
        }'''
OBSERVE='''    static FirstVectorWitness first_vector(v457::expected_vector);
    if(first_vector.active()){
        if(!first_vector.observe(addr,cpu)){std::cout<<"V457_VECTOR_INVALID reason="<<first_vector.failure()<<" stage="<<first_vector.stage()<<std::endl;std::_Exit(91);}
        if(first_vector.stage()==0u){std::cout<<"V457_VECTOR_PRELUDE n="<<first_vector.prelude()<<std::endl;return;}
        std::cout<<"V457_VECTOR_STAGE n="<<first_vector.stage()<<" valid=1"<<std::endl;
        if(first_vector.stage()==4u){std::cout<<"V457_VECTOR_RESULT copied=152 flush=5 invalidate=5 sync=2 isync=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v446_private_ipc_expectations.h"','#include "v446_private_ipc_expectations.h"\n#include "v457_private_vector_expectations.h"')
    seam='    static FullOsIpcWitness os_ipc(v446::expected_ipc);'
    return replace_exact(replace_exact(source,seam,OBSERVE+seam),OLD,NEW)

def return_seam(source,word):
    pat=re.compile(r'(?m)^loc_80520DB8: ;\n    // 0x80520DB8: '+f'{word:08X}'+r'\n',re.I)
    hits=list(pat.finditer(source))
    if len(hits)!=1 or 'V457 original vector cache return' in source:raise ValueError('return seam')
    at=hits[0].end()
    line='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80520DB8, ctx); // V457 original vector cache return\n'
    return source[:at]+line+source[at:]

def install(data,generated,host,digest=OWNER_SHA):
    header,stop,targets=geometry(data,digest)
    counts=dict.fromkeys(sorted(targets),0);shards=[]
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80520DB8: ;$',source):shards.append(shard)
    for i,n in enumerate(counts.values(),1):
        if n!=1:raise VectorPreparationError('trace_missing' if n==0 else 'trace_duplicate',i)
    if len(shards)!=1:raise VectorPreparationError('return_missing' if not shards else 'return_duplicate')
    shard=shards[0]
    if shard.is_symlink():raise ValueError('symlink')
    return_seam(shard.read_text(encoding='utf-8'),stop)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v457_private_vector_expectations.h':header,dest/'wii_exception_vector_witness_v457.h':(host/'wii_exception_vector_witness_v457.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    try:install_ipc(data,generated,host,digest)
    except (PriorHardwareError,IpcPreparationError):raise
    except (ValueError,struct.error):raise VectorPreparationError('prior_install') from None
    probe=dest/'wii_full_start_probe_v419.h'
    updated=patch_probe(probe.read_text(encoding='utf-8'))
    source=return_seam(shard.read_text(encoding='utf-8'),stop)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(updated,encoding='utf-8');shard.write_text(source,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except PriorHardwareError as e:
        print(f'V440_HW_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V457_VECTOR_ROUTE installed=0');return 1
    except IpcPreparationError as e:
        print(f'V448_IPC_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V457_VECTOR_ROUTE installed=0');return 1
    except VectorPreparationError as e:
        print(f'V460_VECTOR_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V457_VECTOR_ROUTE installed=0');return 1
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V460_VECTOR_PREP stage=other ordinal=0 verified=0')
        print('V457_VECTOR_ROUTE installed=0');return 1
    print('V457_VECTOR_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
