#!/usr/bin/env python3
"""V402: independently continue authenticated original Wii code to 48 calls.

Do not change the proven V401 24-call owner process. Instead transform a
second, scratch-only harness to a 48-call limit and link it against the
same authenticated generated Wii AOT code. Preserve the original NAND,
IOS, PPC registers, memory, return routing and old 24-call evidence gate.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

SEAMS={
    'if(owned||v396_calls==24u){':'if(owned||v396_calls==48u){',
    'const bool bounded=!owned&&v396_calls==24u;':
        'const bool bounded=!owned&&v396_calls==48u;',
    'nwii::runtime::v396_calls==24u':
        'nwii::runtime::v396_calls==48u',
    'nwii::runtime::v396_calls<=24u':
        'nwii::runtime::v396_calls<=48u',
}
STOP='''               <<" blr_verified=0"<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
STOP_NEW='''               <<" blr_verified=0"<<std::endl;
      std::cout<<"V402_NAND_LONG_STOP calls="<<v396_calls
               <<" owner="<<unsigned(owned)
               <<" selected_return="<<v398_site_seen
               <<" parent_return="<<v400_parent_site<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};'''
TRIAL='''  check(v401_completed,"V401 original PPC linksite classification incomplete");'''
TRIAL_NEW=r'''  check(v401_completed,"V401 original PPC linksite classification incomplete");
  const bool v402_completed=v401_completed&&
      ((nwii::runtime::v396_kind==1u&&
        nwii::runtime::v396_calls>=1u&&
        nwii::runtime::v396_calls<=48u)||
       (nwii::runtime::v396_kind==2u&&
        nwii::runtime::v396_calls==48u))&&
      nwii::runtime::v398_site_seen==1u&&
      nwii::runtime::v400_parent_site==1u;
  std::cout<<"V402_NAND_LONG_TRIAL calls="<<nwii::runtime::v396_calls
           <<" kind="<<nwii::runtime::v396_kind
           <<" complete="<<unsigned(v402_completed)<<std::endl;
  check(v402_completed,"V402 extended original guest frontier incomplete");'''
MARKER="V402_NAND_LONG_STOP calls="
TRIAL_MARKER="V402_NAND_LONG_TRIAL calls="
def patch(source:str)->str:
    if (MARKER in source or TRIAL_MARKER in source or
        source.count("V401_NAND_CALLSITE mapped=")!=1 or
        source.count("V401_NAND_CALLSITE_TRIAL kind=")!=1 or
        source.count("try{run_game(c);}")!=1):
        # A changed original guest execution loop must fail closed.
        raise ValueError("V402 original bounded harness geometry changed")
    s=source
    for old,new in SEAMS.items():
        if s.count(old)!=1:
            raise ValueError("V402 previous 24-call cap/proof changed")
        s=s.replace(old,new,1)
    if s.count(STOP)!=1 or s.count(TRIAL)!=1:
        raise ValueError("V402 stop or trial witness changed")
    s=s.replace(STOP,STOP_NEW,1).replace(TRIAL,TRIAL_NEW,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL_MARKER)!=1 or
        s.count("V401_NAND_CALLSITE mapped=")!=1 or
        s.count("V396_NAND_CB_BODY kind=")!=1 or
        s.count("V370_NAND_FLAG_W1C n=")!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count('if(owned||v396_calls==48u){')!=1):
        raise ValueError("V402 AOT guest-state route not preserved")
    return s
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        with a.next_private_harness.open("x",encoding="utf-8") as f:
            f.write(patch(a.prior_private_harness.read_text(encoding="utf-8")))
    except (ValueError,OSError):
        print("V402_LONG_FRONTIER_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V402_LONG_FRONTIER_ROUTE installed=1 source=original_guest cap=48 baseline_preserved=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
