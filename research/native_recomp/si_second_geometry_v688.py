"""Exact second direct dependency observed by original V684 execution."""
from prepare_v668_si_ack import geometry,shape,HANDLER
from prepare_v419_full_start import words_at
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
def second_edge(root,words,sizes):
    _,direct,indirect=shape(root,words)
    rows=sorted([(pc,t) for pc,t in direct]+[(pc,None) for pc in indirect])
    if len(rows)<2 or rows[1][1] is None:raise ValueError('second SI call kind')
    site,target=rows[1];size=sizes.get(target,0)
    if target==root or not 4<=size<=4096 or size&3 or site+4>=root+4*len(words):raise ValueError('second SI extent')
    return site,target,size,words[(site-root)//4]
def second_plan(dol,elf):
    n,_,_,_,_=geometry(dol,elf);handler=words_at(dol,HANDLER,n)
    site,target,size,word=second_edge(HANDLER,handler,parse_functions(elf))
    words=exact(dol,elf,target,size//4)
    if len(words)!=189 or words.count(0x4e800020)!=1:raise ValueError('second SI verified shape')
    stores,calls,indirect=shape(target,words)
    if len(stores)!=21 or len(calls)!=2 or indirect:raise ValueError('second SI verified dependencies')
    return site,target,size,word,words
