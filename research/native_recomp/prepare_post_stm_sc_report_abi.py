#!/usr/bin/env python3
"""Prove the original variadic report's actual stack argument construction."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_report import report_trace,REPORT
from prepare_post_stm_sc_version import plan as version_plan
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_stm_final_return import spr

def model(root,words,*,details=False):
    rows,path,slots,fp,frame,dst=report_trace(root,words)
    if fp:raise ValueError('SC report FP path')
    # Symbolic values: incoming register, stack-relative address,
    # incoming LR or known 32-bit constant. No original data exported.
    gp=[('reg',i) for i in range(32)];gp[1]=('stack',0)
    mem={}
    def write(at,n,v):
        if n not in (1,2,4) or at%min(n,4) or at< -frame or at+n>8:
            raise ValueError('SC report ABI range')
        if any(at+i in mem for i in range(n)):raise ValueError('SC report ABI duplicate')
        for i in range(n):
            mem[at+i]=('byte',v[1]>>(8*(n-1-i))&255) if v[0]=='const' else ('part',v,n,i)
    def read(at,n):
        bits=tuple(mem.get(at+i) for i in range(n))
        if all(x is not None and x[0]=='byte' for x in bits):
            v=0
            for x in bits:v=(v<<8)|x[1]
            return ('const',v)
        if all(x is not None and x[0]=='part' and x[1]==bits[0][1] and x[2:]==(n,i) for i,x in enumerate(bits)):
            return bits[0][1]
        return None
    def add(v,n):
        if v[0]=='const':return ('const',(v[1]+n)&0xffffffff)
        if v[0]=='stack':return ('stack',v[1]+n)
        if not n:return v
        raise ValueError('SC report ABI arithmetic')
    for ordinal,pc in enumerate(path,1):
        w=rows[pc];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000
        if pc==path[-1]:
            if direct_bl(w,pc)!=dst:raise ValueError('SC report ABI call')
            break
        if op==37 and rs==ra==1:
            if gp[1]!=('stack',0) or imm!=-frame:raise ValueError('SC report ABI frame')
            write(imm,4,gp[1]);gp[1]=('stack',imm)
        elif op in (36,38,44,47) and ra==1:
            at=gp[1][1]+imm
            if op==47:
                for i in range(rs,32):write(at+4*(i-rs),4,gp[i])
            else:write(at,{36:4,38:1,44:2}[op],gp[rs])
        elif op==31 and xo==339 and spr(w)==8 and rs!=1:
            gp[rs]=('lr',0)
        elif op in (14,15) and rs!=1:
            gp[rs]=add(gp[ra] if ra else ('const',0),imm<<(16 if op==15 else 0))
        elif op in (24,25) and ra!=1:
            v=gp[rs];n=(w&0xffff)<<(16 if op==25 else 0)
            if v[0]!='const' and n:raise ValueError('SC report ABI arithmetic')
            gp[ra]=('const',v[1]|n) if v[0]=='const' else v
        elif op==31 and xo==444 and rs==rb and not w&1 and ra!=1:
            gp[ra]=gp[rs]
        elif op in (16,18) and not w&3:pass
        else:
            kind='integer' if op in (10,11,14,15,20,21,24,25,31) else 'other'
            raise ValueError(f'SC report ABI opcode {kind} {ordinal}')
    if gp[1]!=('stack',-frame) or read(-frame,4)!=('stack',0) or read(4,4)!=('lr',0):
        raise ValueError('SC report ABI frame')
    if gp[3]!=('reg',3) or gp[4][0]!='stack':
        raise ValueError('SC report ABI arguments')
    va=gp[4][1]
    if not -frame+4<=va<=-12 or va&3:raise ValueError('SC report ABI va list')
    if read(va,4)!=('const',0x01000000):raise ValueError('SC report ABI cursor')
    overflow=read(va+4,4);save=read(va+8,4)
    if overflow!=('stack',8) or save is None or save[0]!='stack':
        raise ValueError('SC report ABI pointers')
    start=save[1]
    if not -frame+4<=start<=-32 or start&3:raise ValueError('SC report ABI save area')
    if any(read(start+4*i,4)!=('reg',3+i) for i in range(8)):
        raise ValueError('SC report ABI register save')
    if details:
        return tuple(gp),{at:read(at,4) for at in range(-frame,8,4) if read(at,4) is not None}
    return len(path),len(slots),8,frame,dst

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC report FP path','SC report ABI range','SC report ABI duplicate','SC report ABI arithmetic','SC report ABI call',
          'SC report ABI frame','SC report ABI arguments','SC report ABI va list','SC report ABI cursor','SC report ABI pointers',
          'SC report ABI save area','SC report ABI register save','SC report extent'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();version_plan(d,e)
        n=parse_functions(e).get(REPORT,0)
        if not 16<=n<=4096 or n%4:raise ValueError('SC report extent')
        labels,stores,regs,frame,dst=model(REPORT,exact_words(d,e,REPORT,n//4))
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('SC report ABI opcode '):
            _,_,_,_,kind,ordinal=reason.split()
            if kind in ('integer','other') and ordinal.isdecimal() and 1<=int(ordinal)<=128:
                print(f'POST_STM_SC_REPORT_ABI verified=0 reason=opcode category={kind} ordinal={ordinal}')
                return 1
        print('POST_STM_SC_REPORT_ABI verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_ABI verified=1 labels={labels} stack_store_sites={stores} gpr_saves={regs} frame_bytes={frame} va_cursor=1 overflow_pointer=1 register_save_pointer=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
