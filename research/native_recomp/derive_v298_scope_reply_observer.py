#!/usr/bin/env python3
"""V298: retire historical reply, submit, and IPC client observers after NAND proof.

V297 authenticated a restored NAND child -> 0x8051D20C call. The
inherited V178 observer compares that later call with a V177-only
0x80545100 proof. The V77 submit and client catch-all observers also
outlive their intended IPC phase. Scope the stale observers
after authentic V250 NAND entry. Preserve explicit IPC client entry
handling and all original guest code, registers and IOS responses.
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
CLIENT_OLD="   if((ipc69_active&&v177_next_seen==0u)||addr==0x805194c4u){ipc69_entry(addr,ctx);return;}"
CLIENT_NEW=("   if((ipc69_active&&v177_next_seen==0u&&"
            "(!v250_candidate_mode||v250_nand_seen==0u))||"
            "addr==0x805194c4u){ipc69_entry(addr,ctx);return;}")
# V311: V71 IOS_Open allocator observer is bound to the old startup
# request. The original NAND path calls its allocator tail again with a
# different (authentic) LR. Gate the public observer at its entry, not
# at the old first condition which prior derivations have already changed.
IOS_OPEN_OLD="  static bool open71_trace(uint32_t addr,CPUContext&ctx){"
IOS_OPEN_NEW=(IOS_OPEN_OLD+"\n"+
              "    if(v250_candidate_mode&&v250_nand_seen==1u)return false;")
IOS_OPEN_EXPLICIT="if(addr==0x80519944u){stm70_open_entry(ctx);return;}"

SUBMIT_OLD="   if(!submit72_active||v177_next_seen==1u)return false;"
SUBMIT_NEW=("   if(!submit72_active||v177_next_seen==1u||\n"
            "      (v250_candidate_mode&&v250_nand_seen==1u))return false;")

def summarize_seams(source: str) -> str:
    # Emit only counts of independently written public harness anchors.
    # Never print the source, original PowerPC words or native guest output.
    items=(
        ("reply",OLD),("submit",SUBMIT_OLD),("client",CLIENT_OLD),
        ("ios",IOS_OPEN_OLD),("explicit",IOS_OPEN_EXPLICIT),
        ("check",CHECK),("service","V296_SERVICE_ENTRY kind=")
    )
    return "V313_HARNESS_ANCHORS "+" ".join(
        f"{key}={min(source.count(value),2)}" for key,value in items
    )+f" nand={int('v250_nand_seen' in source)}"

def patch(source: str) -> str:
    if (source.count(OLD)!=1 or source.count(SUBMIT_OLD)!=1 or
        source.count(CLIENT_OLD)!=1 or
        source.count(IOS_OPEN_OLD)!=1 or source.count(IOS_OPEN_EXPLICIT)!=1 or
        source.count(CHECK)!=1 or
        source.count("V296_SERVICE_ENTRY kind=")!=1 or
        "v250_nand_seen" not in source):
        raise ValueError("V298 authenticated reply phase seam changed")
    output=(source.replace(OLD,NEW,1)
            .replace(SUBMIT_OLD,SUBMIT_NEW,1)
            .replace(CLIENT_OLD,CLIENT_NEW,1)
            .replace(IOS_OPEN_OLD,IOS_OPEN_NEW,1))
    if (output.count(NEW)!=1 or output.count(SUBMIT_NEW)!=1 or
        output.count(CLIENT_NEW)!=1 or output.count(IOS_OPEN_NEW)!=1 or
        output.count(IOS_OPEN_EXPLICIT)!=1 or output.count(CHECK)!=1):
        raise ValueError("V298 scoped observer geometry")
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("public_harness",type=Path)
    p.add_argument("private_scoped_harness",type=Path)
    a=p.parse_args()
    raw=a.public_harness.read_text(encoding="utf-8")
    try:
        scoped=patch(raw)
    except ValueError:
        import sys
        print(summarize_seams(raw),file=sys.stderr)
        raise
    with a.private_scoped_harness.open("x",encoding="utf-8") as dst:
        dst.write(scoped)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
