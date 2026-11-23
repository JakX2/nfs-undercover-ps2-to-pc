#!/usr/bin/env python3
"""V398: observe natural guest PC at the saved ISFS-selected callee LR.

Observe the unmodified CPUContext at the pending-callback dispatch boundary
during V396's bounded 24-call window. This does not prove BLR executed,
change guest state, force a PC, or alter any IOS reply. The V396 cap remains.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
STATE='static unsigned v397_same_lr_seen=0u;'
RESET='nwii::runtime::v397_same_lr_seen=0u;'
CALLBACK='bool process_pending_callbacks(CPUContext& ctx){'
STOP=r'''               <<" same_lr_any="<<v397_same_lr_seen<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v397_completed,"V397 guest callback LR lineage witness incomplete");'''
ENTRY="V398_NAND_RETURN_PC samples="
TRIAL_MARKER="V398_NAND_RETURN_TRIAL site="
STATE_ADD='''static unsigned v398_samples=0u,v398_site_seen=0u;
static unsigned v398_site_mapped=0u,v398_pre_cap=0u,v398_reported=0u;'''
RESET_ADD='''  nwii::runtime::v398_samples=0u;
  nwii::runtime::v398_site_seen=0u;
  nwii::runtime::v398_site_mapped=0u;
  nwii::runtime::v398_pre_cap=0u;
  nwii::runtime::v398_reported=0u;'''
PENDING_HOOK=r'''bool process_pending_callbacks(CPUContext& ctx){
  // Never synthesize a guest return. Inspect actual PC at a host boundary.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v394_isfs_seen==1u&&v395_next_seen==1u&&v396_kind==0u&&
     v395_next_lr>=0x804f0e04u&&v395_next_lr<0x804f0f84u&&
     ctx.inst_count>v396_start_inst){
    if(v398_samples<64u)++v398_samples;
    if(ctx.pc==v395_next_lr&&(ctx.pc&3u)==0u){
      v398_site_seen=1u;
      if(ctx.mmu.get_ptr(ctx.pc)!=nullptr)v398_site_mapped=1u;
      if(v396_calls<24u)v398_pre_cap=1u;
    }
  }
'''
STOP_ADD=r'''               <<" same_lr_any="<<v397_same_lr_seen<<std::endl;
      const bool v398_lr_valid=v395_next_lr>=0x804f0e04u&&
          v395_next_lr<0x804f0f84u&&(v395_next_lr&3u)==0u;
      v398_reported=1u;
      std::cout<<"V398_NAND_RETURN_PC samples="<<v398_samples
               <<" site="<<v398_site_seen
               <<" mapped="<<v398_site_mapped
               <<" before_cap="<<v398_pre_cap
               <<" saved_lr_valid="<<unsigned(v398_lr_valid)
               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_ADD=r'''  check(v397_completed,"V397 guest callback LR lineage witness incomplete");
  const bool v398_completed=v397_completed&&
       nwii::runtime::v398_reported==1u&&
       nwii::runtime::v398_samples<=64u&&
       nwii::runtime::v395_next_lr>=0x804f0e04u&&
       nwii::runtime::v395_next_lr<0x804f0f84u;
  std::cout<<"V398_NAND_RETURN_TRIAL site="<<nwii::runtime::v398_site_seen
           <<" completed="<<unsigned(v398_completed)<<std::endl;
  check(v398_completed,"V398 natural guest return-PC probe not completed");'''
def patch(s:str)->str:
    anchors=(STATE,RESET,CALLBACK,STOP,TRIAL,
             "V397_NAND_ORIGINS mask=",
             "V397_NAND_ORIGINS_TRIAL completed=",
             "V396_NAND_CB_BODY kind=",
             "V395_NAND_ISFS_NEXT guest=")
    if (any(s.count(x)!=1 for x in anchors) or
        ENTRY in s or TRIAL_MARKER in s or "v398_site_seen" in s):
        raise ValueError("V398 guest return-PC boundary moved")
    out=s.replace(STATE,STATE+"\n"+STATE_ADD,1)
    out=out.replace(RESET,RESET+"\n"+RESET_ADD,1)
    out=out.replace(CALLBACK,PENDING_HOOK,1)
    out=out.replace(STOP,STOP_ADD,1)
    out=out.replace(TRIAL,TRIAL_ADD,1)
    if (out.count(ENTRY)!=1 or out.count(TRIAL_MARKER)!=1 or
        out.count(PENDING_HOOK)!=1 or out.count(STOP_ADD)!=1 or
        out.count("V397_NAND_ORIGINS mask=")!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V398 did not preserve original guest route")
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
        print("V398_NAND_RETURN_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V398_NAND_RETURN_ROUTE installed=1 read_only=1 original_guest=1 capped=24 no_forced_pc=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
