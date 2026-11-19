#!/usr/bin/env python3
"""Bounded compiler diagnostics for owner-free V110 C++ harness.

The harness is derived entirely from tracked independent source. Never
print the compiler log, generated game translation or owner data.
"""
from pathlib import Path
import re
import sys

def classify(log:str,source:str)->list[str]:
    lines=source.splitlines()
    hits=[]
    for match in re.finditer(
        r"(?:^|/)(?:harness|test_start_to_ipc_ack_v77)\\.cpp:(\\d+):(\\d+): (?:fatal )?error:",
        log,re.MULTILINE,
    ):
        n=int(match.group(1))
        if not 1<=n<=len(lines):continue
        if n in hits:continue
        hits.append(n)
        if len(hits)>=3:break
    # The snippet is independent original-free public test-harness source.
    out=[]
    for n in hits:
        out.append(f"V110_PUBLIC_CXX_LINE number={n}")
        for i in range(max(1,n-2),min(len(lines),n+2)+1):
            snippet=lines[i-1].strip()
            if len(snippet)>180:snippet=snippet[:180]+"..."
            out.append(f"V110_PUBLIC_CXX_CONTEXT line={i} code={snippet}")
    kinds={"expected":0,"undeclared":0,"type":0,"conversion":0}
    for line in log.splitlines():
        if "error:" not in line:continue
        if "expected" in line:kinds["expected"]+=1
        if "not declared" in line:kinds["undeclared"]+=1
        if "does not name a type" in line:kinds["type"]+=1
        if "convert" in line:kinds["conversion"]+=1
    out.append("V110_PUBLIC_CXX_KIND "+" ".join(f"{key}={min(value,9)}" for key,value in kinds.items()))
    return out

def main():
    if len(sys.argv)!=3:raise SystemExit(2)
    log=Path(sys.argv[1]).read_text(errors="replace")
    source=Path(sys.argv[2]).read_text(encoding="utf-8")
    for item in classify(log,source):print(item)

if __name__=="__main__":main()
