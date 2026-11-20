#!/usr/bin/env python3
"""Map private V165 assertion IDs to public source-owned diagnostics only.

Never accept, print, or upload owner-native logs or original game bytes.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v165_sc_y1_post_osdi_harness import derive

def describe(index: int)->str:
    if not 1<=index<=999:
        raise ValueError("V165 assertion index outside public numeric bound")
    original=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    public=derive(original)
    labels=sorted(set(STRING.findall(public)))
    if index>len(labels):
        raise ValueError("V165 assertion index outside public label catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int,nargs="?")
    p.add_argument("--public-cpp-line",type=int,default=None)
    a=p.parse_args()
    if a.public_cpp_line is not None:
        if not 1<=a.public_cpp_line<=10000:
            raise ValueError("public C++ line outside bounded range")
        code=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        rows=derive(code).splitlines()
        if a.public_cpp_line>len(rows):
            raise ValueError("derived public C++ line outside source")
        for index in range(max(1,a.public_cpp_line-3),min(len(rows),a.public_cpp_line+3)+1):
            # Only source-derived, publicly committed harness lines; no owner
            # executable, translated functions or private CI logs are read.
            print(f"V165_PUBLIC_CPP_LINE {index} {rows[index-1][:160]}")
    elif a.index is not None:
        print(f"V165_PUBLIC_ASSERTION id={a.index:03d} label={describe(a.index)}")
    else:
        p.error("supply a source-owned public line or assertion index")
