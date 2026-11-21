#!/usr/bin/env python3
"""V235 verify original Wii ISFS_OpenAsync nonvolatile mode across helper calls.

V234 observed valid ISFS Open pathname/mode, invalid IOS Open arguments.
Probe the original ISFS helper callsites: strnlen, IOS allocator, memcpy,
and the actual IOS_OpenAsync entry. Observe r27 (the original saved mode)
without modifying guest registers or memory.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v234_sc_isfs_origin_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  {
    // Observe only exact original ISFS_OpenAsync nested PPC callsites.
    // Do not change call order, original register values or allocator memory.
    const bool v235_live=v234_isfs_count!=0u&&
          v183_second_phys==0u&&ctx.pc==addr;
    unsigned v235_stage=0u;
    if(v235_live&&addr==0x80519094u&&ctx.lr==0x804f1e60u)v235_stage=1u;
    if(v235_live&&addr==0x8051ad38u&&ctx.lr==0x804f1e84u)v235_stage=2u;
    if(v235_live&&addr==0x80004338u&&ctx.lr==0x804f1eb4u)v235_stage=3u;
    if(v235_live&&addr==0x8051982cu&&ctx.lr==0x804f1eccu)v235_stage=4u;
    if(v235_stage!=0u){
      const unsigned v235_bit=1u<<(v235_stage-1u);
      if((v235_stage_mask&v235_bit)==0u){
        v235_stage_mask|=v235_bit;
        const bool v235_r27_valid=ctx.gpr[27]<=3u;
        const bool v235_r27_source=ctx.gpr[27]==v234_isfs_mode;
        const bool v235_mode_arg=ctx.gpr[4]<=3u;
        const bool v235_same=ctx.gpr[4]==ctx.gpr[27];
        const bool v235_buf=ctx.gpr[3]==ctx.gpr[30];
        if(v235_r27_valid)v235_valid_mask|=v235_bit;
        if(v235_r27_source)v235_source_mask|=v235_bit;
        if(v235_stage==4u){
          v235_ios_modevalid=v235_mode_arg;
          v235_ios_mrsame=v235_same;
          v235_ios_bufsame=v235_buf;
        }
        std::cout<<"V235_HELPER stage="<<v235_stage
                 <<" r27valid="<<v235_r27_valid
                 <<" r27source="<<v235_r27_source
                 <<" mode_arg="<<v235_mode_arg
                 <<" arg_eq_r27="<<v235_same
                 <<" buf_eq_r30="<<v235_buf<<std::endl;
      }
    }
  }
'''
SEND_ANCHOR='''      ++v234_source_seen;'''
SEND='''      ++v234_source_seen;
      std::cout<<"V235_SUMMARY stage="<<v235_stage_mask
               <<" valid="<<v235_valid_mask
               <<" source="<<v235_source_mask
               <<" ios_modevalid="<<v235_ios_modevalid
               <<" ios_eq_r27="<<v235_ios_mrsame
               <<" ios_bufsame="<<v235_ios_bufsame
               <<" isfs="<<(v234_isfs_count!=0u)
               <<" ios="<<(v233_ios_seen!=0u)<<std::endl;
      ++v235_summary_seen;'''
EXTRA='''            nwii::runtime::v234_source_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v234_source_seen==1u&&
            nwii::runtime::v235_summary_seen==1u&&'''
def derive(source:str)->str:
    s=previous(source)
    if not (s.count(TRACE_ANCHOR)==1 and s.count(SEND_ANCHOR)==1 and
            PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V235 authenticated ISFS helper source anchors changed")
    s=once(s,STATE,STATE+'''
 static unsigned v235_stage_mask=0u,v235_valid_mask=0u,v235_source_mask=0u;
 static unsigned v235_summary_seen=0u;
 static bool v235_ios_modevalid=false,v235_ios_mrsame=false,
             v235_ios_bufsame=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v235_stage_mask=nwii::runtime::v235_valid_mask=
         nwii::runtime::v235_source_mask=nwii::runtime::v235_summary_seen=0u;
     nwii::runtime::v235_ios_modevalid=nwii::runtime::v235_ios_mrsame=
         nwii::runtime::v235_ios_bufsame=false;''')
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
