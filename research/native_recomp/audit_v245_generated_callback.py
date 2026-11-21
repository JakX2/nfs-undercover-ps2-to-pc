#!/usr/bin/env python3
"""V245 inspect private original-vs-fixture callback and emitted AOT mapping.

Only independently-written classification code is public. The genuine
Wii executable and NWiiRecomp-generated game C++ are read *inside* the
owner's ephemeral runner. The only output is a bounded boolean row.
Never print or upload guest instruction words, source snippets, file
content, guest pointer values or private paths.
"""
import argparse
import hashlib
import re
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at

SPANS={
    "cb":(0x804f0e04,384),
    "isfs":(0x804f1e2c,184),
    "nand":(0x8051e06c,120),
    "ipc":(0x805190c0,600),
}
CALLS={
    "cb":0x804f0e04,
    "isfs":0x804f1e2c,
    "nand":0x8051e06c,
}
HEADERS=re.compile(r"(?m)^void\s+[A-Za-z_][A-Za-z_0-9]*\s*\(CPUContext& ctx\)\s*\{")

def fixture_match(owner:bytes,fixture:bytes,reader=text_at)->dict[str,bool]:
    result={}
    for key,(address,size) in SPANS.items():
        try:
            original=reader(owner,address,size)
            restored=reader(fixture,address,size)
            result[key]=len(original)==size and original==restored
        except (ValueError,IndexError):
            result[key]=False
    return result

# Explicitly bounded per-function spans; no original source content is emitted.
def body_at(generated:str,address:int)->str:
    lower=generated.lower()
    anchors=list(HEADERS.finditer(generated))
    marker=f"nwii::runtime::trace_call(0x{address:08x}, ctx)"
    found=[]
    for index,m in enumerate(anchors):
        end=anchors[index+1].start() if index+1<len(anchors) else len(generated)
        body=lower[m.start():end]
        if marker in body:
            found.append(body)
    return found[0] if len(found)==1 else ""

def scan(generated:str)->dict[str,bool]:
    cb=body_at(generated,CALLS["cb"])
    isfs=body_at(generated,CALLS["isfs"])
    nand=body_at(generated,CALLS["nand"])
    lower=generated.lower()
    # These strings are independently known to be produced by pinned
    # NWiiRecomp emit_instruction; we do not embed original opcode words.
    return {
        "cb_entry":bool(cb),
        "cb_prologue":"stwu r1, -16(r1)" in cb,
        "cb_bctrl":"loc_804f0f50: ;" in cb,
        "cb_link":"ctx.lr = 0x804f0f54" in cb,
        "cb_ctr":"ctx.pc = ctx.ctr" in cb,
        "cb_return":"loc_804f0f80: ;" in cb,
        "isfs_entry":bool(isfs),
        "isfs_prologue":"stwu r1, -32(r1)" in isfs,
        "isfs_save":"loc_804f1e3c: ;" in isfs,
        "nand_entry":bool(nand),
        "dispatch_cb":bool(re.search(r"\{0x804f0e04,\s*0x[0-9a-f]+,",lower)),
        "dispatch_isfs":bool(re.search(r"\{0x804f1e2c,\s*0x[0-9a-f]+,",lower)),
        "dispatch_nand":bool(re.search(r"\{0x8051e06c,\s*0x[0-9a-f]+,",lower)),
    }

def format_result(verified:bool,fixture:dict[str,bool],
                  generated:dict[str,bool])->str:
    parts=[f"owner={int(verified)}"]
    parts.extend(f"fixture_{k}={int(fixture[k])}" for k in SPANS)
    parts.extend(f"{k}={int(v)}" for k,v in generated.items())
    return "V245_AOT_MAP "+" ".join(parts)

def audit(owner:bytes,fixture:bytes,generated:str)->str:
    verified=hashlib.sha256(owner).hexdigest()==ORIGINAL_SHA
    if not verified:
        raise ValueError("private original Wii authentication changed")
    return format_result(verified,fixture_match(owner,fixture),scan(generated))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original",type=Path)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("private_aot_source",type=Path)
    args=p.parse_args()
    # The runner suppresses stderr/tracebacks. Only the bounded
    # classification row is printed when authenticated.
    try:
        owner=args.private_original.read_bytes()
    except OSError:
        print("V245_AOT_DIAG stage=owner kind=read_failed")
        return 1
    try:
        fixture=args.private_fixture.read_bytes()
    except OSError:
        print("V245_AOT_DIAG stage=fixture kind=read_failed")
        return 1
    try:
        generated=args.private_aot_source.read_text(
            encoding="utf-8",errors="replace")
    except OSError:
        print("V245_AOT_DIAG stage=generated kind=read_failed")
        return 1
    if not generated:
        print("V245_AOT_DIAG stage=generated kind=empty")
        return 1
    try:
        result=audit(owner,fixture,generated)
    except ValueError:
        print("V245_AOT_DIAG stage=audit kind=validation")
        return 1
    except (TypeError,IndexError):
        print("V245_AOT_DIAG stage=audit kind=type")
        return 1
    print(result)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
