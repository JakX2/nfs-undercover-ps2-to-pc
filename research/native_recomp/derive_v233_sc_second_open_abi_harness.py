#!/usr/bin/env python3
"""V233 compare genuine Wii ISFS/IOS_OpenAsync inputs to the second PPCMSG.

Observations are made only at the original game's translated call entries
and actual native MMIO write. Original PowerPC instructions, guest registers,
RAM, negative IOS result, and hardware state are never changed.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v214_sc_y2_negative_reply_harness import derive as previous, NEXT_END as PREVIOUS_END
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  // Read-only provenance at the original ISFS and IOS function entries.
  const bool isfs=addr==0x804f1e2cu,ios=addr==0x8051982cu;
  if(ctx.pc==addr&&v153_phys!=0u&&v183_second_phys==0u&&
     ((isfs&&v233_isfs_seen==0u)||(ios&&v233_ios_seen==0u))){
    const uint32_t p=ctx.gpr[3];
    std::string name;
    bool mapped=true,terminated=false;
    for(unsigned i=0u;i<64u;++i){
      if(p>0xffffffffu-i||ctx.mmu.get_ptr(p+i)==nullptr){mapped=false;break;}
      const uint8_t ch=ctx.mmu.read8(p+i);
      if(ch==0u){terminated=true;break;}
      if(ch<0x20u||ch>0x7eu){mapped=false;break;}
      name.push_back(char(ch));
    }
    const bool path=mapped&&terminated&&!name.empty()&&name[0]=='/';
    const bool sysconf=path&&name=="/shared2/sys/SYSCONF";
    const bool modevalid=ctx.gpr[4]<=3u;
    const bool callback=isfs?ctx.gpr[5]==0x8051e06cu:
                            ctx.gpr[5]==0x804f0e04u;
    if(isfs){
      ++v233_isfs_seen;
      v233_isfs_path=ctx.gpr[3];v233_isfs_mode=ctx.gpr[4];
      v233_isfs_cb=ctx.gpr[5];
    }else{
      ++v233_ios_seen;
      v233_ios_path=ctx.gpr[3];v233_ios_mode=ctx.gpr[4];
      v233_ios_cb=ctx.gpr[5];
    }
    std::cout<<"V233_ABI layer="<<(isfs?"isfs":"ios")
             <<" path="<<path<<" sysconf="<<sysconf
             <<" modevalid="<<modevalid<<" callback="<<callback
             <<" guest="<<(ctx.gpr[13]==v147_first_r13)<<std::endl;
  }
'''
SEND_ANCHOR='''      v183_second_phys=value;'''
SEND='''      v183_second_phys=value;
      // Compare the guest caller ABI with the actual physical IOS request.
      // Never print the original request's pointers, bytes or pathname.
      const bool isfs_seen=v233_isfs_seen!=0u;
      const bool ios_seen=v233_ios_seen!=0u;
      const uint32_t path12=ipc70_ram.read32(value+12u);
      const uint32_t mode16=ipc70_ram.read32(value+16u);
      const bool ios_path12=ios_seen&&path12==(v233_ios_path&0x3fffffffu);
      const bool ios_mode16=ios_seen&&mode16==v233_ios_mode;
      const bool ios_shifted=ios_seen&&
            (mode16==v233_ios_path||mode16==(v233_ios_path&0x3fffffffu));
      const bool isfs_path12=isfs_seen&&path12==(v233_isfs_path&0x3fffffffu);
      const bool isfs_mode16=isfs_seen&&mode16==v233_isfs_mode;
      std::cout<<"V233_SUBMIT isfs="<<isfs_seen<<" ios="<<ios_seen
               <<" isfs_path12="<<isfs_path12
               <<" isfs_mode16="<<isfs_mode16
               <<" ios_path12="<<ios_path12
               <<" ios_mode16="<<ios_mode16
               <<" ios_shifted="<<ios_shifted
               <<" isfs_cb="<<(isfs_seen&&v233_isfs_cb==0x8051e06cu)
               <<" ios_cb="<<(ios_seen&&v233_ios_cb==0x804f0e04u)
               <<std::endl;
      ++v233_send_seen;'''
EXTRA='''            nwii::runtime::v214_negative_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v214_negative_seen==1u&&
            nwii::runtime::v233_send_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (s.count(TRACE_ANCHOR)==1 and
            s.count(SEND_ANCHOR)==1 and PREVIOUS_END.count(EXTRA)==1):
        raise ValueError("V233 authenticated public Wii source anchors differ")
    s=once(s,STATE,STATE+'''
 static unsigned v233_isfs_seen=0u,v233_ios_seen=0u,v233_send_seen=0u;
 static uint32_t v233_isfs_path=0u,v233_isfs_mode=0u,v233_isfs_cb=0u;
 static uint32_t v233_ios_path=0u,v233_ios_mode=0u,v233_ios_cb=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v233_isfs_seen=nwii::runtime::v233_ios_seen=
         nwii::runtime::v233_send_seen=0u;
     nwii::runtime::v233_isfs_path=nwii::runtime::v233_isfs_mode=
         nwii::runtime::v233_isfs_cb=0u;
     nwii::runtime::v233_ios_path=nwii::runtime::v233_ios_mode=
         nwii::runtime::v233_ios_cb=0u;''')
    s=once(s,TRACE_ANCHOR,TRACE)
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_END,PREVIOUS_END.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
