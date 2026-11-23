#!/usr/bin/env python3
"""V400: observe the original _isfsFuncCb -> IPC parent return-PC boundary.

V394 authenticated _isfsFuncCb entry with LR=0x805192AC. V398 observes
a natural return to the selected nested callback's LR. V399 records whether
another original ISFS-origin call follows that observation. Independently
observe whether PPC execution reaches the original ISFS caller LR and
whether the caller subsequently makes a native guest call.

The owner source/opcode remains private. This is read-only and bounded,
not a claim that the final NAND callback or game boot completed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

STATE="static unsigned v399_parent_after=0u,v399_reported=0u;"
RESET="nwii::runtime::v399_reported=0u;"
PENDING="bool process_pending_callbacks(CPUContext& ctx){"
LATER=r"""    if(v398_site_seen==1u&&v398_site_mapped==1u&&
       v398_pre_cap==1u&&ctx.inst_count>v396_start_inst){
      if(v397_isfs)v399_isfs_after=1u;
      if(v397_parent)v399_parent_after=1u;
    }"""
STOP='''               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v399_completed,"V399 original ISFS continuation classification incomplete");'''
MARKER="V400_NAND_PARENT_RESUME site="
TRIAL_MARKER="V400_NAND_PARENT_TRIAL ordered="
HOOK=r"""bool process_pending_callbacks(CPUContext& ctx){
  // Original _isfsFuncCb LR observed in V394; do not force a return.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v394_isfs_seen==1u&&v395_next_seen==1u&&v396_kind==0u&&
     ctx.inst_count>v395_isfs_inst&&ctx.pc==0x805192acu){
    v400_parent_site=1u;
    if(ctx.mmu.get_ptr(ctx.pc)!=nullptr)v400_parent_mapped=1u;
    if(v396_calls<24u)v400_parent_pre_cap=1u;
    if(v398_site_seen==1u&&v398_site_mapped==1u)
      v400_selected_first=1u;
    if(ctx.mmu.get_ptr(0x805192a8u)!=nullptr){
      const uint32_t v400_call=ctx.mmu.read32(0x805192a8u);
      const bool direct=(v400_call>>26)==18u&&(v400_call&1u)==1u;
      const bool indirect=(v400_call>>26)==19u&&
          ((v400_call>>1)&1023u)==528u&&(v400_call&1u)==1u;
      if(direct||indirect)v400_link=1u;
    }
  }
"""
LATER_NEXT=LATER+r"""
    if(v400_parent_site==1u&&v400_parent_mapped==1u&&v397_parent)
      v400_parent_after=1u;"""
STOP_NEXT=r'''               <<" blr_verified=0"<<std::endl;
      const bool v400_ordered=v400_parent_site==1u&&
          v400_parent_mapped==1u&&v400_selected_first==1u&&
          v400_parent_after==1u;
      v400_reported=1u;
      std::cout<<"V400_NAND_PARENT_RESUME site="<<v400_parent_site
               <<" mapped="<<v400_parent_mapped
               <<" linked="<<v400_link
               <<" selected_first="<<v400_selected_first
               <<" parent_after="<<v400_parent_after
               <<" ordered="<<unsigned(v400_ordered)
               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_NEXT=r'''  check(v399_completed,"V399 original ISFS continuation classification incomplete");
  const bool v400_completed=v399_completed&&
      nwii::runtime::v400_reported==1u&&
      nwii::runtime::v400_parent_site<=1u&&
      nwii::runtime::v400_parent_mapped<=1u&&
      nwii::runtime::v400_link<=1u&&
      nwii::runtime::v400_selected_first<=1u&&
      nwii::runtime::v400_parent_after<=1u;
  const bool v400_ordered=nwii::runtime::v400_parent_site==1u&&
      nwii::runtime::v400_parent_mapped==1u&&
      nwii::runtime::v400_selected_first==1u&&
      nwii::runtime::v400_parent_after==1u;
  std::cout<<"V400_NAND_PARENT_TRIAL ordered="<<unsigned(v400_ordered)
           <<" completed="<<unsigned(v400_completed)<<std::endl;
  check(v400_completed,"V400 original parent return-PC classification incomplete");'''
def patch(s:str)->str:
    anchors=(STATE,RESET,PENDING,LATER,STOP,TRIAL,
             "V399_NAND_RETURN_ORDER site=",
             "V399_NAND_RETURN_TRIAL ordered=",
             "V398_NAND_RETURN_PC samples=")
    if (any(s.count(x)!=1 for x in anchors) or
        MARKER in s or TRIAL_MARKER in s or "v400_parent_site" in s):
        raise ValueError("V400 original parent return seam changed")
    out=s.replace(STATE,STATE+"\n"+
       "static unsigned v400_parent_site=0u,v400_parent_mapped=0u;\n"+
       "static unsigned v400_parent_pre_cap=0u,v400_selected_first=0u;\n"+
       "static unsigned v400_link=0u,v400_parent_after=0u,v400_reported=0u;",1)
    out=out.replace(RESET,RESET+"\n"+
       "  nwii::runtime::v400_parent_site=0u;\n"+
       "  nwii::runtime::v400_parent_mapped=0u;\n"+
       "  nwii::runtime::v400_parent_pre_cap=0u;\n"+
       "  nwii::runtime::v400_selected_first=0u;\n"+
       "  nwii::runtime::v400_link=0u;\n"+
       "  nwii::runtime::v400_parent_after=0u;\n"+
       "  nwii::runtime::v400_reported=0u;",1)
    out=out.replace(PENDING,HOOK,1)
    out=out.replace(LATER,LATER_NEXT,1)
    out=out.replace(STOP,STOP_NEXT,1)
    out=out.replace(TRIAL,TRIAL_NEXT,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL_MARKER)!=1 or
        out.count(HOOK)!=1 or out.count(LATER_NEXT)!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V400 modified the original PPC route")
    return out
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
    except (ValueError,OSError):
        print("V400_NAND_PARENT_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V400_NAND_PARENT_ROUTE installed=1 read_only=1 original_lr=1 no_forced_return=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
