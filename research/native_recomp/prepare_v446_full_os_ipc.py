#!/usr/bin/env python3
"""Extend complete-image MEM1 checkpoint through MEM2 and IPC-buffer stores."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v444_full_os_arena import expectations as arena_expectations,install as install_arena
from make_osinit_mem2_v37 import check_source,check_setter
from make_osinit_ipc_v38 import validate_ipc
from prepare_v439_full_os_hardware import PreparationError as PriorHardwareError
EDGES=((0x8052088c,0x80521d68),(0x805208a0,0x80521d50),
       (0x805208a4,0x8052ae80),(0x805208a8,0x80520bf4))
class IpcPreparationError(ValueError):
    def __init__(self,stage,ordinal=0):
        self.stage=stage;self.ordinal=ordinal
        super().__init__('IPC preparation failed')

def require(condition,stage,ordinal=0):
    if not condition:raise IpcPreparationError(stage,ordinal)

def expectations(data,digest=OWNER_SHA):
    try:arena_expectations(data,digest)
    except PriorHardwareError:raise
    except (ValueError,struct.error):raise IpcPreparationError('prior_arena_geometry') from None
    def block(pc,n):return struct.pack('>'+str(n)+'I',*words_at(data,pc,n))
    try:check_source(block(0x80520818,35))
    except (ValueError,struct.error):raise IpcPreparationError('mem2_geometry') from None
    for i,(_,pc) in enumerate(EDGES[:2],1):
        try:check_setter(block(pc,2),pc)
        except (ValueError,struct.error):raise IpcPreparationError('mem2_setter',i) from None
    try:validate_ipc(block(EDGES[2][1],6))
    except (ValueError,struct.error):raise IpcPreparationError('ipc_helper') from None
    rows=[]
    for i,(site,target) in enumerate(EDGES,1):
        try:
            word=words_at(data,site,1)[0]
            require(direct_bl(word,site)==target,'call_geometry',i)
        except (ValueError,struct.error):raise IpcPreparationError('call_geometry',i) from None
        rows.append('IpcEdge{'+','.join(f'0x{w:08x}u' for w in (target,site+4,word,words_at(data,target,1)[0]))+'}')
    return ('#pragma once\n#include "wii_full_os_ipc_witness.h"\nnamespace undercover::wii::v446 {\n'
            'inline constexpr OsIpcExpectations expected_ipc{{'+','.join(rows)+'}};\n}\n')
OLD='        if(os_arena.stage()==4u){std::cout<<"V444_ARENA_RESULT boot_info=1 low_store=1 high_store=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
NEW='''        if(os_arena.stage()==4u){
            std::cout<<"V444_ARENA_RESULT boot_info=1 low_store=1 high_store=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;
            if(!os_ipc.begin(cpu)){std::cout<<"V446_IPC_INVALID reason="<<os_ipc.failure()<<" stage="<<os_ipc.stage()<<std::endl;std::_Exit(90);}
            std::cout<<"V446_IPC_BEGIN clamp="<<unsigned(os_ipc.clamped())<<std::endl;
        }'''
OBSERVE='''    static FullOsIpcWitness os_ipc(v446::expected_ipc);
    if(os_ipc.active()){
        if(!os_ipc.observe(addr,cpu)){std::cout<<"V446_IPC_INVALID reason="<<os_ipc.failure()<<" stage="<<os_ipc.stage()<<std::endl;std::_Exit(90);}
        std::cout<<"V446_IPC_STAGE n="<<os_ipc.stage()<<" valid=1"<<std::endl;
        if(os_ipc.stage()==4u){std::cout<<"V446_IPC_RESULT mem2_stores=2 ipc_stores=2 exception_entry=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v444_private_arena_expectations.h"','#include "v444_private_arena_expectations.h"\n#include "v446_private_ipc_expectations.h"')
    seam='    static FullOsArenaWitness os_arena(v444::expected_arena);'
    return replace_exact(replace_exact(source,seam,OBSERVE+seam),OLD,NEW)
def install(data,generated,host,digest=OWNER_SHA):
    expected=expectations(data,digest)
    counts={pc:0 for _,pc in EDGES}
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    for i,n in enumerate(counts.values(),1):
        require(n==1,'trace_missing' if n==0 else 'trace_duplicate',i)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v446_private_ipc_expectations.h':expected,dest/'wii_full_os_ipc_witness.h':(host/'wii_full_os_ipc_witness.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    try:install_arena(data,generated,host,digest)
    except PriorHardwareError:raise
    except (ValueError,struct.error):raise IpcPreparationError('prior_arena_install') from None
    probe=dest/'wii_full_start_probe_v419.h'
    updated=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(updated,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except PriorHardwareError as e:
        print(f'V440_HW_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V446_IPC_ROUTE installed=0');return 1
    except IpcPreparationError as e:
        print(f'V448_IPC_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V446_IPC_ROUTE installed=0');return 1
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V448_IPC_PREP stage=io_or_other ordinal=0 verified=0')
        print('V446_IPC_ROUTE installed=0');return 1
    print('V446_IPC_ROUTE installed=1 edges=4 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
