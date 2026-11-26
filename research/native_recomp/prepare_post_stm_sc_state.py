#!/usr/bin/env python3
"""Private initial SC decision object audit, no guest initialization or execution."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_disable import decision
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from make_v1243_stm_fixture import data_at,seed_data
from prepare_v629_stm_open import geometry
from prepare_v1385_async_ioctl_geometry import plan as ioctl_plan
from prepare_v1337_open_completion import plan as completion
from prepare_stm_final_return import plan as final_plan

def initial(dol,a,n):
    if n not in (1,2,4) or a%n:raise ValueError('SC state width')
    blob=data_at(dol,a,n)
    if blob is not None:return 1,blob
    bss,size=struct.unpack_from('>II',dol,0xd8)
    if not bss<=a<a+n<=bss+size:raise ValueError('SC state mapping')
    return 2,bytes(n)

def overlap(a,n,b,m):return a<b+m and b<a+n

def store_kind(w):
    op=w>>26;xo=(w>>1)&1023
    if op in (36,37,38,39,44,45,47):return {36:4,37:4,38:1,39:1,44:2,45:2,47:4*(32-((w>>21)&31))}[op]
    if op==31 and xo in (150,151,183,215,247,407,439,661,662,725,918,663,695,727,759,983,1014):return -1
    return 0

def derive(d,e):
    rows,loads,writes,stops=decision(d,e)
    if len(loads)!=1 or len(writes)!=2 or len(stops)!=2:raise ValueError('SC state geometry')
    _,a,n,obj=loads[0]
    kind,blob=initial(d,a,n)
    _,stm,_,_,paths,_=geometry(d,e)
    roots=ioctl_plan(d,e)[0]
    shared=completion(d,e)[0]
    seeded=seed_data(d,tuple(stm)+tuple(w for words in roots.values() for w in words),paths)
    for i,v in enumerate(blob):
        if a+i in seeded and seeded[a+i]!=v:raise ValueError('SC seed identity')
    # Direct SDA store census of earlier translated functions. Dynamic
    # pointer stores are not ruled out; live entry must independently
    # verify the actual state bytes rather than patching them.
    prior_words=tuple(stm)+tuple(w for words in roots.values() for w in words)+tuple(w for words in shared.values() for w in words)
    direct=0
    for w in prior_words:
        width=store_kind(w);ra=(w>>16)&31
        if width<=0 or ra not in (2,13):continue
        disp=((w&0xffff)^0x8000)-0x8000
        addr=(EXPECTED_GPRS[ra]+disp)&0xffffffff
        if overlap(addr,width,*obj):direct+=1
    if direct:raise ValueError('SC earlier direct writer')
    if overlap(*obj,*final_plan(d,e)[1]):raise ValueError('SC STM state overlap')
    same=sum(row[3]==obj for row in writes)
    same_cell=sum(row[1:3]==(a,n) for row in writes)
    return kind,int(not any(blob)),sum(a+i in seeded for i in range(n)),len({x[3] for x in writes}),same,same_cell

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC state width','SC state mapping','SC state geometry','SC seed identity','SC earlier direct writer','SC STM state overlap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        kind,zero,seeded,objects,same,cells=derive(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_STATE verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_STATE verified=1 source_kind={kind} initial_zero={zero} inherited_seed_bytes={seeded} store_objects={objects} same_load_object={same} same_load_cell={cells} earlier_direct_writers=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
