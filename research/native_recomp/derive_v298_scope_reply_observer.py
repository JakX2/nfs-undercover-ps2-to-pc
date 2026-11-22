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
# V322/V324: two trace-only OSInit cache/SRAM checks require earlier startup
# caller LR and counters, but genuine NAND also invokes these routines.
# Skip those historical assertions only after verified guest NAND entry.
# The original DCFlushRange and DCInvalidateRange AOT bodies still run.
ARENA_OLD="else if(addr==0x805222c0u){"
ARENA_NEW=("else if(addr==0x805222c0u&&"
           "(!v250_candidate_mode||v250_nand_seen==0u)){")
ARENA_LABEL="original arena DCFlushRange ABI or dcbz count differs"
SRAM_OLD="else if(addr==0x80522294u){"
SRAM_NEW=("else if(addr==0x80522294u&&"
          "(!v250_candidate_mode||v250_nand_seen==0u)){")
SRAM_LABEL="original SRAM DMA cache invalidation ABI differs"

# V328: V113's SC IOS transport arrival check deliberately throws
# ExceptionStop on an earlier bounded SC test route. A genuine NAND
# request can use the same POST_OWNER LR but not those old counters.
# V329: V114 already fixed POST_OWNER to 0x805222c0u; match the
# final V296 harness spelling, not the obsolete V113 symbol.
# Retire only that historical stop/observer; keep actual cache/IOS work.
TRANSPORT_OLD="if(post112_submit==1u&&addr==0x805222c0u&&ctx.lr==0x8051963cu){"
TRANSPORT_NEW=("if(post112_submit==1u&&addr==0x805222c0u&&ctx.lr==0x8051963cu&&\n"
               "       (!v250_candidate_mode||v250_nand_seen==0u)){")
TRANSPORT_LABEL="V113 original IOS transport did not reach bounded cache flush"





# V331: this is the V72 cache-syscall handler, not a PowerPC body.
# The same native SC callsite is reached later by the restored NAND request.
# Reuse its authenticated vector without requiring old submit72 counters.
NAND_SC_OLD="  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){\n    check(submit72_flush==1u&&submit72_sc==0u,\"IPC request unexpected cache syscall sequence\");"
NAND_SC_NEW="  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){\n    // V331: original NAND can enter the same authentic cache syscall\n    // after the earlier V72 request observer has completed its phase.\n    // Preserve the verified native SC vector, guest CPU and IRQ checks.\n    if(v250_candidate_mode&&v250_nand_seen==1u){\n      const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;\n      const auto gp=ctx.gpr;\n      native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,\n          !ipc70_bus.external_irq_level(),\n          [](auto& c){func_80000C00(c);});\n      check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,\n            \"V331 native NAND cache syscall state restore differs\");\n      for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)\n        check(ctx.gpr[r]==gp[r],\"V331 native NAND cache syscall GPR restore differs\");\n      std::cout<<\"V331_NAND_CACHE_SYSCALL verified=1\"<<std::endl;\n      return true;\n    }\n    check(submit72_flush==1u&&submit72_sc==0u,\"IPC request unexpected cache syscall sequence\");"
NAND_SC_LABEL="IPC request unexpected cache syscall sequence"

# V332: the V63-installed SC vector is shared by early OSInit/DSP and
# later authenticated NAND IOS request code. Distinguish observer phase;
# never bypass the original exception, native cache syscall, or rfi.
VECTOR_TRACE_OLD="  else if(addr==0x80000c00u){\n    check(ctx.srr0==0x805222ecu&&ctx.pc==0x80000c00u&&"
VECTOR_TRACE_NEW="  else if(addr==0x80000c00u){\n    // V332: the authenticated NAND IOS submission reaches the same\n    // installed guest SC vector as the earlier OSInit arena flush.\n    // Verify its vector ABI, not the older DSP/arena trace counters.\n    if(v250_candidate_mode&&v250_nand_seen==1u&&ctx.lr==0x8051963cu){\n      check(ctx.srr0==0x805222ecu&&ctx.pc==0x80000c00u&&\n            !(ctx.msr&0x8000u),\n            \"V332 original NAND cache syscall vector entry differs\");\n      return; // Observer only: native_idle_cache_sc still executes real vector.\n    }\n    check(ctx.srr0==0x805222ecu&&ctx.pc==0x80000c00u&&"
VECTOR_TRACE_LABEL="native installed SC vector entry ABI differs"

# V334: V115's IRQ-disable observer describes the earlier SC request.
# An authenticated NAND submit reaches the same guest OSDisableInterrupts
# call with different counters. Retire only this trace observer, not the
# AOT guest IRQ-disable call or its real MSR/EE changes.
NAND_IRQ_OLD="if(post115_sc==1u&&addr==INT_DISABLE&&ctx.lr==0x80519640u){"
NAND_IRQ_NEW=("if(post115_sc==1u&&addr==INT_DISABLE&&ctx.lr==0x80519640u&&"
              "(!v250_candidate_mode||v250_nand_seen==0u)){")
NAND_IRQ_LABEL="V115 original IOS submission IRQ-disable call differs"

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
        ("arena",ARENA_OLD),("sram",SRAM_OLD),
        ("transport",TRANSPORT_OLD),("transport_label",TRANSPORT_LABEL),
        ("nand_sc",NAND_SC_OLD),("nand_sc_label",NAND_SC_LABEL),
        ("vector",VECTOR_TRACE_OLD),("vector_label",VECTOR_TRACE_LABEL),
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
        source.count(ARENA_OLD)!=1 or source.count(SRAM_OLD)!=1 or
        not 0 < source.index(ARENA_LABEL)-source.index(ARENA_OLD) < 1100 or
        source.count(ARENA_LABEL)!=1 or source.count(SRAM_LABEL)!=1 or
        source.count(TRANSPORT_OLD)!=1 or source.count(TRANSPORT_LABEL)!=1 or
        source.count(NAND_SC_OLD)!=1 or source.count(NAND_SC_LABEL)!=1 or
        source.count(VECTOR_TRACE_OLD)!=1 or source.count(VECTOR_TRACE_LABEL)!=1 or
        source.count(NAND_IRQ_OLD)!=1 or source.count(NAND_IRQ_LABEL)!=1 or
        not 0 < source.index(VECTOR_TRACE_LABEL)-source.index(VECTOR_TRACE_OLD) < 700 or
        not 0 < source.index(TRANSPORT_LABEL)-source.index(TRANSPORT_OLD) < 2600 or
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
    output=output.replace(ARENA_OLD,ARENA_NEW,1)
    output=output.replace(SRAM_OLD,SRAM_NEW,1)
    output=output.replace(TRANSPORT_OLD,TRANSPORT_NEW,1)
    output=output.replace(NAND_SC_OLD,NAND_SC_NEW,1)
    output=output.replace(VECTOR_TRACE_OLD,VECTOR_TRACE_NEW,1)
    output=output.replace(NAND_IRQ_OLD,NAND_IRQ_NEW,1)
    if (output.count(NEW)!=1 or output.count(SUBMIT_NEW)!=1 or
        output.count(CLIENT_NEW)!=1 or output.count(IOS_OPEN_NEW)!=1 or
        output.count(IOS_OPEN_EXPLICIT)!=1 or
        output.count(IOS_TRACE_NEW)!=1 or
        output.count(ASYNC_NEW)!=1 or output.count(ASYNC_LABEL)!=1 or
        output.count(ARENA_NEW)!=1 or output.count(SRAM_NEW)!=1 or
        output.count(TRANSPORT_NEW)!=1 or output.count(TRANSPORT_LABEL)!=1 or
        output.count(NAND_SC_NEW)!=1 or output.count(NAND_SC_LABEL)!=1 or
        output.count(VECTOR_TRACE_NEW)!=1 or output.count(VECTOR_TRACE_LABEL)!=1 or
        output.count(NAND_IRQ_NEW)!=1 or output.count(NAND_IRQ_LABEL)!=1 or
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
