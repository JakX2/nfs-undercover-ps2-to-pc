#!/usr/bin/env python3
"""V134 locate original Wii direct readers/writers of the SC SDA status byte.

Outputs only addresses, register fields and aggregate counts, never game code.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from extend_private_text import unpack
from make_osinit_execparams_v28 import ORIGINAL_SHA

STATUS_DISP=-3176
STATUS_READ_PC=0x8052F84C
LOADS={32:"lwz",34:"lbz",40:"lhz",42:"lha"}
STORES={36:"stw",38:"stb",44:"sth"}

def scan_slots(slots):
    sites=[]
    for kind,idx,base,code in slots:
        if kind!=0:continue
        if len(code)%4:raise ValueError("V134 text section not word aligned")
        for i in range(0,len(code),4):
            word=struct.unpack_from(">I",code,i)[0]
            major=word>>26
            if major not in LOADS and major not in STORES:continue
            ra=(word>>16)&31
            disp=(word&0xFFFF)
            disp=disp-0x10000 if disp>=0x8000 else disp
            if ra!=13 or disp!=STATUS_DISP:continue
            direction="read" if major in LOADS else "write"
            sites.append(dict(pc=base+i,kind=direction,op=LOADS.get(major,STORES.get(major)),
                              register=(word>>21)&31))
    return sorted(sites,key=lambda site:site["pc"])

def describe(sites)->list[str]:
    reads=[x for x in sites if x["kind"]=="read"]
    writes=[x for x in sites if x["kind"]=="write"]
    header=f"V134_SDA_XREF reads={len(reads)} writes={len(writes)} canonical={int(any(x['pc']==STATUS_READ_PC and x['op']=='lbz' for x in reads))}"
    lines=[header]
    for x in sites[:32]:
        lines.append(f"V134_SDA_SITE pc={x['pc']:08x} kind={x['kind']} op={x['op']} register={x['register']}")
    return lines

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("sha_pinned_owner",type=Path)
    args=p.parse_args()
    try:
        raw=args.sha_pinned_owner.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V134 authenticated Wii owner differs")
        sites=scan_slots(unpack(raw))
        if not any(x["pc"]==STATUS_READ_PC and x["op"]=="lbz" and x["kind"]=="read" for x in sites):
            raise ValueError("V134 original SC SDA reference absent")
    except Exception:
        print("V134_SDA_XREF result=failed")
        return 1
    for line in describe(sites):print(line)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
