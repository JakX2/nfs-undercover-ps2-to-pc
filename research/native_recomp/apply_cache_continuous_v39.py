#!/usr/bin/env python3
"""Original-free cache-line trace patch compatible with continuous V30 HID4.

Diagnostic cache events and host fences are not emulation of real Wii cache
coherency. Fail closed on any unexpected NWiiRecomp source revision.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from apply_cache_events_v43 import (
    CONTEXT, EMITTER, CTX_AFTER, EMIT_BEFORE, EMIT_AFTER,
    ISYNC_BEFORE, ISYNC_AFTER, transform
)

CTX_BEFORE = "  uint32_t hid4 = 0; // Wii HID4 guest-visible state\n\n  struct BackupState {"
CTX_AFTER_CONT = CTX_AFTER.replace(
    "  uint32_t hid4 = 0;\n",
    "  uint32_t hid4 = 0; // Wii HID4 guest-visible state\n", 1
)

def apply(root:Path) -> bool:
    cpath,epath=root/CONTEXT,root/EMITTER
    ctx,em=cpath.read_text(encoding="utf-8"),epath.read_text(encoding="utf-8")
    def state(text,old,new):
        if text.count(old)==1 and new not in text: return "old"
        if text.count(new)==1 and old not in text: return "new"
        raise ValueError("ambiguous or partially installed cache source patch")
    state_set=(state(ctx,CTX_BEFORE,CTX_AFTER_CONT),
               state(em,EMIT_BEFORE,EMIT_AFTER),
               state(em,ISYNC_BEFORE,ISYNC_AFTER))
    if len(set(state_set))!=1:
        raise ValueError("mixed cache runtime/emitter patch states; refused atomically")
    if state_set[0]=="new":return False
    new_ctx=transform(ctx,[(CTX_BEFORE,CTX_AFTER_CONT)])
    new_em=transform(em,[(EMIT_BEFORE,EMIT_AFTER),(ISYNC_BEFORE,ISYNC_AFTER)])
    cpath.write_text(new_ctx,encoding="utf-8")
    epath.write_text(new_em,encoding="utf-8")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nwiirecomp_root",type=Path)
    a=parser.parse_args()
    print("V39 continuous Wii cache patch:", "installed" if apply(a.nwiirecomp_root) else "already applied")
