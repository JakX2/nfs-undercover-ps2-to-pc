#!/usr/bin/env python3
"""Owner-local DOL text extension for independent native startup tests.

Only a physically absent range or an explicitly identified placeholder can
be installed. Other verified sections, initialized data and BSS metadata
must remain unchanged. Never outputs original instructions to logs.
"""
import struct

NOP=struct.pack(">I",0x60000000)
STUB=struct.pack(">II",0x44000002,0x4e800020)
MAX_EXTENSION=0x10000

def unpack(raw):
    if len(raw)<256:raise ValueError("private DOL header missing")
    slots=[];regions=[];file_spans=[]
    for kind,limit in ((0,7),(1,11)):
        for i in range(limit):
            off,base,size=(struct.unpack_from(">I",raw,k+4*i)[0] for k in
                ((0x1c,0x64,0xac) if kind else (0,0x48,0x90)))
            if not size:
                if off or base:raise ValueError("empty DOL section is not canonical")
                continue
            if (off|base)&3 or off<256 or off+size>len(raw) or (not kind and size%4):
                raise ValueError("invalid private DOL section")
            if any(base<hi and lo<base+size for lo,hi in regions) or any(off<hi and lo<off+size for lo,hi in file_spans):
                raise ValueError("overlapping private DOL section")
            regions.append((base,base+size));file_spans.append((off,off+size))
            slots.append((kind,i,base,bytearray(raw[off:off+size])))
    return slots

def repack(raw,slots):
    out=bytearray(raw[:256])
    for kind,i,base,code in slots:
        for k,v in zip((0x1c,0x64,0xac) if kind else (0,0x48,0x90),(len(out),base,len(code))):
            struct.pack_into(">I",out,k+4*i,v)
        out.extend(code)
        out.extend(bytes((-len(out))%4))
    if out[0xe0:0x100]!=raw[0xe0:0x100]:raise ValueError("private entry or BSS metadata changed")
    return bytes(out)

def install(raw,patches):
    slots=unpack(raw)
    prior=unpack(raw)
    ordered=sorted(patches,key=lambda p:p[0])
    if any(a[0]+len(a[2])>b[0] for a,b in zip(ordered,ordered[1:])):
        raise ValueError("overlapping requested private text patches")
    for pc,expected,body in ordered:
        if pc&3 or not body or len(body)%4 or len(body)!=len(expected):
            raise ValueError("invalid exact installation span")
        end=pc+len(body)
        hits=[s for s in slots if not s[0] and s[2]<=pc< s[2]+len(s[3])]
        if hits:
            _,_,base,code=hits[0]
        else:
            candidates=[s for s in slots if not s[0] and s[2]+len(s[3])<=pc]
            if not candidates:raise ValueError("no preceding private text segment")
            _,_,base,code=max(candidates,key=lambda s:s[2]+len(s[3]))
        previous_end=base+len(code)
        if end>previous_end:
            if end-previous_end>MAX_EXTENSION or any(other is not code and addr<end and previous_end<addr+len(other)
                                                   for _,_,addr,other in slots):
                raise ValueError("private text extension crosses bounded segment")
            bss,bss_size=struct.unpack_from(">II",raw,0xd8)
            if bss_size and bss<end and previous_end<bss+bss_size:
                raise ValueError("private text extension intersects BSS")
            code.extend(NOP*((end-previous_end)//4))
        at=pc-base
        if bytes(code[at:at+len(body)])!=expected:
            raise ValueError("private text patch does not match exact prior placeholder")
        code[at:at+len(body)]=body
    result=repack(raw,slots)
    check=unpack(result)
    if len(check)!=len(prior):raise ValueError("private DOL slot count changed")
    for before,after in zip(prior,check):
        k,i,base,old=before
        if after[:3]!=(k,i,base):raise ValueError("existing private segment relocated")
        restored=bytearray(after[3][:len(old)])
        for pc,expected,body in ordered:
            lo=max(base,pc);hi=min(base+len(old),pc+len(body))
            if lo<hi:
                restored[lo-base:hi-base]=expected[lo-pc:hi-pc]
        if restored!=old:raise ValueError("unrelated private original bytes changed")
    return result
