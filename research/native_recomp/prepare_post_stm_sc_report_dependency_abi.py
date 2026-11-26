#!/usr/bin/env python3
"""Trace only the actual call arguments into the first diagnostic leaf."""
import argparse,struct
from pathlib import Path
from private_plan_cache import memoized_plan
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_post_stm_sc_report_helper_prefix import prefix
from prepare_post_stm_sc_report_abi import model
from prepare_post_stm_sc_report import REPORT
from prepare_post_stm_sc_report_dependency import census
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from prepare_post_stm_sc_version import plan as version_plan,elf_data
from prepare_post_stm_sc_state import overlap,store_kind
from prepare_stm_event_return_geometry import object_at,plan as event_plan
from prepare_stm_final_return import plan as final_plan
from prepare_ipc_profile_geometry import layout
from prepare_ipc_dispatch_geometry import credit_object
from prepare_v1414_ipc_ring import ring_object
from prepare_post_stm_sc_disable import decision
from make_v1243_stm_fixture import data_at,seed_data
from prepare_v629_stm_open import geometry
from prepare_v1385_async_ioctl_geometry import plan as ioctl_plan
from prepare_v1337_open_completion import plan as completion
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def compose(value,report_regs,report_frame):
    kind,n=value
    if kind=='reg':return report_regs[n]
    if kind=='stack':return ('stack',n-report_frame)
    if kind=='expr':
        v,imm=n;k,x=compose(v,report_regs,report_frame)
        if k in ('stack','const'):return (k,x+imm if k=='stack' else (x+imm)&0xffffffff)
        return ('computed',0)
    return value

def classify(words):
    # This is an opcode census, not a reconstruction of private instructions.
    # Return only counts of admissible public PPC operation forms.
    counts={}
    for w in words:
        op=w>>26;xo=(w>>1)&1023
        if w==0x4e800020:k='return'
        elif op==16:k='bc_cr' if (w>>21)&4 else 'bc_ctr'
        elif op==18:k='b'
        elif op in (10,11):k='cmp_imm'
        elif op in (14,15):k='add_imm'
        elif op in (20,21,23):k='rotate'
        elif op in (24,25,26,27,28,29):k='logic_imm'
        elif op in (32,34,40,42):k='load_'+str({32:4,34:1,40:2,42:2}[op])
        elif op in (36,38,44):k='store_'+str({36:4,38:1,44:2}[op])
        elif op==31 and xo in (0,32):k='cmp_reg'
        elif op==31 and xo in (444,28,316):k='logic_reg'
        elif op==31 and xo in (266,40):k='add_sub_reg'
        elif op==31 and xo in (24,536):k='shift_reg'
        else:k='other'
        counts[k]=counts.get(k,0)+1
    return counts

def arguments(report_regs,report_frame,helper_regs):
    return tuple(compose(helper_regs[r],report_regs,report_frame) for r in range(3,11))

def memory_sites(root,ws,base):
    out=[]
    for i,w in enumerate(ws):
        op=w>>26;ra=(w>>16)&31
        if op not in (32,34,40,42,36,38,44):continue
        if ra!=3:raise ValueError('dependency memory base')
        width={32:4,34:1,40:2,42:2,36:4,38:1,44:2}[op]
        addr=(base+((w&0xffff)^0x8000)-0x8000)&0xffffffff
        if addr%width:raise ValueError('dependency memory alignment')
        out.append((root+4*i,addr,width,op in (36,38,44)))
    if len(out)!=3 or sum(x[3] for x in out)!=2:raise ValueError('dependency memory count')
    return tuple(out)

@memoized_plan
def plan(d,e):
    prior=helper_plan(d,e);helper,_,root,_,_=prior[3]
    sizes=parse_functions(e)
    report=exact_words(d,e,REPORT,sizes[REPORT]//4)
    report_regs,report_slots=model(REPORT,report,details=True)
    _,_,ranges,fields=version_plan(d,e)
    initial_regs={2:EXPECTED_GPRS[2],13:EXPECTED_GPRS[13],3:fields[5],4:fields[4]}
    report_regs=tuple(('const',initial_regs[v[1]]) if v[0]=='reg' and v[1] in initial_regs else v for v in report_regs)
    helper_regs,_,_,_=prefix(helper,exact_words(d,e,helper,30),details=True)
    args=arguments(report_regs,128,helper_regs)
    ws=exact_words(d,e,root,33)
    edges,rows,returns,_,_,_,back,_=census(root,ws)
    if edges or back or len(returns)!=2:raise ValueError('dependency leaf')
    counts=classify(ws)
    if counts.get('other',0) or counts.get('bc_ctr',0):raise ValueError('dependency instruction class')
    if args[0][0]!='const' or args[1][0]!='const':
        raise ValueError('dependency arguments '+args[0][0]+' '+args[1][0])
    addr=args[0][1]
    sites=memory_sites(root,ws,addr)
    obj=object_at(d,e,addr,1)
    if obj[1]>4096 or any(object_at(d,e,a,n)!=obj for _,a,n,_ in sites):
        raise ValueError('dependency object identity')
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3],final_plan(d,e)[1],
               *(x[3] for x in decision(d,e)[2]),*((a,len(blob)) for a,blob in ranges)]
    if any(overlap(*obj,*p) for p in protected):raise ValueError('dependency object overlap')
    blob=data_at(d,*obj)
    kind=1
    if blob is None:
        bss,size=struct.unpack_from('>II',d,0xd8)
        if not bss<=obj[0]<obj[0]+obj[1]<=bss+size:raise ValueError('dependency initial mapping')
        blob=bytes(obj[1]);kind=2
    elif elf_data(e,*obj)!=blob:raise ValueError('dependency data identity')
    _,stm,_,_,paths,_=geometry(d,e)
    roots=ioctl_plan(d,e)[0];shared=completion(d,e)[0]
    seeded=seed_data(d,tuple(stm)+tuple(w for words in roots.values() for w in words),paths)
    if any(obj[0]+i in seeded and seeded[obj[0]+i]!=v for i,v in enumerate(blob)):
        raise ValueError('dependency seed identity')
    for w in tuple(stm)+tuple(w for words in (*roots.values(),*shared.values()) for w in words):
        n=store_kind(w);ra=(w>>16)&31
        if n>0 and ra in (2,13):
            at=(EXPECTED_GPRS[ra]+((w&0xffff)^0x8000)-0x8000)&0xffffffff
            if overlap(*obj,at,n):raise ValueError('dependency earlier direct writer')
    # Preserve the actual helper continuation as a guarded original word.
    caller=helper+13*4;caller_word=exact_words(d,e,caller,1)[0]
    return counts,args,obj,sites,kind,blob,(root,caller,caller_word),ws

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','dependency leaf','dependency memory base','dependency instruction class','dependency memory alignment','dependency memory count','dependency object identity','dependency object overlap','dependency initial mapping','dependency data identity','dependency seed identity','dependency earlier direct writer','STM object identity','STM object range'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        counts,args,obj,sites,kind,blob,fields,ws=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('dependency arguments '):
            _,_,x,y=reason.split()
            if x in ('reg','stack','const','computed','lr','expr') and y in ('reg','stack','const','computed','lr','expr'):
                print(f'POST_STM_SC_REPORT_DEPENDENCY_ABI verified=0 reason=argument_provenance first={x} second={y}');return 1
        print('POST_STM_SC_REPORT_DEPENDENCY_ABI verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_DEPENDENCY_ABI verified=1 global_object=1 constant_selector=1 object_bytes={obj[1]} initial_kind={kind} original_data_identity=1 memory_sites={len(sites)} original_execution=0')
    print('POST_STM_SC_REPORT_DEPENDENCY_OPS '+' '.join(f'{k}={v}' for k,v in sorted(counts.items())))
    return 0
if __name__=='__main__':raise SystemExit(main())
