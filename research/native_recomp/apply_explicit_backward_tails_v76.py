#!/usr/bin/env python3
"""Extend the strict explicit-root rule to backward assembly tail transfers.

An explicit source root and explicit target before it are independent entry
points. Keep ordinary nonexplicit interior branches and forward local control
flow unchanged. Apply only in lanes that explicitly seed both entry points.
"""
import argparse
from pathlib import Path
FILE=Path("nWiiAnalyzer/src/analyzer.cpp")
OLD="""          if (current_pc == func_start && target != func_start &&
              explicit_roots.count(target) && known_functions.count(target))
            break;"""
NEW="""          if (target != func_start && explicit_roots.count(target) &&
              known_functions.count(target) &&
              (current_pc == func_start ||
               (explicit_roots.count(func_start) && target < func_start)))
            break;"""
def rewrite(src):
    if src.count(NEW)==1 and OLD not in src:return src
    if src.count(OLD)!=1 or NEW in src:raise ValueError("unexpected explicit backward tail layout")
    return src.replace(OLD,NEW)
def apply(root):
    p=root/FILE;s=p.read_text();n=rewrite(s)
    if s!=n:p.write_text(n)
    return s!=n
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("PASS: explicit backward assembly tail transfers",apply(a.root))
