#!/usr/bin/env python3
"""V298: disarm only the stale V177/178 reply observer after V250 NAND proof.

V297 authenticated a restored NAND child -> 0x8051D20C call. The
inherited V178 observer compares that later call with a V177-only
0x80545100 proof. Scope the observer only after the authentic V250
NAND entry, without changing game code, guest state or callback results.
"""
from __future__ import annotations
import argparse
from pathlib import Path

OLD=("  if(v176_next_seen==1u&&v177_next_seen==0u&&\n"
     "     addr>=0x80400000u&&addr<0x80600000u){")
NEW=("  if(v176_next_seen==1u&&v177_next_seen==0u&&\n"
     "     (!v250_candidate_mode||v250_nand_seen==0u)&&\n"
     "     addr>=0x80400000u&&addr<0x80600000u){")
CHECK="V178 owner-original SC reply callee differs from V177 proof"
SUBMIT_OLD="   if(!submit72_active||v177_next_seen==1u)return false;"
SUBMIT_NEW=("   if(!submit72_active||v177_next_seen==1u||\n"
            "      (v250_candidate_mode&&v250_nand_seen==1u))return false;")

def patch(source: str) -> str:
    if (source.count(OLD)!=1 or source.count(SUBMIT_OLD)!=1 or
        source.count(CHECK)!=1 or
        source.count("V296_SERVICE_ENTRY kind=")!=1 or
        "v250_nand_seen" not in source):
        raise ValueError("V298 authenticated reply phase seam changed")
    output=source.replace(OLD,NEW,1).replace(SUBMIT_OLD,SUBMIT_NEW,1)
    if output.count(NEW)!=1 or output.count(SUBMIT_NEW)!=1 or output.count(CHECK)!=1:
        raise ValueError("V298 scoped observer geometry")
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_harness",type=Path)
    p.add_argument("private_scoped_harness",type=Path)
    a=p.parse_args()
    with a.private_scoped_harness.open("x",encoding="utf-8") as dst:
        dst.write(patch(a.public_harness.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
