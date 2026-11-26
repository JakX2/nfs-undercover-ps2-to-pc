#!/usr/bin/env python3
"""Install only the authenticated held third callback restore and caller resume."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_callback_after_setter_v842 import plan
from prepare_v667_si_dispatch import exact
from prepare_v668_si_ack import HANDLER,geometry
from prepare_v789_alarm_suffix import expectations
from prepare_v850_callback_return import render as render_old,BLOCK_END
from prepare_v1124_postalarm_suffix import render as render_suffix
from prepare_v1097_after_alarm import patch_label,fmt,ACTIVE,SI,OLD_SUPPRESS,NEW_SUPPRESS,OLD_ACTIVE,OLD_THIRD
from prepare_v1106_postalarm_time import verify_resume
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v1029_third_transfer import replace_body,include_once

def render(call,R,caller,restore,tail,w):
    return ('#pragma once\n#include "wii_callback_return_v846.h"\nnamespace undercover::wii::v1132 {\n'
            'inline constexpr CallbackReturnExpectation expected{'+fmt((call,R,caller))+',{'+fmt(restore)+'},{'
            +fmt(tail)+'},'+fmt((w,))+'};\n}\n')

def legacy_forms(hook):
    # Exactly the wrappers already emitted by V1048/V1097, not arbitrary
    # substring matches or arbitrary executable statements.
    stmt=hook.strip()
    return ('    '+stmt+'\n',OLD_SUPPRESS+stmt+' }\n',
            NEW_SUPPRESS+stmt+' }\n',f'    if(!{ACTIVE}) {{ {stmt} }}\n')

def select_legacy(block,hook,kind):
    forms=legacy_forms(hook)
    lines=[line for line in block.splitlines(keepends=True) if kind+'(' in line]
    if len(lines)!=1 or lines[0] not in forms:
        raise ValueError('postalarm return legacy')
    return lines[0]

def patch_return_label(body,pc,w,dispatch=False):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('postalarm return label')
    i=hits[0].end();end=BLOCK_END.search(body,i);j=end.start() if end else len(body)
    block=body[i:j]
    tick='    ++ctx.inst_count;\n'
    args=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    old_dispatch='    undercover::wii::v850::dispatch_resume('+args+');\n'
    role='handler_resume' if dispatch else 'before'
    legacy='    undercover::wii::v850::'+role+'('+args+');\n'
    old=select_legacy(block,legacy,'v850::'+role)
    if block.count(tick)!=1 or block.count(SI)!=1 or not block.index(tick)<block.index(SI)<block.index(old):
        raise ValueError('postalarm return legacy')
    pre=None
    if dispatch:
        pre=select_legacy(block,old_dispatch,'v850::dispatch_resume')
        if not block.startswith(pre+tick):
            raise ValueError('postalarm return dispatch hook')
    elif 'v850::dispatch_resume(' in block:raise ValueError('postalarm return dispatch hook')
    # An earlier bounded route can reach the same emitted label through an
    # alternate branch. Verify and reuse its existing observer, not a new
    # instruction tick. Otherwise extend the exact older legacy wrappers.
    already=ACTIVE in block
    if already:
        verify_resume(body,pc,w)
        if old not in legacy_forms(legacy)[2:] or (pre is not None and pre not in legacy_forms(old_dispatch)[2:]):
            raise ValueError('postalarm return legacy')
        out=body
    else:out=patch_label(body,pc,w)
    if dispatch:
        m=pat.search(out);assert m is not None
        stop=BLOCK_END.search(out,m.end());updated=out[m.end():stop.start() if stop else len(out)]
        guarded=select_legacy(updated,old_dispatch,'v850::dispatch_resume')
        if guarded not in legacy_forms(old_dispatch)[2:] or not updated.startswith(guarded+tick):
            raise ValueError('postalarm return dispatch hook')
        new='    undercover::wii::v958::postalarm_dispatch_resume('+args+');\n'
        out=out.replace(guarded,guarded+new,1)
    verify_resume(out,pc,w)
    return out

def derive(dol,elf):
    joined,C,resume,seen,stops=plan(dol,elf,True)
    roots=joined[1][0][0]
    original=exact(dol,elf,C,172);candidate,words,sites=expectations(dol,elf)
    if C!=candidate or tuple(original)!=tuple(words) or len(seen)!=21 or len(set(seen))!=21 or len(sites)!=2 or \
       sorted((i,k) for i,k,_ in stops.values())!=[(4,2),(13,1)] or not set(stops).issubset(seen):
        raise ValueError('postalarm return geometry')
    call,R=next((pc,dst) for pc,(i,k,dst) in stops.items() if i==13)
    restore=tuple(roots[R]);tail=tuple(original[(call+4-C)//4:(call+20-C)//4])
    if len(restore)!=7 or tuple(exact(dol,elf,R,7))!=restore or len(tail)!=4 or \
       restore[-1]!=0x4e800020 or tail[-1]!=0x4e800020 or set(seen)&{call+4+4*i for i in range(4)}:
        raise ValueError('postalarm return geometry')
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    if any(not HANDLER<=pc<HANDLER+4*(n-1) or pc&3 for pc in sites):raise ValueError('postalarm return caller')
    callers=[(pc,handler[(pc-HANDLER)//4],i,handler[(pc+4-HANDLER)//4]) for pc,i in zip(sites,(6,11))]
    if any(w!=0x4e800421 for _,w,_,_ in callers):raise ValueError('postalarm return caller')
    site,word,ordinal,caller_word=callers[0];caller=site+4
    suffix_words={pc:original[(pc-C)//4] for pc in seen}
    return C,resume,suffix_words,stops,words,call,R,caller,restore,tail,caller_word,callers

def install(dol,elf,root,host):
    C,resume,suffix_words,stops,words,call,R,caller,restore,tail,caller_word,callers=derive(dol,elf)
    site,word,_,_=callers[0]
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    suffix_header=dest/'v1123_private_postalarm_suffix.h';prior=dest/'v850_private_callback_return.h'
    result=dest/'v1132_private_postalarm_return.h'
    witnesses=('wii_third_alarm_suffix_v1047.h','wii_callback_return_v846.h')
    if dest.is_symlink() or result.exists() or result.is_symlink() or \
       any(p.is_symlink() or not p.is_file() for p in (private,suffix_header,prior,*[dest/n for n in witnesses])):
        raise ValueError('postalarm return destination')
    if suffix_header.read_text()!=render_suffix(C,resume,suffix_words,stops) or \
       prior.read_text()!=render_old(C,resume,suffix_words,stops,R,restore,tail,callers) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('postalarm return identity')
    old=private.read_text();macro='#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1\n'
    newmacro='#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1\n'
    row=f'inline constexpr std::array<uint32_t,172> third_postalarm_words{{'+fmt(words)+'};\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN' in old or old.count(row)!=1 or \
       len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm return metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('postalarm return tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('postalarm return owner')
        return hits[0]
    for a,rows in ((C,{call+4+4*i:w for i,w in enumerate(tail)}),
                   (R,{R+4*i:w for i,w in enumerate(restore)}),(HANDLER,{caller:caller_word})):
        p=owner(a);source=changes.get(p,src[p]);body=exact_function(source,a);out=body
        expected={pc:(a,w) for pc,w in rows.items()}
        if a==C:
            verify_direct(body,call,R);verify_resume(body,call,words[(call-C)//4]);expected[call]=(a,words[(call-C)//4])
        if a==HANDLER:
            verify_indirect(body,site);verify_resume_dispatch(outer,HANDLER,caller);expected[site]=(a,word)
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('postalarm return coverage')
        for pc,w in sorted(rows.items()):
            try:out=patch_return_label(out,pc,w,a==HANDLER)
            except ValueError:
                # A bounded role/index and hook shape census, no proprietary
                # code, addresses, registers or generated source.
                role='handler' if a==HANDLER else 'restore' if a==R else 'tail'
                block=body
                pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
                match=pat.search(body)
                if match:
                    stop=BLOCK_END.search(body,match.end());block=body[match.end():stop.start() if stop else len(body)]
                print(f'V1160_RETURN_HOOK_REFUSAL role={role} index={(pc-min(rows))//4} tick={int(block.count("++ctx.inst_count;")==1)} si={int(block.count(SI)==1)} old={int("v850::" in block)} prior={int(ACTIVE in block)}')
                raise
        changes[p]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    changes[private]=old.replace(macro,macro+newmacro,1)
    changes[result]=render(call,R,caller,restore,tail,caller_word)
    for p,s in changes.items():p.write_text(s)
    print('V1134_POSTALARM_RETURN_ROUTE installed=1 restore_labels=7 tail_labels=4 handler_resume=1 outer_tick=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration,TypeError) as e:
        safe=('postalarm return geometry','postalarm return caller','postalarm return destination','postalarm return identity',
              'postalarm return metadata','postalarm return tree','postalarm return owner','postalarm return coverage',
              'postalarm return label','postalarm return legacy','postalarm return dispatch hook','postalarm label',
              'postalarm tick','postalarm duplicate','postalarm hook','postalarm time resume','resume dispatcher identity',
              'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
              'helper call label','helper direct native call','helper native return edge','indirect label','indirect LR','indirect dispatch','indirect fallback')
        print('V1134_POSTALARM_RETURN_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
