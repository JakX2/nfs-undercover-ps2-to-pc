#!/usr/bin/env python3
"""V242 actual NWiiRecomp translated-call route after first _isfsFuncCb.

V241 owner-original observed correct _isfsFuncCb entry. Collect only
up to 24 text-PC/LR function entries after that callback and before
the second malformed SYSCONF IPC request, to distinguish a valid
intermediate callback path from an AOT internal-entry jump. Read-only.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v241_sc_first_callback_dispatch_harness import derive as previous, TRACE as PREVIOUS_TRACE, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once
TRACE='''  // Trace original AOT function calls *after* _isfsFuncCb is entered,
  // through the second PPCMSG. Limit to 24 text-only PC/LR pairs, never
  // print guest memory pointers or translated PowerPC instruction bytes.
  if(v241_cb_count>0u&&v183_second_phys==0u&&v242_count<24u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    const bool v242_cb=addr==0x804f0e04u;
    const bool v242_isfs=addr==0x804f1e2cu;
    const bool v242_ipc=addr>=0x80519000u&&addr<0x80519c00u;
    const bool v242_lr_text=ctx.lr>=0x80400000u&&
          ctx.lr<0x80600000u&&!(ctx.lr&3u);
    const bool v242_lr_handler=ctx.lr==0x805192acu;
    ++v242_count;
    if(v242_cb)++v242_callback_entries;
    if(v242_isfs)++v242_isfs_entries;
    if(v242_lr_handler)++v242_handler_returns;
    v242_last_pc=addr;v242_last_lr=v242_lr_text?ctx.lr:0u;
    std::cout<<"V242_TRACE seq="<<v242_count
             <<" cb="<<v242_cb<<" isfs="<<v242_isfs
             <<" ipc="<<v242_ipc<<" lr_text="<<v242_lr_text
             <<" handler_lr="<<v242_lr_handler
             <<" pc="<<std::hex<<addr
             <<" lr="<<v242_last_lr<<std::dec<<std::endl;
  }
'''
SEND_ANCHOR='''      ++v241_submit_seen;'''
SEND='''      ++v241_submit_seen;
      const bool v242_captured=v241_cb_count==1u&&
            v242_count>0u&&v240_cb_isfsfunc;
      const bool v242_second=v238_save_count>=2u&&
            v239_return_pc==0x805192acu;
      std::cout<<"V242_ROUTE count="<<v242_count
               <<" cb="<<v242_callback_entries
               <<" isfs_entry="<<v242_isfs_entries
               <<" handler_lr="<<v242_handler_returns
               <<" captured="<<v242_captured
               <<" second="<<v242_second
               <<" last_pc="<<std::hex<<v242_last_pc
               <<" last_lr="<<v242_last_lr<<std::dec
               <<std::endl;
      check(v242_captured&&v242_second,
            "V242 original first callback to second ISFS call trace missing");
      ++v242_submit_seen;'''
EXTRA='''            nwii::runtime::v241_submit_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v241_submit_seen==1u&&
            nwii::runtime::v242_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (s.count(PREVIOUS_TRACE)==1 and s.count(SEND_ANCHOR)==1
            and PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V242 original translated callback trace seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v242_count=0u,v242_callback_entries=0u,
       v242_isfs_entries=0u,v242_handler_returns=0u,
       v242_submit_seen=0u;
 static uint32_t v242_last_pc=0u,v242_last_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v242_count=nwii::runtime::v242_callback_entries=
         nwii::runtime::v242_isfs_entries=
         nwii::runtime::v242_handler_returns=
         nwii::runtime::v242_submit_seen=0u;
     nwii::runtime::v242_last_pc=nwii::runtime::v242_last_lr=0u;''')
    s=once(s,PREVIOUS_TRACE,PREVIOUS_TRACE+TRACE)
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
