#!/usr/bin/env python3
"""Private original resumed SI handler prefix, through exact status load."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_path_v887 import unique_prefix,step
from audit_handler_frontier_v896 import paths
from audit_handler_index_v902 import classify_index
from prepare_owner_packet_choice_v881 import writable_spans
from prepare_owner_restore_v735 import H,BLR,caller,header,install
from prepare_owner_cancel_v754 import patch_analyzer

def plan(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    if unique_prefix(rows,start)[0]!='si_status':raise ValueError('status identity')
    code=[rows[start+4*i][0] for i in range(12)]
    if [w>>26 for w in code[:10]] != [15,15,21,15,31,32,21,14,31,36] or (code[4]>>1)&1023!=792:raise ValueError('status prefix shape')
    if paths(rows,start,10)!=[('store','si_status',36)] or any(rows[start+4*i][1:]!=(0,0) for i in range(12)):raise ValueError('status store identity')
    if code[-1]>>26!=31 or (code[-1]>>1)&1023!=23:raise ValueError('indexed load identity')
    return start,code+[BLR],0,0

def status_mask(code,seed,status):
    # Independent public PPC integer semantics, actual private words.
    r=tuple(seed)
    for i,w in enumerate(code[:9]):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        if i==5:
            if op!=32:raise ValueError('load identity')
            out=list(r);out[rs]=status;r=tuple(out)
        elif op==31 and xo in (60,536):
            out=list(r)
            x,y=r[rs],r[rb]
            out[ra]=None if x is None or y is None else (x&~y)&0xffffffff if xo==60 else 0 if y&32 else x>>(y&31)
            r=tuple(out)
        else:r=step(w,r)
    return r[(code[9]>>21)&31]

def channel_register(code):
    # Authenticate one nonvolatile input as the channel selector; do not
    # expose the original register number in public logs. Check varied
    # status patterns AND unrelated register values.
    hits=[]
    statuses=(0,0x0f0f0f0f,0x08080808,0x01020408,0xffffffff)
    for reg in range(14,32):
        good=True
        for seed in (0,0x13579bdf):
            for ch in range(4):
                regs=[seed^((i*0x1234567)&0xffffffff) if seed else 0 for i in range(32)]
                regs[reg]=ch
                for status in statuses:
                    expected=status&(0x0f<<((3-ch)*8))
                    if status_mask(code,regs,status)!=expected:good=False;break
                if not good:break
            if not good:break
        if good:hits.append(reg)
    if len(hits)!=1:raise ValueError('channel selector identity')
    return hits[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());root,code,_,_=q
        channel=channel_register(code)
        candidates=classify_index(code[:-1])
        if len(candidates)!=1 or candidates[0][0] is not None or candidates[0][2]!=4:raise ValueError('indexed table provenance')
        addresses=candidates[0][1];spans=writable_spans(a.dol.read_bytes(),a.elf.read_bytes())
        if any(a&3 or sum(lo<=a and a+4<=hi for lo,hi in spans)!=1 for a in addresses):raise ValueError('indexed table extent')
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(({H:caller(root),root:code},),a.output)
        else:
            header(q,a.output)
            with a.output.open('a') as f:
                f.write(f'inline constexpr unsigned StatusChannelRegister={channel}u;\n')
                f.write('inline constexpr std::array<uint32_t,4> ChannelTable{'+','.join(f'0x{a:08x}u' for a in addresses)+'};\n')
            print('V904_STATUS_GEOMETRY verified=1 prefix=5 original_load=1 original_store=1 synthetic_stop=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('indexed table provenance','indexed table extent','indexed load identity','channel selector identity','load identity','status store identity','status identity','status prefix shape','native coverage','caller owner','hook identity','include','hook coverage','private output')
        print('V904_STATUS_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
