#!/usr/bin/env python3
"""Extend the authenticated held callback return into the original SI handler."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import HANDLER
from prepare_v868_handler_suffix import derive,render as render_prior
from prepare_v1134_postalarm_return import derive as derive_return,render as render_return,legacy_forms
from prepare_v1097_after_alarm import patch_label,ACTIVE,SI,fmt,suffix_line
from prepare_v1106_postalarm_time import verify_resume
from prepare_v850_callback_return import BLOCK_END
from prepare_v672_si_ack_route import call_census
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v1029_third_transfer import replace_body,include_once

def render(rows,rd,wr,index):
    start,code,table,selector,dest=index
    return ('#pragma once\n#include "wii_handler_suffix_guard_v868.h"\n'
            '#include "wii_handler_index_branch_v911.h"\nnamespace undercover::wii::v1139 {\n'
            +suffix_line('rows',rows)
            +f'inline constexpr uint32_t rd=0x{rd:08x}u,wr=0x{wr:08x}u;\n'
            +'inline constexpr HandlerIndexBranchExpectation index{'+fmt((start,*code[11:14],dest))
            +',{'+fmt(table)+'},'+str(selector)+'u};\n}\n')

def block_at(body,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('held handler label')
    i=hits[0].end();end=BLOCK_END.search(body,i)
    return body[i:end.start() if end else len(body)]

def patch_handler(body,pc,w,o,k,caller):
    block=block_at(body,pc,w)
    args=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    legacy=f'undercover::wii::v672::before({args},{o}u,{k}u);'
    # The exact old handler observer must survive, but never execute while
    # the third route owns this label. Its ordinal and kind are immutable.
    if block.count('v672::before(')!=1 or block.count(legacy)!=1 or block.count(SI)!=1 or block.index(SI)>block.index(legacy):
        raise ValueError('held handler legacy')
    if pc==caller:
        pre=f'    undercover::wii::v958::postalarm_dispatch_resume({args});\n'
        old=f'    undercover::wii::v850::dispatch_resume({args});\n'
        if not any(block.startswith(line+pre+'    ++ctx.inst_count;\n') for line in legacy_forms(old)[2:]) or block.count('postalarm_dispatch_resume(')!=1:
            raise ValueError('held handler resume')
        out=body
    elif 'postalarm_dispatch_resume(' in block or 'v850::handler_resume(' in block or 'v850::dispatch_resume(' in block:
        # The other callback's return is an indirect call frontier,
        # not an admitted continuation. No second dispatch seam is added.
        raise ValueError('held handler resume')
    elif ACTIVE in block:
        out=body
    else:
        out=patch_label(body,pc,w)
    verify_resume(out,pc,w)
    updated=block_at(out,pc,w)
    if updated.count(legacy)!=1 or not any(
        line.startswith('    if(!') and 'v958::' in line and legacy in line
        for line in updated.splitlines()):
        raise ValueError('held handler legacy')
    return out

def install(dol,elf,root,host):
    words,sites,lanes,rd,wr,index=derive(dol,elf)
    _,_,_,_,_,call,R,caller,restore,tail,caller_word,callers=derive_return(dol,elf)
    rows=lanes[0]
    if len(rows)!=52 or len(sites)!=2 or caller!=sites[0]+4 or caller!=index[0] or \
       rows.get(caller)!=(caller_word,0,0) or caller!=callers[0][0]+4:
        raise ValueError('held handler geometry')
    census=call_census(HANDLER,words)
    if any(census.get(pc,(0,0))!=(o,k) for pc,(_,o,k) in rows.items()) or \
       sorted((o,k) for _,o,k in rows.values() if k)!=[(7,1),(8,1),(12,1)]:
        raise ValueError('held handler census')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    prior=dest/'v868_private_handler_suffix.h';ret=dest/'v1132_private_postalarm_return.h'
    result=dest/'v1139_private_postalarm_handler.h'
    witnesses=('wii_handler_suffix_guard_v868.h','wii_handler_index_branch_v911.h',
               'wii_third_alarm_suffix_v1047.h','wii_second_ack_live_v958.h')
    if dest.is_symlink() or result.exists() or result.is_symlink() or any(
        x.is_symlink() or not x.is_file() for x in (private,prior,ret,*[dest/n for n in witnesses])):
        raise ValueError('held handler destination')
    if prior.read_text()!=render_prior(lanes,rd,wr,index) or ret.read_text()!=render_return(call,R,caller,restore,tail,caller_word) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('held handler identity')
    old=private.read_text();macro='#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER' in old:
        raise ValueError('held handler mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('held handler tree')
    src={x:x.read_text() for x in paths};outer=main.read_text()
    owners=[x for x,s in src.items() if owns_root(s,HANDLER)]
    if len(owners)!=1 or sum(entry_count(s,HANDLER) for s in src.values())!=1:
        raise ValueError('held handler owner')
    owner=owners[0];body=exact_function(src[owner],HANDLER)
    if audit_native([body],outer,{pc:(HANDLER,w) for pc,(w,_,_) in rows.items()})!=len(rows):
        raise ValueError('held handler coverage')
    verify_resume_dispatch(outer,HANDLER,caller)
    out=body
    for pc,(w,o,k) in sorted(rows.items()):
        out=patch_handler(out,pc,w,o,k,caller)
    updated=include_once(replace_body(src[owner],body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    new=old.replace(macro,macro+'#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1\n',1)
    # Perform all validation before writing anything to the private tree.
    for path,value in ((owner,updated),(private,new),(result,render(rows,rd,wr,index))):path.write_text(value)
    print('V1141_POSTALARM_HANDLER_ROUTE installed=1 labels=52 resume_reused=1 exact_status=1 original_frontiers=3 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        # Never include raw guest addresses, code, paths, or arbitrary exception text.
        safe={'held handler '+s for s in ('label','legacy','resume','geometry','census','destination','identity','mode','tree','owner','coverage')}
        safe|={'postalarm label','postalarm tick','postalarm hook','postalarm duplicate','postalarm time resume',
               'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
               'resume dispatcher identity'}
        print('V1141_POSTALARM_HANDLER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
