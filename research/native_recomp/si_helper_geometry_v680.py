"""Authenticate only the first direct dependency observed by V673."""
from prepare_v668_si_ack import geometry,shape,HANDLER
from prepare_v419_full_start import words_at
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
def first_edge(root,words,sizes):
    _,direct,indirect=shape(root,words)
    if not direct or (indirect and min(indirect)<direct[0][0]):raise ValueError('first SI dependency not direct')
    site,target=direct[0];n=sizes.get(target,0)
    if target==root or not 4<=n<=4096 or n&3 or site+4>=root+4*len(words):raise ValueError('first SI dependency extent')
    return site,target,n,words[(site-root)//4]
def helper_geometry(dol,elf):
    n,_,_,_,_=geometry(dol,elf);handler=words_at(dol,HANDLER,n)
    site,target,size,word=first_edge(HANDLER,handler,parse_functions(elf))
    helper=exact(dol,elf,target,size//4)
    if 0x4e800020 not in helper:raise ValueError('first SI dependency return')
    return site,target,size,word,helper
