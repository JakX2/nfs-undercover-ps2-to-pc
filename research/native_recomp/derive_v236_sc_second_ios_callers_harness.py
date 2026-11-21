#!/usr/bin/env python3
"""V236 distinguish successive Wii IOS_OpenAsync callers before second PPCMSG.

V235 verifies the original ISFS_OpenAsync to IOS_OpenAsync call preserves its
r27/mode. V233 separately observes a malformed IOS_OpenAsync entry. Compare
all original IOS_OpenAsync entries, their authentic LR and first-reply phase,
then tie the final caller's r3/r4 to the second physical request packet.
Never modify game registers, guest memory, IPC ABI, or IOS response.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v235_sc_isfs_helper_abi_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  {
    // Original translated IOS_OpenAsync entries, irrespective of whether
    // the first request has already been received. Never synthesize a call.
    if(ctx.pc==addr&&addr==0x8051982cu&&
       v183_second_phys==0u&&v236_ios_count<8u){
      const uint32_t seq=++v236_ios_count;
      const bool after_first=v153_phys!=0u;
      const uint32_t pathname=ctx.gpr[3];
      bool mapped=true,terminated=false;
      std::string candidate;
      for(unsigned i=0u;i<64u;++i){
        if(pathname>0xffffffffu-i||
           ctx.mmu.get_ptr(pathname+i)==nullptr){mapped=false;break;}
        const uint8_t ch=ctx.mmu.read8(pathname+i);
        if(ch==0u){terminated=true;break;}
        if(ch<0x20u||ch>0x7eu){mapped=false;break;}
        candidate.push_back(char(ch));
      }
      const bool path=mapped&&terminated&&
            !candidate.empty()&&candidate.front()=='/';
      const bool sysconf=path&&candidate=="/shared2/sys/SYSCONF";
      const bool valid=ctx.gpr[4]<=3u;
      const bool from_isfs=ctx.lr==0x804f1eccu;
      const bool lr_isfs=ctx.lr>=0x804f1e2cu&&
            ctx.lr<0x804f1f84u;
      const bool callback=ctx.gpr[5]==0x804f0e04u;
      const bool mode_mem2=ctx.gpr[4]>=0x90000000u&&
            ctx.gpr[4]<0x94000000u;
      const bool lr_text=ctx.lr>=0x80400000u&&
            ctx.lr<0x80600000u;
      if(after_first)++v236_late_count;
      else ++v236_early_count;
      if(from_isfs)++v236_from_isfs_count;
      v236_last_path=ctx.gpr[3];v236_last_mode=ctx.gpr[4];
      v236_last_lr=ctx.lr;v236_last_mode_valid=valid;
      v236_last_path_valid=path;v236_last_from_isfs=from_isfs;
      v236_last_after_first=after_first;
      std::cout<<"V236_IOS seq="<<seq<<" after_first="<<after_first
               <<" from_isfs="<<from_isfs<<" lr_isfs="<<lr_isfs
               <<" lr_text="<<lr_text
               <<" path="<<path<<" sysconf="<<sysconf
               <<" modevalid="<<valid<<" mode_mem2="<<mode_mem2
               <<" cb="<<callback
               <<" lr="<<std::hex<<ctx.lr<<std::dec<<std::endl;
    }
  }
'''
SEND_ANCHOR='''      ++v235_summary_seen;'''
SEND='''      ++v235_summary_seen;
      // The true physical request address and original GPR inputs are
      // compared privately and reported only as bounded booleans.
      const bool seen=v236_ios_count!=0u;
      const bool same_path=seen&&
            ipc70_ram.read32(value+12u)==(v236_last_path&0x3fffffffu);
      const bool same_mode=seen&&
            ipc70_ram.read32(value+16u)==v236_last_mode;
      const bool early=v236_early_count>0u;
      const bool later=v236_late_count>0u;
      const bool caller_original=v236_last_lr>=0x80400000u&&
            v236_last_lr<0x80600000u;
      std::cout<<"V236_SUBMIT entries="<<v236_ios_count
               <<" early="<<v236_early_count
               <<" late="<<v236_late_count
               <<" isfs="<<v236_from_isfs_count
               <<" after_first="<<v236_last_after_first
               <<" from_isfs="<<v236_last_from_isfs
               <<" pathvalid="<<v236_last_path_valid
               <<" modevalid="<<v236_last_mode_valid
               <<" same_path="<<same_path<<" same_mode="<<same_mode
               <<" original_caller="<<caller_original
               <<" lr="<<std::hex<<v236_last_lr<<std::dec<<std::endl;
      check(seen&&early&&later&&same_path&&same_mode,
          "V236 latest authentic IOS caller does not match second PPCMSG header");
      ++v236_submit_seen;'''
EXTRA='''            nwii::runtime::v235_summary_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v235_summary_seen==1u&&
            nwii::runtime::v236_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (s.count(TRACE_ANCHOR)==1 and s.count(SEND_ANCHOR)==1 and
            PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V236 source-only previous authentic IOS observation changed")
    s=once(s,STATE,STATE+'''
 static unsigned v236_ios_count=0u,v236_early_count=0u,v236_late_count=0u;
 static unsigned v236_from_isfs_count=0u,v236_submit_seen=0u;
 static uint32_t v236_last_path=0u,v236_last_mode=0u,v236_last_lr=0u;
 static bool v236_last_mode_valid=false,v236_last_path_valid=false;
 static bool v236_last_from_isfs=false,v236_last_after_first=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v236_ios_count=nwii::runtime::v236_early_count=
         nwii::runtime::v236_late_count=nwii::runtime::v236_from_isfs_count=
         nwii::runtime::v236_submit_seen=0u;
     nwii::runtime::v236_last_path=nwii::runtime::v236_last_mode=
         nwii::runtime::v236_last_lr=0u;
     nwii::runtime::v236_last_mode_valid=nwii::runtime::v236_last_path_valid=
         nwii::runtime::v236_last_from_isfs=
         nwii::runtime::v236_last_after_first=false;''')
    s=once(s,TRACE_ANCHOR,TRACE)
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
