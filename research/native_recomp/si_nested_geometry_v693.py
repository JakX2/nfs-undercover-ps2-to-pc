"""Authenticate the first reachable direct dependency of the second SI helper."""
from si_second_geometry_v688 import second_plan
from prepare_v668_si_ack import shape
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_si_nested_v690 import prefix
def nested_edge(root,words,sizes):
    _,direct,indirect=shape(root,words)
    if len(direct)!=2 or indirect or prefix(root,words)['first_calls']!=(1,):raise ValueError('nested first route')
    site,dst=direct[0];size=sizes.get(dst,0)
    if dst==root or size!=100 or site+4>=root+4*len(words):raise ValueError('nested extent')
    return site,dst,size,words[(site-root)//4]
def nested_plan(dol,elf):
    _,root,_,_,words=second_plan(dol,elf)
    site,dst,size,w=nested_edge(root,words,parse_functions(elf))
    code=exact(dol,elf,dst,size//4)
    stores,calls,indirect=shape(dst,code)
    if len(stores)!=5 or len(calls)+len(indirect)!=3 or code.count(0x4e800020)!=1:
        raise ValueError('nested verified shape')
    return site,dst,size,w,code
