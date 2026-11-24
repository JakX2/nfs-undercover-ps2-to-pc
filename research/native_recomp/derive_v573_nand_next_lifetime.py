#!/usr/bin/env python3
"""Preserve historical original V393 context-call proof, if independently observed."""
import argparse,hashlib,re,struct
from pathlib import Path
from derive_v542_nand_successor_lifetime import authenticated as auth542,patch as patch542,inspect as inspect542
from derive_v551_nand_chain_lifetime import patch as patch551,one
from derive_v563_nand_cache_lifetime import patch as patch563,event_history as history563,PROOF as PROOF563
from derive_v508_nand_ack_lifetime import next_guard
from derive_v478_nand_post_return import MAX_LOG,MAX_CPP,abort_row,tracked_public_source
from make_osinit_execparams_v28 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

BEGIN='  const bool v393_completed='
END='  std::cout<<"V393_NAND_NEXT_TRIAL'
LABEL='V393 original non-cache NAND callee did not reach next guest function'
GUARD='  check(v393_completed,\n        "'+LABEL+'");'
NEXT=re.compile(rb'V393_NAND_NEXT_CALL guest=1 clear=1 registered=1 masked=1 reply=1 clearctx=0 setctx=1 cache=0 isfs=0')
ISFS=re.compile(rb'V394_NAND_ISFS_ENTRY guest=1 clear=1 masked=1 registered=1 mapped=[01] selected=[01] result=[01] userdata=[01]')
TRIAL=re.compile(rb'V393_NAND_NEXT_TRIAL first=([01]) next=([01]) completed=([01])')
PROOF=re.compile(rb'V573_NAND_NEXT_PROOF history=([01]) legacy_stop=([01])')
NEW='''  const bool v393_completed=v392_completed&&
       nwii::runtime::v392_kind==1u&&nwii::runtime::v393_next_seen==1u&&
       nwii::runtime::v393_next_pc==0x805228ccu&&nwii::runtime::v393_next_lr==0x80519298u&&
       nwii::runtime::v394_context_seen==1u&&nwii::runtime::v394_isfs_seen==1u&&
       nwii::runtime::v394_context_inst>nwii::runtime::v393_start_inst&&
       nwii::runtime::v395_isfs_inst>nwii::runtime::v394_context_inst&&
       nwii::runtime::v395_isfs_inst<=c.inst_count;
  std::cout<<"V573_NAND_NEXT_PROOF history="<<unsigned(v393_completed)
           <<" legacy_stop="<<unsigned(v573_legacy_next)<<std::endl;
'''
def history(raw,control=True):
    history563(raw,False)
    lines=raw.splitlines()
    a=next(i for i,l in enumerate(lines) if l.startswith(b'V392_NAND_POST_CACHE_EVENT '))
    b,_=one(lines,b'V393_NAND_NEXT_CALL ',NEXT)
    c,_=one(lines,b'V394_NAND_ISFS_ENTRY ',ISFS)
    d,p=one(lines,b'V563_NAND_CACHE_TRIAL ',PROOF563)
    e,t=one(lines,b'V393_NAND_NEXT_TRIAL ',TRIAL)
    if not a<b<c<d<e or p[1]!=b'1' or t.groups()!=(b'1',b'1',b'0' if control else b'1'):
        raise ValueError('historical call order')
    if not control:
        k,q=one(lines,b'V573_NAND_NEXT_PROOF ',PROOF)
        if not d<k<e or q[1]!=b'1':raise ValueError('historical trial')
    return 'V573_NAND_NEXT_HISTORY owner=1 context=1 isfs_entry=1 ordered=1 boot_verified=0'

def patch(source):
    seams=(BEGIN,END,GUARD,'v394_context_inst=ctx.inst_count;','v395_isfs_inst=ctx.inst_count;')
    if 'v573_' in source or any(source.count(x)!=1 for x in seams):
        raise ValueError('source seam')
    a=source.index(BEGIN);b=source.index(END,a);old=source[a:b]
    if not old.endswith(';\n') or any(x not in old for x in ('v392_completed','v393_next_seen','v393_next_pc','v393_next_lr','c.pc==','c.lr==')):
        raise ValueError('legacy proof')
    new=old.replace(BEGIN,'  const bool v573_legacy_next=',1)+NEW
    out=source[:a]+new+source[b:]
    if out.replace(new,old,1)!=source or out.count(GUARD)!=1:raise ValueError('roundtrip')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','base','control','prior','prior_log','candidate','chain','cache','cache_log','output'):
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
        candidate=get(a.candidate,24_000_000,True);chain=get(a.chain,24_000_000,True);cache=get(a.cache,24_000_000,True)
        if candidate!=patch542(prior) or chain!=patch551(candidate) or cache!=patch563(chain):raise ValueError('source identity')
        raw=get(a.cache_log,MAX_LOG)
        inspect542(raw,134,owner,fixture,sizes,q)
        if not abort_row(raw,cache,134)[1].endswith('label='+LABEL):raise ValueError('guard identity')
        print(history(raw));new=patch(cache)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V573_NAND_NEXT_ROUTE installed=1 legacy_snapshot=1 later_guards=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('candidate identity')
            raw=get(a.run_log,MAX_LOG);history(raw,False)
            row=inspect542(raw,a.run_rc,owner,fixture,sizes,q)
            print(row.replace('V542_FRAME_RESULT','V573_FRAME_RESULT',1)+' next_history=1')
            host=Path(__file__).resolve().parent
            for row in next_guard(raw,a.run_rc,new,host,tracked_public_source(host)):
                print(row.replace('V517_NAND_','V573_NAND_',1))
        print('V573_NAND_NEXT_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError):
        print('V573_NAND_NEXT_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
