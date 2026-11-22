#!/usr/bin/env python3
"""V261 original-free instrumentation of V260's already-verified 64 calls.

This pass does NOT widen V260's bound or move its guest stop point. The
private owner log contains bounded entry PC/LR and instruction counters only;
the public workflow emits aggregate statistics instead.
"""
import argparse
from pathlib import Path
from derive_v260_ipc_ppcmsg_boundary_harness import (
    derive as previous, FRONTIER_OBSERVER as PRIOR_FRONTIER,
)
from derive_v194_osrestore_next_harness import once

ANCHOR = '''    ++v260_post_calls;'''
INSTRUMENTED = '''    ++v260_post_calls;
    // V261: exact guest-call census, original MMIO and CPU unchanged.
    // The bounded log remains owner-private; report only aggregates.
    if(v260_post_calls<=64u){
      std::cout<<"V261_CALL n="<<v260_post_calls
               <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
               <<std::dec<<" inst="<<ctx.inst_count<<std::endl;
    }'''


def derive(source: str) -> str:
    s = previous(source)
    if PRIOR_FRONTIER.count(ANCHOR) != 1 or s.count(PRIOR_FRONTIER) != 1:
        raise ValueError("V261 owner-verified V260 64-call instrumentation changed")
    return once(s, PRIOR_FRONTIER, PRIOR_FRONTIER.replace(ANCHOR, INSTRUMENTED, 1))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    with a.output.open("x", encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
