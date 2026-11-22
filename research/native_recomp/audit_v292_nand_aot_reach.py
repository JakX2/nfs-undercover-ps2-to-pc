#!/usr/bin/env python3
"""V292: private owner DOL vs reduced fixture and emitted AOT reachability.

Inspect SHA-pinned Wii original DOL, only the private generated fixture
and C++ already present in owner CI. Print counts and booleans only.
No private PPC words, translated source or proprietary bytes leave CI.
"""
import argparse
import hashlib
from pathlib import Path
import re
import struct
import sys
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from audit_v245_generated_callback import body_at

TARGETS=((0x8052fa60,192),(0x8051d20c,120),(0x8051e150,136),(0x8052fca4,64))
CHILD=0x8052fa60
SOURCE=0x8051d20c

def word_counts(owner,fixture):
    if not owner or len(owner)!=len(fixture) or len(owner)%4:
        raise ValueError("span_geometry")
    result=dict(same=0,nop=0,blr=0,other=0)
    for i in range(0,len(owner),4):
        a=struct.unpack_from(">I",owner,i)[0]
        c=struct.unpack_from(">I",fixture,i)[0]
        k=("same" if a==c else "nop" if c==0x60000000 else
           "blr" if c==0x4e800020 else "other")
        result[k]+=1
    return result

def emitted(generated,pc):
    if not generated or len(generated)>50000000:
        raise ValueError("cpp_geometry")
    body=body_at(generated,pc).lower()
    low=generated.lower()
    return dict(body=int(bool(body)),dispatch=int(bool(re.search(
        r"\{0x"+f"{pc:08x}"+r",\s*0x[0-9a-f]+,",low))))

def link(generated):
    s=body_at(generated,CHILD).lower()
    target=f"0x{SOURCE:08x}"
    seen=int(f"ctx.pc = {target}" in s)
    unmapped=int(bool(re.search(
        r"ctx\.pc\s*=\s*"+target+r"\s*;\s*return\s*;\s*//\s*bl to unmapped target",s)))
    direct=int(bool(re.search(
        r"ctx\.pc\s*=\s*"+target+r"\s*;[^{}]{0,120}\(ctx\)",s)))
    return seen,unmapped,direct

def audit(owner,fixture,generated,sha=ORIGINAL_SHA,reader=text_at):
    if hashlib.sha256(owner).hexdigest()!=sha:
        raise ValueError("original_sha")
    if not owner or not fixture or max(len(owner),len(fixture))>20000000:
        raise ValueError("fixture_geometry")
    rows=[]
    orig={}
    for pc,size in TARGETS:
        a=reader(owner,pc,size)
        if len(a)!=size:raise ValueError("original_span")
        # The intentionally reduced owner fixture has fewer text sections
        # and can omit whole original functions. An absent span is a
        # meaningful missing-coverage result, not an error or fake NOP.
        try:
            c=reader(fixture,pc,size)
        except (ValueError,IndexError,struct.error):
            c=None
        if c is not None and len(c)!=size:
            raise ValueError("fixture_span")
        present=int(c is not None)
        counts=(word_counts(a,c) if present else
                dict(same=0,nop=0,blr=0,other=0))
        flags=emitted(generated,pc)
        orig[pc]=int(present and counts["same"]==size//4)
        rows.append(
            f"V292_AOT_TARGET pc={pc:08x} words={size//4} present={present} "+
            " ".join(f"{k}={counts[k]}" for k in ("same","nop","blr","other"))+
            f" emitted={flags['body']} dispatch={flags['dispatch']}")
    have,unmapped,direct=link(generated)
    rows.insert(0,
        "V292_AOT_REACH owner=1 fixture=1 targets=4 "+
        f"child_original={orig[CHILD]} source_original={orig[SOURCE]} "+
        f"child_aot={emitted(generated,CHILD)['body']} "+
        f"source_aot={emitted(generated,SOURCE)['body']} "+
        f"child_bl={have} unmapped_bl={unmapped} direct_emit={direct}")
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("private_fixture_dol",type=Path)
    p.add_argument("private_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        rows=audit(a.owner_dol.read_bytes(),a.private_fixture_dol.read_bytes(),
                   a.private_generated_cpp.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        print("V292_AOT_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V292_AOT_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
