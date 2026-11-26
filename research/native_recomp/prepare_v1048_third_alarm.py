#!/usr/bin/env python3
"""Authenticate a third-transfer alarm continuation, reusing existing native roots."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v786_alarm_return import render
from prepare_v789_alarm_suffix import expectations as callback_expectations,patch_private
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from collect_third_alarm_suffix_v1044 import collect_after_alarm
from prepare_owner_scheduler_v722 import reachable
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v850_callback_return import BLOCK_END
from prepare_v1029_third_transfer import replace_body,replace_stage,include_once,SI

# Include already-guarded statements: the preceding transfer installer
# uses third_active(), which becomes false inside the resume label.
LEGACY=re.compile(r'(?m)^    ((?:if\([^\n]*\)[ \t]+)?undercover::wii::(?:v672::before|v680::before|v709::before|v693::before|v726::resume|v786::before|v768::(?:before|save_before|restore_before)|v807::before|v813::before|v850::(?:before|handler_resume|dispatch_resume))\(ctx,[^\n]+;\n)')
def suppress_legacy(block):
    return LEGACY.sub(lambda m:'    if(!undercover::wii::v958::third_active()&&!undercover::wii::v958::third_alarm_active()) { '+m[1].rstrip('\n')+' }\n',block)

def hook(body,pc,w,handoff=False):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('third alarm label')
    i=hits[0].end();end=BLOCK_END.search(body,i);j=end.start() if end else len(body);block=body[i:j]
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or block.index('++ctx.inst_count;')>block.index(SI):
        raise ValueError('third alarm tick')
    base=f'undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
    current='    '+base+'false);\n';guard='    '+base+'true);\n'
    hits=re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block)
    if handoff:
        # Same label is consumed by V1028 and V1047 in one before().
        # Do not add another tick or another observer call.
        conditional='    if(undercover::wii::v958::third_active()) '+current.lstrip()
        allowed=(current,conditional,conditional+'    else '+guard.lstrip())
        # A single logical if/else hook occupies two emitted lines.
        # Require adjacency and exact identity; concatenating disjoint
        # statements alone would accidentally accept an extra side effect.
        observed=''.join(hits)
        if observed not in allowed or block.count(observed)!=1 or block.index(observed)<block.index(SI):
            raise ValueError('third alarm handoff hook')
        return body[:i]+suppress_legacy(block)+body[j:]
    if len(hits)>1:raise ValueError('third alarm duplicate hook')
    if hits:
        old=hits[0]
        if block.index(old)<block.index(SI):raise ValueError('third alarm tick')
        if old==current:pass
        elif old==guard:
            block=replace_stage(block,old,'    if(undercover::wii::v958::third_alarm_active()) '+current.lstrip()+'    else '+guard.lstrip(),'third alarm hook seam')
        elif old=='    if(undercover::wii::v958::callback_active()) '+current.lstrip():
            block=replace_stage(block,old,'    if(undercover::wii::v958::third_alarm_active()||undercover::wii::v958::callback_active()) '+current.lstrip(),'third alarm hook seam')
        else:raise ValueError('third alarm shared hook')
    else:
        k=block.index(SI)+len(SI)
        block=block[:k]+'    if(undercover::wii::v958::third_alarm_active()) '+current.lstrip()+block[k:]
    block=suppress_legacy(block)
    return body[:i]+block+body[j:]

def verify_alarm_identity(actual,base,callback):
    # V789 extends the exact V786 header with the authenticated callback
    # candidate, words and call sites before this installer runs. Rebuild
    # the entire expected composed header, not just the V786 prefix.
    if actual!=patch_private(base,*callback):raise ValueError('third alarm identity')

def install(dol,elf,root,host):
    roots,C,D,R,T,U,K,site,edges,leaves,header=render(dol,elf)
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);transfer,_,_=edge(HANDLER,handler,4)
    rows=collect_after_alarm(HANDLER,handler,handler,set(),transfer+4)
    if rows.get(site)!=(handler[(site-HANDLER)//4],5,1):raise ValueError('third alarm suffix geometry')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    witness=dest/'wii_third_alarm_suffix_v1047.h';prior=dest/'v786_private_alarm.h'
    if dest.is_symlink() or any(x.is_symlink() or not x.is_file() for x in (private,prior)) or witness.exists() or witness.is_symlink():
        raise ValueError('third alarm destination')
    verify_alarm_identity(prior.read_text(),header,callback_expectations(dol,elf))
    old=private.read_text();macro='#define UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1048_PRIVATE_THIRD_ALARM' in old:raise ValueError('third alarm mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('third alarm tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    def owner(addr):
        found=[x for x,s in src.items() if owns_root(s,addr)]
        if len(found)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('third alarm owner')
        return found[0]
    count=0
    for addr in (HANDLER,C,D,R,T,U,K):
        path=owner(addr);source=changes.get(path,src[path]);body=exact_function(source,addr);out=body
        if addr==HANDLER:
            words=handler;pcs=set(rows)|{site+4};verify_direct(body,site,C)
        else:
            words=roots[addr];pcs=set(reachable(addr,words))
            for s,t in (edges if addr==C else [(v[0],v[1]) for v in leaves] if addr==T else []):
                verify_direct(body,s,t)
        expected={pc:(addr,words[(pc-addr)//4]) for pc in pcs}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('third alarm coverage')
        for pc,(_,w) in sorted(expected.items()):
            out=hook(out,pc,w,handoff=pc==transfer+4)
        changes[path]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"');count+=len(expected)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    old=replace_stage(old,macro,macro+'#define UNDERCOVER_V1048_PRIVATE_THIRD_ALARM 1\n','third alarm header seam')
    old+='\n#include "wii_handler_suffix_guard_v868.h"\nnamespace undercover::wii::v958 {\n'
    old+=f'inline constexpr std::array<HandlerSuffixLabel,{len(rows)}> third_alarm_suffix{{{{'+','.join('HandlerSuffixLabel{'+fmt((pc,w))+f',{o}u,{k}u'+'}' for pc,(w,o,k) in sorted(rows.items()))+'}};\n}\n'
    changes[private]=old;changes[witness]=(host/witness.name).read_text()
    for p,s in changes.items():p.write_text(s)
    print(f'V1048_THIRD_ALARM_ROUTE installed=1 native_labels={count} suffix_labels={len(rows)} original_edges=11 token_owner=3 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('third alarm label','third alarm tick','third alarm duplicate hook','third alarm hook seam','third alarm shared hook','third alarm handoff hook','third alarm suffix geometry','third alarm suffix extent','third alarm suffix boundary','third alarm suffix word','third alarm suffix guard','third alarm suffix call','third alarm destination','third alarm identity','third alarm mode','third alarm tree','third alarm owner','third alarm coverage','third alarm header seam','third body seam','third include seam','helper call label','helper direct native call','helper native return edge','native IPC coverage','native IPC label identity','native IPC label body','native IPC dispatch')
        print('V1048_THIRD_ALARM_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
