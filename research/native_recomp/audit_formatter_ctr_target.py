#!/usr/bin/env python3
"""Authenticate the conditional CTR destination without following the transfer."""
import argparse,struct
from pathlib import Path
from analyze_formatter_three_cell_path import plan as three_cell
from audit_formatter_nested_read import classify_section
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def geometry(root,dst,sizes):
    if dst is None:return 'unknown',0
    if not isinstance(dst,int) or dst&3:return 'unaligned',0
    if not 0x80000000<=dst<0x81800000:return 'outside_mem1',0
    size=sizes.get(root,0)
    if size!=383*4:raise ValueError('ctr owner size')
    if root<=dst<root+size:
        return ('local_entry' if dst==root else 'local_interior'),1
    owners=[(a,n) for a,n in sizes.items() if a<=dst<dst+4<=a+n]
    if len(owners)>1:return 'ambiguous',len(owners)
    if len(owners)==1:return ('function_entry' if owners[0][0]==dst else 'function_interior'),1
    return 'no_symbol',0

def plan(d,e):
    kind,path,frame,sites,words,width,section,entry,control,cells=three_cell(d,e,details=True)
    if (kind,len(path),len(set(path)),frame,len(sites))!=('ctr_tail',76,76,48,19):
        raise ValueError('ctr predecessor')
    root,initial,parent,caller,readonly=entry
    pc,w,full,_,_,gp,mem,cr,ctr,lr,saves=control
    if w!=0x4e800420 or full[-1]!=pc or tuple(path)!=tuple(full[:-1]):
        raise ValueError('ctr control identity')
    sizes=parse_functions(e)
    target,owners=geometry(root,ctr,sizes)
    mapped='none';word_match=0
    if target not in ('unknown','unaligned','outside_mem1'):
        mapped=classify_section(e,ctr,4)
        if mapped=='executable':
            exact_words(d,e,ctr,1)
            word_match=1
    last=exact_words(d,e,path[-1],1)[0]
    source=(last>>21)&31
    mtctr=int(last>>26==31 and (last>>1)&1023==467 and (((last>>16)&31)|(((last>>11)&31)<<5))==9)
    agrees=int(mtctr and ctr is not None and gp[source]==('const',ctr))
    return target,owners,mapped,word_match,mtctr,agrees,int(ctr is not None and ctr in path),int(gp[1][0]=='stack' and gp[1][1]==initial[1][1]-48)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','ctr owner size','ctr predecessor','ctr control identity'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            target,owners,mapped,word,mtctr,agrees,visited,frame=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CTR_TARGET verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CTR_TARGET verified=1 target={target} owners={owners} section={mapped} word_agreement={word} preceding_mtctr={mtctr} source_agrees={agrees} target_previously_visited={visited} frame_held={frame} conditional=1 transfer_executed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
