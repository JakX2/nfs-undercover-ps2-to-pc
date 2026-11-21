#!/usr/bin/env python3
"""V238 owner-original prologue forensics: second ISFS saved caller LR.

V237 confirmed two genuine ISFS helper sequences on different stack
frames but only one function-entry observer. Verify the second _savegpr_26
prologue's original saved caller LR (NANDOpen versus NAND logging), the mode
in r4 *before* register-save, path class and r11 ABI. Do not alter PPC state.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v237_sc_isfs_reentry_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE='''void trace_call(uint32_t addr, CPUContext&ctx){
  {
    // Original _savegpr_26 at the real ISFS_OpenAsync prologue.
    // The caller LR has already been stored at 36(r1). Read only.
    if(v183_second_phys==0u&&ctx.pc==addr&&
       addr==0x80545100u&&ctx.lr==0x804f1e40u&&
       v238_save_count<8u){
      const unsigned seq=++v238_save_count;
      const uint32_t sp=ctx.gpr[1];
      const bool mapped=sp<=0xffffffdbu&&
            ctx.mmu.get_ptr(sp+36u)!=nullptr;
      const uint32_t caller=mapped?ctx.mmu.read32(sp+36u):0u;
      const bool nand=mapped&&caller==0x8051de3cu;
      const bool logging=mapped&&caller==0x8051f700u;
      const bool other=mapped&&!nand&&!logging&&
            caller>=0x80400000u&&caller<0x80600000u;
      const bool r11=ctx.gpr[11]==sp+32u;
      const bool mode=ctx.gpr[4]<=3u;
      const bool srcmode=ctx.gpr[4]==v237_source_mode;
      const bool nandcb=ctx.gpr[5]==0x8051e06cu;
      const uint32_t pathptr=ctx.gpr[3];
      std::string chars;
      bool pathmapped=true,terminated=false;
      for(unsigned i=0u;i<64u;++i){
        if(pathptr>0xffffffffu-i||
           ctx.mmu.get_ptr(pathptr+i)==nullptr){
          pathmapped=false;break;
        }
        const uint8_t ch=ctx.mmu.read8(pathptr+i);
        if(ch==0u){terminated=true;break;}
        if(ch<0x20u||ch>0x7eu){pathmapped=false;break;}
        chars.push_back(char(ch));
      }
      const bool validpath=pathmapped&&terminated&&
            !chars.empty()&&chars[0]=='/';
      const bool sysconf=validpath&&chars=="/shared2/sys/SYSCONF";
      if(seq==2u){
        v238_second_mode=ctx.gpr[4];
        v238_second_modevalid=mode;
        v238_second_nand=nand;
        v238_second_logging=logging;
        v238_second_other=other;
        v238_second_r11=r11;
        v238_second_pathvalid=validpath;
        v238_second_sysconf=sysconf;
      }
      std::cout<<"V238_SAVE seq="<<seq<<" mapped="<<mapped
               <<" nand="<<nand<<" logging="<<logging
               <<" other="<<other<<" r11="<<r11
               <<" mode="<<mode<<" srcmode="<<srcmode
               <<" path="<<validpath<<" sysconf="<<sysconf
               <<" nandcb="<<nandcb<<std::endl;
    }
  }
'''
SEND_ANCHOR='''      ++v237_seen;'''
SEND='''      ++v237_seen;
      const bool second=v238_save_count>=2u;
      const bool same_mode=second&&v238_second_mode==v236_last_mode;
      const bool ios_invalid=v236_ios_count>=2u&&!v236_last_mode_valid;
      std::cout<<"V238_SOURCE saves="<<v238_save_count
               <<" second="<<second
               <<" nand="<<v238_second_nand
               <<" logging="<<v238_second_logging
               <<" other="<<v238_second_other
               <<" r11="<<v238_second_r11
               <<" modevalid="<<v238_second_modevalid
               <<" pathvalid="<<v238_second_pathvalid
               <<" sysconf="<<v238_second_sysconf
               <<" same_ios_mode="<<same_mode
               <<" ios_invalid="<<ios_invalid
               <<std::endl;
      ++v238_source_seen;'''
EXTRA='''            nwii::runtime::v237_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v237_seen==1u&&
            nwii::runtime::v238_source_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(TRACE_ANCHOR)!=1 or s.count(SEND_ANCHOR)!=1 or PREVIOUS_EXTRA.count(EXTRA)!=1:
        raise ValueError("V238 original second ISFS prologue provenance changed")
    s=once(s,STATE,STATE+'''
 static unsigned v238_save_count=0u,v238_source_seen=0u;
 static uint32_t v238_second_mode=0u;
 static bool v238_second_modevalid=false,v238_second_nand=false,
       v238_second_logging=false,v238_second_other=false,
       v238_second_r11=false,v238_second_pathvalid=false,
       v238_second_sysconf=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v238_save_count=nwii::runtime::v238_source_seen=0u;
     nwii::runtime::v238_second_mode=0u;
     nwii::runtime::v238_second_modevalid=nwii::runtime::v238_second_nand=
         nwii::runtime::v238_second_logging=nwii::runtime::v238_second_other=
         nwii::runtime::v238_second_r11=nwii::runtime::v238_second_pathvalid=
         nwii::runtime::v238_second_sysconf=false;''')
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
