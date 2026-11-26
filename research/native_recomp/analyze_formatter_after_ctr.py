#!/usr/bin/env python3
"""Conditional symbolic analysis beyond one authenticated local CTR transfer."""
import argparse,struct
from pathlib import Path
from audit_formatter_ctr_target import plan as ctr_audit
from analyze_formatter_nested_path import plan as nested
from analyze_formatter_three_cell_path import control_kind,target_size
from audit_formatter_nested_read import classify_section
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def verify_path(path,sites,prior,prior_sites,edge):
    site,dst=edge
    if len(prior)!=77 or len(prior_sites)!=19 or len(path)<78 or tuple(path[:77])!=tuple(prior) or path[76:78]!=(site,dst):
        raise ValueError('post CTR prefix')
    if tuple(sites[:19])!=tuple(prior_sites):raise ValueError('post CTR accesses')
    if path.count(site)!=1:raise ValueError('post CTR repeated edge')
    return len(path),len(set(path))

def classify_stack(at,n,sp,frame,mem,parent):
    if n not in (1,2,4) or at%n or frame!=48 or sp>=0:
        raise ValueError('post CTR stack geometry')
    end=at+n
    if end<=sp-frame:region='below_frame'
    elif sp-frame<=at<end<=sp:region='child_local'
    elif sp<=at<end<=sp+8:region='caller_linkage'
    elif sp+8<=at<end<=8:region='caller_storage'
    elif at>=8:region='outside_parent'
    else:region='cross_boundary'
    known=sum(a in mem for a in range(at,end))
    inherited=sum(a in parent for a in range(at,end))
    return region,known,inherited

def plan(d,e):
    audit,entry,control,cells=ctr_audit(d,e,details=True)
    if audit!=('local_interior',1,'executable',1,1,1,0,1):raise ValueError('post CTR audit')
    site,w,prior,frame,prior_sites,gp,mem,cr,ctr,lr,saves=control
    if w!=0x4e800420 or frame!=48 or len(prior)!=77 or prior[-1]!=site:raise ValueError('post CTR predecessor')
    edge=(site,ctr);missed=[];controls=[];stack=[]
    try:path,frame,sites,words,_=nested(d,e,candidates=cells,third=True,local_ctr_edge=edge,
            read_refusal=lambda *args:missed.append(args),control_refusal=lambda *args:controls.append(args),stack_refusal=lambda *args:stack.append(args))
    except ValueError:
        if len(stack)==1 and not missed and not controls:
            at,n,path,frame,sites,gp,mem,cr,ctr,lr,saves=stack[0]
            verify_path(tuple(path),sites,prior,prior_sites,edge)
            if any(mem.get(a)!=v for a,v in entry[2].items()):raise ValueError('post CTR parent changed')
            region,known,inherited=classify_stack(at,n,entry[1][1][1],frame,mem,entry[2])
            return 'stack_load',path[:-1],frame,sites,0,n,region,(known,inherited)
        if len(missed)==1 and not controls and not stack:
            at,n,path,frame,sites,*_=missed[0]
            verify_path(tuple(path),sites,prior,prior_sites,edge)
            return 'load',path[:-1],frame,sites,0,n,classify_section(e,at,n),None
        if len(controls)==1 and not missed and not stack:
            pc,w,path,frame,sites,gp,mem,cr,ctr,lr,saves=controls[0]
            verify_path(tuple(path),sites,prior,prior_sites,edge)
            kind,dst=control_kind(w,ctr,lr)
            return kind,path[:-1],frame,sites,target_size(d,e,kind,dst),0,'none',None
        raise
    verify_path(tuple(path),sites,prior,prior_sites,edge)
    return 'call',path,frame,sites,words,0,'none',None

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post CTR stack geometry','post CTR parent changed','post CTR prefix','post CTR accesses','post CTR repeated edge','post CTR audit','post CTR predecessor',
          'formatter local CTR geometry','formatter local CTR identity','formatter local CTR unused','formatter unknown arithmetic',
          'formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance',
          'formatter duplicate stack write','formatter stack write provenance','formatter CR provenance','formatter CTR provenance',
          'formatter escape','formatter region cap','formatter path bound','formatter frame identity','formatter indexed load provenance','formatter other boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            kind,path,frame,sites,words,width,section,stack=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'FORMATTER_AFTER_CTR analyzed=0 reason=opcode category={k} ordinal={n} original_execution=0');return 1
        print('FORMATTER_AFTER_CTR analyzed=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input')+' original_execution=0');return 1
    print(f'FORMATTER_AFTER_CTR analyzed=1 conditional=1 visits={len(path)} unique={len(set(path))} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} boundary={kind} target_words={words} next_width={width} section={section} local_edge_symbolic=1 native_transfer=0 original_execution=0')
    if stack is not None:print(f'FORMATTER_AFTER_CTR_STACK ordinal={len(path)+1} width={width} region={section} known_bytes={stack[0]} inherited_bytes={stack[1]} value_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
