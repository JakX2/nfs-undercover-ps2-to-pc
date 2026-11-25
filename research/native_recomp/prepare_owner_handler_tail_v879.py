#!/usr/bin/env python3
"""Owner-only original SI handler slot-12 restore and original final four words."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_owner_restore_v735 import plan as restore_plan
from prepare_owner_callback_prefix_v797 import header,install
from prepare_owner_callback_after_setter_v842 import install_resume
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_pair_v753 import H,BLR

def tail_geometry(words):
    if len(words)!=4 or words[-1]!=BLR:raise ValueError('handler tail extent')
    body=words[:-1];loads=[w for w in body if w>>26==32 and (w>>21)&31==0 and (w>>16)&31==1]
    adds=[w for w in body if w>>26==14 and (w>>21)&31==1 and (w>>16)&31==1]
    moves=[w for w in body if w==0x7c0803a6]
    if len(loads)!=1 or len(adds)!=1 or len(moves)!=1 or body.index(loads[0])>body.index(moves[0]) or body.index(loads[0])>body.index(adds[0]):
        raise ValueError('handler tail shape')
    frame=adds[0]&0xffff;off=(loads[0]&0xffff)^0x8000;off-=0x8000
    if frame<16 or frame>0x300 or frame&3 or off!=frame+4:raise ValueError('handler tail frame')
    return frame,off

def plan(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    C,S,branch=edge(HANDLER,words,12)
    root,restore,base,disp=restore_plan(dol,elf)
    if S!=root:raise ValueError('handler tail target')
    i=(C-HANDLER)//4
    code=list(words[i:i+5]);frame,off=tail_geometry(code[1:])
    if code[0]!=branch or i+5>len(words):raise ValueError('handler tail target')
    roots={H:[0x4e800421,0x60000000,BLR],C:code,S:restore}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=3 or any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('handler tail overlap')
    return (roots,C,S,C,base,disp),frame,off

def write_header(q,out):
    p,frame,off=q;header(p,out)
    with out.open('a') as f:
        f.write(f'inline constexpr unsigned FrameSize={frame}u,LinkOffset={off}u;\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q[0],a.output,indirect_caller=True);install_resume(a.output)
        elif a.patch_analyzer:patch_analyzer(q[0],a.output)
        else:
            write_header(q,a.output);print('V879_HANDLER_TAIL_GEOMETRY verified=1 restore_gprs=15 tail_words=4 frame=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('handler tail extent','handler tail shape','handler tail frame','handler tail target','handler tail overlap','native coverage','native owner','hook identity','hook include','hook coverage','private output','dispatch caller owner','dispatch resume label','resume dispatcher identity','outer dispatcher extent','local resume dispatcher identity')
        print('V879_HANDLER_TAIL_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
