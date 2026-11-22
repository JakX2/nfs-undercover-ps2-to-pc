#!/usr/bin/env python3
"""V296: read-only service-call observation in owner-private restored native AOT."""
from __future__ import annotations
import argparse
from pathlib import Path

TRACE = "void trace_call(uint32_t addr, CPUContext&ctx){"
PROBE = """void trace_call(uint32_t addr, CPUContext&ctx){
  // Only read guest ABI state at known, authenticated NAND call targets.
  // No register, memory, return code, or branch conditions are modified.
  if(v250_candidate_mode &&
     (addr==0x8051d20cu || addr==0x8051e150u)){
    const unsigned kind=addr==0x8051d20cu?1u:2u;
    const bool guest=(ctx.pc==addr && ctx.gpr[13]==v147_first_r13);
    const bool direct=(ctx.lr==(kind==1u?0x8052fab4u:0x8052fb10u));
    std::cout<<"V296_SERVICE_ENTRY kind="<<kind
             <<" guest="<<unsigned(guest)
             <<" direct="<<unsigned(direct)
             <<" inst="<<ctx.inst_count<<std::endl;
  }
"""

def patch(source: str) -> str:
    if (source.count(TRACE) != 1 or
        source.count("V289_NAND_ENTRY n=") != 1 or
        source.count("V278_FCA4_ENTRY n=") != 1):
        raise ValueError("V296 authenticated harness seam changed")
    return source.replace(TRACE, PROBE, 1)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inherited_harness", type=Path)
    parser.add_argument("private_output", type=Path)
    opts = parser.parse_args()
    with opts.private_output.open("x", encoding="utf-8") as stream:
        stream.write(patch(opts.inherited_harness.read_text(encoding="utf-8")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
