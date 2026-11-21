#!/usr/bin/env python3
"""V246: classify original NAND's second-level callback and real PPC CTR.

V243 confirms _isfsFuncCb has no immediate branch to the ISFS prologue.
V244 proves its first indirect callback targets NAND. This public-only
read-only instrumentation compares NAND's user callback pointer (+4 of
the nested user object) with CTR at the later native ISFS prologue.
No raw guest data or translated game source is ever emitted.
"""
import argparse
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as previous, TRACE as PARENT_TRACE
from derive_v194_osrestore_next_harness import STATE, RESET, once

PROBE='''  // Original callback r4 is an IOS-owned context pointer. Its +0x104
  // field is the NAND callback user context; NAND invokes the callback
  // stored at user-context +4 on success/error. Observe both stages.
  if(v244_cb_seen==1u&&v246_user_seen==0u&&
     v183_second_phys==0u&&ctx.pc==addr&&addr==0x804f0e04u){
    const uint32_t v246_outer=ctx.gpr[4];
    const bool v246_outer_map=v246_outer<=0xfffffef8u&&
          ctx.mmu.get_ptr(v246_outer+260u)!=nullptr&&
          ctx.mmu.get_ptr(v246_outer+263u)!=nullptr;
    const uint32_t v246_nested=v246_outer_map?
          ctx.mmu.read32(v246_outer+260u):0u;
    const bool v246_nested_map=v246_outer_map&&v246_nested<=0xfffffff8u&&
          ctx.mmu.get_ptr(v246_nested+4u)!=nullptr&&
          ctx.mmu.get_ptr(v246_nested+7u)!=nullptr;
    v246_user_callback=v246_nested_map?
          ctx.mmu.read32(v246_nested+4u):0u;
    const bool v246_target_text=v246_nested_map&&
          v246_user_callback>=0x80400000u&&
          v246_user_callback<0x80600000u&&!(v246_user_callback&3u);
    const bool v246_target_isfs=v246_target_text&&
          v246_user_callback==0x804f1e2cu;
    const bool v246_target_nand=v246_target_text&&
          v246_user_callback==0x8051e06cu;
    const bool v246_target_cb=v246_target_text&&
          v246_user_callback==0x804f0e04u;
    std::cout<<"V246_SECOND_TARGET outer="<<v246_outer_map
             <<" nested="<<v246_nested_map<<" text="<<v246_target_text
             <<" isfs="<<v246_target_isfs<<" nand="<<v246_target_nand
             <<" cb="<<v246_target_cb
             <<" null="<<(v246_nested_map&&v246_user_callback==0u)
             <<std::endl;
    ++v246_user_seen;
  }
  // Actual original _savegpr_26 is the first helper called after the
  // registered callback. Its CTR is compared to the captured second
  // callback address without setting a branch, LR or register.
  if(v244_save_seen==1u&&v246_save_seen==0u&&
     v183_second_phys==0u&&ctx.pc==addr&&
     addr==0x80545100u&&ctx.lr==0x804f1e40u){
    const bool v246_known=v246_user_seen==1u&&v244_cb_userdata;
    const bool v246_match=v246_known&&ctx.ctr==v246_user_callback;
    const bool v246_ctr_isfs=ctx.ctr==0x804f1e2cu;
    const bool v246_ctr_nand=ctx.ctr==0x8051e06cu;
    const bool v246_ctr_cb=ctx.ctr==0x804f0e04u;
    const bool v246_ctr_text=ctx.ctr>=0x80400000u&&
          ctx.ctr<0x80600000u&&!(ctx.ctr&3u);
    const bool v246_outer_lr=v244_saved_outer&&!v244_saved_nested;
    std::cout<<"V246_SECOND_CTR known="<<v246_known
             <<" match="<<v246_match<<" isfs="<<v246_ctr_isfs
             <<" nand="<<v246_ctr_nand<<" cb="<<v246_ctr_cb
             <<" text="<<v246_ctr_text<<" outer_lr="<<v246_outer_lr
             <<std::endl;
    ++v246_save_seen;
  }
'''
SEND_ANCHOR='''      ++v244_submit_seen;'''
SEND='''      ++v244_submit_seen;
      check(v246_user_seen==1u&&v246_save_seen==1u,
            "V246 genuine NAND user callback/CTR evidence missing");'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(PARENT_TRACE)!=1 or s.count(SEND_ANCHOR)!=1:
        raise ValueError("V246 prior verified callback observer changed")
    s=once(s,STATE,STATE+'''
 static unsigned v246_user_seen=0u,v246_save_seen=0u;
 static uint32_t v246_user_callback=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v246_user_seen=nwii::runtime::v246_save_seen=0u;
     nwii::runtime::v246_user_callback=0u;''')
    s=once(s,PARENT_TRACE,PARENT_TRACE+PROBE)
    s=once(s,SEND_ANCHOR,SEND)
    return s

if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("source",type=Path)
    args.add_argument("output",type=Path)
    a=args.parse_args()
    with a.output.open("x",encoding="utf-8") as dst:
        dst.write(derive(a.source.read_text(encoding="utf-8")))
