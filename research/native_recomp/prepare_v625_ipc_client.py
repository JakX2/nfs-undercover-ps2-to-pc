#!/usr/bin/env python3
"""Complete-image cold IPC client continuation after original IRQ enable."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256
from make_v624_ipc_geometry import geometry,render,SPANS,RETURN
from prepare_v616_irq_enable import install as install_irq
INCLUDE='#include "v616_private_irq_expectations.h"'
DECL='    static IrqEnableWitness irq_enable(v616::expected_irq);'
NEXT=DECL+'''
    static IpcClientWitness ipc_client(v624::expected_client);
    if(ipc_client.stage()){
        if(!ipc_client.observe(addr,cpu)){
            std::cout<<"V625_IPC_INVALID reason="<<ipc_client.failure()<<" stage="<<ipc_client.stage()<<std::endl;std::_Exit(120);
        }
        std::cout<<"V625_IPC_STAGE n="<<ipc_client.stage()<<std::endl;
        if(ipc_client.stage()==19u){
            std::cout<<"V625_IPC_RESULT calls=17 heap=1 handler=1 mailbox=1 returned=1 queued=0 serviced=0 actual_ios=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
END='''            std::cout<<"V616_IRQ_RESULT returned=1 ee=1 previous=0 ticks=5 pending=0 actual_irq=0 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);'''
CONT=END.replace('std::_Exit(0);','''const char* ipc=std::getenv("UNDERCOVER_V625_IPC");
            if(!ipc||ipc[0]!='1'||ipc[1]!='\\0'||!ipc_client.begin(cpu)){
                std::cout<<"V625_IPC_INVALID reason=1 stage=0"<<std::endl;std::_Exit(120);}
            std::cout<<"V625_IPC_STAGE n=1"<<std::endl;''')
LABEL=re.compile(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n')
DEF=re.compile(r'(?m)^void ((?:fn|func)_[0-9A-Fa-f]+)\(CPUContext& ctx\) \{')
ERRORS={'native IPC label identity','native IPC label body','native IPC duplicate root','native IPC coverage',
        'native IPC dispatch','native IPC entry trace','native IPC return label','IPC tree','IPC destination',
        'source seam','identity','span','span identity','call coverage','handler constant','handler root',
        'handler span','word identity','route','return'}
def patch_probe(s):
    return replace_exact(replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n#include "v624_private_ipc_expectations.h"'),DECL,NEXT),END,CONT)
def patch_return(s,word,pc=RETURN):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {word:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pat.findall(s))!=1:raise ValueError('native IPC return label')
    return pat.sub(lambda m:m[0]+f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V625 IPC client return\n',s,count=1)
def audit_native(shards,main,expected):
    hits=dict.fromkeys(expected,0);owners={}
    roots={owner for owner,_ in expected.values()}
    for s in shards:
        fs=list(DEF.finditer(s))
        for i,f in enumerate(fs):
            root=int(f[1].split('_')[1],16)
            if root in roots:
                if root in owners:raise ValueError('native IPC duplicate root')
                owners[root]=f[1]
            body=s[f.end():fs[i+1].start() if i+1<len(fs) else len(s)]
            for j,l in enumerate(labels:=list(LABEL.finditer(body))):
                pc=int(l[1],16)
                if pc not in hits:continue
                owner,w=expected[pc];hits[pc]+=1
                if root!=owner or int(l[2],16)!=pc or int(l[3],16)!=w:raise ValueError('native IPC label identity')
                block=body[l.end():labels[j+1].start() if j+1<len(labels) else len(body)].split('\n}',1)[0]
                if block.count('++ctx.inst_count;')!=1 or any(x in block for x in ('interpret_step','micro_interpret','UNIMPLEMENTED','unimplemented')):
                    raise ValueError('native IPC label body')
    if set(owners)!=roots or any(n!=1 for n in hits.values()):raise ValueError('native IPC coverage')
    for pc,name in owners.items():
        rows=re.findall(r'(?mi)^[ \t]*case[ \t]+0x'+f'{pc:X}'+r'[ \t]*:[ \t]*([^\r\n]*)',main)
        if len(rows)!=1 or not re.fullmatch(re.escape(name)+r'\(ctx\);[ \t]*break;[ \t]*',rows[0]):
            raise ValueError('native IPC dispatch')
    return len(hits)
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    g=geometry(dol,elf,dd,ed);rows,handler,hword,ret=g
    header=render(*g);targets={r[0] for r in rows};counts=dict.fromkeys(targets,0)
    expected={pc+4*i:(pc,w) for pc,n in SPANS for i,w in enumerate(words_at(dol,pc,n//4))}
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):
        raise ValueError('IPC tree')
    native=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),expected)
    owner=None
    for p in shards:
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_'+f'{RETURN:X}'+r': ;$',s):
            if owner is not None:raise ValueError('native IPC return label')
            patch_return(s,ret);owner=p
    if any(n!=1 for n in counts.values()):raise ValueError('native IPC entry trace')
    if owner is None:raise ValueError('native IPC return label')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v624_private_ipc_expectations.h':header,dest/'wii_ipc_client_witness_v623.h':(host/'wii_ipc_client_witness_v623.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('IPC destination')
    install_irq(dol,elf,generated,host,dd,ed)
    probe=dest/'wii_full_start_probe_v419.h'
    files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    files[owner]=patch_return(owner.read_text(encoding='utf-8'),ret)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    return native
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('identity')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        reason=str(e) if str(e) in ERRORS else 'prior_or_io'
        print('V625_IPC_ROUTE installed=0 reason='+reason.replace(' ','_'));return 1
    print(f'V625_IPC_ROUTE installed=1 calls=17 native_words={n} roots=10 handler_identity=1 actual_ios=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
