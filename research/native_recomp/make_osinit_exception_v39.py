#!/usr/bin/env python3
"""Owner-private V39 entry into original Wii OSExceptionInit, bounded before vector writes.

The original PPC instructions are copied only from the SHA-pinned owner DOL.
No extracted instructions, generated game code, or proprietary data are shipped.
"""
from pathlib import Path
import argparse
import struct
from make_osinit_ipc_v38 import make as make_v38, STOP as OLD_STOP, OSINIT
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import be32

ENTRY = 0x80520BF4
EXC_DEBUG_STOP = 0x80520C44  # original DBPrintf call, replaced for safety
EXC_NORMAL_STOP = 0x80520CA8  # before exception vector marking/copy loop
NEXT_OS_STOP = 0x805208AC  # original __OSInitSystemCall call (not executed)
EXC_SOURCE_WORD = 0x80520F28


def make(owner):
    baseline = make_v38(owner)
    original = Path(owner).read_bytes()  # SHA checked by V38 builder
    call = text_at(original, OLD_STOP, 4)
    if target(be32(call, 0), OLD_STOP, True) != ENTRY:
        raise ValueError('OSInit no longer calls original OSExceptionInit')
    prefix = text_at(original, ENTRY, EXC_NORMAL_STOP - ENTRY)
    if len(prefix) != 180 or be32(prefix, 0) != 0x9421FFC0:
        raise ValueError('original exception stack prologue changed')
    if target(be32(prefix, 16), ENTRY + 16, True) != 0x805450E8:
        raise ValueError('original exception nonvolatile-save call changed')
    if be32(prefix, EXC_DEBUG_STOP-ENTRY)>>26 != 18 or target(
            be32(prefix, EXC_DEBUG_STOP-ENTRY), EXC_DEBUG_STOP, True) != 0x804E50B8:
        raise ValueError('exception debug callback call changed')
    if be32(prefix, 0x44) != 0x4082004C:
        raise ValueError('exception path selection changed')
    if be32(prefix, EXC_NORMAL_STOP-ENTRY-4) != 0x3EC08052:
        # The last expected word is a lis r22; verify it explicitly.
        raise ValueError('original exception setup source changed')
    # Extract authentic original code-data word read through lwzu. In the test,
    # guest text memory is explicitly seeded from this private image.
    literal = text_at(original, EXC_SOURCE_WORD, 4)
    parts = []
    for i in range(7):
        off, addr, n = (be32(baseline, base + 4*i) for base in (0, 0x48, 0x90))
        if off<256 or n<=0 or off+n>len(baseline):
            raise ValueError('invalid parent private DOL geometry')
        parts.append((addr, bytearray(baseline[off:off+n])))
    base, os = parts[0]
    if base != OSINIT or be32(os, OLD_STOP-OSINIT) != SC:
        raise ValueError('expected previous synthetic stop was not present')
    os[OLD_STOP-OSINIT:OLD_STOP-OSINIT+4] = call
    struct.pack_into('>II', os, NEXT_OS_STOP-OSINIT, SC, BLR)
    start = ENTRY - OSINIT
    os[start:start+len(prefix)] = prefix
    struct.pack_into('>II', os, EXC_DEBUG_STOP-OSINIT, SC, BLR)
    struct.pack_into('>II', os, EXC_NORMAL_STOP-OSINIT, SC, BLR)
    os[EXC_SOURCE_WORD-OSINIT:EXC_SOURCE_WORD-OSINIT+4] = literal
    # NWiiAnalyzer conservatively treats the inlined absolute-address operands
    # as potential code targets. These are not guest calls on the tested path;
    # bound each placeholder with a fail-closed syscall rather than letting the
    # analyzer translate thousands of test-only NOPs as apparent functions.
    for address in (0x80520E98,0x80520E9C,0x80520EC0,0x80520F58):
        struct.pack_into('>I', os, address-OSINIT, SC)
    for address in (0x80520EA0,0x80520EC4,0x80520F5C):
        struct.pack_into('>I', os, address-OSINIT, BLR)
    parts[0] = (base,os)
    out = bytearray(256 + sum((len(b)+3)&~3 for _,b in parts))
    p=256
    for i,(addr,payload) in enumerate(parts):
        for h,v in ((0,p),(0x48,addr),(0x90,len(payload))):
            struct.pack_into('>I',out,h+4*i,v)
        out[p:p+len(payload)] = payload
        p += (len(payload)+3)&~3
    struct.pack_into('>I',out,0xe0,OSINIT)
    return bytes(out)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_dol',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    if args.output.exists(): ap.error('refusing output overwrite')
    image=make(args.owner_dol)
    args.output.write_bytes(image)
    print('PASS: V39 SHA-pinned original OSExceptionInit bounded private DOL',len(image),'bytes')
