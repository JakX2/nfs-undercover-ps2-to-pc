#!/usr/bin/env python3
"""Original-free explicit opt-in to AOT compile verified immutable low-memory entries."""
import argparse
from pathlib import Path
HEADER=Path("nWiiRecomp/include/recompiler/recompiler.h")
EMITTER=Path("nWiiRecomp/src/recompiler.cpp")
OLD_H="    std::map<uint32_t, std::string> hle_hooks;"
NEW_H="""    std::map<uint32_t, std::string> hle_hooks;
    // Caller must authenticate the installed bytes before dispatch.
    std::set<uint32_t> native_low_mem_entries;"""
OLD_E="""  if (all_zero || os_low_mem) {"""
NEW_E="""  if (all_zero || (os_low_mem && config_.native_low_mem_entries.count(func.start_address)==0)) {"""
def rewrite(h,e):
    if h.count(NEW_H)==1 and e.count(NEW_E)==1:return h,e
    if NEW_H in h or NEW_E in e or h.count(OLD_H)!=1 or e.count(OLD_E)!=1:
        raise ValueError("unknown or mixed low-memory AOT emitter state")
    return h.replace(OLD_H,NEW_H),e.replace(OLD_E,NEW_E)
def apply(root):
    hp,ep=root/HEADER,root/EMITTER
    h,e=hp.read_text(),ep.read_text();nh,ne=rewrite(h,e)
    if (h,e)!=(nh,ne):hp.write_text(nh);ep.write_text(ne);return True
    return False
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("V63 explicit immutable low-memory AOT opt-in:",apply(a.root))
