#!/usr/bin/env python3
"""V401: classify original PPC caller instruction at the saved ISFS LR.

V399 authenticated natural guest-PC resumption and ordered ISFS-origin
calls, but the saved return address's preceding instruction was not bcctrl.
Classify direct BL, conditional BCL, BCLRL, BCCTRL, and other guest opcodes
read-only. For direct branches, independently compare the calculated PPC
target to the actual V395 guest-selected callee address.

Never emit proprietary instruction words/targets, change guest state,
or claim the selected callee's BLR executed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
STATE="static unsigned v400_link=0u,v400_parent_after=0u,v400_reported=0u;"
RESET="nwii::runtime::v400_reported=0u;"
WORD="        const uint32_t v399_call=ctx.mmu.read32(ctx.pc-4u);"
STOP='''               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v400_completed,"V400 original parent return-PC classification incomplete");'''
ENTRY="V401_NAND_CALLSITE mapped="
TRIAL_MARKER="V401_NAND_CALLSITE_TRIAL kind="
WORD_NEXT=r"""        const uint32_t v399_call=ctx.mmu.read32(ctx.pc-4u);
        // Read-only PPC instruction class, never export raw guest code.
        v401_mapped=1u;
        const uint32_t v401_op=v399_call>>26;
        const uint32_t v401_xo=(v399_call>>1)&1023u;
        if((v399_call&1u)==0u)v401_kind=5u;
        else if(v401_op==18u)v401_kind=1u; // direct BL
        else if(v401_op==16u)v401_kind=2u; // conditional BCL
        else if(v401_op==19u&&v401_xo==16u)v401_kind=3u;
        else if(v401_op==19u&&v401_xo==528u)v401_kind=4u;
        else v401_kind=5u;
        if(v401_kind==1u||v401_kind==2u){
          uint32_t disp=v401_kind==1u?
              (v399_call&0x03fffffcu):(v399_call&0xfffcu);
          if(v401_kind==1u&&(disp&0x02000000u)!=0u)
            disp|=0xfc000000u;
          if(v401_kind==2u&&(disp&0x8000u)!=0u)
            disp|=0xffff0000u;
          const uint32_t target=(v399_call&2u)!=0u?
              disp:((ctx.pc-4u)+disp);
          if(target==v395_next_pc)v401_direct_match=1u;
        }"""
STOP_NEXT=r'''               <<" blr_verified=0"<<std::endl;
      v401_reported=1u;
      std::cout<<"V401_NAND_CALLSITE mapped="<<v401_mapped
               <<" kind="<<v401_kind
               <<" direct_match="<<v401_direct_match
               <<" selected_site="<<v398_site_seen
               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL_NEXT=r'''  check(v400_completed,"V400 original parent return-PC classification incomplete");
  const bool v401_completed=v400_completed&&
      nwii::runtime::v401_reported==1u&&
      nwii::runtime::v401_kind<=5u&&
      nwii::runtime::v401_mapped<=1u&&
      nwii::runtime::v401_direct_match<=1u;
  std::cout<<"V401_NAND_CALLSITE_TRIAL kind="<<nwii::runtime::v401_kind
           <<" completed="<<unsigned(v401_completed)<<std::endl;
  check(v401_completed,"V401 original PPC linksite classification incomplete");'''
def patch(s:str)->str:
    anchors=(STATE,RESET,WORD,STOP,TRIAL,
             "V400_NAND_PARENT_RESUME site=",
             "V399_NAND_RETURN_ORDER site=",
             "V398_NAND_RETURN_PC samples=")
    if (any(s.count(x)!=1 for x in anchors) or
        ENTRY in s or TRIAL_MARKER in s or "v401_direct_match" in s):
        raise ValueError("V401 original PowerPC callsite seam changed")
    out=s.replace(STATE,STATE+"\n"+
       "static unsigned v401_mapped=0u,v401_kind=0u;\n"+
       "static unsigned v401_direct_match=0u,v401_reported=0u;",1)
    out=out.replace(RESET,RESET+"\n"+
       "  nwii::runtime::v401_mapped=0u;\n"+
       "  nwii::runtime::v401_kind=0u;\n"+
       "  nwii::runtime::v401_direct_match=0u;\n"+
       "  nwii::runtime::v401_reported=0u;",1)
    out=out.replace(WORD,WORD_NEXT,1)
    out=out.replace(STOP,STOP_NEXT,1)
    out=out.replace(TRIAL,TRIAL_NEXT,1)
    if (out.count(ENTRY)!=1 or out.count(TRIAL_MARKER)!=1 or
        out.count(WORD_NEXT)!=1 or out.count(STOP_NEXT)!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V401 modified original guest execution")
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
        print("V401_NAND_CALLSITE_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V401_NAND_CALLSITE_ROUTE installed=1 guest_opcode_read_only=1 targets_hidden=1 no_forced_return=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
