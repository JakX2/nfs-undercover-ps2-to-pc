#!/usr/bin/env python3
"""Owner-only branch path census for the V876 sixth-visit refusal."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_suffix_v728 import target

def signed(w):return ((w&0xffff)^0x8000)-0x8000
def classify(w,regs):
    op=w>>26;xo=(w>>1)&1023;ra=(w>>16)&31;rb=(w>>11)&31
    base=regs[ra] if ra else 0
    kind='integer';addr=None
    if 32<=op<=47:
        kind='store' if op in (36,37,38,39,44,45,47) else 'load'
        if base is not None:addr=(base+signed(w))&0xffffffff
    elif op==31 and xo in (23,55,534,87,119,279,311,343,375,790,151,183,215,247,407,439,662,918):
        kind='store' if xo in (151,183,215,247,407,439,662,918) else 'load'
        if base is not None and regs[rb] is not None:addr=(base+regs[rb])&0xffffffff
    elif op==31 and xo in (20,150,533,597,661,725,535,567,599,631,663,695,727,759,983,54,86,246,278,470,982,1014):kind='unsupported_x'
    elif op>=48 or op==4:kind='unsupported_fp'
    elif op in (16,18):kind='branch'
    region='unknown'
    if addr is not None:
        phys=(addr&0x3fffffff)&~0x00800000
        region='si' if 0x0d006400<=phys<0x0d006500 else 'mem1' if 0x80000000<=addr<0x81800000 else 'other'
    return kind,region,ra in (1,2,13),op

def rotate(value,sh,mb,me):
    mask=sum(1<<(31-i) for i in range(32) if (mb<=i<=me if mb<=me else i>=mb or i<=me))
    return ((value<<sh)|(value>>(32-sh)))&mask&0xffffffff

def step(w,regs):
    op=w>>26;rd=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023
    r=list(regs);base=regs[ra] if ra else 0
    if op in (14,15):r[rd]=None if base is None else (base+(signed(w)<<(16 if op==15 else 0)))&0xffffffff
    elif op in (24,25):r[ra]=None if regs[rd] is None else regs[rd]|((w&0xffff)<<(16 if op==25 else 0))
    elif op==21:r[ra]=None if regs[rd] is None else rotate(regs[rd],rb,(w>>6)&31,(w>>1)&31)
    elif op==31 and xo in (444,28,316):
        x,y=regs[rd],regs[rb];r[ra]=None if x is None or y is None else x|y if xo==444 else x&y if xo==28 else x^y
    elif op==31 and xo in (266,40):
        x,y=regs[ra],regs[rb];r[rd]=None if x is None or y is None else (x+y if xo==266 else y-x)&0xffffffff
    elif op==31 and xo==24:
        x,y=regs[rd],regs[rb];r[ra]=None if x is None or y is None else 0 if y&32 else (x<<(y&31))&0xffffffff
    elif op==31 and xo==792:
        x,y=regs[rd],regs[rb]
        signed_x=None if x is None else (x^0x80000000)-0x80000000
        r[ra]=None if x is None or y is None else (signed_x>>min(y&63,31))&0xffffffff
    elif op==31 and xo==824:
        x=regs[rd]
        r[ra]=None if x is None else (((x^0x80000000)-0x80000000)>>rb)&0xffffffff
    elif op in (10,11,16,18,36,38,44):pass
    elif op in (32,34,40,42):r[rd]=None
    else:r=[None]*32
    return tuple(r)

def unique_prefix(rows,start):
    # The owner census shows a straight-line six-label sequence.
    words=[rows[start+4*i][0] for i in range(6)]
    if any(rows[start+4*i][1:]!=(0,0) or w>>26 in (16,18,19) for i,w in enumerate(words)) or words[-1]>>26!=32:
        raise ValueError('prefix shape')
    regs=(None,)*32
    for w in words[:-1]:regs=step(w,regs)
    base=(words[-1]>>16)&31
    # Only export classes, not the original register number or guest address.
    producers=[]
    for i,w in enumerate(words[:-1],1):
        op=w>>26;xo=(w>>1)&1023;rd=(w>>21)&31;ra=(w>>16)&31
        dst=ra if op in (21,24,25) or op==31 and xo in (444,28,316,24,792,824) else rd
        if dst==base:producers.append(i)
    # Try a range of bounded low-valued initial-state inputs to classify
    # a channel-indexed effective address, without asserting it was live.
    classes=set()
    for value in range(4):
        r=(value,)*32
        for w in words[:-1]:r=step(w,r)
        classes.add(classify(words[-1],r)[1])
    region=classify(words[-1],regs)[1]
    if regs[base] is not None:
        addr=(regs[base]+signed(words[-1]))&0xffffffff
        physical=(addr&0x3fffffff)&~0x00800000
        if 0x0d006400<=physical<0x0d006500:
            off=physical-0x0d006400
            region='si_control' if off==0x34 else 'si_status' if off==0x38 else 'si_poll' if off==0x30 else 'si_buffer' if 0x80<=off<0x100 else 'si_other'
        elif 0x80000000<=addr<0x81800000:region='mem1_cached'
        elif 0xc0000000<=addr<0xc1800000:region='mem1_uncached'
    return region,','.join(map(str,producers)) or 'none',','.join(sorted(classes)),(words[4]>>1)&1023

def paths(rows,start,depth=6):
    work=[(start,0,(None,)*32)];out=set()
    while work:
        pc,i,regs=work.pop()
        if pc not in rows:raise ValueError('path extent')
        w,o,k=rows[pc];op=w>>26
        if i+1==depth:
            out.add(classify(w,regs));continue
        if k:continue
        r=step(w,regs)
        if op in (16,18):
            dst=target(pc,w)
            if dst<=pc:raise ValueError('backward path')
            work.append((dst,i+1,r))
            if op==18:continue
        work.append((pc+4,i+1,r))
        if len(work)>128:raise ValueError('path count')
    return sorted(out)

def inspect(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    for depth in range(1,9):
        for k,region,base,op in paths(rows,start,depth):
            print(f'V887_HANDLER_PATH visit={depth} class={k} region={region} special_base={int(base)} opcode_class={op}')
    known,producers,trial,arithmetic=unique_prefix(rows,start)
    print(f'V888_HANDLER_LOAD static_region={known} base_producers={producers} bounded_input_regions={trial} arithmetic_class={arithmetic} execution=0')
    print('V887_HANDLER_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):print('V887_HANDLER_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
