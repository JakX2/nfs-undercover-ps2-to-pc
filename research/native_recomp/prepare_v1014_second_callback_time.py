#!/usr/bin/env python3
"""Privately reuse the first callback's authenticated time route for the second."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_callback_time_v802 import plan
from prepare_v813_callback_time import render
from prepare_owner_scheduler_v722 import reachable
from prepare_v667_si_dispatch import exact
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v850_callback_return import BLOCK_END
from prepare_v807_callback_prefix import SI

def hook(body,pc,w,existing=False):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('second callback time label')
    i=hits[0].end();end=BLOCK_END.search(body,i);j=end.start() if end else len(body)
    block=body[i:j]
    current=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n'
    legacy=f'    undercover::wii::v813::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or block.index('++ctx.inst_count;')>block.index(SI):
        raise ValueError('second callback time tick')
    if existing:
        if block.count(current)!=1 or block.count('v958::before(')!=1 or block.index(current)<block.index(SI):
            raise ValueError('second callback time shared hook')
        return body
    if block.count(legacy)!=1 or block.index(legacy)<block.index(SI) or 'v958::before(' in block:
        raise ValueError('second callback time old hook')
    k=block.index(SI)+len(SI)
    block=block[:k]+'    if(undercover::wii::v958::callback_active()) '+current.lstrip()+block[k:]
    return body[:i]+block+body[j:]

def install(dol,elf,root,host):
    q,T,D,U,R,ts,leaves=plan(dol,elf);roots,C,S,site,_,_=q
    resume=site+4;continuation=roots[C][(resume-C)//4:-1]
    original=exact(dol,elf,C,172)
    if tuple(continuation)!=original[(resume-C)//4:(ts-C)//4+2] or len(roots[T])!=25:
        raise ValueError('second callback time geometry')
    dest=root/'nWiiRuntime/include/undercover'
    private=dest/'v958_private_second_ack.h';prior=dest/'v813_private_callback_time.h';witness=dest/'wii_callback_time_v810.h'
    if dest.is_symlink() or any(x.is_symlink() or not x.is_file() for x in (private,prior,witness)):
        raise ValueError('second callback time destination')
    text=private.read_text()
    if prior.read_text()!=render(C,ts,continuation,T,roots[T],leaves) or witness.read_text()!=(host/witness.name).read_text():
        raise ValueError('second callback time identity')
    if '#define UNDERCOVER_V1009_PRIVATE_CALLBACK 1\n' not in text or 'UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME' in text:
        raise ValueError('second callback time mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('second callback time tree')
    src={x:x.read_text() for x in paths};outer=main.read_text()
    def owner(addr):
        found=[x for x,s in src.items() if owns_root(s,addr)]
        if len(found)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('second callback time owner')
        return found[0]
    cp=owner(C);body=exact_function(src[cp],C);verify_direct(body,ts,T)
    pcs={pc for pc in reachable(C,roots[C]) if resume<=pc<=ts+4}
    if len(pcs)!=13 or resume not in pcs or ts+4 not in pcs:raise ValueError('second callback time geometry')
    expected={pc:(C,original[(pc-C)//4]) for pc in pcs}
    # The shared handler time installer has already installed v958 hooks
    # on all 45 native labels. Do not add a duplicate SI/device tick.
    for addr in (T,D,U,R):
        p=owner(addr);b=exact_function(src[p],addr)
        if addr==T:
            for row in leaves:verify_direct(b,row[0],row[1])
        for pc in reachable(addr,roots[addr]):
            w=roots[addr][(pc-addr)//4]
            if pc in expected:raise ValueError('second callback time overlap')
            expected[pc]=(addr,w);hook(b,pc,w,True)
    if len(expected)-len(pcs)!=45 or audit_native(src.values(),outer,expected)!=len(expected):
        raise ValueError('second callback time geometry')
    # The resume hook was installed by V1009 and may be conditional.
    out=body
    for pc in sorted(pcs-{resume}):out=hook(out,pc,expected[pc][1])
    s=replace_exact(src[cp],body,out)
    inc='#include "undercover/wii_second_ack_live_v958.h"'
    if s.count(inc)!=1:raise ValueError('second callback time prefix include')
    text=replace_exact(text,'#define UNDERCOVER_V1009_PRIVATE_CALLBACK 1\n',
                       '#define UNDERCOVER_V1009_PRIVATE_CALLBACK 1\n#define UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME 1\n')
    cp.write_text(s);private.write_text(text)
    print('V1014_CALLBACK_TIME_ROUTE installed=1 callback_labels=13 shared_labels=45 direct_edges=4 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('second callback time label','second callback time tick','second callback time shared hook','second callback time old hook','second callback time geometry','second callback time destination','second callback time identity','second callback time mode','second callback time tree','second callback time owner','second callback time overlap','second callback time prefix include','source seam')
        print('V1014_CALLBACK_TIME_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
