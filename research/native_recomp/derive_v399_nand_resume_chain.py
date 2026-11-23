#!/usr/bin/env python3
"""V399: classify ordered original ISFS guest return-PC continuation.

V398 observed CPUContext.pc at the real LR saved by the original indirect
ISFS call. Independently test the PowerPC bcctr-with-link opcode at LR-4,
and determine whether *later* native guest calls originate in _isfsFuncCb.
Neither observed PC equality nor opcode classification forces a return,
and a BLR instruction in the selected callee remains unproven.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

STATE="static unsigned v398_site_mapped=0u,v398_pre_cap=0u,v398_reported=0u;"
RESET="nwii::runtime::v398_reported=0u;"
CALLSITE="      if(ctx.mmu.get_ptr(ctx.pc)!=nullptr)v398_site_mapped=1u;"
LATER="""    v397_last_origin=v397_class;
    if(ctx.lr==v395_next_lr)v397_same_lr_seen=1u;"""
STOP='''               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v398_completed,"V398 natural guest return-PC probe not completed");'''
ENTRY="V399_NAND_RETURN_ORDER site="
TRIAL_MARKER="V399_NAND_RETURN_TRIAL ordered="

CALLSITE_NEXT=r"""      if(ctx.mmu.get_ptr(ctx.pc)!=nullptr)v398_site_mapped=1u;
      // Inspect guest text, never emit or modify the original opcode.
      if(ctx.pc>=4u&&ctx.mmu.get_ptr(ctx.pc-4u)!=nullptr){
        const uint32_t v399_call=ctx.mmu.read32(ctx.pc-4u);
        if((v399_call>>26)==19u&&
           ((v399_call>>1)&1023u)==528u&&(v399_call&1u)==1u)
          v399_bctrl=1u;
      }"""
LATER_NEXT=r"""    v397_last_origin=v397_class;
    if(ctx.lr==v395_next_lr)v397_same_lr_seen=1u;
    // A later original call out of the ISFS body after the natural
    // saved-LR PC observation is stronger than aggregate, unordered masks.
    if(v398_site_seen==1u&&v398_site_mapped==1u&&
       v398_pre_cap==1u&&ctx.inst_count>v396_start_inst){
      if(v397_isfs)v399_isfs_after=1u;
      if(v397_parent)v399_parent_after=1u;
    }"""
STOP_NEXT=r'''               <<" blr_verified=0"<<std::endl;
      const bool v399_ordered=v398_site_seen==1u&&
          v398_site_mapped==1u&&v399_isfs_after==1u;
      v399_reported=1u;
      std::cout<<"V399_NAND_RETURN_ORDER site="<<v398_site_seen
               <<" mapped="<<v398_site_mapped
               <<" bctrl="<<v399_bctrl
               <<" isfs_after="<<v399_isfs_after
               <<" parent_after="<<v399_parent_after
               <<" ordered="<<unsigned(v399_ordered)
               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_NEXT=r'''  check(v398_completed,"V398 natural guest return-PC probe not completed");
  const bool v399_completed=v398_completed&&
      nwii::runtime::v399_reported==1u&&
      nwii::runtime::v399_bctrl<=1u&&
      nwii::runtime::v399_isfs_after<=1u&&
      nwii::runtime::v399_parent_after<=1u;
  const bool v399_ordered=nwii::runtime::v398_site_seen==1u&&
      nwii::runtime::v398_site_mapped==1u&&
      nwii::runtime::v399_isfs_after==1u;
  std::cout<<"V399_NAND_RETURN_TRIAL ordered="<<unsigned(v399_ordered)
           <<" completed="<<unsigned(v399_completed)<<std::endl;
  check(v399_completed,"V399 original ISFS continuation classification incomplete");'''
def patch(s:str)->str:
    anchors=(STATE,RESET,CALLSITE,LATER,STOP,TRIAL,
             'V398_NAND_RETURN_PC samples=',
             'V398_NAND_RETURN_TRIAL site=',
             'V397_NAND_ORIGINS mask=',
             'V396_NAND_CB_BODY kind=')
    if (any(s.count(x)!=1 for x in anchors) or
        ENTRY in s or TRIAL_MARKER in s or 'v399_isfs_after' in s):
        raise ValueError("V399 original callsite/source anchor changed")
    out=s.replace(STATE,STATE+'\n'+
         'static unsigned v399_bctrl=0u,v399_isfs_after=0u;\n'+
         'static unsigned v399_parent_after=0u,v399_reported=0u;',1)
    out=out.replace(RESET,RESET+'\n'+
         '  nwii::runtime::v399_bctrl=0u;\n'+
         '  nwii::runtime::v399_isfs_after=0u;\n'+
         '  nwii::runtime::v399_parent_after=0u;\n'+
         '  nwii::runtime::v399_reported=0u;',1)
    out=out.replace(CALLSITE,CALLSITE_NEXT,1)
    out=out.replace(LATER,LATER_NEXT,1)
    out=out.replace(STOP,STOP_NEXT,1)
    out=out.replace(TRIAL,TRIAL_NEXT,1)
    if (out.count(ENTRY)!=1 or out.count(TRIAL_MARKER)!=1 or
        out.count(CALLSITE_NEXT)!=1 or out.count(LATER_NEXT)!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V399 did not preserve original PowerPC route")
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
        print("V399_NAND_RETURN_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V399_NAND_RETURN_ROUTE installed=1 read_only=1 ordered=1 original_opcode_classify=1 no_forced_return=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
