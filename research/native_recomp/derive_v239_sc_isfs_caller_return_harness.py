#!/usr/bin/env python3
"""V239 owner-original: locate the second ISFS saved return code address.

V238 verified 16/16 that the second _savegpr_26 already sees malformed
pathname/mode but valid r11 save ABI. This original-free observer
classifies only the saved text return site, never the owner's private
strings, pointer data or translated instruction bytes. No guest writes.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v238_sc_isfs_prologue_source_harness import (
    derive as previous, TRACE as PREVIOUS_TRACE,
    NEXT_EXTRA as PREVIOUS_EXTRA,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
TRACE_ANCHOR="      const bool sysconf=validpath&&chars==\"/shared2/sys/SYSCONF\";"
PROBE='''      // Only original saved text return-PCs are printed; never guest
      // strings, RAM pointers, register values or original code bytes.
      if(seq==2u&&v239_caller_seen==0u){
        const bool v239_obs_text=mapped&&!(caller&3u)&&
              caller>=0x80400000u&&caller<0x80600000u;
        const bool v239_obs_ipc=v239_obs_text&&
              caller>=0x80519000u&&caller<0x80519c00u;
        const bool v239_obs_isfs=v239_obs_text&&
              caller>=0x804f0000u&&caller<0x804f2200u;
        const bool v239_obs_nand=v239_obs_text&&
              caller>=0x8051d000u&&caller<0x8051f000u;
        const bool v239_obs_os=v239_obs_text&&
              caller>=0x80522000u&&caller<0x80546000u;
        const bool v239_obs_same=v239_obs_text&&
              v237_first_lr_mapped&&caller==v237_first_lr;
        v239_return_pc=v239_obs_text?caller:0u;
        v239_text=v239_obs_text;v239_ipc=v239_obs_ipc;
        v239_isfs=v239_obs_isfs;v239_nand=v239_obs_nand;
        v239_os=v239_obs_os;v239_same_first=v239_obs_same;
        v239_mode_valid=ctx.gpr[4]<=3u;
        v239_path_valid=validpath;
        std::cout<<"V239_ISFS_RETURN text="<<v239_text
                 <<" ipc="<<v239_ipc<<" isfs="<<v239_isfs
                 <<" nand_region="<<v239_nand<<" os="<<v239_os
                 <<" same_first="<<v239_same_first
                 <<" modevalid="<<v239_mode_valid
                 <<" pathvalid="<<v239_path_valid
                 <<" ret="<<std::hex<<v239_return_pc<<std::dec
                 <<std::endl;
        ++v239_caller_seen;
      }
'''
SEND_ANCHOR='''      ++v238_source_seen;'''
SEND='''      ++v238_source_seen;
      const bool v239_ready=v239_caller_seen==1u&&
            v238_save_count>=2u;
      const bool v239_invalid=!v239_mode_valid&&
            !v239_path_valid&&!v238_second_modevalid;
      std::cout<<"V239_ISFS_CHAIN ready="<<v239_ready
               <<" text="<<v239_text
               <<" same_first="<<v239_same_first
               <<" invalid="<<v239_invalid
               <<" ios_invalid="<<(v236_ios_count>=2u&&
                                    !v236_last_mode_valid)
               <<" same_ios_mode="<<(v238_second_mode==v236_last_mode)
               <<std::endl;
      check(v239_ready&&v239_text&&v239_invalid,
            "V239 second original ISFS return or incoming ABI differs");
      ++v239_submit_seen;'''
EXTRA='''            nwii::runtime::v238_source_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v238_source_seen==1u&&
            nwii::runtime::v239_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (PREVIOUS_TRACE.count(TRACE_ANCHOR)==1 and
            s.count(SEND_ANCHOR)==1 and PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V239 verified V238 caller-prologue anchors changed")
    s=once(s,STATE,STATE+'''
 static unsigned v239_caller_seen=0u,v239_submit_seen=0u;
 static uint32_t v239_return_pc=0u;
 static bool v239_text=false,v239_ipc=false,v239_isfs=false,
       v239_nand=false,v239_os=false,v239_same_first=false,
       v239_mode_valid=false,v239_path_valid=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v239_caller_seen=nwii::runtime::v239_submit_seen=0u;
     nwii::runtime::v239_return_pc=0u;
     nwii::runtime::v239_text=nwii::runtime::v239_ipc=
         nwii::runtime::v239_isfs=nwii::runtime::v239_nand=
         nwii::runtime::v239_os=nwii::runtime::v239_same_first=
         nwii::runtime::v239_mode_valid=
         nwii::runtime::v239_path_valid=false;''')
    s=once(s,PREVIOUS_TRACE,PREVIOUS_TRACE.replace(
        TRACE_ANCHOR,TRACE_ANCHOR+'\n'+PROBE,1))
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
