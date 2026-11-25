#!/usr/bin/env python3
"""Private SITransfer native continuation through its first OSDisableInterrupts."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_owner_transfer_prefix_v872 import plan as prefix_plan
from prepare_owner_callback_prefix_v797 import header,install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_v667_si_dispatch import exact
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_owner_pair_v753 import BLR

def continuation(root,code,resume,D):
    i=(resume-root)//4
    if not root<=resume<root+4*len(code) or resume&3:raise ValueError('transfer resume')
    for j in range(i,min(i+32,len(code)-1)):
        w=code[j];pc=root+4*j;op=w>>26;xo=(w>>1)&1023
        if op==18 and w&3==1:
            if direct_bl(w,pc)!=D:raise ValueError('transfer disable target')
            # The resume itself is observed but not executed.
            if code[j+1]>>26 in (16,17,18,19) or code[j+1]>>26==31 and (code[j+1]>>1)&1023==146:
                raise ValueError('transfer disable resume')
            return pc,list(code[i:j+1]),code[j+1]
        if op in (16,17,18,19) or op==31 and xo==146:
            raise ValueError('transfer prefix control')
    raise ValueError('transfer disable missing')

def plan(dol,elf):
    q=prefix_plan(dol,elf);roots,C,S,site,sb,disp=q
    d,*_=leaf_plan(dol,elf);D=d[1]
    code=exact(dol,elf,C,91)
    ds,words,after=continuation(C,code,site+4,D)
    roots[C]=list(code[:(ds-C)//4+2])+[BLR]
    roots[D]=list(d[5])
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=4 or any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('transfer disable overlap')
    return q,D,ds,words,after

def write_header(p,out):
    q,D,ds,words,after=p
    header(q,out);roots,C,S,site,_,_=q
    fmt=lambda w:f'0x{w:08x}u'
    with out.open('a') as f:
        f.write(f'inline constexpr uint32_t D={fmt(D)},DisableCall={fmt(ds)},DisableResume={fmt(ds+4)},DisableResumeWord={fmt(after)};\n')
        f.write(f'inline constexpr std::array<uint32_t,{len(roots[D])}> disable_words{{'+','.join(map(fmt,roots[D]))+'};\n')
        f.write(f'inline constexpr std::array<uint32_t,{len(words)}> after_save_words{{'+','.join(map(fmt,words))+'};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());base,D,ds,words,_=q
        if a.install:install(base,a.output,extra_links=((base[1],ds,D),))
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            write_header(q,a.output);print(f'V874_TRANSFER_DISABLE_GEOMETRY verified=1 continuation={len(words)} disable_words=5 original_execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('transfer resume','transfer disable target','transfer disable resume','transfer prefix control','transfer disable missing','transfer disable overlap','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V874_TRANSFER_DISABLE_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
