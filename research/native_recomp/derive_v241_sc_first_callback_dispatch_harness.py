#!/usr/bin/env python3
"""V241 read-only tracing of registered original ISFS callback AOT entry.

The original first IOS reply targets _isfsFuncCb 0x804F0E04, CTR agrees,
yet the second ISFS_OpenAsync prologue sees callback-shaped arguments.
Determine whether the actual translated callback function is entered.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v240_sc_first_callback_abi_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  // Actual AOT-translated entry to the registered first reply callback.
  // Observe without emitting original game data or forcing native calls.
  if(ctx.pc==addr&&addr==0x804f0e04u&&v153_phys!=0u&&
     v183_second_phys==0u&&v241_cb_count<8u){
    const bool v241_req=ipc70_ram.valid(v153_phys,64u);
    const uint32_t v241_target=v241_req?ipc70_ram.read32(v153_phys+32u):0u;
    const uint32_t v241_result=v241_req?ipc70_ram.read32(v153_phys+4u):0u;
    const uint32_t v241_user=v241_req?ipc70_ram.read32(v153_phys+36u):0u;
    const bool v241_lr=ctx.lr==0x805192acu;
    const bool v241_target_ok=v241_req&&v241_target==addr;
    const bool v241_abi=v241_req&&ctx.gpr[3]==v241_result&&
          ctx.gpr[4]==v241_user;
    const bool v241_ctr=v241_req&&ctx.ctr==v241_target;
    ++v241_cb_count;
    v241_cb_lr_ok|=v241_lr;v241_cb_target_ok|=v241_target_ok;
    v241_cb_abi_ok|=v241_abi;v241_cb_ctr_ok|=v241_ctr;
    std::cout<<"V241_CB_ENTRY seq="<<v241_cb_count
             <<" lr="<<v241_lr<<" target="<<v241_target_ok
             <<" abi="<<v241_abi<<" ctr="<<v241_ctr<<std::endl;
  }
'''
SEND_ANCHOR='''      ++v240_submit_seen;'''
SEND='''      ++v240_submit_seen;
      const bool v241_registered=v240_cb_isfsfunc&&v240_ctr_cb&&
            !v240_cb_isfsopen;
      const bool v241_invalid=!v238_second_modevalid&&
            !v238_second_pathvalid&&v239_ipc;
      std::cout<<"V241_DISPATCH cb_count="<<v241_cb_count
               <<" traced="<<(v241_cb_count>0u)
               <<" registered="<<v241_registered
               <<" trace_enabled="<<g_trace_calls
               <<" lr_ok="<<v241_cb_lr_ok
               <<" target_ok="<<v241_cb_target_ok
               <<" abi_ok="<<v241_cb_abi_ok
               <<" ctr_ok="<<v241_cb_ctr_ok
               <<" second_invalid="<<v241_invalid
               <<" first_reply="<<v240_reply<<std::endl;
      check(v241_registered&&v241_invalid&&v240_reply,
            "V241 authenticated first callback dispatch provenance differs");
      ++v241_submit_seen;'''
EXTRA='''            nwii::runtime::v240_submit_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v240_submit_seen==1u&&
            nwii::runtime::v241_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(TRACE_ANCHOR)!=1 or s.count(SEND_ANCHOR)!=1 or PREVIOUS_EXTRA.count(EXTRA)!=1:
        raise ValueError("V241 previous owner-authenticated callback source changed")
    s=once(s,STATE,STATE+'''
 static unsigned v241_cb_count=0u,v241_submit_seen=0u;
 static bool v241_cb_lr_ok=false,v241_cb_target_ok=false,
       v241_cb_abi_ok=false,v241_cb_ctr_ok=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v241_cb_count=nwii::runtime::v241_submit_seen=0u;
     nwii::runtime::v241_cb_lr_ok=nwii::runtime::v241_cb_target_ok=
         nwii::runtime::v241_cb_abi_ok=nwii::runtime::v241_cb_ctr_ok=false;''')
    s=once(s,TRACE_ANCHOR,TRACE)
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
