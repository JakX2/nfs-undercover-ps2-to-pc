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
# different (authentic) LR. Guard only the allocator-tail observation
# that falsely asserted during authenticated NAND execution.
# V315: patch the one original V71 allocator-tail observation, even if
# preceding research derivations rename or rewrite the observer function.
IOS_OPEN_OLD="if(addr==0x8051ad38u){"
IOS_OPEN_NEW=("if(addr==0x8051ad38u&&"
              "!(v250_candidate_mode&&v250_nand_seen==1u)){")
IOS_OPEN_LABEL="native IOS_Open allocator tail entry differs"
IOS_OPEN_EXPLICIT="if(addr==0x80519944u){stm70_open_entry(ctx);return;}"
# V318: the V71 observer is only valid during its original IOS_Open
# initialization. Keep the explicit original IOS_Open entry unchanged,
# but do not send authenticated NAND calls through its historical checks.
IOS_TRACE_OLD="if(open71_trace(addr,ctx))return;"
IOS_TRACE_NEW=(
    "if((!v250_candidate_mode||v250_nand_seen==0u)&&"
    "open71_trace(addr,ctx))return;"
)
# V320: V112 IOS_OpenAsync instrumentation is a proof for the earlier SC
# request, not a global allocator/interrupt ABI contract. Do not run it
# after verified original NAND child entry. Original guest calls proceed.
ASYNC_OLD="if(post111_open==1u&&post110_chosen==2u){"
ASYNC_NEW=("if(post111_open==1u&&post110_chosen==2u&&\n"
           "       (!v250_candidate_mode||v250_nand_seen==0u)){")
ASYNC_LABEL="V112 original IOS_OpenAsync allocator disable differs"



SUBMIT_OLD="   if(!submit72_active||v177_next_seen==1u)return false;"
SUBMIT_NEW=("   if(!submit72_active||v177_next_seen==1u||\n"
            "      (v250_candidate_mode&&v250_nand_seen==1u))return false;")

def summarize_seams(source: str) -> str:
    # Emit only counts of independently written public harness anchors.
    # Never print the source, original PowerPC words or native guest output.
    items=(
        ("reply",OLD),("submit",SUBMIT_OLD),("client",CLIENT_OLD),
        ("ios",IOS_OPEN_OLD),("ios_label",IOS_OPEN_LABEL),
        ("ios_call",IOS_TRACE_OLD),
        ("async",ASYNC_OLD),("async_label",ASYNC_LABEL),
        ("explicit",IOS_OPEN_EXPLICIT),
        ("check",CHECK),("service","V296_SERVICE_ENTRY kind=")
    )
    return "V313_HARNESS_ANCHORS "+" ".join(
        f"{key}={min(source.count(value),2)}" for key,value in items
    )+f" nand={int('v250_nand_seen' in source)} near={min(len(nearby_ios_tails(source)),2)}"

def nearby_ios_tails(source: str) -> list[int]:
    # No source, instruction bytes, or guest state are exported.
    if source.count(IOS_OPEN_LABEL)!=1:
        return []
    label_at=source.index(IOS_OPEN_LABEL)
    starts=[]
    at=0
    while (at:=source.find(IOS_OPEN_OLD,at))!=-1:
        if 0<label_at-at<300:
            starts.append(at)
        at+=len(IOS_OPEN_OLD)
    return starts

def choose_ios_tail(source: str) -> int:
    # Two branches may have the same address. Select only the one
    # associated with the unique historical V71 allocator assertion.
    starts=nearby_ios_tails(source)
    if len(starts)!=1:
        raise ValueError("V316 ambiguous V71 allocator-tail branch")
    return starts[0]

def patch(source: str) -> str:
    if (source.count(OLD)!=1 or source.count(SUBMIT_OLD)!=1 or
        source.count(CLIENT_OLD)!=1 or
        source.count(IOS_OPEN_EXPLICIT)!=1 or
        source.count(IOS_TRACE_OLD)!=1 or
        source.count(ASYNC_OLD)!=1 or source.count(ASYNC_LABEL)!=1 or
        not 0 < source.index(ASYNC_LABEL)-source.index(ASYNC_OLD) < 2600 or
        source.count(IOS_OPEN_LABEL)!=1 or
        source.count(CHECK)!=1 or
        source.count("V296_SERVICE_ENTRY kind=")!=1 or
        "v250_nand_seen" not in source):
        raise ValueError("V298 authenticated reply phase seam changed")
    output=(source.replace(OLD,NEW,1)
            .replace(SUBMIT_OLD,SUBMIT_NEW,1)
            .replace(CLIENT_OLD,CLIENT_NEW,1))
    pos=choose_ios_tail(output)
    output=output[:pos]+IOS_OPEN_NEW+output[pos+len(IOS_OPEN_OLD):]
    output=output.replace(IOS_TRACE_OLD,IOS_TRACE_NEW,1)
    output=output.replace(ASYNC_OLD,ASYNC_NEW,1)
    if (output.count(NEW)!=1 or output.count(SUBMIT_NEW)!=1 or
        output.count(CLIENT_NEW)!=1 or output.count(IOS_OPEN_NEW)!=1 or
        output.count(IOS_OPEN_EXPLICIT)!=1 or
        output.count(IOS_TRACE_NEW)!=1 or
        output.count(ASYNC_NEW)!=1 or output.count(ASYNC_LABEL)!=1 or
        output.count(IOS_OPEN_LABEL)!=1 or output.count(CHECK)!=1):
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
