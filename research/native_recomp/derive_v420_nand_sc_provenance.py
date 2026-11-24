#!/usr/bin/env python3
"""Capture actual callback lineage and live code words without changing the guest.
Only the private owner log contains PCs, LR and instruction words.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from derive_v413_nand_context_resume import HEAD
from derive_v416_nand_wait_state import NEW

SELECT='      v396_start_inst=ctx.inst_count;'
CALL='    ++v396_calls;'
HELPER=r'''// V420: read-only entry and caller-word witness, including the selected callback.
static void v420_entry(CPUContext& ctx,uint32_t addr,unsigned call,bool resumed){
  const uint32_t r13=ctx.gpr[13];
  const bool sda=(r13>=0x80000000u+3176u&&r13<0x81800000u)||
                 (r13>=0x90000000u+3176u&&r13<0x94000000u);
  const unsigned raw=sda&&ctx.mmu.get_ptr(r13-3176u)!=nullptr?
                     ctx.mmu.read8(r13-3176u):256u;
  const unsigned sc=raw<=3u?raw:(raw==256u?5u:4u);
  const auto mapped_word=[&](uint32_t a){
    return (a&3u)==0u&&a>=0x80000000u&&a<=0x817ffffcu&&
           ctx.mmu.get_ptr(a)!=nullptr&&ctx.mmu.get_ptr(a+3u)!=nullptr;
  };
  const bool ep=mapped_word(addr);
  const bool lp=ctx.lr>=4u&&mapped_word(ctx.lr-4u);
  const uint32_t ew=ep?ctx.mmu.read32(addr):0u;
  const uint32_t lw=lp?ctx.mmu.read32(ctx.lr-4u):0u;
  const unsigned result=ctx.gpr[3]==0u?0u:((ctx.gpr[3]&0x80000000u)?2u:1u);
  std::cout<<"V420_CB_ENTRY call="<<call<<" pc="<<std::hex<<addr
           <<" lr="<<ctx.lr<<" ew="<<ew<<" lw="<<lw<<std::dec
           <<" em="<<unsigned(ep)<<" lm="<<unsigned(lp)
           <<" resumed="<<unsigned(resumed)<<" sc="<<sc<<" r3="<<result<<std::endl;
}
'''
PAIRS=((HEAD,HELPER+HEAD),(SELECT,SELECT+'\n      v420_entry(ctx,addr,0u,false);'),
       (CALL,CALL+'\n    v420_entry(ctx,addr,v396_calls,v413_context.restored()&&v413_context.interrupted==1u);'))

def patch(source:str)->str:
    if 'V420_CB_ENTRY' in source or 'v420_entry' in source or source.count(NEW)!=1 or any(source.count(a)!=1 for a,_ in PAIRS):raise ValueError('geometry')
    out=source
    for old,new in PAIRS:out=out.replace(old,new,1)
    back=out
    for old,new in reversed(PAIRS):back=back.replace(new,old,1)
    if back!=source:raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('prior',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    try:
        data=patch(a.prior.read_text(encoding='utf-8'))
        with a.output.open('x',encoding='utf-8') as f:f.write(data)
    except (OSError,ValueError):
        print('V420_SC_ROUTE installed=0');return 1
    print('V420_SC_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
