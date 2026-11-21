#!/usr/bin/env python3
"""V244 owner-native register-link and stack provenance of nested ISFS callback.

The original _isfsFuncCb includes a register-indirect linked call, and
V242 observed subsequent ISFS_OpenAsync work with no explicit ISFS
entry trace. At the first original callback entry capture only the
private nested-callback *class*, entry stack and reply ABI. Observe
the second genuine ISFS register-save helper later in the same original
execution path. Classify the stack-frame delta and saved LR without
printing pointers, strings, instruction words or modifying guest state.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v242_sc_callback_call_route_harness import (
    derive as previous, TRACE as PREVIOUS_TRACE,
    NEXT_EXTRA as PREVIOUS_EXTRA,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  // Capture the authentic IpcReplyHandler -> _isfsFuncCb entry.
  if(ctx.pc==addr&&addr==0x804f0e04u&&v183_second_phys==0u&&
     v241_cb_count==0u&&v244_cb_seen==0u){
    const uint32_t userdata=ctx.gpr[4];
    const bool valid=userdata<=0xfffffefcu&&
          ctx.mmu.get_ptr(userdata+256u)!=nullptr&&
          ctx.mmu.get_ptr(userdata+259u)!=nullptr;
    v244_nested_target=valid?ctx.mmu.read32(userdata+256u):0u;
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    v244_cb_sp=ctx.gpr[1];
    v244_cb_userdata=valid;
    v244_cb_registered=reply&&ctx.lr==0x805192acu&&
          ctx.ctr==0x804f0e04u;
    v244_cb_abi=reply&&ctx.gpr[3]==ipc70_ram.read32(v153_phys+4u)&&
          userdata==ipc70_ram.read32(v153_phys+36u);
    ++v244_cb_seen;
    const bool target_text=valid&&
          v244_nested_target>=0x80400000u&&
          v244_nested_target<0x80600000u&&
          !(v244_nested_target&3u);
    const bool nested_isfs=target_text&&
          v244_nested_target==0x804f1e2cu;
    const bool nested_nand=target_text&&
          v244_nested_target==0x8051e06cu;
    std::cout<<"V244_CB_NEST registered="<<v244_cb_registered
             <<" abi="<<v244_cb_abi<<" mapped="<<valid
             <<" text="<<target_text<<" isfs="<<nested_isfs
             <<" nand="<<nested_nand
             <<" null="<<(valid&&v244_nested_target==0u)
             <<std::endl;
  }
  // The first ISFS prologue precedes this callback; the second one
  // follows it. Read LR saved by the real second prologue at 36(r1).
  if(v244_cb_seen==1u&&v238_save_count==1u&&
     ctx.pc==addr&&addr==0x80545100u&&
     ctx.lr==0x804f1e40u&&v244_save_seen==0u){
    const uint32_t sp=ctx.gpr[1];
    const bool stack=sp<=0xffffffdbu&&
          ctx.mmu.get_ptr(sp+36u)!=nullptr;
    const uint32_t saved=stack?ctx.mmu.read32(sp+36u):0u;
    const bool delta=v244_cb_sp>=sp;
    v244_frame32=delta&&v244_cb_sp-sp==32u;
    v244_frame48=delta&&v244_cb_sp-sp==48u;
    v244_saved_outer=stack&&saved==0x805192acu;
    v244_saved_nested=stack&&saved==0x804f0f54u;
    const bool within=stack&&saved>=0x80400000u&&saved<0x80600000u;
    v244_save_mapped=stack;
    ++v244_save_seen;
    std::cout<<"V244_FRAME mapped="<<stack
             <<" frame32="<<v244_frame32
             <<" frame48="<<v244_frame48
             <<" other="<<(!v244_frame32&&!v244_frame48)
             <<" outer_lr="<<v244_saved_outer
             <<" nested_lr="<<v244_saved_nested
             <<" text_lr="<<within<<std::endl;
  }
'''
SEND_ANCHOR='''      ++v242_submit_seen;'''
SEND='''      ++v242_submit_seen;
      // Preserve every observed branch and stack property even if
      // inconsistent with the original nested bctrl link. Diagnostic
      // checks require provenance, never a forced expected LR.
      const bool v244_seen=v244_cb_seen==1u&&v244_save_seen==1u;
      const bool v244_same=v244_cb_registered&&v244_cb_abi&&
            v244_save_mapped;
      std::cout<<"V244_LINK cb="<<(v244_cb_seen==1u)
               <<" save="<<(v244_save_seen==1u)
               <<" registered="<<v244_cb_registered
               <<" abi="<<v244_cb_abi
               <<" userdata="<<v244_cb_userdata
               <<" frame32="<<v244_frame32
               <<" frame48="<<v244_frame48
               <<" outer_lr="<<v244_saved_outer
               <<" nested_lr="<<v244_saved_nested
               <<" isfs_entry="<<v242_isfs_entries
               <<" nested_text="<<(v244_nested_target>=0x80400000u&&
                                   v244_nested_target<0x80600000u)
               <<std::endl;
      check(v244_seen&&v244_same&&v242_count>0u,
            "V244 original callback nested link provenance missing");
      ++v244_submit_seen;'''
EXTRA='''            nwii::runtime::v242_submit_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v242_submit_seen==1u&&
            nwii::runtime::v244_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if (s.count(TRACE_ANCHOR)!=1 or s.count(SEND_ANCHOR)!=1 or
            PREVIOUS_EXTRA.count(EXTRA)!=1):
        raise ValueError("V244 original callback route/seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v244_cb_seen=0u,v244_save_seen=0u,v244_submit_seen=0u;
 static uint32_t v244_cb_sp=0u,v244_nested_target=0u;
 static bool v244_cb_userdata=false,v244_cb_registered=false,
       v244_cb_abi=false,v244_frame32=false,v244_frame48=false,
       v244_saved_outer=false,v244_saved_nested=false,
       v244_save_mapped=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v244_cb_seen=nwii::runtime::v244_save_seen=
         nwii::runtime::v244_submit_seen=0u;
     nwii::runtime::v244_cb_sp=nwii::runtime::v244_nested_target=0u;
     nwii::runtime::v244_cb_userdata=nwii::runtime::v244_cb_registered=
         nwii::runtime::v244_cb_abi=nwii::runtime::v244_frame32=
         nwii::runtime::v244_frame48=nwii::runtime::v244_saved_outer=
         nwii::runtime::v244_saved_nested=nwii::runtime::v244_save_mapped=false;''')
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
