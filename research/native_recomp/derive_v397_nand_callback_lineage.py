#!/usr/bin/env python3
"""V397: classify original guest LR callsite origins, never infer a return."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
STATE="static uint32_t v396_stop_pc=0u,v396_stop_lr=0u;"
RESET="nwii::runtime::v396_stop_lr=0u;"
COUNT="    ++v396_calls;\n    if(owned||v396_calls==24u){"
STOP="""      check(verified,
            "V396 original callback body next guest entry not verified");
      ctx.is_running=false;throw ExceptionStop{};"""
PREVIOUS='''  check(v396_completed,
        "V396 original guest-selected ISFS callback did not reach next call");'''
MARKER="V397_NAND_ORIGINS mask="
TRIAL="V397_NAND_ORIGINS_TRIAL completed="
COUNT_NEW=r"""    ++v396_calls;
    // Caller LR range is observational; it cannot prove function return.
    const bool v397_selected=ctx.lr>=v395_next_pc&&
         ctx.lr-v395_next_pc<0x800u&&(ctx.lr&3u)==0u;
    const bool v397_isfs=ctx.lr>=0x804f0e04u&&
         ctx.lr<0x804f0f84u&&(ctx.lr&3u)==0u;
    const bool v397_parent=ctx.lr>=0x805192acu&&
         ctx.lr<0x80519318u&&(ctx.lr&3u)==0u;
    const unsigned v397_class=v397_selected?1u:
         (v397_isfs?2u:(v397_parent?3u:4u));
    v397_origin_mask|=(1u<<(v397_class-1u));
    v397_last_origin=v397_class;
    if(ctx.lr==v395_next_lr)v397_same_lr_seen=1u;
    if(owned||v396_calls==24u){"""
STOP_NEW=r"""      check(verified,
            "V396 original callback body next guest entry not verified");
      std::cout<<"V397_NAND_ORIGINS mask="<<v397_origin_mask
               <<" last="<<v397_last_origin
               <<" calls="<<v396_calls
               <<" selected_any="<<unsigned((v397_origin_mask&1u)!=0u)
               <<" isfs_any="<<unsigned((v397_origin_mask&2u)!=0u)
               <<" parent_any="<<unsigned((v397_origin_mask&4u)!=0u)
               <<" other_any="<<unsigned((v397_origin_mask&8u)!=0u)
               <<" same_lr_any="<<v397_same_lr_seen<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};"""
PROOF=r"""  const bool v397_completed=v396_completed&&
       nwii::runtime::v397_origin_mask!=0u&&
       nwii::runtime::v397_last_origin>=1u&&
       nwii::runtime::v397_last_origin<=4u&&
       nwii::runtime::v396_calls>=1u&&
       nwii::runtime::v396_calls<=24u;
  std::cout<<"V397_NAND_ORIGINS_TRIAL completed="
           <<unsigned(v397_completed)
           <<" stopped="<<unsigned(!c.is_running)<<std::endl;
  check(v397_completed,"V397 guest callback LR lineage witness incomplete");"""
def patch(src:str)->str:
    if any(src.count(s)!=1 for s in
           (STATE,RESET,COUNT,STOP,PREVIOUS,"V396_NAND_CB_BODY kind=",
            "V396_NAND_CB_TRIAL kind=","V395_NAND_ISFS_NEXT guest=")):
        raise ValueError("V397 selected-callee source seam moved")
    if MARKER in src or TRIAL in src or "v397_origin_mask" in src:
        raise ValueError("V397 already applied")
    s=src.replace(STATE,STATE+"\n"+
       "static unsigned v397_origin_mask=0u,v397_last_origin=0u;"+
       "\nstatic unsigned v397_same_lr_seen=0u;",1)
    s=s.replace(RESET,RESET+"\n"+
       "  nwii::runtime::v397_origin_mask=0u;\n"+
       "  nwii::runtime::v397_last_origin=0u;\n"+
       "  nwii::runtime::v397_same_lr_seen=0u;",1)
    s=s.replace(COUNT,COUNT_NEW,1).replace(STOP,STOP_NEW,1)
    s=s.replace(PREVIOUS,PREVIOUS+"\n"+PROOF,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or
        s.count(COUNT_NEW)!=1 or s.count(STOP_NEW)!=1 or
        s.count("V396_NAND_CB_BODY kind=")!=1 or
        s.count("try{run_game(c);}")!=src.count("try{run_game(c);}") or
        s.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V397 altered the original guest route")
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
        print("V397_NAND_ORIGINS_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V397_NAND_ORIGINS_ROUTE installed=1 guest_lr_only=1 cap=24 no_return_claim=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
