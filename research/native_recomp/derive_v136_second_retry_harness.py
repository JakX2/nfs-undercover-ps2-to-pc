#!/usr/bin/env python3
"""V136 exercise a second original SC status check before a bounded third entry.

The first completed retry has been verified by V131/V133. This extension
allows one additional complete original function invocation, including the
original interrupt-disable/restore calls. It never mutates guest SC state.
"""
import argparse
from pathlib import Path
from derive_v133_sc_sda_harness import derive as previous

STATE_ANCHOR = " static uint32_t post130_pc=0,post130_lr=0;"
RESET_ANCHOR = (
    "nwii::runtime::post130_next=nwii::runtime::post130_pc="
    "nwii::runtime::post130_lr=0;"
)
STOP_ANCHOR = """     post130_pc=addr;post130_lr=ctx.lr;++post130_next;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""

STOP_REPLACEMENT = """     post130_pc=addr;post130_lr=ctx.lr;++post130_next;return;
   }
   if(post130_next==1u&&addr==0x805265acu){
     ++post136_disable;
     check(post136_disable==1u&&post136_restore==0u,
           "V136 second original SC critical section out of order");
     return;
   }
   if(post130_next==1u&&addr==0x805265d4u){
     ++post136_restore;
     check(post136_disable==1u&&post136_restore==1u,
           "V136 second original SC restore mismatch");
     return;
   }
   if(post130_next==1u&&addr==0x8052f830u){
     const uint32_t status_addr=ctx.gpr[13]-3176u;
     const bool mapped=ctx.mmu.get_ptr(status_addr)!=nullptr;
     const uint32_t status=mapped?uint32_t(ctx.mmu.read8(status_addr)):256u;
     const bool route=(ctx.lr==0x80520970u&&post136_disable==1u&&
           post136_restore==1u&&post129_next==1u&&post128_next==1u);
     std::cout<<"V136_SECOND_PASS pc="<<std::hex<<addr<<" lr="<<ctx.lr
              <<std::dec<<" status="<<status<<" r3="<<ctx.gpr[3]
              <<" eq="<<ctx.cr[0].eq<<" disable="<<post136_disable
              <<" restore="<<post136_restore<<" route="<<route<<std::endl;
     check(mapped&&status==1u&&ctx.gpr[3]==1u&&ctx.cr[0].eq&&route,
           "V136 second authentic SC retry did not preserve pending state");
     ++post136_seen;
     post90_target=addr;observed_stop_pc=ctx.pc;
     ++post_stops;ctx.is_running=false;throw ExceptionStop{};
   }"""


def one_replace(s: str, old: str, new: str, purpose: str) -> str:
    n = s.count(old)
    if n != 1:
        raise ValueError(f"V136 {purpose} anchor expected once, got {n}")
    return s.replace(old, new, 1)


def derive(source: str) -> str:
    s = previous(source)
    s = one_replace(
        s, STATE_ANCHOR,
        STATE_ANCHOR + "\n static unsigned post136_disable=0,post136_restore=0,post136_seen=0;",
        "guest observer variables"
    )
    s = one_replace(s, STOP_ANCHOR, STOP_REPLACEMENT, "second SC entry stop")
    s = one_replace(
        s, RESET_ANCHOR,
        RESET_ANCHOR + "\n     nwii::runtime::post136_disable=nwii::runtime::post136_restore="
        "nwii::runtime::post136_seen=0;",
        "per-trial reset"
    )
    # The earlier regression checks remain intact, but third entry now
    # becomes the test-owned stop rather than the second-entry boundary.
    return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
