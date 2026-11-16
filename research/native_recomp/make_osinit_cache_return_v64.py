#!/usr/bin/env python3
"""Private original OSInit cache/error-handler bridge; no owner PowerPC opcodes in source."""
import argparse
import struct
from pathlib import Path
from make_osinit_l2poll_v62 import make as inherited
from make_osinit_cache_l1_v59 import OSINIT,NOP
from make_alarm_v47 import original_text,call_target,be32,SC,BLR

ERROR=0x805230B8
ERROR_END=0x80523340
CACHE_TAIL=0x80522644
CACHE_END=0x80522678
OSINIT_STOP=0x805208C4
DISABLE=0x805265AC
RESTORE=0x805265D4
FPSCR_READ=0x804B7994
FPSCR_WRITE=0x804B79B4

def make(owner:Path)->bytes:
 out=bytearray(inherited(owner))
 raw=owner.read_bytes()
 tail=original_text(raw,CACHE_TAIL,CACHE_END-CACHE_TAIL)
 error=original_text(raw,ERROR,ERROR_END-ERROR)
 fp_read=original_text(raw,FPSCR_READ,0x20)
 fp_write=original_text(raw,FPSCR_WRITE,0x28)
 for pc,dest in ((0x80522650,ERROR),(0x8052265c,0x804e50b8)):
  if call_target(tail,pc,CACHE_TAIL)!=dest:raise ValueError(f'V64 original cache call {pc:#x} changed')
 for pc,dest in ((0x805230DC,DISABLE),(0x80523110,FPSCR_READ),
                 (0x80523308,FPSCR_WRITE),(0x80523318,RESTORE)):
  if call_target(error,pc,ERROR)!=dest:raise ValueError(f'V64 original handler call {pc:#x} changed')
 if (len(error)!=0x288 or be32(error,len(error)-4)!=BLR or
     len(tail)!=0x34 or be32(tail,len(tail)-4)!=BLR or
     len(fp_read)!=0x20 or len(fp_write)!=0x28):
  raise ValueError('V64 original call/return/body differs')
 first,base,length=[be32(out,x) for x in (0,0x48,0x90)]
 helper_off,helper_base,helper_len=[be32(out,x) for x in (0x10,0x58,0xa0)]
 if (base!=OSINIT or first<0x100 or first+length>len(out) or
     ERROR_END>base+length or helper_base!=0x804B7910 or
     helper_len<0xcc or helper_off+helper_len>len(out)):
  raise ValueError('V64 source-backed fixture geometry differs')
 tail_at=first+CACHE_TAIL-base
 if be32(out,tail_at)!=SC or be32(out,tail_at+4)!=BLR or any(
    be32(out,tail_at+i)!=NOP for i in range(8,len(tail),4)):
  raise ValueError('V64 refused non-synthetic cache tail')
 out[tail_at:tail_at+len(tail)]=tail
 error_at=first+ERROR-base
 if any(be32(out,error_at+i)!=NOP for i in range(0,len(error),4)):
  raise ValueError('V64 refused non-synthetic error-handler body')
 out[error_at:error_at+len(error)]=error
 for addr,body in ((FPSCR_READ,fp_read),(FPSCR_WRITE,fp_write)):
  at=helper_off+addr-helper_base
  if any(be32(out,at+i)!=NOP for i in range(0,len(body),4)):
   raise ValueError('V64 refused non-synthetic FPU helper body')
  out[at:at+len(body)]=body
 at=first+OSINIT_STOP-base
 if be32(out,at)!=BLR or be32(out,at+4)!=NOP:
  raise ValueError('V64 original OSInit return is not test-only padding')
 struct.pack_into('>II',out,at,SC,BLR)
 return bytes(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('original_owner_wii_dol',type=Path);p.add_argument('private_output',type=Path)
 a=p.parse_args()
 if a.private_output.exists():p.error('refuse overwrite owner-private fixture')
 a.private_output.write_bytes(make(a.original_owner_wii_dol))
 print('PASS: V64 original OSInit cache/error handler bridge installed privately')
