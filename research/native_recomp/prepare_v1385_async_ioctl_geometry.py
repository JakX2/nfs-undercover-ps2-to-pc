#!/usr/bin/env python3
"""Private full IOS_Ioctl wrapper and exact compiler leaf closure."""
import argparse,struct
from pathlib import Path
from prepare_v629_stm_open import geometry
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words
from make_v639_open_geometry import geometry as open_geometry
from make_v651_open_fixture import submit_geometry
from make_private_elf_symbol_map import parse_functions
from restore_stm_ioctl_v86 import IOCTL,SIZE,EDGES
from classify_save_leaf_v683 import classify_suffix,symbol_evidence
from audit_handler_suffix_v728 import restore_suffix
from si_helper_geometry_v680 import alias_owner
from prepare_v1377_stm_tail import scan
from make_v1243_stm_fixture import seed_data
BLR=0x4e800020

def leaf_shape(words,restore=False):
    if restore:
        n=restore_suffix(words)
        if not n:raise ValueError('ioctl restore leaf shape')
        return n,(words[0]>>16)&31,((words[0]&0xffff)^0x8000)-0x8000
    leaf=classify_suffix(words)
    if leaf['kind']!=1:raise ValueError('ioctl save leaf shape')
    return leaf['registers'],leaf['base'],((words[0]&0xffff)^0x8000)-0x8000

def compiler_leaf(d,e,root,sizes,restore=False):
    words=[]
    for i in range(19):
        words.extend(exact_words(d,e,root+4*i,1))
        if words[-1]==BLR:break
    regs,base,disp=leaf_shape(words,restore)
    size=4*len(words);alias=False
    if root in sizes:
        if sizes[root]!=size:raise ValueError('ioctl leaf extent')
    else:
        alias_owner(root,size,sizes)
        ev=symbol_evidence(e,root)
        if not(ev['zero_func'] or ev['notype']):raise ValueError('ioctl leaf symbol')
        alias=True
    return tuple(words),regs,base,disp,alias

def wrapper_shape(words,root=IOCTL,edges=EDGES):
    if len(words)*4!=SIZE:raise ValueError('ioctl wrapper extent')
    want=dict(edges)
    got={root+4*i:direct_bl(w,root+4*i) for i,w in enumerate(words) if w>>26==18 and w&3==1}
    if got!=want:raise ValueError('ioctl wrapper calls')
    seen,calls,returns,stores,sda=scan(root,words,root,want)
    if calls!=set(edges) or not returns:raise ValueError('ioctl wrapper route')
    return seen,returns,stores,sda

def plan(d,e):
    _,stm,_,_,paths,_=geometry(d,e)
    sizes=parse_functions(e)
    if sizes.get(IOCTL)!=SIZE:raise ValueError('ioctl wrapper extent')
    body=exact_words(d,e,IOCTL,SIZE//4)
    seen,returns,stores,sda=wrapper_shape(body)
    save,restore=EDGES[0][1],EDGES[-1][1]
    a=compiler_leaf(d,e,save,sizes);b=compiler_leaf(d,e,restore,sizes,True)
    if a[1:4]!=b[1:4]:raise ValueError('ioctl leaf pair')
    _,_,opens=open_geometry(d,e);sub,_=submit_geometry(d,e)
    shared={**opens,**sub}
    shared_targets={dst for _,dst in EDGES if dst not in (save,restore)}
    if not shared_targets<=set(shared):raise ValueError('ioctl shared root')
    for dst in shared_targets:
        if not shared[dst] or tuple(shared[dst])!=exact_words(d,e,dst,len(shared[dst])):
            raise ValueError('ioctl shared identity')
    roots={IOCTL:body,save:a[0],restore:b[0]}
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in {**shared,**roots}.items())
    if any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('ioctl root overlap')
    before=seed_data(d,stm,paths);after=seed_data(d,tuple(stm)+body,paths)
    if any(after.get(addr)!=v for addr,v in before.items()):raise ValueError('ioctl seed identity')
    return roots,seen,returns,stores,sda,a,b,len(shared_targets),len(after)-len(before)

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);q=p.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        roots,seen,returns,stores,sda,a,b,shared,seed=plan(q.dol.read_bytes(),q.elf.read_bytes())
        print(f'V1385_IOCTL_GEOMETRY verified=1 wrapper_words={len(roots[IOCTL])} reachable={len(seen)} '
              f'direct_calls=6 returns={len(returns)} direct_stores={len(stores)} sda_sites={len(sda)} '
              f'save_gprs={a[1]} restore_gprs={b[1]} alias_roots={int(a[4])+int(b[4])} '
              f'shared_roots={shared} additional_seed_bytes={seed} original_execution=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','ioctl restore leaf shape','ioctl save leaf shape','ioctl leaf extent','ioctl leaf symbol',
            'ioctl wrapper extent','ioctl wrapper calls','ioctl wrapper route','ioctl leaf pair','ioctl shared root',
            'ioctl shared identity','ioctl root overlap','ioctl seed identity','tail escape','tail call','tail control',
            'tail reachability','save leaf terminator','save leaf shape','save leaf extent','save leaf sequence',
            'first SI alias containment','word identity'}
        print('V1385_IOCTL_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
