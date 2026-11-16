#!/usr/bin/env python3
"""V67 fail-closed image generator guard, including every original-code byte."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse,subprocess,hashlib
from make_osmask_v67 import make,OWNER_SHA

def test(owner:Path,generator:Path):
 if hashlib.sha256(owner.read_bytes()).hexdigest()!=OWNER_SHA:raise RuntimeError('owner SHA mismatch')
 original=make(owner);checks=0
 with TemporaryDirectory(prefix='v67_guards_') as td:
  root=Path(td);inp=root/'private.dol';out=root/'out';out.mkdir()
  def check(blob,expect_ok=False):
   nonlocal checks
   inp.write_bytes(blob)
   result=subprocess.run([str(generator),str(inp),str(out)],capture_output=True,text=True)
   if (result.returncode==0)!=expect_ok:raise RuntimeError('unexpected accepted/rejected image: '+result.stderr)
   if not expect_ok and list(out.iterdir()):raise RuntimeError('generator produced output after refusing malformed image')
   if expect_ok:
    import shutil
    shutil.rmtree(out);out.mkdir()
   checks+=1
  check(original,True)
  # All four byte lanes in all authentic PPC instructions, and synthetic stop.
  for pos in range(0x100,len(original)):
   b=bytearray(original);b[pos]^=0x01;check(bytes(b))
  # DOL section triples, entrypoint and reserved section slots.
  for pos in (0,3,4,0x14,0x1c,0x48,0x4b,0x4c,0x5c,0x64,0x90,0x93,0x94,0xa4,0xac,0xe0,0xe3):
   b=bytearray(original);b[pos]^=0x01;check(bytes(b))
  check(original[:-1]);check(original+b'\x00')
  inp.write_bytes(original)
  sentinel=out/'KEEP.txt';sentinel.write_text('do-not-touch')
  result=subprocess.run([str(generator),str(inp),str(out)],capture_output=True,text=True)
  if result.returncode==0 or sentinel.read_text()!='do-not-touch':raise RuntimeError('unsafe overwrite accepted')
  checks+=1
  bad=root/'wrong-owner.dol';bad.write_bytes(owner.read_bytes()+b'\x00')
  try:make(bad)
  except ValueError:checks+=1
  else:raise RuntimeError('modified owner original accepted')
 print(f'PASS: {checks}/{checks} V67 original-code, DOL geometry, SHA and overwrite guards')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('owner',type=Path);p.add_argument('generator',type=Path);a=p.parse_args();test(a.owner,a.generator)
