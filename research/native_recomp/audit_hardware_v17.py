#!/usr/bin/env python3
"""Original-only startup Wii OS dependency audit; emits edges and counts,
not copyrighted machine code. Never commit owner's input DOL or ELF.
"""
import argparse
import hashlib
import struct
from collections import Counter
from pathlib import Path

ORIGINAL_SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
FUNCTIONS={
    '__init_hardware':(0x800042e0,36),
    '__OSPSInit':(0x80520fb4,84),
    '__OSFPRInit':(0x8051fbb0,296),
    '__OSCacheInit':(0x80522540,312),
}
EXPECTED_DIRECT={
    '__init_hardware':(0x80520fb4,0x8051fbb0,0x80522540),
    '__OSPSInit':(0x804b79dc,0x804b79e4,0x805223ac),
}
KNOWN={
    0x80520fb4:'__OSPSInit',0x8051fbb0:'__OSFPRInit',
    0x80522540:'__OSCacheInit',0x804b79dc:'PPCMfhid2',
    0x804b79e4:'PPCMthid2',0x805223ac:'ICFlashInvalidate',
    0x804b7920:'PPCMfhid0',0x805223bc:'ICEnable',
    0x804e50b8:'DBPrintf',0x80522280:'DCEnable',
    0x804b7930:'PPCMfl2cr',0x804b7910:'PPCMfmsr',
    0x804b7918:'PPCMtmsr',0x804b7938:'PPCMtl2cr',
    0x805230b8:'OSSetErrorHandler',
}


def extract(dol:bytes,addr:int,size:int)->bytes:
    if len(dol)<256:raise ValueError('invalid DOL header')
    for i in range(7):
        offset,start,length=(struct.unpack_from('>I',dol,base+4*i)[0]
                             for base in (0,0x48,0x90))
        if length and start<=addr and addr+size<=start+length:
            at=offset+addr-start
            if at<256 or at+size>len(dol):raise ValueError('DOL text out of file')
            return dol[at:at+size]
    raise ValueError('guest routine not contained in DOL text')


def analyze(words:bytes,addr:int):
    counts=Counter()
    targets=[]
    for i,(word,) in enumerate(struct.iter_unpack('>I',words)):
        opcode=word>>26
        if opcode==18:
            disp=word&0x03fffffc
            if disp&0x02000000:disp-=0x04000000
            target=(disp if word&2 else addr+4*i+disp)&0xffffffff
            if word&1:
                counts['direct_bl']+=1
                targets.append((addr+4*i,target))
            else:counts['nonlink_b']+=1
        elif opcode==16:counts['conditional_branches']+=1
        elif opcode==4:counts['paired_single']+=1
        elif opcode in (59,63):counts['floating_point']+=1
        elif opcode==31:
            xo=(word>>1)&1023
            if xo==83:counts['mfmsr']+=1
            elif xo==146:counts['mtmsr']+=1
            elif xo==339:counts['mfspr']+=1
            elif xo==467:counts['mtspr']+=1
            elif xo==598:counts['sync']+=1
    return counts,targets


def audit(path:Path):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('owner DOL SHA256 mismatch')
    results={}
    for name,(address,length) in FUNCTIONS.items():
        counts,targets=analyze(extract(data,address,length),address)
        expected=EXPECTED_DIRECT.get(name)
        if expected is not None and tuple(t for _,t in targets)!=expected:
            raise ValueError(name+' direct callers changed')
        results[name]=(address,length,counts,targets)
    if results['__OSFPRInit'][3]:
        raise ValueError('unexpected direct BL inside OS FPR initializer')
    return results


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('original_wii_dol',type=Path)
    a=ap.parse_args()
    for name,(address,length,counts,targets) in audit(a.original_wii_dol).items():
        print(f'{name} 0x{address:08X} length={length} bytes: '+
              ', '.join(f'{key}={value}' for key,value in sorted(counts.items())))
        for site,target in targets:
            print(f'  BL 0x{site:08X} -> 0x{target:08X} {KNOWN.get(target,"(unlabeled)")}')
    print('Not executed: original Wii OS service bodies. This is a dependency census only.')

if __name__=='__main__':main()
