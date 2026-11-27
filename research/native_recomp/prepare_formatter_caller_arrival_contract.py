#!/usr/bin/env python3
"""Private guarded caller-label arrival after the original nested return.

Replace exactly the synthetic caller guard with one authenticated original
load label and retain a guard after it. This does not execute the load.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_return_contract import plan as return_plan
from prepare_formatter_release_contract import plan as release_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_partial_copy import boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL,direct_bl
from private_plan_cache import plan_cache_scope

def extend(release,return_info,words):
    blocks,fields,rows,access,slots,known=release
    child,link,ret,retword,frame,addr,width=fields
    owner,caller,guard,family,kind=return_info
    if (len(rows),len(access),frame,addr,width,retword)!=(97,32,48,0,0,0x4e800020):
        raise ValueError('caller arrival predecessor')
    if owner==child or caller!=link or guard!=GUARD or family!='load' or caller<=owner or caller&3 or owner&3:
        raise ValueError('caller arrival identity')
    i=(caller-owner)//4
    body=blocks.get(owner,())
    if not 1<=i<len(body) or i+1>=len(words) or body[i]!=GUARD or words[i]==GUARD or boundary_shape(words[i])!='load':
        raise ValueError('caller arrival guard')
    call=words[i-1]
    if call>>26!=18 or call&3!=1 or direct_bl(call,caller-4)!=child or body[i-1]!=call:
        raise ValueError('caller arrival call')
    if i+1<len(body) and body[i+1]!=GUARD:
        raise ValueError('caller arrival overlap')
    if any(w!=GUARD and (j>=len(words) or words[j]!=w) for j,w in enumerate(body)):
        raise ValueError('caller arrival history')
    new=list(body)+[GUARD]*max(0,i+2-len(body));new[i]=words[i]
    expanded={**blocks,owner:tuple(new)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return expanded,(owner,caller,words[i],call)

def plan(d,e,*,release=None,previous=None,return_info=None):
    if previous is None:previous=continuation_plan(d,e)
    if release is None:release=release_plan(d,e)
    if return_info is None:return_info=return_plan(d,e,release=release,previous=previous)
    size=parse_functions(e).get(return_info[0],0)
    if not 4<=size<=65536 or size%4:raise ValueError('caller arrival extent')
    return extend(release,return_info,exact_words(d,e,return_info[0],size//4))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller arrival predecessor','caller arrival identity','caller arrival guard','caller arrival call','caller arrival overlap','caller arrival history','caller arrival extent'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():blocks,info=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_ARRIVAL_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print('FORMATTER_CALLER_ARRIVAL_CONTRACT verified=1 nested_visits=98 caller_labels=1 original_call=1 same_owner=1 next_guard=1 caller_body_executed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
