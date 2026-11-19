#!/usr/bin/env python3
"""V127 execute SHA-authenticated first OSInit BL after post-SC GPR save."""
import argparse
from pathlib import Path
from derive_v125_sc_helper_harness import derive as previous
from derive_v126_sc_post_gpr_harness import EDITS as post_gpr_edits

EDITS=[item for item in post_gpr_edits if item[0]!="bool handle_syscall(CPUContext&ctx){"]
def derive(source):
    s=previous(source)
    for before,after in EDITS:
        count=s.count(before)
        if count!=1:raise ValueError("V127 source anchor missing or ambiguous: "+before[:90]+" count="+str(count))
        s=s.replace(before,after,1)
    s=s.replace("post126_","post127_")
    s=s.replace("V126","V127")
    s=s.replace("V127 recovered continuous original __start->SC IOS post-helper GPR-save and next call",
                "V127 recovered original OSInit first authenticated BL after post-SC GPR save")
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
