#!/usr/bin/env python3
"""Private read-only STM post-restore ABI geometry. No original data exported."""
import argparse
import re
import struct
from pathlib import Path
from prepare_v629_stm_open import geometry,STM,EDGES
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from prepare_stm_event_return_geometry import object_at,plan as event_plan
from prepare_ipc_dispatch_geometry import credit_object
from prepare_ipc_profile_geometry import layout
from prepare_v1414_ipc_ring import ring_object
from prepare_stm_outer_restore import plan as outer_plan
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v1337_open_completion import ensure_resume,hook_submit

BLR=0x4e800020

def imm(w):
    return ((w&0xffff)^0x8000)-0x8000

def spr(w):
    return ((w>>16)&31)|(((w>>11)&31)<<5)

def prologue(words):
    # Provenance relative to incoming r1; no guest bytes copied to the report.
    # Each incoming nonvolatile register must have its own saved slot.
    reg=list(range(32));sp=0;slots={};frame=0
    for w in words[:24]:
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;xo=(w>>1)&1023
        if op==37 and rs==ra==1:
            if frame or not -256<=imm(w)<=-8 or imm(w)%8:
                raise ValueError('prologue frame')
            sp=imm(w);frame=-sp
        elif op==31 and xo==339 and spr(w)==8:
            reg[rs]='lr'
        elif op in (36,47) and ra==1:
            if not frame:raise ValueError('prologue store before frame')
            for n in range(32-rs if op==47 else 1):
                off=sp+imm(w)+4*n;value=reg[rs+n]
                if off%4 or not -frame+4<=off<=4 or off in slots:
                    raise ValueError('prologue slot')
                if value=='lr' or isinstance(value,int) and 14<=value<=31:
                    if value in slots.values():raise ValueError('prologue duplicate register')
                    slots[off]=value
                else:
                    # An unrelated local store is not an ABI save.
                    slots[off]=None
        elif op in (14,15) and rs!=1:
            reg[rs]=None
        elif op==31 and xo==444 and ra!=1:
            rb=(w>>11)&31
            reg[ra]=reg[rs] if rs==rb else None
        elif op in (32,34,40,42) and rs!=1:
            reg[rs]=None
        elif op==24 and ra!=1:
            reg[ra]=reg[rs] if not imm(w) else None
        else:
            break
    if not frame or list(slots.values()).count('lr')!=1:
        raise ValueError('prologue identity')
    return frame,{off:value for off,value in slots.items() if value is not None}

def tail(words,frame,slots,store_sites=()):
    # After the outer restore call the native epilogue is a leaf. Require
    # every restored nonvolatile register to originate at its prologue slot.
    sp=-frame;values=[None]*32;lr=False;loaded=set();loads=0;stores=0
    if len(set(store_sites))!=len(store_sites):raise ValueError('tail store identity')
    if not words or len(words)>32 or words[-1]!=BLR:
        raise ValueError('tail extent')
    for ordinal,w in enumerate(words,1):
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;xo=(w>>1)&1023
        if w==BLR:
            if w!=words[-1] or sp or not lr or loaded!=set(slots.values()) or stores!=len(store_sites):
                raise ValueError('tail ABI')
        elif op in (32,46) and ra==1:
            for n in range(32-rs if op==46 else 1):
                r=rs+n;off=sp+imm(w)+4*n;value=slots.get(off)
                if value is None or value in loaded or r==1 or (value!='lr' and value!=r) or (value=='lr' and r>=14):
                    raise ValueError('tail load')
                values[r]=value;loaded.add(value);loads+=1
        elif op==36 and ra in (2,13):
            if ordinal not in store_sites or values[rs]!=('constant',1):
                raise ValueError('tail store value')
            stores+=1
        elif op==14 and rs==ra==1:
            if sp!=-frame or imm(w)!=frame:raise ValueError('tail stack')
            sp=0
        elif op==31 and xo==467 and spr(w)==8:
            if values[rs]!='lr' or lr:raise ValueError('tail LR')
            lr=True
        elif op in (14,15) and rs in (0,*range(3,13)):
            source=values[ra] if ra else ('constant',0)
            if isinstance(source,tuple) and source[0]=='constant':
                add=imm(w)*(65536 if op==15 else 1)
                values[rs]=('constant',(source[1]+add)&0xffffffff)
            else:values[rs]=source if op==14 and not imm(w) else None
        elif op==31 and xo==444 and ra in (0,*range(3,13)):
            values[ra]=values[rs] if rs==((w>>11)&31) else None
        elif op==24 and ra in (0,*range(3,13)) and isinstance(values[rs],tuple):
            values[ra]=('constant',values[rs][1]|(w&0xffff))
        elif op in (20,21,23,24,25,26,27,28,29) and ra in (0,*range(3,13)):
            # An integer return-value computation is not LR provenance.
            # Reserved SDA/SP and nonvolatile registers cannot be changed.
            values[ra]=None
        else:
            category=('branch' if op in (16,18,19) else 'load' if op in (32,33,34,35,40,41,42,43,46)
                      else 'store' if op in (36,37,38,39,44,45,47,52,53,54,55)
                      else 'integer' if op in (7,8,10,11,12,13,14,15,20,21,23,24,25,26,27,28,29,31)
                      else 'other')
            raise ValueError(f'tail opcode {category} {ordinal}')
    if words.count(BLR)!=1:raise ValueError('tail return count')
    return loads,sum(isinstance(v,int) for v in loaded)

def plan(d,e):
    _,body,edge,_,_,_=geometry(d,e)
    caller,caller_word,*_=outer_plan(d,e)
    if caller!=EDGES[-1][0]+4 or caller_word!=body[(caller-STM)//4]:
        raise ValueError('tail caller')
    start=(caller-STM)//4
    frame,slots=prologue(body[:start])
    # Only an exact SDA word store to a privately identified writable
    # ELF object is admissible. It must not alias the already-registered
    # event or any IPC accounting object.
    stores=[]
    for i,w in enumerate(body[start:],1):
        if w>>26!=36:continue
        ra=(w>>16)&31
        if ra not in (2,13):raise ValueError('tail store base')
        a=(EXPECTED_GPRS[ra]+imm(w))&0xffffffff
        obj=object_at(d,e,a,4)
        protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3]]
        if any(obj[0]<b+n and b<obj[0]+obj[1] for b,n in protected):
            raise ValueError('tail store overlap')
        stores.append((i,caller+4*(i-1),a,(w>>21)&31,obj))
    if len(stores)!=1:raise ValueError('tail store count')
    loads,saved=tail(body[start:],frame,slots,tuple(row[0] for row in stores))
    # Caller identity is authenticated privately; the focused fixture
    # still models the OSInit bridge and must stop before its continuation.
    returned=edge[1];ret=exact_words(d,e,returned,1)[0]
    _,site,address,reg,obj=stores[0]
    words={caller+4*i:(STM,w) for i,w in enumerate(body[start:])}
    return (STM,caller,returned,ret,frame,site,address,reg),obj,slots,words,loads,saved

def derive(d,e):
    p=plan(d,e)
    return len(p[3]),p[4],p[5],1

def render(p):
    fields,obj,slots,words,*_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    slot_rows=','.join('undercover::wii::StmFinalSlot{'+str(off)+','+str(32 if reg=='lr' else reg)+'u}'
                       for off,reg in sorted(slots.items()))
    word_rows=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}'
                       for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_stm_final_return.h"\nnamespace stm_final_private {\n'
            f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+slot_rows+'};\n'
            f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+word_rows+'};\n'
            'inline constexpr undercover::wii::StmFinalExpectation expected{'+fmt(fields)+
            ',undercover::wii::AllocatorRange{'+fmt(obj)+'},slots,words};\n}\n')

def install(root,p):
    fields,_,_,words,*_=p
    owner,start,*_=fields
    paths=sorted(root.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=root/'main_output.cpp';text=main.read_text()
    audit_native(sources.values(),text,words)
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{owner:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('tail native owner')
    verify_direct(owners[0],start-4,EDGES[-1][1])
    out,added=ensure_resume(text,exact_function(owners[0],owner),owner,start)
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,(_,word) in words.items():
            s,found=hook_submit(s,pc,word)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{word:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('tail native hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','stm_final_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('tail native hook')
            changed[path]=s.replace(anchor,anchor+'\nvoid stm_final_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(words):raise ValueError('tail native coverage')
    for path,s in changed.items():path.write_text(s)
    if added:main.write_text(out)
    print(f'STM_FINAL_RETURN_TRANSLATION verified=1 labels={len(done)} outer_resume=1 added={int(added)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--out',type=Path);m.add_argument('--install',type=Path);q=a.parse_args()
    allowed={'size','prologue frame','prologue store before frame','prologue slot','prologue duplicate register',
             'prologue identity','tail extent','tail ABI','tail load','tail stack','tail LR','tail opcode','tail return count','tail caller','tail store identity','tail store value',
             'tail store base','tail store overlap','tail store count','tail native owner','tail native hook','tail native coverage',
             'completion local resume','completion root dispatch','completion outer resume','completion hook label',
             'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
             'helper exact root','helper call label','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.install,p);return 0
        if q.out:
            with (q.out/'private_stm_final_return.h').open('x') as f:f.write(render(p))
        labels,loads,saved,stores=len(p[3]),p[4],p[5],1
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('tail opcode '):
            _,_,category,ordinal=reason.split()
            if category in {'branch','load','store','integer','other'} and ordinal.isdecimal() and 1<=int(ordinal)<=32:
                print(f'STM_FINAL_RETURN_GEOMETRY verified=0 reason=tail_opcode category={category} ordinal={ordinal}')
                return 1
        print('STM_FINAL_RETURN_GEOMETRY verified=0 reason='+(reason.replace(' ','_') if reason in allowed else 'private_input'))
        return 1
    print(f'STM_FINAL_RETURN_GEOMETRY verified=1 labels={labels} stack_loads={loads} saved_gprs={saved} state_stores={stores} lr=1 caller=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
