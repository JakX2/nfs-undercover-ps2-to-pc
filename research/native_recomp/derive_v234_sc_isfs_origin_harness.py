#!/usr/bin/env python3
"""V234 widen the real ISFS_OpenAsync probe before second PPCMSG submission.

V233 established that IOS_OpenAsync correctly serializes already-malformed
guest arguments. V234 observes the upstream ISFS_OpenAsync caller earlier
than V153's completion, and compares its mode with the downstream IOS ABI.
All data are read-only and emit only bounded categories.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v233_sc_second_open_abi_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  {
    // Observe every pre-submission original ISFS_OpenAsync entry;
    // unlike V233, do not assume V153 first open has completed yet.
    const bool v234_isfs=addr==0x804f1e2cu;
    const bool v234_ios=addr==0x8051982cu;
    if(ctx.pc==addr&&v183_second_phys==0u&&
       v234_isfs&&v234_isfs_count<8u){
      const uint32_t v234_p=ctx.gpr[3];
      std::string v234_pathname;
      bool v234_mapped=true,v234_term=false;
      for(unsigned i=0u;i<64u;++i){
        if(v234_p>0xffffffffu-i||ctx.mmu.get_ptr(v234_p+i)==nullptr){
          v234_mapped=false;break;
        }
        const uint8_t ch=ctx.mmu.read8(v234_p+i);
        if(ch==0u){v234_term=true;break;}
        if(ch<0x20u||ch>0x7eu){v234_mapped=false;break;}
        v234_pathname.push_back(char(ch));
      }
      const bool v234_path=v234_mapped&&v234_term&&
            !v234_pathname.empty()&&v234_pathname[0]=='/';
      const bool v234_sysconf=v234_path&&
            v234_pathname=="/shared2/sys/SYSCONF";
      ++v234_isfs_count;
      v234_isfs_mode=ctx.gpr[4];
      v234_isfs_callback=ctx.gpr[5];
      v234_isfs_userdata=ctx.gpr[6];
      std::cout<<"V234_ISFS seq="<<v234_isfs_count
               <<" path="<<v234_path<<" sysconf="<<v234_sysconf
               <<" modevalid="<<(ctx.gpr[4]<=3u)
               <<" nand_cb="<<(ctx.gpr[5]==0x8051e06cu)
               <<" guest="<<(ctx.gpr[13]==v147_first_r13)
               <<std::endl;
    }
    if(ctx.pc==addr&&v183_second_phys==0u&&v234_ios&&
       v234_ios_seen==0u&&v153_phys!=0u){
      ++v234_ios_seen;
      const bool v234_has_isfs=v234_isfs_count!=0u;
      const bool v234_mode_same=v234_has_isfs&&
            ctx.gpr[4]==v234_isfs_mode;
      std::cout<<"V234_ROUTE isfs="<<v234_has_isfs
               <<" mode_same="<<v234_mode_same
               <<" isfs_modevalid="<<(v234_has_isfs&&v234_isfs_mode<=3u)
               <<" ios_modevalid="<<(ctx.gpr[4]<=3u)
               <<" ios_cb="<<(ctx.gpr[5]==0x804f0e04u)
               <<std::endl;
    }
  }
'''
SEND_ANCHOR='''      ++v233_send_seen;'''
SEND='''      ++v233_send_seen;
      // The native packet's existing mode value is read, not modified.
      const bool v234_isfs_seen=v234_isfs_count!=0u;
      const bool v234_mode_from_isfs=v234_isfs_seen&&
            ipc70_ram.read32(value+16u)==v234_isfs_mode;
      const bool v234_mode_from_ios=v233_ios_seen!=0u&&
            ipc70_ram.read32(value+16u)==v233_ios_mode;
      std::cout<<"V234_SOURCE isfs="<<v234_isfs_seen
               <<" count="<<v234_isfs_count
               <<" ios="<<(v234_ios_seen!=0u)
               <<" isfs_valid="<<(v234_isfs_seen&&v234_isfs_mode<=3u)
               <<" ios_valid="<<(v233_ios_seen!=0u&&v233_ios_mode<=3u)
               <<" mode_isfs="<<v234_mode_from_isfs
               <<" mode_ios="<<v234_mode_from_ios
               <<" nand_cb="<<(v234_isfs_seen&&
                                  v234_isfs_callback==0x8051e06cu)
               <<std::endl;
      ++v234_source_seen;'''
EXTRA='''            nwii::runtime::v233_send_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v233_send_seen==1u&&
            nwii::runtime::v234_source_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (s.count(TRACE_ANCHOR)==1 and s.count(SEND_ANCHOR)==1 and
            PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V234 upstream ISFS diagnostic anchors changed")
    s=once(s,STATE,STATE+'''
 static unsigned v234_isfs_count=0u,v234_ios_seen=0u,v234_source_seen=0u;
 static uint32_t v234_isfs_mode=0u,v234_isfs_callback=0u,v234_isfs_userdata=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v234_isfs_count=nwii::runtime::v234_ios_seen=
         nwii::runtime::v234_source_seen=0u;
     nwii::runtime::v234_isfs_mode=nwii::runtime::v234_isfs_callback=
         nwii::runtime::v234_isfs_userdata=0u;''')
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
