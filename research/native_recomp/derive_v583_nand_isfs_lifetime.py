#!/usr/bin/env python3
"""Retain historical original V394 ISFS entry only after selected callback proof."""
import argparse,hashlib,re,struct
from pathlib import Path
from derive_v542_nand_successor_lifetime import authenticated as auth542,patch as patch542,inspect as inspect542
from derive_v551_nand_chain_lifetime import patch as patch551,one
from derive_v563_nand_cache_lifetime import patch as patch563
from derive_v573_nand_next_lifetime import patch as patch573,history as history573
from derive_v508_nand_ack_lifetime import next_guard
from derive_v478_nand_post_return import MAX_LOG,MAX_CPP,abort_row,tracked_public_source
from make_osinit_execparams_v28 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

BEGIN='  const bool v394_completed='
END='  std::cout<<"V394_NAND_ISFS_TRIAL'
LABEL='V394 original NAND reply path did not enter authentic ISFS callback'
GUARD='  check(v394_completed,\n        "'+LABEL+'");'
ISFS=re.compile(rb'V394_NAND_ISFS_ENTRY guest=1 clear=1 masked=1 registered=1 mapped=[01] selected=[01] result=[01] userdata=[01]')
SELECTED=re.compile(rb'V395_NAND_ISFS_NEXT guest=1 clear=1 masked=1 registered=1 mapped=1 selected=1 userdata=1 nand=[01]')
PRIOR=re.compile(rb'V393_NAND_NEXT_TRIAL first=1 next=1 completed=1')
TRIAL=re.compile(rb'V394_NAND_ISFS_TRIAL context=([01]) isfs=([01]) completed=([01])')
PROOF=re.compile(rb'V583_NAND_ISFS_PROOF history=([01]) legacy_stop=([01])')
NEW='''  const bool v394_completed=v393_completed&&
       nwii::runtime::v394_context_seen==1u&&nwii::runtime::v394_isfs_seen==1u&&
       nwii::runtime::v395_next_seen==1u&&
       nwii::runtime::v395_next_pc>=0x80400000u&&nwii::runtime::v395_next_pc<0x80600000u&&
       (nwii::runtime::v395_next_pc&3u)==0u&&
       nwii::runtime::v395_next_lr>=0x804f0e04u&&nwii::runtime::v395_next_lr<0x804f0f84u&&
       (nwii::runtime::v395_next_lr&3u)==0u&&
       nwii::runtime::v395_isfs_inst>nwii::runtime::v394_context_inst&&
       nwii::runtime::v396_start_inst>nwii::runtime::v395_isfs_inst&&
       nwii::runtime::v396_start_inst<=c.inst_count;
  std::cout<<"V583_NAND_ISFS_PROOF history="<<unsigned(v394_completed)
           <<" legacy_stop="<<unsigned(v583_legacy_isfs)<<std::endl;
'''
def history(raw,control=True):
    history573(raw,False)
    lines=raw.splitlines()
    a,_=one(lines,b'V394_NAND_ISFS_ENTRY ',ISFS)
    b,_=one(lines,b'V395_NAND_ISFS_NEXT ',SELECTED)
    c,_=one(lines,b'V393_NAND_NEXT_TRIAL ',PRIOR)
    d,t=one(lines,b'V394_NAND_ISFS_TRIAL ',TRIAL)
    if not a<b<c<d or t.groups()!=(b'1',b'1',b'0' if control else b'1'):raise ValueError('selected callback order')
    if not control:
        k,q=one(lines,b'V583_NAND_ISFS_PROOF ',PROOF)
        if not c<k<d or q[1]!=b'1':raise ValueError('historical trial')
    return 'V583_NAND_ISFS_HISTORY owner=1 entry=1 selected=1 userdata=1 ordered=1 boot_verified=0'
def patch(source):
    seams=(BEGIN,END,GUARD,'v395_isfs_inst=ctx.inst_count;','v396_start_inst=ctx.inst_count;')
    if 'v583_' in source or any(source.count(x)!=1 for x in seams):raise ValueError('source seam')
    a=source.index(BEGIN);b=source.index(END,a);old=source[a:b]
    if not old.endswith(';\n') or any(x not in old for x in ('v393_completed','v394_context_seen','v394_isfs_seen','c.pc==','c.lr==')):
        raise ValueError('legacy proof')
    new=old.replace(BEGIN,'  const bool v583_legacy_isfs=',1)+NEW
    out=source[:a]+new+source[b:]
    if out.replace(new,old,1)!=source or out.count(GUARD)!=1:raise ValueError('roundtrip')
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','base','control','prior','prior_log','candidate','chain','cache','next_candidate','next_log','output'):
        p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    def get(path,cap,txt=False):
        if path.stat().st_size>cap:raise ValueError('size')
        return path.read_text(encoding='utf-8') if txt else path.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000);prior=get(a.prior,24_000_000,True)
        q=auth542(owner,fixture,sizes,get(a.cpp,MAX_CPP,True),get(a.base,24_000_000,True),get(a.control,MAX_LOG),prior,get(a.prior_log,MAX_LOG))
        candidate=get(a.candidate,24_000_000,True);chain=get(a.chain,24_000_000,True);cache=get(a.cache,24_000_000,True);nxt=get(a.next_candidate,24_000_000,True)
        if candidate!=patch542(prior) or chain!=patch551(candidate) or cache!=patch563(chain) or nxt!=patch573(cache):raise ValueError('source identity')
        raw=get(a.next_log,MAX_LOG);inspect542(raw,134,owner,fixture,sizes,q)
        if not abort_row(raw,nxt,134)[1].endswith('label='+LABEL):raise ValueError('guard identity')
        print(history(raw));new=patch(nxt)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V583_NAND_ISFS_ROUTE installed=1 legacy_snapshot=1 later_guards=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('candidate identity')
            raw=get(a.run_log,MAX_LOG);history(raw,False)
            row=inspect542(raw,a.run_rc,owner,fixture,sizes,q)
            print(row.replace('V542_FRAME_RESULT','V583_FRAME_RESULT',1)+' isfs_history=1')
            host=Path(__file__).resolve().parent
            for row in next_guard(raw,a.run_rc,new,host,tracked_public_source(host)):
                print(row.replace('V517_NAND_','V583_NAND_',1))
        print('V583_NAND_ISFS_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V583_NAND_ISFS_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
