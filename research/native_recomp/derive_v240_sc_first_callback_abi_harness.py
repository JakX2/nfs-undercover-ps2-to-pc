#!/usr/bin/env python3
"""V240 owner-original first-reply callback ABI versus malformed second ISFS.

V239 owner-original identified second ISFS prologue saved LR 0x805192AC
inside IpcReplyHandler. The first successful native IOS reply provides
an independently authenticated callback pointer and userdata. Compare
original r3/r4 and CTR to that registered callback without patching them,
changing the IOS wire or printing proprietary buffer data.
"""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v239_sc_isfs_caller_return_harness import (
    derive as previous, PROBE as PREVIOUS_PROBE,
    NEXT_EXTRA as PREVIOUS_EXTRA,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
PROBE_ANCHOR="        v239_path_valid=validpath;"
PROBE='''        // The first successfully completed IOS request is an independent
        // control. Compare its registered callback/user-data with the
        // second malformed ISFS prologue, without exposing any pointers.
        const bool v240_obs_first=v153_phys!=0u&&
              ipc70_ram.valid(v153_phys,64u);
        const uint32_t v240_obs_cb=v240_obs_first?
              ipc70_ram.read32(v153_phys+32u):0u;
        const uint32_t v240_obs_user=v240_obs_first?
              ipc70_ram.read32(v153_phys+36u):0u;
        const uint32_t v240_obs_result=v240_obs_first?
              ipc70_ram.read32(v153_phys+4u):0u;
        v240_first=v240_obs_first;
        v240_reply=v240_obs_first&&
              ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
        v240_cb_isfsfunc=v240_obs_cb==0x804f0e04u;
        v240_cb_isfsopen=v240_obs_cb==0x804f1e2cu;
        v240_cb_text=v240_obs_cb>=0x80400000u&&
              v240_obs_cb<0x80600000u&&!(v240_obs_cb&3u);
        v240_r3_result=v240_obs_first&&ctx.gpr[3]==v240_obs_result;
        v240_r4_user=v240_obs_first&&ctx.gpr[4]==v240_obs_user;
        v240_ctr_cb=v240_obs_first&&ctx.ctr==v240_obs_cb;
        v240_ctr_isfsopen=ctx.ctr==0x804f1e2cu;
        v240_ipc_return=v239_return_pc==0x805192acu;
        std::cout<<"V240_FIRST_CB first="<<v240_first
                 <<" reply="<<v240_reply
                 <<" cb_isfsfunc="<<v240_cb_isfsfunc
                 <<" cb_isfsopen="<<v240_cb_isfsopen
                 <<" cb_text="<<v240_cb_text
                 <<" r3_reply="<<v240_r3_result
                 <<" r4_userdata="<<v240_r4_user
                 <<" ctr_cb="<<v240_ctr_cb
                 <<" ctr_isfsopen="<<v240_ctr_isfsopen
                 <<" ipc_return="<<v240_ipc_return
                 <<std::endl;
        ++v240_callback_seen;
'''
SEND_ANCHOR='''      ++v239_submit_seen;'''
SEND='''      ++v239_submit_seen;
      const bool v240_seen=v240_callback_seen==1u;
      std::cout<<"V240_CB_CHAIN seen="<<v240_seen
               <<" first="<<v240_first
               <<" reply="<<v240_reply
               <<" cb_isfsfunc="<<v240_cb_isfsfunc
               <<" cb_isfsopen="<<v240_cb_isfsopen
               <<" cb_text="<<v240_cb_text
               <<" r3_reply="<<v240_r3_result
               <<" r4_userdata="<<v240_r4_user
               <<" ctr_cb="<<v240_ctr_cb
               <<" ctr_isfsopen="<<v240_ctr_isfsopen
               <<" ipc_return="<<v240_ipc_return
               <<std::endl;
      check(v240_seen&&v240_first&&v240_ipc_return,
            "V240 first IOS reply callback provenance not captured");
      ++v240_submit_seen;'''
EXTRA='''            nwii::runtime::v239_submit_seen==1u&&'''
NEXT_EXTRA='''            nwii::runtime::v239_submit_seen==1u&&
            nwii::runtime::v240_submit_seen==1u&&'''

def derive(source:str)->str:
    s=previous(source)
    if not (PREVIOUS_PROBE.count(PROBE_ANCHOR)==1 and
            s.count(SEND_ANCHOR)==1 and PREVIOUS_EXTRA.count(EXTRA)==1):
        raise ValueError("V240 verified V239 second callback-source seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v240_callback_seen=0u,v240_submit_seen=0u;
 static bool v240_first=false,v240_reply=false,v240_cb_isfsfunc=false,
       v240_cb_isfsopen=false,v240_cb_text=false,v240_r3_result=false,
       v240_r4_user=false,v240_ctr_cb=false,v240_ctr_isfsopen=false,
       v240_ipc_return=false;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v240_callback_seen=nwii::runtime::v240_submit_seen=0u;
     nwii::runtime::v240_first=nwii::runtime::v240_reply=
         nwii::runtime::v240_cb_isfsfunc=nwii::runtime::v240_cb_isfsopen=
         nwii::runtime::v240_cb_text=nwii::runtime::v240_r3_result=
         nwii::runtime::v240_r4_user=nwii::runtime::v240_ctr_cb=
         nwii::runtime::v240_ctr_isfsopen=
         nwii::runtime::v240_ipc_return=false;''')
    s=once(s,PREVIOUS_PROBE,PREVIOUS_PROBE.replace(
        PROBE_ANCHOR,PROBE_ANCHOR+'\n'+PROBE,1))
    s=once(s,SEND_ANCHOR,SEND)
    s=once(s,PREVIOUS_EXTRA,PREVIOUS_EXTRA.replace(EXTRA,NEXT_EXTRA,1))
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
