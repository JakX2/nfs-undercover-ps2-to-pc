#!/usr/bin/env python3
"""Preserve selected ISFS callback evidence only after exact native BLR/resume proof."""
import argparse,hashlib,re,struct
from pathlib import Path
from derive_v542_nand_successor_lifetime import authenticated as auth542,patch as patch542,inspect as inspect542
from derive_v551_nand_chain_lifetime import patch as patch551,one
from derive_v563_nand_cache_lifetime import patch as patch563
from derive_v573_nand_next_lifetime import patch as patch573
from derive_v583_nand_isfs_lifetime import patch as patch583,history as history583,SELECTED,TRIAL as PRIOR
from derive_v508_nand_ack_lifetime import next_guard
from derive_v478_nand_post_return import MAX_LOG,MAX_CPP,abort_row,tracked_public_source,trace
from derive_v437_nand_restored_frame import BEGIN as FRAME,BLR,RESUME
from audit_v414_nand_resumed_coverage import classify
from repair_v424_nand_aot_placeholder import aot_entry
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
BEGIN='  const bool v395_completed='
END='  std::cout<<"V395_NAND_ISFS_TRIAL'
LABEL='V395 original NAND _isfsFuncCb did not reach its next guest call'
GUARD='  check(v395_completed,\n        "'+LABEL+'");'
TRIAL=re.compile(rb'V395_NAND_ISFS_TRIAL isfs=([01]) next=([01]) completed=([01])')
PROOF=re.compile(rb'V605_NAND_SELECTED_PROOF history=([01]) legacy_stop=([01])')
FRAME_RESULT='V542_FRAME_RESULT rc=134 begins=1 blr=1 resume=1 nested=2 max_calls=44 unique=25 original=25 first_nonoriginal=none boot_verified=0 history=1 final_clear=0 successor=1 legacy_stop=0'
def history(raw,control=True):
    history583(raw,False)
    lines=raw.splitlines()
    a,_=one(lines,b'V395_NAND_ISFS_NEXT ',SELECTED)
    f,_=one(lines,b'V437_FRAME_BEGIN ',re.compile(re.escape(FRAME)))
    g,_=one(lines,b'V437_FRAME_BLR ',re.compile(re.escape(BLR)))
    h,_=one(lines,b'V437_FRAME_RESUME ',re.compile(re.escape(RESUME)))
    j,_=one(lines,b'V394_NAND_ISFS_TRIAL ',PRIOR)
    k,t=one(lines,b'V395_NAND_ISFS_TRIAL ',TRIAL)
    first=[i for i,l in enumerate(lines) if l.startswith(b'V420_CB_ENTRY call=0 ')]
    e=trace(raw)
    if len(first)!=1 or not e or not a<f<first[0]<g<h<j<k or t.groups()!=(b'1',b'1',b'0' if control else b'1'):
        raise ValueError('selected return order')
    if not control:
        n,p=one(lines,b'V605_NAND_SELECTED_PROOF ',PROOF)
        if not j<n<k or p[1]!=b'1':raise ValueError('historical selected trial')
    _,pc,lr,ew,lw,em,lm,resumed,_,_=e[0]
    if not em or not lm or resumed or not 0x80400000<=pc<0x80600000 or not 0x804f0e04<=lr<0x804f0f84:raise ValueError('selected trace geometry')
    return pc,lr,ew,lw
def authenticate(raw,owner,fixture,sizes,cpp,control=True,reader=text_at):
    pc,lr,ew,lw=history(raw,control)
    if classify(owner,fixture,sizes,pc,reader)[0]!='original' or aot_entry(cpp,pc)!=(1,1):raise ValueError('selected original root')
    caller=0x804f0e04
    n=sizes.get(caller,0)
    if not 4<=n<=4096 or lr-4<caller or lr>caller+n:raise ValueError('ISFS extent')
    for addr,w in ((pc,ew),(lr-4,lw)):
        data=struct.pack('>I',w)
        if reader(owner,addr,4)!=data or reader(fixture,addr,4)!=data:raise ValueError('selected live word')
    # An authenticated bctrl (indirect call) or exact relative BL. No
    # arbitrary address-range-only classification of the selected caller.
    direct=lw>>26==18 and lw&3==1
    disp=lw&0x03fffffc
    if disp&0x02000000:disp-=0x04000000
    indirect=lw>>26==19 and ((lw>>1)&1023)==528 and lw&1
    if not (indirect or direct and (lr-4+disp)&0xffffffff==pc):raise ValueError('selected link')
    return pc,lr
def patch(source,pc,lr):
    if pc&3 or lr&3 or not 0x80400000<=pc<0x80600000 or not 0x804f0e04<=lr<0x804f0f84:raise ValueError('selected geometry')
    seams=(BEGIN,END,GUARD,'V583_NAND_ISFS_PROOF history=','v396_start_inst=ctx.inst_count;','V437_FRAME_RESUME valid=1')
    if 'v605_' in source or any(source.count(x)!=1 for x in seams):raise ValueError('source seam')
    a=source.index(BEGIN);b=source.index(END,a);old=source[a:b]
    if not old.endswith(';\n') or any(x not in old for x in ('v394_completed','v395_next_seen','v395_next_pc','v395_next_lr','c.pc==','c.lr==')):raise ValueError('legacy proof')
    new=old.replace(BEGIN,'  const bool v605_legacy_selected=',1)+f'''  const bool v395_completed=v394_completed&&
       nwii::runtime::v395_next_seen==1u&&
       nwii::runtime::v395_next_pc==0x{pc:08x}u&&
       nwii::runtime::v395_next_lr==0x{lr:08x}u&&
       nwii::runtime::v437_frame.stage()==3u&&
       nwii::runtime::v396_start_inst>nwii::runtime::v395_isfs_inst&&
       nwii::runtime::v396_start_inst<=c.inst_count;
  std::cout<<"V605_NAND_SELECTED_PROOF history="<<unsigned(v395_completed)
           <<" legacy_stop="<<unsigned(v605_legacy_selected)<<std::endl;
'''
    out=source[:a]+new+source[b:]
    if out.replace(new,old,1)!=source or out.count(GUARD)!=1:raise ValueError('roundtrip')
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','base','control','prior','prior_log','candidate','chain','cache','next_candidate','isfs_candidate','isfs_log','output'):
        p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    def get(path,cap,txt=False):
        if path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if txt else path.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000);prior=get(a.prior,24_000_000,True);cpp=get(a.cpp,MAX_CPP,True)
        q=auth542(owner,fixture,sizes,cpp,get(a.base,24_000_000,True),get(a.control,MAX_LOG),prior,get(a.prior_log,MAX_LOG))
        candidate=get(a.candidate,24_000_000,True);chain=get(a.chain,24_000_000,True);cache=get(a.cache,24_000_000,True);nxt=get(a.next_candidate,24_000_000,True);isfs=get(a.isfs_candidate,24_000_000,True)
        if candidate!=patch542(prior) or chain!=patch551(candidate) or cache!=patch563(chain) or nxt!=patch573(cache) or isfs!=patch583(nxt):raise ValueError('source identity')
        raw=get(a.isfs_log,MAX_LOG)
        if inspect542(raw,134,owner,fixture,sizes,q)!=FRAME_RESULT or not abort_row(raw,isfs,134)[1].endswith('label='+LABEL):raise ValueError('guard identity')
        pc,lr=authenticate(raw,owner,fixture,sizes,cpp)
        print('V605_NAND_SELECTED_HISTORY owner=1 selected=1 original_link=1 blr=1 resume=1 ordered=1 boot_verified=0')
        new=patch(isfs,pc,lr)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V605_NAND_SELECTED_ROUTE installed=1 legacy_snapshot=1 later_guards=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('candidate identity')
            raw=get(a.run_log,MAX_LOG)
            if authenticate(raw,owner,fixture,sizes,cpp,False)!=(pc,lr):raise ValueError('selected replay identity')
            row=inspect542(raw,a.run_rc,owner,fixture,sizes,q)
            print(row.replace('V542_FRAME_RESULT','V605_FRAME_RESULT',1)+' selected_history=1')
            host=Path(__file__).resolve().parent
            for row in next_guard(raw,a.run_rc,new,host,tracked_public_source(host)):print(row.replace('V517_NAND_','V605_NAND_',1))
        print('V605_NAND_SELECTED_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V605_NAND_SELECTED_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
