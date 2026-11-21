#!/usr/bin/env python3
"""Bounded original-free V250 callback native execution diagnostic.

Only the exact ephemeral compiled PUBLIC C++ harness is used to match
assertions. Private native logs are read locally inside owner CI, never
uploaded. Messages not found in the public C++ string catalog are ignored.
"""
import argparse
import re
from pathlib import Path
from classify_v38_native_failure import STRING, ERROR

BEG=re.compile(r"(?m)^V250_CB_BEGIN candidate=1 reply=[01] captured=1$")
NAND=re.compile(r"(?m)^V250_NAND_BCTRL auth=[01] frame16=[01] link=[01] ctr=[01] abi=[01] userdata=[01] progressed=[01] reply=[01]$")
TRIAL=re.compile(r"(?m)^V250_TRIAL_PASS trial=(?:[1-9]|1[0-6])$")
SAFE=re.compile(r"[A-Za-z0-9 _.,:/()\-]{1,170}\Z")

def describe(log:str,public_harness:str)->str:
    public=sorted(set(STRING.findall(public_harness)))
    matched=next((s for s in ERROR.findall(log) if s in public),None)
    ident=public.index(matched)+1 if matched is not None else 0
    label=matched if matched is not None and SAFE.fullmatch(matched) else "other"
    begin=bool(BEG.search(log))
    nand=bool(NAND.search(log))
    trials=min(len(TRIAL.findall(log)),16)
    return (f"V250_PUBLIC_FAILURE id={ident:04d} label={label}"
            f" callback={int(begin)} nand={int(nand)} trials={trials}")

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_log",type=Path)
    parser.add_argument("exact_compiled_public_harness",type=Path)
    opts=parser.parse_args()
    print(describe(
        opts.private_native_log.read_text(encoding="utf-8",errors="replace"),
        opts.exact_compiled_public_harness.read_text(encoding="utf-8",errors="replace")))

if __name__=="__main__":
    main()
