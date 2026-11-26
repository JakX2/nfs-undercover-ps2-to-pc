#!/usr/bin/env python3
"""Private SC version registration argument and original diagnostic tail audit."""
import argparse
import struct
from pathlib import Path
from private_plan_cache import memoized_plan
from prepare_post_stm_sc_restore import plan as restore_plan,version_region,ROOT,EDGES
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS,direct_bl
from make_private_elf_symbol_map import HEADER,SECTION,parse_functions
from make_v624_ipc_geometry import exact_words
from make_v594_boot_report_geometry import REPORT
from make_v1243_stm_fixture import data_at,seed_data
from prepare_post_stm_sc_state import overlap,store_kind
from prepare_v629_stm_open import geometry
from prepare_v1337_open_completion import plan as completion
from prepare_v1385_async_ioctl_geometry import plan as ioctl_plan
from prepare_post_stm_sc_disable import decision
from prepare_stm_final_return import plan as final_plan
from prepare_stm_event_return_geometry import plan as event_plan
from prepare_ipc_profile_geometry import layout
from prepare_ipc_dispatch_geometry import credit_object
from prepare_v1414_ipc_ring import ring_object
VERSION=EDGES[3][1]

def cstring(dol,addr):
    out=bytearray()
    for i in range(256):
        b=data_at(dol,addr+i,1)
        if b is None:raise ValueError('SC version string mapping')
        out.extend(b)
        if b==b'\0':
            if len(out)==1:raise ValueError('SC version empty string')
            return bytes(out)
        if not 32<=b[0]<127 and b[0] not in (9,10,13):raise ValueError('SC version string encoding')
    raise ValueError('SC version string length')

def elf_data(elf,addr,size):
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf):
        raise ValueError('SC version ELF sections')
    found=[]
    for i in range(n):
        _,kind,flags,base,fo,length,*_=SECTION.unpack_from(elf,off+i*unit)
        if kind==1 and flags&2 and not flags&4 and base<=addr<addr+size<=base+length and fo+length<=len(elf):
            found.append(elf[fo+addr-base:fo+addr-base+size])
    if len(found)!=1:raise ValueError('SC version ELF mapping')
    return found[0]

def thunk(root,words,report,sda,ptr):
    if not 3<=len(words)<=8:raise ValueError('SC version thunk extent')
    gp={3:ptr,**sda}
    for i,w in enumerate(words):
        pc=root+4*i;op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        if i==len(words)-1:
            if op!=18 or w&3 or pc+((w&0x03fffffc)^0x02000000)-0x02000000!=report or gp.get(4)!=ptr or gp.get(3) is None:
                raise ValueError('SC version tail')
            return gp[3]
        if op==14 and rs in (0,*range(3,13)) and (ra==0 or ra in gp):
            gp[rs]=((gp[ra] if ra else 0)+((w&0xffff)^0x8000)-0x8000)&0xffffffff
        elif op==31 and xo==444 and not w&1 and rs==rb and rs in gp and ra in (0,*range(3,13)):
            gp[ra]=gp[rs]
        elif op==19 and xo==193 and rs==ra==rb==6 and not w&1:
            # EABI variadic calls clear CR bit 6 (no floating arguments).
            pass
        else:
            kind='cr' if op==19 else 'integer' if op in (14,15,24,31) else 'other'
            raise ValueError(f'SC version thunk opcode {kind} {i+1}')
    raise ValueError('SC version tail')

@memoized_plan
def plan(d,e):
    p=restore_plan(d,e);rows,loads=version_region(d,e,p)
    pc,rs,addr,ptr=loads[0]
    if rs!=3 or pc!=p[0][1] or set(rows)!={pc,pc+4} or direct_bl(rows[pc+4],pc+4)!=VERSION:
        raise ValueError('SC version call')
    size=parse_functions(e).get(VERSION,0)
    if not 12<=size<=32 or size%4:raise ValueError('SC version thunk extent')
    body=exact_words(d,e,VERSION,size//4)
    fmt=thunk(VERSION,body,REPORT,{i:EXPECTED_GPRS[i] for i in (2,13)},ptr)
    version=cstring(d,ptr);format_=cstring(d,fmt)
    if format_.count(b'%s')!=1 or b'%' in format_.replace(b'%%',b'').replace(b'%s',b''):
        raise ValueError('SC version format')
    ranges=((addr,ptr.to_bytes(4,'big')),(ptr,version),(fmt,format_))
    for a,data in ranges:
        if data_at(d,a,len(data))!=data or elf_data(e,a,len(data))!=data:
            raise ValueError('SC version data identity')
    if any(overlap(a,len(data),b,len(other)) for i,(a,data) in enumerate(ranges) for b,other in ranges[i+1:]):
        raise ValueError('SC version overlap')
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3],final_plan(d,e)[1],
               *(x[3] for x in decision(d,e)[2])]
    if any(overlap(a,len(data),b,n) for a,data in ranges for b,n in protected):
        raise ValueError('SC version object overlap')
    _,stm,_,_,paths,_=geometry(d,e)
    shared=completion(d,e)[0];roots=ioctl_plan(d,e)[0]
    seed=seed_data(d,tuple(stm)+tuple(w for words in roots.values() for w in words),paths)
    for a,data in ranges:
        if any(a+i in seed and seed[a+i]!=v for i,v in enumerate(data)):raise ValueError('SC version seed identity')
    for w in tuple(stm)+tuple(w for ws in (*roots.values(),*shared.values()) for w in ws):
        n=store_kind(w);ra=(w>>16)&31
        if n>0 and ra in (2,13):
            at=(EXPECTED_GPRS[ra]+((w&0xffff)^0x8000)-0x8000)&0xffffffff
            if any(overlap(a,len(data),at,n) for a,data in ranges):raise ValueError('SC version earlier writer')
    report_word=exact_words(d,e,REPORT,1)[0]
    return rows,body,ranges,(pc,VERSION,REPORT,report_word,ptr,fmt)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC version string mapping','SC version empty string','SC version string encoding','SC version string length',
          'SC version ELF sections','SC version ELF mapping','SC version thunk extent','SC version tail','SC version thunk opcode','SC version call',
          'SC version format','SC version data identity','SC version overlap','SC version object overlap','SC version seed identity','SC version earlier writer'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        rows,body,ranges,_=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('SC version thunk opcode '):
            _,_,_,_,kind,ordinal=reason.split()
            if kind in ('cr','integer','other') and ordinal.isdecimal() and 1<=int(ordinal)<=8:
                print(f'POST_STM_SC_VERSION_PROVENANCE verified=0 reason=SC_version_thunk_opcode category={kind} ordinal={ordinal}')
                return 1
        print('POST_STM_SC_VERSION_PROVENANCE verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_VERSION_PROVENANCE verified=1 caller_labels={len(rows)} thunk_labels={len(body)} initialized_ranges={len(ranges)} elf_identity=1 diagnostic_tail=1 earlier_direct_writers=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
