#!/usr/bin/env python3
"""Owner-only SI handler geometry. Emit only bounded counts, not owner code."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
HANDLER=0x80531b34
def is_word_store(w):
    op=w>>26;xo=(w>>1)&1023
    return op in (36,37) or op==31 and xo in (151,183,662)
def shape(root,words):
    if root&3 or not 4<=len(words)<=0x1000//4:raise ValueError('handler extent')
    stores=tuple(root+4*i for i,w in enumerate(words) if is_word_store(w))
    calls=tuple((root+4*i,direct_bl(w,root+4*i)) for i,w in enumerate(words) if w>>26==18 and w&3==1)
    indirect=tuple(root+4*i for i,w in enumerate(words) if w==0x4e800421)
    if not stores:raise ValueError('no store candidates')
    return stores,calls,indirect
def geometry(dol,elf):
    if hashlib.sha256(dol).hexdigest()!=OWNER_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('identity')
    sizes=parse_functions(elf);n=sizes.get(HANDLER,0)
    if not 16<=n<=0x1000 or n&3:raise ValueError('handler extent')
    words=words_at(dol,HANDLER,n//4)
    if words!=tuple(read_words(elf,HANDLER,n//4)):raise ValueError('DOL ELF identity')
    stores,calls,indirect=shape(HANDLER,words)
    exact_roots=0
    for _,target in calls:
        size=sizes.get(target,0)
        if size and size%4==0:
            if words_at(dol,target,1)!=tuple(read_words(elf,target,1)):raise ValueError('call root identity')
            exact_roots+=1
    return n//4,len(stores),len(calls),len(indirect),exact_roots
INCLUDE='#include "wii_si_controller_v511.h"'
WRITE='active_->controller_.write(*off,value);'
def patch_binding(s):
    """Future opt-in native install seam; leave prior discovery observers intact."""
    s=replace_exact(s,INCLUDE,INCLUDE+'\n#include "wii_si_completion_ack_v668.h"')
    return replace_exact(s,WRITE,'si_completion_ack_trace.write(active_->controller_,*off,value);')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        words,stores,calls,indirect,roots=geometry(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V668_SI_HANDLER_GEOMETRY verified=0');return 1
    print(f'V668_SI_HANDLER_GEOMETRY verified=1 words={words} store_candidates={stores} direct_calls={calls} indirect_calls={indirect} exact_call_roots={roots} execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
