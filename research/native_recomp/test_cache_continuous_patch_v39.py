#!/usr/bin/env python3
"""Synthetic tests for continuous HID4/cache patch. No game fixture."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
from apply_cache_continuous_v39 import (
    apply,CONTEXT,EMITTER,CTX_BEFORE,CTX_AFTER_CONT,
    EMIT_BEFORE,EMIT_AFTER,ISYNC_BEFORE,ISYNC_AFTER
)
def try_fixture(ctx:str,em:str,good:bool) -> None:
    with TemporaryDirectory() as d:
        root=Path(d)
        for rel,content in ((CONTEXT,ctx),(EMITTER,em)):
            dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(content,encoding="utf-8")
        try:
            changed=apply(root)
        except ValueError:
            if good:raise
            assert (root/CONTEXT).read_text()==ctx
            assert (root/EMITTER).read_text()==em
            return
        if not good:raise AssertionError("unsafe source accepted")
        assert changed and not apply(root)
        assert (root/CONTEXT).read_text()==ctx.replace(CTX_BEFORE,CTX_AFTER_CONT)
        assert (root/EMITTER).read_text()==em.replace(EMIT_BEFORE,EMIT_AFTER).replace(ISYNC_BEFORE,ISYNC_AFTER)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nwiirecomp_root",nargs="?",type=Path)
    a=parser.parse_args()
    ctx="TEST\n"+CTX_BEFORE+"\nEND\n"
    em="TEST\n"+EMIT_BEFORE+"\n"+ISYNC_BEFORE+"\nEND\n"
    try_fixture(ctx,em,True)
    try_fixture(ctx+CTX_BEFORE,em,False)
    try_fixture(ctx,em+EMIT_BEFORE,False)
    try_fixture(ctx,em.replace(ISYNC_BEFORE,"missing"),False)
    try_fixture(ctx.replace(CTX_BEFORE,CTX_AFTER_CONT),em,False)
    try_fixture(ctx,em.replace(EMIT_BEFORE,EMIT_AFTER),False)
    if a.nwiirecomp_root:
        root=a.nwiirecomp_root
        assert (root/CONTEXT).read_text().count(CTX_AFTER_CONT)==1
        assert (root/EMITTER).read_text().count(EMIT_AFTER)==1
        assert (root/EMITTER).read_text().count(ISYNC_AFTER)==1
        assert not apply(root)
    print("PASS: continuous V39 cache runtime patch idempotent and fail closed")
if __name__=="__main__":
    main()
