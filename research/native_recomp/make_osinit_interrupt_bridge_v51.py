#!/usr/bin/env python3
"""Build owner-private original Wii OSInit -> interrupt-table prefix integration.

Never publishes original PowerPC instructions. Original bytes are extracted
exclusively from the SHA-256-pinned owner DOL and remain in private output.
The entire downstream MMIO/interrupt-mask path is explicitly unexecuted.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_module_v49 import make as make_v49, NEW_STOP as PREVIOUS_STOP, OSINIT, TIME_SECTION, NOP
from make_alarm_v47 import original_text, call_target, be32, BLR, SC
from make_interrupt_prefix_v50 import ENTRY as INTERRUPT, STOP as INTERRUPT_STOP, CALL as INTERRUPT_MEMSET_CALL, MEMSET, FILL

FAILSAFE=PREVIOUS_STOP+4
FILL_LENGTH=0xE4
PREFIX_LENGTH=INTERRUPT_STOP-INTERRUPT


def make(owner: Path) -> bytes:
    previous=make_v49(owner)  # verifies original owner SHA and inherited call graph
    raw=owner.read_bytes()
    segments=[]
    for i in range(7):
        off, base, length=(be32(previous,start+4*i) for start in (0,0x48,0x90))
        if i<6:
            if off<0x100 or length<=0 or off+length>len(previous):
                raise ValueError('V51 inherited private text section out of bounds')
            segments.append([base,bytearray(previous[off:off+length])])
        elif any((off,base,length)):
            raise ValueError('V51 inherited private text section layout unexpectedly changed')
    if (segments[0][0]!=OSINIT or segments[1][0]!=TIME_SECTION or
        segments[3][0]!=0x80004338 or len(segments[3][1])!=0x50):
        raise ValueError('V51 expected inherited module/memcpy section geometry')
    osinit=segments[0][1]
    original_call=original_text(raw,PREVIOUS_STOP,4)
    if (call_target(original_call,PREVIOUS_STOP,PREVIOUS_STOP)!=INTERRUPT or
        be32(osinit,PREVIOUS_STOP-OSINIT)!=SC or
        be32(osinit,FAILSAFE-OSINIT)!=BLR or
        be32(osinit,FAILSAFE-OSINIT+4)!=NOP):
        raise ValueError('V51 original OSInit interrupt call or test-stop replacement changed')
    original_interrupt=original_text(raw,INTERRUPT,PREFIX_LENGTH)
    original_fill=original_text(raw,FILL,FILL_LENGTH)
    if (call_target(original_interrupt,INTERRUPT_MEMSET_CALL,INTERRUPT)!=MEMSET or
        be32(original_fill,0xB0)!=BLR or be32(original_fill,0xE0)!=BLR):
        raise ValueError('V51 original memset/__fill_mem callgraph or return changed')
    region=segments[1][1]
    at=INTERRUPT-TIME_SECTION
    if at<0 or at+PREFIX_LENGTH+8>len(region):
        raise ValueError('V51 private original interrupt prefix lies outside guest section')
    if any(be32(region,at+i)!=NOP for i in range(0,PREFIX_LENGTH+8,4)):
        raise ValueError('V51 interrupt prefix would overwrite non-synthetic instructions')
    osinit[PREVIOUS_STOP-OSINIT:PREVIOUS_STOP-OSINIT+4]=original_call
    struct.pack_into('>II',osinit,FAILSAFE-OSINIT,SC,BLR)
    region[at:at+PREFIX_LENGTH]=original_interrupt
    struct.pack_into('>II',region,at+PREFIX_LENGTH,SC,BLR)
    segments[3][1].extend(original_fill)
    data_off,data_addr,data_len=(be32(previous,h) for h in (0x1c,0x64,0xac))
    if (data_off<0x100 or data_len!=0x98 or data_off+data_len>len(previous)):
        raise ValueError('V51 original exception-template data section changed')
    template=previous[data_off:data_off+data_len]
    output=bytearray(0x100+sum(len(b) for _,b in segments)+len(template))
    pos=0x100
    for i,(base,blob) in enumerate(segments):
        for h,value in ((0,pos),(0x48,base),(0x90,len(blob))):
            struct.pack_into('>I',output,h+4*i,value)
        output[pos:pos+len(blob)]=blob
        pos+=len(blob)
    for h,value in ((0x1c,pos),(0x64,data_addr),(0xac,len(template))):
        struct.pack_into('>I',output,h,value)
    output[pos:pos+len(template)]=template
    struct.pack_into('>I',output,0xe0,OSINIT)
    return bytes(output)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_original_dol',type=Path)
    ap.add_argument('private_test_image',type=Path)
    args=ap.parse_args()
    if args.private_test_image.exists():
        ap.error('refusing to overwrite existing private image')
    args.private_test_image.write_bytes(make(args.owner_original_dol))
    print('PASS: V51 original Wii OSInit -> __OSInterruptInit private fixture built')
