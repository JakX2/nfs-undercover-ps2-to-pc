#!/usr/bin/env python3
"""Resolve V125 generator assertion IDs against the actual public C++ generator.

Never reads original game files or native/private logs. The diagnostics come
only from the independently written generator source.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v125_sc_helper_generator import derive

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"generate_start_to_ipc_ack_v77.cpp"

def messages():
    return sorted(set(STRING.findall(derive(SOURCE.read_text(encoding="utf-8")))))

def describe(index:int):
    labels=messages()
    if index<1 or index>len(labels):
        raise ValueError("V125 generator ID outside public catalog")
    return labels[index-1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    a=p.parse_args()
    print(f"V125_GENERATOR_ASSERTION id={a.id:03d} label={describe(a.id)}")
if __name__=="__main__":
    main()
