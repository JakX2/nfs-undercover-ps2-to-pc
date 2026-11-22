#!/usr/bin/env python3
"""V262 read-only Wii interrupt and IOS-state census at V261 64-call frontier."""
import argparse
from pathlib import Path
from derive_v261_guest_call_census_harness import (
    derive as previous, INSTRUMENTED as PREVIOUS_INSTRUMENTED,
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
    if (PREVIOUS_INSTRUMENTED.count(LAST_CALL)!=1 or
            s.count(PREVIOUS_INSTRUMENTED)!=1):
        raise ValueError("V262 owner-verified original guest call-census seam changed")
    instrumented=PREVIOUS_INSTRUMENTED.replace(
        LAST_CALL,LAST_CALL+'\n'+STATE_OBSERVER,1)
    return once(s,PREVIOUS_INSTRUMENTED,instrumented)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
