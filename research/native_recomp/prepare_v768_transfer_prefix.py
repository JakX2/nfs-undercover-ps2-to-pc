#!/usr/bin/env python3
"""Extend original handler through exact transfer entry, save and disable; stop before MMIO."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_transfer_v765 import plan
from prepare_owner_pair_v753 import plan as pair
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_scheduler_v722 import reachable
def expectations(dol,elf):
    roots,C,D,Q,S,R,edges=plan(dol,elf)
    n,*_=geometry(dol,elf);site,target,w=edge(HANDLER,exact(dol,elf,HANDLER,n),4)
    a,b,count,sb,rb,disp,_=pair(dol,elf,4)
    if target!=C or (a,b)!=(S,R) or count!=6:raise ValueError('transfer edge')
    ss,ds=edges[0][0],edges[1][0]
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    h='#pragma once\n#include "wii_transfer_prefix_v768.h"\nnamespace undercover::wii::v768 {\n'
    h+='inline constexpr TransferPrefixExpectation expected{'+fmt((site,C,C+432,w,roots[C][0]))+','
    h+='SiHelperExpectation{'+fmt((ss,S,S+4*len(roots[S]),roots[C][(ss-C)//4]))+f',26u,{sb}u,{disp}'+'},'
    h+='PostAckLeafExpectation{'+fmt((ds,D,D+4*len(roots[D]),roots[C][(ds-C)//4]))+',1u},0x80619a60u};\n}\n'
    return roots,C,D,S,site,edges,h
def patch_handler(s):
    a='#include "wii_si_handler_time_binding_v742.h"'
    s=replace_exact(s,a,a+'\n#include "wii_transfer_prefix_binding_v768.h"')
    a='    const bool allow=v742::eligible(pc,w,ordinal,kind);'
    return replace_exact(s,a,a+r'''
    if(v768::eligible(pc,w,ordinal,kind)){
        if(allow||!witness.before_authenticated(c,pc,w,held(),4))reject(3);
        v768::start(c,pc,w);return;
    }''')
def patch_ack(s):
    a='    if(v742::route.active())return v742::poll(c);'
    s=replace_exact(s,a,'    if(v768::active())return v768::poll(c);\n'+a)
    a='if(v742::observe(a,c))return;'
    return replace_exact(s,a,'if(v768::observe(a,c))return;'+a)
def patch_leaf(s):
    a='#include "wii_si_handler_time_binding_v742.h"'
    s=replace_exact(s,a,a+'\n#include "wii_transfer_prefix_binding_v768.h"')
    a='    if(v742::route.active()){v742::leaf_before(c,pc,word,ordinal);return;}'
    return replace_exact(s,a,'    if(v768::active()){v768::disable_before(c,pc,word,ordinal);return;}\n'+a)
def patch_body(s,root,words,alias):
    body=exact_function(s,root);out=body
    pcs=set(range(root,root+4*len(words),4)) if alias else reachable(root,words)
    for pc in pcs:
        w=words[(pc-root)//4]
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        if len(pat.findall(out))!=1:raise ValueError('label identity')
        method='save_before' if alias else 'before'
        out=pat.sub(lambda m:m[0]+f'    undercover::wii::v768::{method}(ctx,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
    s=replace_exact(s,body,out);inc='#include "undercover/wii_transfer_prefix_binding_v768.h"'
    return s if inc in s else replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
def install(dol,elf,root,host):
    roots,C,D,S,site,edges,header=expectations(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('private tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    for a in (C,S):
        owners=[(p,exact_function(s,a)) for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('entry coverage')
        p,body=owners[0];words=roots[a]
        pcs=set(range(a,a+4*len(words),4)) if a==S else reachable(a,words)
        expected={pc:(a,words[(pc-a)//4]) for pc in pcs}
        audit_native([body] if a==S else src.values(),outer,expected)
        if a==C:
            for pc,dst in edges:verify_direct(body,pc,dst)
        changes[p]=patch_body(changes.get(p,src[p]),a,words,a==S)
    owners=[exact_function(s,HANDLER) for s in src.values() if owns_root(s,HANDLER)]
    if len(owners)!=1:raise ValueError('handler owner')
    verify_direct(owners[0],site,C)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_transfer_prefix_v768.h','wii_transfer_prefix_binding_v768.h')}
    files[dest/'v768_private_transfer_prefix.h']=header
    edits={dest/n:fn for n,fn in (('wii_si_handler_return_binding_v726.h',patch_handler),('wii_si_ack_binding_v672.h',patch_ack),('wii_si_os_leaf_binding_v709.h',patch_leaf))}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() for p in edits):raise ValueError('destination')
    for p,fn in edits.items():files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print('V768_TRANSFER_ROUTE installed=1 exact_root=1 save_alias=1 disable_reused=1 mmio_guard=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        safe=('transfer edge','private tree','entry coverage','handler owner','destination','label identity','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V768_TRANSFER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
