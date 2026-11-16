#!/usr/bin/env python3
"""SHA-pinned owner-private Wii __OSMaskInterrupts fixture (no game code in source)."""
import hashlib,struct,argparse
from pathlib import Path
OWNER_SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
MASK=0x8052693c
DISABLE=0x805265ac
RESTORE=0x805265d4
SETMASK=0x805266e0
STOP=0x90050000
SC=0x44000002
BLR=0x4e800020
SEGMENTS=[(MASK,0x80),(DISABLE,0x14),(RESTORE,0x24),(SETMASK,0x25c)]
def be32(b,at):return struct.unpack_from('>I',b,at)[0]
def extract(b,addr,n):
 for i in range(7):
  off,base,size=(be32(b,j) for j in (4*i,0x48+4*i,0x90+4*i))
  if size and off>=0x100 and base<=addr and addr+n<=base+size and off+size<=len(b):
   return b[off+addr-base:off+addr-base+n]
 raise ValueError('owner Wii original text missing, malformed or truncated')
def make(owner):
 raw=owner.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=OWNER_SHA:raise ValueError('original owner Wii DOL digest mismatch')
 pieces=[extract(raw,addr,n) for addr,n in SEGMENTS]
 # Anchor the original function geometry without embedding original instructions.
 if be32(pieces[0],0)>>26!=37 or be32(pieces[0],0x7c)!=BLR:raise ValueError('OSMask prologue/epilogue changed')
 if be32(pieces[1],0x10)!=BLR or be32(pieces[2],0x20)!=BLR:raise ValueError('interrupt helper return changed')
 if be32(pieces[3],0x258)!=BLR:raise ValueError('SetInterruptMask original body changed')
 # Validate all original function call boundaries, including the seven-bank loop.
 for src,offset,dst in ((0,0x1c,DISABLE),(0,0x4c,SETMASK),(0,0x5c,RESTORE)):
  addr=SEGMENTS[src][0]+offset;v=be32(pieces[src],offset)
  if v>>26!=18:raise ValueError('original Wii mask call opcode changed')
  delta=v&0x3fffffc
  if delta&0x2000000:delta-=0x4000000
  if (addr+delta)&0xffffffff !=dst:raise ValueError('original Wii mask call destination differs')
 sections=list(zip((addr for addr,_ in SEGMENTS),pieces))+[(STOP,struct.pack('>II',SC,BLR))]
 out=bytearray(0x100+sum(len(b) for _,b in sections));cursor=0x100
 for i,(base,blob) in enumerate(sections):
  for hdr,val in ((i*4,cursor),(0x48+i*4,base),(0x90+i*4,len(blob))):struct.pack_into('>I',out,hdr,val)
  out[cursor:cursor+len(blob)]=blob;cursor+=len(blob)
 struct.pack_into('>I',out,0xe0,MASK)
 return bytes(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('original_dol',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
 if a.out.exists():p.error('refusing to overwrite private image')
 a.out.write_bytes(make(a.original_dol));print('PASS: V67 private original Wii __OSMaskInterrupts slice created')
