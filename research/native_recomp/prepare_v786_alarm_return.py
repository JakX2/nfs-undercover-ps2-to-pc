#!/usr/bin/env python3
"""Install exact original fifth-call cancellation after transfer suffix."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_head_v782 import plan
from prepare_owner_cancel_v754 import QUEUE
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_scheduler_v722 import reachable
def render(dol,elf):
    roots,C,D,R,T,U,K,edges,leaves=plan(dol,elf)
    n,*_=geometry(dol,elf);site,target,w=edge(HANDLER,exact(dol,elf,HANDLER,n),5)
    if target!=C:raise ValueError('alarm edge')
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    h='#pragma once\n#include "wii_alarm_cancel_return_v782.h"\nnamespace undercover::wii::v786 {\n'
    h+='inline constexpr AlarmCancelExpectation expected{'+fmt((site,w,C,C+280,T,K,*QUEUE))+',{{'
    h+=','.join('AlarmCallEdge{'+fmt((a,b,b+4*len(roots[b]),roots[C][(a-C)//4]))+'}' for a,b in edges)+'}},{{'
    h+=','.join('PostAckLeafExpectation{'+fmt((v[0],v[1],v[1]+4*len(v[5]),v[3]))+f',{i}u'+'}' for i,v in enumerate(leaves,1))+'}}};\n}\n'
    return roots,C,D,R,T,U,K,site,edges,leaves,h
def patch_handler(s):
    a='#include "wii_transfer_prefix_binding_v768.h"'
    s=replace_exact(s,a,a+'\n#include "wii_alarm_return_binding_v786.h"')
    a='    const bool allow=v742::eligible(pc,w,ordinal,kind);'
    return replace_exact(s,a,r'''    if(v786::active()){
        v786::returned(c,pc,w);
        return;
    }
    if(v768::returned_active()&&v786::eligible(pc,w,ordinal,kind)){
        if(!witness.before_authenticated(c,pc,w,held(),5))reject(3);
        v786::start(c,pc,w);return;
    }
'''+a)
def patch_ack(s):
    a='    if(v768::active()&&!v768::returned_active())return v768::poll(c);'
    s=replace_exact(s,a,'    if(v786::active())return v786::poll(c);\n'+a)
    a='if(v768::observe(a,c))return;'
    return replace_exact(s,a,'if(v786::observe(a,c))return;'+a)
def patch_leaf(s):
    a='    if(v768::active()){v768::disable_before(c,pc,word,ordinal);return;}'
    s=replace_exact(s,a,'    if(v786::active()){v786::before(c,pc,word);return;}\n'+a)
    return replace_exact(s,'#include "wii_transfer_prefix_binding_v768.h"','#include "wii_transfer_prefix_binding_v768.h"\n#include "wii_alarm_return_binding_v786.h"')
def patch_nested(s):
    a='    if(v742::route.active()){v742::before(c,pc,word,ordinal,kind);return;}'
    s=replace_exact(s,a,'    if(v786::active()){v786::before(c,pc,word);return;}\n'+a)
    return replace_exact(s,'#include "wii_si_handler_time_binding_v742.h"','#include "wii_si_handler_time_binding_v742.h"\n#include "wii_alarm_return_binding_v786.h"')
def scheduler_hook(s,pc,w,method):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    m=list(pat.finditer(s))
    if len(m)!=1:raise ValueError('alarm label')
    start=m[0].end();end=s.find('    ctx.si_instruction_boundary();\n',start,start+2048)
    if end<0 or '\nloc_' in s[start:end]:raise ValueError('alarm scheduler order')
    end+=len('    ctx.si_instruction_boundary();\n')
    middle=s[start:end]
    if not re.fullmatch(r'(?:    (?:ctx\.[a-z_]+_instruction_boundary\(\)|undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n]+\));\n)+',middle):raise ValueError('alarm intervening code')
    if method=='move':
        hits=list(re.finditer(r'(?m)^    undercover::wii::v693::before\(ctx,[^\n]+\);\n',middle))
        if len(hits)!=1:raise ValueError('alarm nested hook')
        m=hits[0];middle=middle[:m.start()]+middle[m.end():]+m[0]
    else:middle+=f'    undercover::wii::v786::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    return s[:start]+middle+s[end:]
def install(dol,elf,root,host):
    roots,C,D,R,T,U,K,site,edges,leaves,header=render(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('alarm tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    expected={pc:(a,roots[a][(pc-a)//4]) for a in (C,D,R,T,U,K) for pc in reachable(a,roots[a])}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('alarm coverage')
    for a,links in ((HANDLER,[(site,C)]),(C,edges),(T,[(v[0],v[1]) for v in leaves])):
        owners=[exact_function(s,a) for s in src.values() if owns_root(s,a)]
        if len(owners)!=1:raise ValueError('alarm owner')
        for pc,b in links:verify_direct(owners[0],pc,b)
    if any(sum(entry_count(s,a) for s in src.values())!=1 for a in (C,D,R,T,U,K)):raise ValueError('alarm entries')
    changes={}
    for a in (C,T,K):
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1:raise ValueError('alarm owner')
        p=owners[0];s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        for pc in reachable(a,roots[a]):
            out=scheduler_hook(out,pc,roots[a][(pc-a)//4],'move' if a==T else 'insert')
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_alarm_return_binding_v786.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_alarm_cancel_return_v782.h','wii_alarm_cancel_queue_v780.h','wii_alarm_return_binding_v786.h')}
    files[dest/'v786_private_alarm.h']=header
    edits={'wii_si_handler_return_binding_v726.h':patch_handler,'wii_si_ack_binding_v672.h':patch_ack,
           'wii_si_os_leaf_binding_v709.h':patch_leaf,'wii_si_nested_binding_v693.h':patch_nested}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    for n,fn in edits.items():
        p=dest/n
        if p.is_symlink() or not p.is_file():raise ValueError('destination')
        files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V786_ALARM_ROUTE installed=1 native_labels={len(expected)} direct_edges=11 new_roots=2 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        safe=('alarm edge','alarm label','alarm scheduler order','alarm intervening code','alarm nested hook','alarm tree','alarm coverage','alarm owner','alarm entries','destination')
        print('V786_ALARM_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
