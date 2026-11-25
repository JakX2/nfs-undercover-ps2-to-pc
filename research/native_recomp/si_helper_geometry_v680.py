"""Authenticate only the first direct dependency observed by V673."""
from prepare_v668_si_ack import geometry,shape,HANDLER
from prepare_v419_full_start import words_at
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from classify_save_leaf_v683 import inspect_suffix,classify_suffix
def first_edge(root,words,sizes):
    _,direct,indirect=shape(root,words)
    if not direct or (indirect and min(indirect)<direct[0][0]):raise ValueError('first SI dependency not direct')
    site,target=direct[0];n=sizes.get(target,0)
    if target==root or not 4<=n<=4096 or n&3 or site+4>=root+4*len(words):raise ValueError('first SI dependency extent')
    return site,target,n,words[(site-root)//4]
def alias_owner(target,size,sizes):
    owners=[(a,n) for a,n in sizes.items() if a<target<a+n]
    if len(owners)!=1 or target+size>owners[0][0]+owners[0][1]:raise ValueError('first SI alias containment')
    return owners[0]
def helper_plan(dol,elf):
    n,_,_,_,_=geometry(dol,elf);handler=words_at(dol,HANDLER,n)
    _,direct,indirect=shape(HANDLER,handler)
    if not direct or (indirect and min(indirect)<direct[0][0]):raise ValueError('first SI dependency not direct')
    site,target=direct[0];sizes=parse_functions(elf)
    if target==HANDLER or site+4>=HANDLER+4*n:raise ValueError('first SI dependency extent')
    alias=False;save=(0,0,0)
    if target in sizes:
        site,target,size,word=first_edge(HANDLER,handler,sizes)
        helper=exact(dol,elf,target,size//4)
    else:
        # The observed direct target is interior to an authenticated ELF
        # function. Only a recognized, exact GPR-save suffix is eligible.
        leaf=inspect_suffix(dol,elf,target)
        if leaf['kind']!=1:raise ValueError('first SI alias unsupported kind')
        size=4*(leaf['registers']+1);alias_owner(target,size,sizes)
        helper=exact(dol,elf,target,size//4)
        if classify_suffix(helper)!=leaf:raise ValueError('first SI alias identity')
        word=handler[(site-HANDLER)//4];alias=True
        save=(32-leaf['registers'],leaf['base'],((helper[0]&0xffff)^0x8000)-0x8000)
    if 0x4e800020 not in helper:raise ValueError('first SI dependency return')
    return (site,target,size,word,helper),alias,save
def helper_geometry(dol,elf):return helper_plan(dol,elf)[0]
