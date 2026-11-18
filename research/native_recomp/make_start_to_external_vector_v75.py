#!/usr/bin/env python3
"""Private original IRQ vector execution with explicit nonexecuted handler boundary."""
import argparse,struct
from pathlib import Path
from make_start_to_select_thread_v74 import make as previous
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import SC,BLR,NOP
STOP=0x80526ce0
def make(owner):
    old=bytearray(previous(owner))
    replace(old,STOP,struct.pack(">II",NOP,NOP),struct.pack(">II",SC,BLR))
    return bytes(old)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("owner",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error("refusing private overwrite")
    with a.output.open("xb") as f:f.write(make(a.owner))
    print("PASS: V75 private original IRQ vector handler boundary fixture")
