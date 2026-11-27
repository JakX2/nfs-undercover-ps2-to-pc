#!/usr/bin/env python3
"""Aggregate-only audit of the first instruction after caller LR restoration."""
import argparse,struct
from pathlib import Path
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from audit_formatter_partial_integer import describe,special_destination
from prepare_formatter_special_contract import plan as special_plan
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def classify_next(w,gp,frame):
    if len(gp)!=32 or not 8<=frame<=4096 or gp[1][0]!='stack':
        raise ValueError('epilogue state')
    op,rt,ra=w>>26,(w>>21)&31,(w>>16)&31
    imm=((w&0xffff)^0x8000)-0x8000
    exact=op==14 and rt==ra==1 and imm==frame
    info=describe(w,gp)
    return info[0],int(exact),int(1 in ((rt,) if op in (14,15) else ())),info[3],info[4],info[5],info[6]

def plan(d,e):
    c,info=special_plan(d,e)
    if info[:2]!=('link',1):raise ValueError('epilogue predecessor')
    result,extra,trace,admitted,entry,record=replay_plan(d,e,details=True)
    _,fields,rows,access,slots,known=c
    root,caller,pc,w,frame,_,_=fields
    _,last_word,gp,mem=trace[-1]
    if special_destination(last_word,gp,caller)!=('link',1,1):
        raise ValueError('epilogue predecessor')
    words=exact_words(d,e,root,383);i=(pc-root)//4
    if not 0<=i<len(words)-1 or words[i]!=w or len(rows)!=96:
        raise ValueError('epilogue words')
    parent_sp=entry[1][1][1]
    if gp[1]!=('stack',parent_sp-frame):
        raise ValueError('epilogue state')
    next_word=words[i+1]
    return classify_next(w,gp,frame),boundary_shape(next_word),int(next_word==0x4e800020)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','epilogue predecessor','epilogue words','epilogue state'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            (kind,release,sp_write,constant,stack,partial,other),next_family,ret=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_EPILOGUE_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_EPILOGUE_AUDIT verified=1 family={kind} exact_frame_release={release} immediate_sp_write={sp_write} constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} other_inputs={other} next_family={next_family} next_blr={ret} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
