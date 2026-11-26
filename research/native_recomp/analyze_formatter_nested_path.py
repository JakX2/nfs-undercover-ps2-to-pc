#!/usr/bin/env python3
"""Read-only symbolic entry probe for the next formatter dependency.

The parent memory and arguments are propagated as symbolic byte cells. The
child cannot fabricate bytes, borrow unproven pointer values or overwrite
already-authenticated parent memory. No original instructions are printed.
"""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_formatter_path import plan as prefix_plan,first_path,const
from prepare_post_stm_sc_formatter_leaf_path import run as leaf_run
from prepare_post_stm_sc_formatter_resume_path import resume
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions,HEADER,SECTION
from make_v1243_stm_fixture import data_at
from make_v624_ipc_geometry import exact_words

def immutable_read(dol,elf,at,n):
    if n not in (1,2,4) or at%n or not 0x80000000<=at<at+n<=0x81800000:
        raise ValueError('nested data range')
    h=HEADER.unpack_from(elf);off,unit,count=h[6],h[11],h[12]
    if h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or unit!=SECTION.size or not 1<=count<10000 or off+count*unit>len(elf):
        raise ValueError('nested data sections')
    hits=[]
    for i in range(count):
        _,kind,flags,base,fo,size,*_=SECTION.unpack_from(elf,off+i*unit)
        if flags&2 and at<base+size and base<at+n:
            if kind!=1 or flags&5 or not base<=at<at+n<=base+size or fo+size>len(elf):
                raise ValueError('nested data not immutable')
            hits.append(elf[fo+at-base:fo+at-base+n])
    if len(hits)!=1:raise ValueError('nested data mapping')
    if data_at(dol,at,n)!=hits[0]:raise ValueError('nested data identity')
    return hits[0]

def nested(root,words,gp,mem,state,readonly,caller_pc,*,read_resolver=None):
    if len(gp)!=32 or gp[1][0]!='stack' or gp[1][1]>=0:raise ValueError('nested caller stack')
    sp=gp[1][1]
    result=first_path(root,words,{i:v for i,v in enumerate(gp) if i!=1},{},readonly,sp,
                      details=True,seed_bytes=mem,initial_cr=state[2],initial_ctr=state[3],
                      entry_lr=const(caller_pc),read_resolver=read_resolver)
    path,frame,sites,_,dst,out_gp,out_mem,_=result
    if any(out_mem.get(at)!=v for at,v in mem.items()):raise ValueError('nested parent memory changed')
    if out_gp[1]!=('stack',sp-frame):raise ValueError('nested stack identity')
    return result

def plan(d,e,*,on_unknown=None,candidate=None):
    path,frame,accesses,saved,leaf_root,gp,mem,ws,state,readonly=prefix_plan(d,e,details=True)
    leaf=leaf_run(leaf_root,exact_words(d,e,leaf_root,12),gp,readonly,mem,initial_cr=state[2],details=True)
    if len(leaf[0])!=8 or len(leaf[1])!=1 or len(leaf[3])!=12:raise ValueError('nested predecessor')
    active,_,sites,_,root,out_gp,out_mem,out_state=resume(path[0],ws,(path,frame,accesses,saved,leaf_root,gp,mem,state),leaf,readonly)
    if len(active)!=10 or sites or direct_bl(ws[(active[-1]-path[0])//4],active[-1])!=root:raise ValueError('nested predecessor')
    sizes=parse_functions(e)
    if sizes.get(root)!=383*4:raise ValueError('nested function geometry')
    # Only pass parent cells at or above the live caller stack pointer.
    parent={at:v for at,v in out_mem.items() if at>=out_gp[1][1]}
    extra=set();candidate_used=False
    def resolve(at,n):
        nonlocal candidate_used
        if candidate is not None and (at,n)==(candidate[0],len(candidate[1])):
            candidate_used=True
            return candidate[1]
        try:value=immutable_read(d,e,at,n)
        except ValueError:
            if on_unknown is not None:on_unknown(at,n)
            raise
        extra.add((at,n))
        if len(extra)>32:raise ValueError('nested data cap')
        return value
    result=nested(root,exact_words(d,e,root,383),out_gp,parent,out_state,readonly,active[-1]+4,read_resolver=resolve)
    if candidate is not None and not candidate_used:raise ValueError('nested candidate unused')
    active,frame,sites,_,dst,*_=result
    n=sizes.get(dst,0)
    if frame!=48 or not 4<=n<=65536 or n%4:raise ValueError('nested next geometry')
    exact_words(d,e,dst,1)
    return active,frame,sites,n//4,len(extra)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','nested caller stack','nested predecessor','nested function geometry','nested parent memory changed','nested stack identity','nested next geometry',
          'nested data range','nested data sections','nested data not immutable','nested data mapping','nested data identity','nested data cap','formatter nested memory geometry','formatter nested state','formatter unknown arithmetic','formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance','formatter stack write provenance','formatter caller linkage provenance','formatter duplicate stack write','formatter update store','formatter indexed store provenance','formatter path bound','formatter frame identity','formatter other boundary','formatter update load','formatter compare','formatter branch','formatter CTR provenance','formatter CR provenance','formatter escape','formatter region cap','formatter boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        path,frame,sites,target_words,extra_reads=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'FORMATTER_NESTED_PATH verified=0 reason=opcode category={k} ordinal={n}');return 1
        print('FORMATTER_NESTED_PATH verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'FORMATTER_NESTED_PATH verified=1 visits={len(path)} unique={len(set(path))} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} target_words={target_words} immutable_reads={extra_reads} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
