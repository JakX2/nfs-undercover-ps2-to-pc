#!/usr/bin/env python3
"""Census of the first consumer of a partially initialized stack word."""
import argparse,struct
from pathlib import Path
from analyze_formatter_after_ctr import plan as after_ctr
from prepare_post_stm_sc_report_dependency_path import rotate,bitmask
from prepare_formatter_nested_contract import boundary_width
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def known_mask(mem,at,n):
    if n!=4 or at&3:raise ValueError('partial stack geometry')
    mask=0
    for i in range(n):
        cell=mem.get(at+i)
        if cell is not None and cell[0]=='byte':mask|=0xff<<(8*(n-1-i))
    return mask

def consumer(w,loaded,mask):
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    if op==21 and rs==loaded:
        sh=rb;selected=bitmask((w>>6)&31,(w>>1)&31)
        needed=rotate(selected,(32-sh)&31)
        return 'rotate_mask',int((needed&~mask)==0),int(ra==loaded),needed.bit_count()
    if op in (28,29) and rs==loaded:
        needed=(w&0xffff)<<(16 if op==29 else 0)
        return 'and_immediate',int((needed&~mask)==0),int(ra==loaded),needed.bit_count()
    if op==31 and xo in (922,954) and rs==loaded:
        needed=0xffff if xo==922 else 0xff
        return 'sign_extend',int((needed&~mask)==0),int(ra==loaded),needed.bit_count()
    return 'other',0,0,32

def plan(d,e):
    kind,path,frame,sites,words,width,region,counts,entry,record,cells=after_ctr(d,e,details=True)
    if (kind,len(path),len(set(path)),frame,len(sites),width,region,counts)!=('stack_load',84,84,48,21,4,'child_local',(2,0)):
        raise ValueError('partial stack predecessor')
    at,n,full,_,_,gp,mem,cr,ctr,lr,saves=record
    pc=full[-1];load,next_word=exact_words(d,e,pc,2)
    if boundary_width(load)!=4:raise ValueError('partial stack load')
    loaded=(load>>21)&31;mask=known_mask(mem,at,n)
    k,independent,overwrite,bits=consumer(next_word,loaded,mask)
    return mask.bit_count(),k,independent,overwrite,bits

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','partial stack geometry','partial stack predecessor','partial stack load'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            known,kind,independent,overwrite,bits=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_STACK verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_STACK verified=1 known_bits={known} consumer={kind} independent_of_unknown={independent} overwrites_loaded_register={overwrite} required_bits={bits} value_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
