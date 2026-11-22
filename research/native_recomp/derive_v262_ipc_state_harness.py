#!/usr/bin/env python3
"""V262 read-only Wii interrupt and IOS-state census at V261 64-call frontier.

Derive directly from V260 and compose V261/V262 sampling in one edit.
This avoids the deep recursive milestone-generator chain without changing
any original PowerPC function, instruction, host return or MMIO behavior.
"""
import argparse
from pathlib import Path
from derive_v260_ipc_ppcmsg_boundary_harness import (
    derive as previous, FRONTIER_OBSERVER as PRIOR_FRONTIER,
)
from derive_v261_guest_call_census_harness import (
    ANCHOR as PRIOR_ANCHOR, INSTRUMENTED as PRIOR_CENSUS,
)
from derive_v194_osrestore_next_harness import once

LAST_CALL='''               <<std::dec<<" inst="<<ctx.inst_count<<std::endl;'''
STATE_OBSERVER='''      // V262 owner-only observation; do not mutate IPC or guest state.
      using V262Bus=undercover::wii::IosBus;
      const bool v262_map=ctx.mmu.get_ptr(ctx.gpr[13]-3176u)!=nullptr;
      const uint32_t v262_sc=v262_map?ctx.mmu.read8(ctx.gpr[13]-3176u):0u;
      const bool v262_reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
      const bool v262_ee=(ctx.msr&V262Bus::MSR_EE)!=0u;
      const bool v262_irq=ipc70_bus.external_irq_level();
      const bool v262_request=ipc70_bus.pending_native_ios_request();
      const auto v262_queue=ipc70_bus.services().queued_replies();
      std::cout<<"V262_STATE n="<<v260_post_calls
               <<" mapped="<<unsigned(v262_map)
               <<" ee="<<unsigned(v262_ee)
               <<" irq="<<unsigned(v262_irq)
               <<" native_request="<<unsigned(v262_request)
               <<" queued="<<v262_queue<<" sc="<<v262_sc
               <<" reply="<<unsigned(v262_reply)<<std::endl;'''

def derive(source:str)->str:
    s=previous(source)
    if (PRIOR_FRONTIER.count(PRIOR_ANCHOR)!=1 or
            PRIOR_CENSUS.count(LAST_CALL)!=1 or
            s.count(PRIOR_FRONTIER)!=1):
        raise ValueError("V262 original V260/V261 guest call-census source changed")
    census=PRIOR_FRONTIER.replace(PRIOR_ANCHOR,PRIOR_CENSUS,1)
    census=census.replace(LAST_CALL,LAST_CALL+'\n'+STATE_OBSERVER,1)
    return once(s,PRIOR_FRONTIER,census)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
