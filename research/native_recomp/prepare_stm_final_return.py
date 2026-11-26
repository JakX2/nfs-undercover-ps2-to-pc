#!/usr/bin/env python3
"""Private read-only STM post-restore ABI geometry. No original data exported."""
import argparse
import struct
from pathlib import Path
from prepare_v629_stm_open import geometry,STM,EDGES
from prepare_v419_full_start import MAX_DOL
from prepare_stm_outer_restore import plan as outer_plan
from make_v624_ipc_geometry import exact_words

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

def tail(words,frame,slots):
    # After the outer restore call the native epilogue is a leaf. Require
    # every restored nonvolatile register to originate at its prologue slot.
    sp=-frame;values=[None]*32;lr=False;loaded=set();loads=0
    if not words or len(words)>32 or words[-1]!=BLR:
        raise ValueError('tail extent')
    for w in words:
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;xo=(w>>1)&1023
        if w==BLR:
            if w!=words[-1] or sp or not lr or loaded!=set(slots.values()):
                raise ValueError('tail ABI')
        elif op in (32,46) and ra==1:
            for n in range(32-rs if op==46 else 1):
                r=rs+n;off=sp+imm(w)+4*n;value=slots.get(off)
                if value is None or value in loaded or r==1 or (value!='lr' and value!=r) or (value=='lr' and r>=14):
                    raise ValueError('tail load')
                values[r]=value;loaded.add(value);loads+=1
        elif op==14 and rs==ra==1:
            if sp!=-frame or imm(w)!=frame:raise ValueError('tail stack')
            sp=0
        elif op==31 and xo==467 and spr(w)==8:
            if values[rs]!='lr' or lr:raise ValueError('tail LR')
            lr=True
        elif op==14 and rs==3 and ra==0:
            values[3]=None
        elif op==31 and xo==444 and ra==3 and rs==((w>>11)&31):
            values[3]=values[rs]
        elif w==0x60000000:
            pass
        else:
            raise ValueError('tail opcode')
    if words.count(BLR)!=1:raise ValueError('tail return count')
    return loads,sum(isinstance(v,int) for v in loaded)

def derive(d,e):
    _,body,edge,_,_,_=geometry(d,e)
    caller,caller_word,*_=outer_plan(d,e)
    if caller!=EDGES[-1][0]+4 or caller_word!=body[(caller-STM)//4]:
        raise ValueError('tail caller')
    start=(caller-STM)//4
    frame,slots=prologue(body[:start])
    loads,saved=tail(body[start:],frame,slots)
    # Caller identity is authenticated privately; the focused fixture
    # still models the OSInit bridge and must stop before its continuation.
    exact_words(d,e,edge[1],1)
    return len(body[start:]),loads,saved

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    allowed={'size','prologue frame','prologue store before frame','prologue slot','prologue duplicate register',
             'prologue identity','tail extent','tail ABI','tail load','tail stack','tail LR','tail opcode','tail return count','tail caller'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        labels,loads,saved=derive(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('STM_FINAL_RETURN_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'STM_FINAL_RETURN_GEOMETRY verified=1 labels={labels} stack_loads={loads} saved_gprs={saved} lr=1 caller=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
