#!/usr/bin/env python3
"""V237 read-only source probe: both IOS callsite frame and saved-mode registers."""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v236_sc_second_ios_callers_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  {
    if(ctx.pc==addr&&v183_second_phys==0u){
      unsigned stage=0u;
      if(addr==0x804f1e2cu)stage=1u;
      else if(addr==0x80545100u&&ctx.lr==0x804f1e40u)stage=2u;
      else if(addr==0x80519094u&&ctx.lr==0x804f1e60u)stage=3u;
      else if(addr==0x8051ad38u&&ctx.lr==0x804f1e84u)stage=4u;
      else if(addr==0x80004338u&&ctx.lr==0x804f1eb4u)stage=5u;
      else if(addr==0x8051982cu&&ctx.lr==0x804f1eccu)stage=6u;
      if(stage&&v237_counts[stage-1u]<8u){
        ++v237_counts[stage-1u];
        if(stage==1u)v237_source_mode=ctx.gpr[4];
        if(stage==6u){
          const bool mapped=ctx.gpr[1]<=0xffffffdbu&&
              ctx.mmu.get_ptr(ctx.gpr[1]+36u)!=nullptr;
          const uint32_t saved=mapped?ctx.mmu.read32(ctx.gpr[1]+36u):0u;
          if(v237_counts[5u]==1u){
            v237_first_sp=ctx.gpr[1];v237_first_lr=saved;
            v237_first_lr_mapped=mapped;
            v237_first_r30=ctx.gpr[30];
          }else if(v237_counts[5u]==2u){
            v237_same_stack=ctx.gpr[1]==v237_first_sp;
            v237_same_saved_lr=mapped&&v237_first_lr_mapped&&
                saved==v237_first_lr;
            v237_r27_valid=ctx.gpr[27]<=3u;
            v237_r27_source=ctx.gpr[27]==v237_source_mode;
            v237_arg_r27=ctx.gpr[4]==ctx.gpr[27];
            v237_path_r30=ctx.gpr[3]==ctx.gpr[30];
            v237_same_r30=ctx.gpr[30]==v237_first_r30;
            std::cout<<"V237_SECOND stack="<<v237_same_stack
                     <<" saved_lr="<<v237_same_saved_lr
                     <<" r27valid="<<v237_r27_valid
                     <<" r27source="<<v237_r27_source
                     <<" arg_r27="<<v237_arg_r27
                     <<" path_r30="<<v237_path_r30
                     <<" same_r30="<<v237_same_r30<<std::endl;
          }
        }
      }
    }
  }
'''
SEND_ANCHOR='''      ++v236_submit_seen;'''
SEND='''      ++v236_submit_seen;
      std::cout<<"V237_CHAIN isfs="<<v237_counts[0u]
               <<" save="<<v237_counts[1u]
               <<" strn="<<v237_counts[2u]
               <<" alloc="<<v237_counts[3u]
               <<" copy="<<v237_counts[4u]
               <<" ios="<<v237_counts[5u]
               <<" stack="<<v237_same_stack
               <<" saved_lr="<<v237_same_saved_lr
               <<" r27valid="<<v237_r27_valid
               <<" r27source="<<v237_r27_source
               <<" arg_r27="<<v237_arg_r27
               <<" path_r30="<<v237_path_r30
               <<std::endl;
      ++v237_seen;'''
EXTRA='''            nwii::runtime::v236_submit_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v236_submit_seen==1u&&
            nwii::runtime::v237_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(TRACE_ANCHOR)!=1 or s.count(SEND_ANCHOR)!=1 or PREVIOUS_EXTRA.count(EXTRA)!=1:
        raise ValueError("V237 prior original IOS callsite evidence changed")
    s=once(s,STATE,STATE+'''
 static std::array<unsigned,6> v237_counts{};
 static unsigned v237_seen=0u;
 static uint32_t v237_source_mode=0u,v237_first_sp=0u,v237_first_lr=0u,v237_first_r30=0u;
 static bool v237_first_lr_mapped=false,v237_same_stack=false,v237_same_saved_lr=false;
 static bool v237_r27_valid=false,v237_r27_source=false,v237_arg_r27=false,
             v237_path_r30=false,v237_same_r30=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v237_counts.fill(0u);nwii::runtime::v237_seen=0u;
     nwii::runtime::v237_source_mode=nwii::runtime::v237_first_sp=
         nwii::runtime::v237_first_lr=nwii::runtime::v237_first_r30=0u;
     nwii::runtime::v237_first_lr_mapped=nwii::runtime::v237_same_stack=
         nwii::runtime::v237_same_saved_lr=nwii::runtime::v237_r27_valid=
         nwii::runtime::v237_r27_source=nwii::runtime::v237_arg_r27=
         nwii::runtime::v237_path_r30=nwii::runtime::v237_same_r30=false;''')
    s=once(s,TRACE_ANCHOR,TRACE)
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
