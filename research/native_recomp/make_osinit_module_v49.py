#!/usr/bin/env python3
"""Build owner-private OSInit -> __OSModuleInit native integration fixture.

Only the SHA-pinned owner's original Wii DOL supplies original PowerPC code.
This original-free builder never prints, publishes or embeds game instruction bodies.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_alarm_bridge_v48 import make as make_v48, OSINIT, NOP, NEW_STOP as LAST_STOP
from make_alarm_v47 import original_text, call_target, be32, BLR, SC

MODULE = 0x80526D30
NEW_STOP = 0x805208B8
TIME_SECTION = 0x805265AC


def make(owner: Path) -> bytes:
    prior = make_v48(owner)  # verifies original DOL SHA and inherited function graph
    original = owner.read_bytes()
    segments = []
    for index in range(7):
        offset, base, length = (be32(prior, start+4*index)
                                for start in (0, 0x48, 0x90))
        if index < 6:
            if offset < 0x100 or length == 0 or offset+length > len(prior):
                raise ValueError('invalid inherited private DOL text section')
            segments.append((base, bytearray(prior[offset:offset+length])))
        elif any((offset,base,length)):
            raise ValueError('unexpected seventh DOL text section')
    if segments[0][0] != OSINIT or segments[1][0] != TIME_SECTION:
        raise ValueError('inherited private section roots changed')
    caller = segments[0][1]
    region = segments[1][1]
    target = original_text(original, LAST_STOP, 4)
    module = original_text(original, MODULE, 24)
    if call_target(target, LAST_STOP, LAST_STOP) != MODULE:
        raise ValueError('original OSInit module-call target differs')
    if (be32(caller, LAST_STOP-OSINIT) != SC or
        be32(caller, NEW_STOP-OSINIT) != BLR or
        be32(caller, NEW_STOP-OSINIT+4) != NOP):
        raise ValueError('previous test-only stop changed')
    position = MODULE-TIME_SECTION
    if (position < 0 or position+len(module) > len(region) or
        any(be32(region,position+at) != NOP for at in range(0,len(module),4))):
        raise ValueError('original module function overlaps a non-synthetic private section')
    if be32(module,20) != BLR:
        raise ValueError('original OS module initializer missing return')
    caller[LAST_STOP-OSINIT:LAST_STOP-OSINIT+4] = target
    struct.pack_into('>II',caller,NEW_STOP-OSINIT,SC,BLR)
    region[position:position+len(module)] = module
    data_offset,data_address,data_length=(be32(prior,h) for h in (0x1c,0x64,0xac))
    if data_offset < 0x100 or data_length != 0x98 or data_offset+data_length>len(prior):
        raise ValueError('original source template section geometry changed')
    payload=prior[data_offset:data_offset+data_length]
    result=bytearray(0x100+sum(len(data) for _,data in segments)+len(payload))
    off=0x100
    for i,(address,data) in enumerate(segments):
        for h,val in ((0,off),(0x48,address),(0x90,len(data))):
            struct.pack_into('>I',result,h+4*i,val)
        result[off:off+len(data)]=data
        off+=len(data)
    for h,val in ((0x1c,off),(0x64,data_address),(0xac,len(payload))):
        struct.pack_into('>I',result,h,val)
    result[off:off+len(payload)]=payload
    struct.pack_into('>I',result,0xe0,OSINIT)
    return bytes(result)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_wii_dol',type=Path)
    p.add_argument('private_output_dol',type=Path)
    args=p.parse_args()
    if args.private_output_dol.exists():
        p.error('refusing to overwrite a private Wii image')
    args.private_output_dol.write_bytes(make(args.owner_original_wii_dol))
    print('PASS: V49 owner-private original Wii OSInit -> OSModuleInit fixture created')
