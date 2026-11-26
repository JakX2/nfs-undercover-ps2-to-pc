#!/usr/bin/env python3
"""Build a bounded continuation contract in memory. Emit only safe counts."""
import argparse,struct
from pathlib import Path
from guarded_continuation import extend_guarded,saved_mask
from prepare_post_stm_sc_formatter_leaf_fixture import plan as fixture_plan
from prepare_post_stm_sc_report_formatter_path import plan as prefix_plan
from prepare_post_stm_sc_formatter_leaf_path import run as leaf_run
from prepare_post_stm_sc_formatter_resume_path import resume
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def contract(prior,root,words,result,target_word):
    active,frame,sites,saves,dst,gp,mem,state=result
    if len(active)!=10 or sites or frame!=704 or saves!=16 or root!=prior[0][3][0]:
        raise ValueError('continuation contract')
    start=prior[3][1]
    if active[0]!=start or any(pc<root or pc>=root+4*len(words) or pc&3 for pc in active):
        raise ValueError('continuation geometry')
    rows=tuple((pc,words[(pc-root)//4]) for pc in active)
    blocks=extend_guarded(prior[2],root,start,rows,dst,target_word)
    mask=saved_mask(prior[0][6])
    if mask.bit_count()!=16:raise ValueError('continuation mask')
    args=tuple((i,k,v) for i,(k,v) in enumerate(gp) if 3<=i<=10 and k in ('const','stack'))
    if len(args)!=4 or sum(k=='stack' for _,k,_ in args)!=3 or sum(k=='const' for _,k,_ in args)!=1:
        raise ValueError('continuation arguments')
    return blocks,root,start,dst,target_word,rows,mask,args

def plan(d,e):
    prior=fixture_plan(d,e)
    path,frame,accesses,saved,leaf_root,gp,mem,ws,state,readonly=prefix_plan(d,e,details=True)
    leaf=leaf_run(leaf_root,exact_words(d,e,leaf_root,12),gp,readonly,mem,initial_cr=state[2],details=True)
    if len(leaf[0])!=8 or len(leaf[1])!=1 or len(leaf[3])!=12:raise ValueError('continuation predecessor')
    result=resume(path[0],ws,(path,frame,accesses,saved,leaf_root,gp,mem,state),leaf,readonly)
    dst=result[4]
    if parse_functions(e).get(dst)!=383*4:raise ValueError('continuation target size')
    return contract(prior,path[0],ws,result,exact_words(d,e,dst,1)[0])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','continuation contract','continuation geometry','continuation mask','continuation arguments','continuation predecessor','continuation target size','continuation ownership','continuation labels','continuation start','continuation overlap','continuation final call','continuation return guard','continuation saved registers'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        blocks,root,start,dst,word,rows,mask,args=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_CONTINUATION_PLAN verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'FORMATTER_CONTINUATION_PLAN verified=1 labels={len(rows)} saved_registers={mask.bit_count()} known_arguments={len(args)} new_roots=1 guarded_return=1 target_words=383 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
