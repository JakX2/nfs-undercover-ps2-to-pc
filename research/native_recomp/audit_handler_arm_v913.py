#!/usr/bin/env python3
"""Private post-branch load provenance; never emit guest addresses or register indices."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_status_w1c_v908 import plan,branch_seeds,channel_register
from audit_handler_path_v887 import step,classify,signed
from audit_handler_index_v902 import inputs
from audit_handler_suffix_v728 import target
from prepare_owner_packet_choice_v881 import writable_spans

def ea(w,r):
    op=w>>26;ra=(w>>16)&31;rb=(w>>11)&31
    a=r[ra] if ra else 0
    b=r[rb] if op==31 else signed(w)
    return None if a is None or b is None else (a+b)&0xffffffff

def location(a,spans):
    if a is None:return 'unknown'
    if 0x80000000<=a<0x81800000:
        return 'data' if any(lo<=a and a+4<=hi for lo,hi in spans) else 'mem1'
    p=(a&0x3fffffff)&~0x00800000
    if 0x0d006400<=p<0x0d006500:
        return {0x30:'si_poll',0x34:'si_control',0x38:'si_status'}.get(p-0x0d006400,'si_other')
    return 'other'

def arm_address(code,ch,table_value,seed,override=None):
    selector=channel_register(code);r=inputs(code,(selector,ch),0x08080808,seed,*(override or (None,0)))
    rr=list(r);rr[(code[11]>>21)&31]=table_value;r=tuple(rr)
    for i,w in enumerate(code[14:19],14):
        if classify(w,r)[0]=='load':return i,w,ea(w,r)
        r=step(w,r)
    raise ValueError('arm load absent')

def inspect(dol,elf):
    root,code,_,_=plan(dol,elf);spans=writable_spans(dol,elf)
    seed=branch_seeds(code)[0];sel=channel_register(code)
    i,w,a=arm_address(code,0,seed,0x13579bdf)
    print(f'V913_ARM_LOAD visit={i+1} opcode={w>>26} region={location(a,spans)} aligned={int(a is not None and a%4==0)}')
    static=[arm_address(code,ch,seed,s)[2] for s in (0,0x13579bdf) for ch in range(4)]
    print(f'V913_ARM_STATIC invariant={int(static[:4]==static[4:])} region={location(static[0],spans)}')
    for reg in range(32):
        if reg==sel:continue
        one=arm_address(code,0,seed,0x13579bdf,(reg,0x80090000))[2]
        two=arm_address(code,0,seed,0x13579bdf,(reg,0x800a0000))[2]
        if one is not None and two is not None and (two-one)&0xffffffff==0x10000:
            print(f'V913_ARM_INPUT class={"stack" if reg==1 else "sda" if reg in (2,13) else "nonvolatile" if reg>=14 else "volatile"} region={location(one,spans)} aligned={int(one%4==0)}')
    # Check whether the indexed table value itself is consumed as a pointer.
    one=arm_address(code,0,0x80090000,0x13579bdf)[2]
    two=arm_address(code,0,0x800a0000,0x13579bdf)[2]
    print(f'V913_ARM_TABLE_VALUE pointer={int(one is not None and two is not None and (two-one)&0xffffffff==0x10000)} region={location(one,spans)}')
    print('V913_ARM_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V913_ARM_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
