#!/usr/bin/env python3
"""Private opt-in continuation of the verified third alarm into callback prefix."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v1048_third_alarm import LEGACY,verify_alarm_identity
from prepare_v786_alarm_return import render as alarm_render
from prepare_v789_alarm_suffix import expectations
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from collect_third_alarm_suffix_v1044 import collect_after_alarm
from prepare_owner_callback_prefix_v797 import plan
from prepare_v807_callback_prefix import render as callback_render,SI
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v625_ipc_client import audit_native
from prepare_v850_callback_return import BLOCK_END
from prepare_v1029_third_transfer import replace_body,include_once

ACTIVE='undercover::wii::v958::third_postalarm_active()'
OLD_ACTIVE='undercover::wii::v958::third_alarm_active()'
OLD_THIRD='undercover::wii::v958::third_active()'
CALLBACK='undercover::wii::v958::callback_active()'
OLD_SUPPRESS=f'    if(!{OLD_THIRD}&&!{OLD_ACTIVE}) {{ '
NEW_SUPPRESS=f'    if(!{OLD_THIRD}&&!{OLD_ACTIVE}&&!{ACTIVE}) {{ '

def patch_label(body,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('postalarm label')
    i=hits[0].end();end=BLOCK_END.search(body,i);j=end.start() if end else len(body);block=body[i:j]
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or block.index('++ctx.inst_count;')>block.index(SI):
        raise ValueError('postalarm tick')
    if ACTIVE in block:raise ValueError('postalarm duplicate')
    base=f'undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
    current='    '+base+'false);\n';guard='    '+base+'true);\n'
    cond=lambda name:'    if('+name+') '+current.lstrip()
    hits=re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block)
    observed=''.join(hits)
    if hits:
        if block.count(observed)!=1 or block.index(observed)<block.index(SI):raise ValueError('postalarm hook')
        allowed={current:current,guard:cond(ACTIVE)+'    else '+guard.lstrip()}
        for prior in (CALLBACK,OLD_ACTIVE,OLD_ACTIVE+'||'+CALLBACK):
            allowed[cond(prior)]=cond(prior+'||'+ACTIVE)
            if prior==OLD_ACTIVE:allowed[cond(prior)+'    else '+guard.lstrip()]=cond(prior+'||'+ACTIVE)+'    else '+guard.lstrip()
        if observed not in allowed:raise ValueError('postalarm hook')
        block=block.replace(observed,allowed[observed],1)
    else:
        k=block.index(SI)+len(SI);block=block[:k]+cond(ACTIVE)+block[k:]
    # A V1048 return label changes owner during the observer invocation.
    # Extend its exact old legacy wrapper rather than introducing another
    # live call. Also suppress existing conditional legacy statements.
    block=block.replace(OLD_SUPPRESS,NEW_SUPPRESS)
    block=LEGACY.sub(lambda m:f'    if(!{ACTIVE}) {{ '+m[1].rstrip('\n')+' }\n',block)
    return body[:i]+block+body[j:]

def fmt(xs):return ','.join(f'0x{x:08x}u' for x in xs)
def suffix_line(name,rows):
    return f'inline constexpr std::array<HandlerSuffixLabel,{len(rows)}> {name}{{{{'+','.join('HandlerSuffixLabel{'+fmt((pc,w))+f',{o}u,{k}u'+'}' for pc,(w,o,k) in sorted(rows.items()))+'}};\n'

def install(dol,elf,root,host):
    *_,alarm_site,edges,leaves,base=alarm_render(dol,elf)
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    transfer,_,_=edge(HANDLER,handler,4)
    prior_rows=collect_after_alarm(HANDLER,handler,handler,set(),transfer+4)
    rows=collect_after_alarm(HANDLER,handler,handler,set(),alarm_site+4)
    roots,C,S,save_site,_,_=plan(dol,elf);candidate,words,sites=expectations(dol,elf)
    prefix=roots[C][:-1];save=roots[S]
    if C!=candidate or tuple(prefix)!=words[:len(prefix)] or len(prefix)!=6 or len(save)!=7 or len(sites)!=2 or \
       rows.get(sites[0])!=(0x4e800421,6,2) or prior_rows.get(alarm_site)!=(handler[(alarm_site-HANDLER)//4],5,1):
        raise ValueError('postalarm geometry')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    witness=dest/'wii_third_alarm_suffix_v1047.h';alarm=dest/'v786_private_alarm.h'
    callback=dest/'v807_private_callback_prefix.h';prefix_header=dest/'wii_callback_prefix_v800.h'
    if dest.is_symlink() or any(x.is_symlink() or not x.is_file() for x in (private,witness,alarm,callback,prefix_header)):
        raise ValueError('postalarm destination')
    verify_alarm_identity(alarm.read_text(),base,(candidate,words,sites))
    if callback.read_text()!=callback_render(C,S,prefix,save) or any(
        x.read_text()!=(host/x.name).read_text() for x in (witness,prefix_header)):
        raise ValueError('postalarm identity')
    old=private.read_text();macro='#define UNDERCOVER_V1048_PRIVATE_THIRD_ALARM 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1095_PRIVATE_AFTER_ALARM' in old or \
       old.count(suffix_line('third_alarm_suffix',prior_rows))!=1:
        raise ValueError('postalarm mode')
    if len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm callback identity')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('postalarm tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    def owner(addr):
        found=[x for x,s in src.items() if owns_root(s,addr)]
        if len(found)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('postalarm owner')
        return found[0]
    count=0
    for addr,expected_words in ((HANDLER,handler),(C,prefix),(S,save)):
        path=owner(addr);source=changes.get(path,src[path]);body=exact_function(source,addr);out=body
        if addr==HANDLER:
            pcs=set(rows);verify_indirect(body,sites[0])
        else:
            pcs={addr+4*i for i in range(len(expected_words))}
            if addr==C:verify_direct(body,save_site,S)
        expected={pc:(addr,expected_words[(pc-addr)//4]) for pc in pcs}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('postalarm coverage')
        for pc,(_,w) in sorted(expected.items()):out=patch_label(out,pc,w)
        changes[path]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
        count+=len(expected)
    old=old.replace(macro,macro+'#define UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1\n',1)
    old+='\nnamespace undercover::wii::v958 {\n'+suffix_line('third_postalarm_suffix',rows)
    old+=f'inline constexpr uint32_t third_postalarm_save_root=0x{S:08x}u;\n'
    for name,ws in (('third_postalarm_prefix',prefix),('third_postalarm_save',save),('third_postalarm_words',words),('third_postalarm_sites',sites)):
        old+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n'
    changes[private]=old+'}\n'
    for path,value in changes.items():path.write_text(value)
    print(f'V1097_AFTER_ALARM_ROUTE installed=1 native_labels={count} suffix_labels={len(rows)} callback_words={len(words)} token_owner=3 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        # No raw game words, paths, registers, or private source fragments.
        safe=('postalarm label','postalarm tick','postalarm duplicate','postalarm hook','postalarm geometry','postalarm destination','postalarm identity','postalarm mode','postalarm callback identity','postalarm tree','postalarm owner','postalarm coverage')
        print('V1097_AFTER_ALARM_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
