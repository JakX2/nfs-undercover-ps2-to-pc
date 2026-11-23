#!/usr/bin/env python3
"""V403: original Wii guest LR provenance and selected callsite opcode family.

An authentic V395 selected guest call entered from the original _isfsFuncCb,
but V401 found that LR-4 is not a PPC instruction with LK set (16/16).
Observe read-only CTR/selected-target agreement, the saved selected-entry
SP versus the resumed ISFS SP, LR equality at the saved PC, and the
non-link opcode family at LR-4. None of these alone proves a PPC BLR.
Keep the original V401 bounded 24-call process and V402 independent
extended horizon unchanged; the translated guest code and IOS stay intact.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

STATE="static unsigned v401_direct_match=0u,v401_reported=0u;"
RESET="nwii::runtime::v401_reported=0u;"
ENTRY_SAVE="    v395_next_pc=addr;v395_next_lr=ctx.lr;"
RESUME='''      v398_site_seen=1u;'''
OPCODE='''        if(v401_kind==1u||v401_kind==2u){'''
STOP='''               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v401_completed,"V401 original PPC linksite classification incomplete");'''
MARKER="V403_NAND_CALL_PROVENANCE ctr="
TRIAL_MARKER="V403_NAND_CALL_PROVENANCE_TRIAL family="

STATE_NEW="""static unsigned v401_direct_match=0u,v401_reported=0u;
static unsigned v403_target_ctr=0u,v403_return_lr=0u;
static unsigned v403_return_sp=0u,v403_family=0u,v403_reported=0u;
static uint32_t v403_selected_sp=0u;"""
RESET_NEW="""nwii::runtime::v401_reported=0u;
  nwii::runtime::v403_target_ctr=0u;
  nwii::runtime::v403_return_lr=0u;
  nwii::runtime::v403_return_sp=0u;
  nwii::runtime::v403_family=0u;
  nwii::runtime::v403_reported=0u;
  nwii::runtime::v403_selected_sp=0u;"""
ENTRY_NEW="""    v395_next_pc=addr;v395_next_lr=ctx.lr;
    v403_target_ctr=unsigned(ctx.ctr==addr);
    v403_selected_sp=ctx.gpr[1];"""
RESUME_NEW=r"""      v398_site_seen=1u;
      if(ctx.lr==ctx.pc)v403_return_lr=1u;
      if(ctx.gpr[1]==v403_selected_sp)v403_return_sp=1u;"""
OPCODE_NEW=r"""        // Only the previously-unclassified V401 LR-4 word is grouped;
        // no original instruction bits or game-code bytes are exported.
        if(v401_kind==5u){
          if(v401_op==18u&&(v399_call&1u)==0u)
            v403_family=1u; // direct B without LK
          else if(v401_op==16u&&(v399_call&1u)==0u)
            v403_family=2u; // conditional BC without LK
          else if(v401_op==19u&&v401_xo==16u&&(v399_call&1u)==0u)
            v403_family=3u; // BCLR without LK
          else if(v401_op==19u&&v401_xo==528u&&(v399_call&1u)==0u)
            v403_family=4u; // BCCTR without LK
          else if(v399_call==0x60000000u)
            v403_family=5u; // PPC NOP (ORI 0,0,0)
          else if(v401_op>=32u&&v401_op<=47u)
            v403_family=6u; // load/store family
          else if(v401_op==31u)
            v403_family=7u; // extended ALU or SPR operation
          else
            v403_family=8u; // other non-LK or unsupported encoding
        }
        if(v401_kind==1u||v401_kind==2u){"""
STOP_NEW=r'''               <<" blr_verified=0"<<std::endl;
      v403_reported=1u;
      std::cout<<"V403_NAND_CALL_PROVENANCE ctr="<<v403_target_ctr
               <<" sp="<<v403_return_sp
               <<" lr="<<v403_return_lr
               <<" family="<<v403_family
               <<" v401_kind="<<v401_kind
               <<" selected_site="<<v398_site_seen
               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_NEW=r'''  check(v401_completed,"V401 original PPC linksite classification incomplete");
  const bool v403_completed=v401_completed&&
       nwii::runtime::v403_reported==1u&&
       nwii::runtime::v403_target_ctr<=1u&&
       nwii::runtime::v403_return_sp<=1u&&
       nwii::runtime::v403_return_lr<=1u&&
       nwii::runtime::v403_family<=8u&&
       (nwii::runtime::v401_kind==5u)==
           (nwii::runtime::v403_family!=0u);
  std::cout<<"V403_NAND_CALL_PROVENANCE_TRIAL family="
           <<nwii::runtime::v403_family
           <<" complete="<<unsigned(v403_completed)<<std::endl;
  check(v403_completed,"V403 original PPC LR provenance not classified");'''

def patch(source:str)->str:
    anchors=(STATE,RESET,ENTRY_SAVE,RESUME,OPCODE,STOP,TRIAL,
             "V401_NAND_CALLSITE mapped=",
             "V401_NAND_CALLSITE_TRIAL kind=",
             "V395_NAND_ISFS_NEXT guest=",
             "V389_NAND_FLAG_ACK before=")
    if (any(source.count(s)!=1 for s in anchors) or
        MARKER in source or TRIAL_MARKER in source or
        "v403_target_ctr" in source):
        raise ValueError("V403 original guest callsite source seam moved")
    s=source.replace(STATE,STATE_NEW,1)
    s=s.replace(RESET,RESET_NEW,1)
    s=s.replace(ENTRY_SAVE,ENTRY_NEW,1)
    s=s.replace(RESUME,RESUME_NEW,1)
    s=s.replace(OPCODE,OPCODE_NEW,1)
    s=s.replace(STOP,STOP_NEW,1)
    s=s.replace(TRIAL,TRIAL_NEW,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL_MARKER)!=1 or
        s.count(ENTRY_NEW)!=1 or s.count(OPCODE_NEW)!=1 or
        s.count(RESUME_NEW)!=1 or s.count(STOP_NEW)!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V403 modified original guest execution route")
    return s

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        with a.next_private_harness.open("x",encoding="utf-8") as out:
            out.write(patch(a.prior_private_harness.read_text(encoding="utf-8")))
    except (OSError,ValueError):
        print("V403_NAND_CALL_PROVENANCE_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V403_NAND_CALL_PROVENANCE_ROUTE installed=1 original_guest=1 read_only=1 cap24=1 opcode_hidden=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
