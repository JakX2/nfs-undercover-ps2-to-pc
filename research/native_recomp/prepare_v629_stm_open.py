#!/usr/bin/env python3
"""Private original STM geometry and complete-image continuation to IOS_Open."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from make_v624_ipc_geometry import geometry as ipc_geometry,exact_words
from make_start_to_stm_v70 import STM,STM_SIZE,OPEN,EDGES,SKIP
from prepare_v625_ipc_client import install as install_ipc,audit_native
BEGIN=0x8052094c
OSINIT=0x80520670
DECL='    static IpcClientWitness ipc_client(v624::expected_client);'
INCLUDE='#include "v624_private_ipc_expectations.h"'
END='''            std::cout<<"V625_IPC_RESULT calls=17 heap=1 handler=1 mailbox=1 returned=1 queued=0 serviced=0 actual_ios=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
NEXT=DECL+'''
    static StmPrefixWitness stm_prefix(v629::expected_stm);
    if(stm_prefix.stage()){
        if(!stm_prefix.observe(addr,cpu)){
            std::cout<<"V629_STM_INVALID reason="<<stm_prefix.failure()<<" stage="<<stm_prefix.stage()<<std::endl;std::_Exit(121);
        }
        std::cout<<"V629_STM_STAGE n="<<stm_prefix.stage()<<std::endl;
        if(stm_prefix.stage()==3u){
            std::cout<<"V629_STM_RESULT entry=1 open=1 pathname="<<stm_prefix.path_kind()<<" mode=0 native_transport=1 serviced=0 actual_ios=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
CONT=END.replace('std::_Exit(0);','''const char* stm=std::getenv("UNDERCOVER_V629_STM");
            if(!stm||stm[0]!='1'||stm[1]!='\\0'||!stm_prefix.begin(cpu,true)){
                std::cout<<"V629_STM_INVALID reason=1 stage=0"<<std::endl;std::_Exit(121);}
            std::cout<<"V629_STM_STAGE n=1"<<std::endl;''')
PATHS=(b'/dev/stm/immediate\0',b'/dev/stm/eventhook\0')
def paths_at(dol):
    out=[];ranges=[]
    for i in range(11):
        off,base,n=(struct.unpack_from('>I',dol,k+4*i)[0] for k in (0x1c,0x64,0xac))
        if not n:continue
        if off<256 or off+n>len(dol) or base+n>2**32:raise ValueError('data geometry')
        if any(base<e and a<base+n for a,e in ranges):raise ValueError('data overlap')
        ranges.append((base,base+n))
        if not 0x80000000<=base<base+n<=0x81800000:continue
        data=dol[off:off+n]
        for kind,p in enumerate(PATHS,1):
            at=0
            while (hit:=data.find(p,at))>=0:
                out.append((base+hit,kind));at=hit+len(p)
                if len(out)>8:raise ValueError('path census')
    if not out or len({a for a,k in out})!=len(out):raise ValueError('path census')
    return sorted(out)
def geometry(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    _,handler,_,_=ipc_geometry(dol,elf,dd,ed)
    sizes=parse_functions(elf)
    if sizes.get(STM)!=STM_SIZE or not 0<sizes.get(OPEN,0)<=4096:raise ValueError('STM spans')
    bridge=exact_words(dol,elf,BEGIN,7);body=exact_words(dol,elf,STM,STM_SIZE//4)
    if body[-1]!=0x4e800020:raise ValueError('STM return')
    found={(STM+4*i,direct_bl(w,STM+4*i)) for i,w in enumerate(body) if w>>26==18 and w&3==1}
    if found!=set(EDGES[1:]) or direct_bl(bridge[-1],BEGIN+24)!=STM:raise ValueError('STM call geometry')
    for pc in (0x80520954,0x80520960):
        w=bridge[(pc-BEGIN)//4];disp=w&0xfffc
        if disp&0x8000:disp-=0x10000
        if w>>26!=16 or w&3 or pc+disp!=SKIP:raise ValueError('STM alternate geometry')
    def edge(site,target):
        w=exact_words(dol,elf,site,1)[0]
        if direct_bl(w,site)!=target:raise ValueError('STM call geometry')
        return (target,site+4,w,exact_words(dol,elf,target,1)[0])
    return bridge,body,edge(0x80520964,STM),edge(0x8052b08c,OPEN),paths_at(dol),handler
def render(g):
    bridge,body,stm,op,paths,handler=g
    fmt=lambda x:','.join(f'0x{v:08x}u' for v in x)
    return ('#pragma once\n#include "wii_stm_prefix_witness_v629.h"\nnamespace undercover::wii::v629 {\n'
            'inline constexpr StmPrefixExpectations expected_stm{{'+fmt(bridge)+'},VectorEdge{'+fmt(stm)+'},VectorEdge{'+fmt(op)+'},'
            'std::array<StmPath,8>{'+','.join('StmPath{'+fmt(p)+'}' for p in paths)+'},'
            +f'{len(paths)}u,0x{handler:08x}u'+'};\n}\n')
def patch_probe(s):
    return replace_exact(replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n#include "v629_private_stm_expectations.h"'),DECL,NEXT),END,CONT)
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    g=geometry(dol,elf,dd,ed);bridge,body,stm,op,paths,handler=g
    expected={**{BEGIN+4*i:(OSINIT,w) for i,w in enumerate(bridge)},
              **{STM+4*i:(STM,w) for i,w in enumerate(body)},OPEN:(OPEN,op[3])}
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):
        raise ValueError('STM tree')
    words=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),expected)
    counts={STM:0,OPEN:0}
    for p in shards:
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('STM trace')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v629_private_stm_expectations.h':render(g),
           dest/'wii_stm_prefix_witness_v629.h':(host/'wii_stm_prefix_witness_v629.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('STM destination')
    install_ipc(dol,elf,generated,host,dd,ed)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    return words
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('identity')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        allow={'data geometry','data overlap','path census','STM spans','STM return','STM call geometry','STM alternate geometry','STM tree','STM trace','STM destination',
               'native IPC label identity','native IPC label body','native IPC duplicate root','native IPC coverage','native IPC dispatch','source seam','identity'}
        reason=str(e) if str(e) in allow else 'prior_or_io'
        print('V629_STM_ROUTE installed=0 reason='+reason.replace(' ','_'));return 1
    print(f'V629_STM_ROUTE installed=1 native_words={n} edges=2 pathname_identity=1 actual_ios=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
