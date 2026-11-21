#!/usr/bin/env python3
"""V247 safe private-only restoration of Wii callback bodies from owner DOL.

The reduced native fixture still contains synthetic instructions at the
_isfsFuncCb and NAND callback. Restore only the two SHA-authenticated,
bounded, exact original owner spans. Refuse unexpected non-placeholder
words, preserve all unrelated private DOL sections and metadata, and
never print, upload or commit any game-derived instruction bytes.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from extend_private_text import NOP, STUB, install
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at

SPANS={
    "cb":(0x804f0e04,0x180),
    "nand":(0x8051e06c,0x78),
}
ALLOWED=(NOP, STUB[:4], STUB[4:])

class PatchError(ValueError):
    def __init__(self,stage:str,kind:str):
        super().__init__(stage+":"+kind)
        self.stage,self.kind=stage,kind

def select_patches(owner:bytes,fixture:bytes):
    patches=[]
    changed={}
    saw_nop=saw_stub=saw_original=False
    for key,(address,size) in SPANS.items():
        try:
            original=text_at(owner,address,size)
            current=text_at(fixture,address,size)
        except (ValueError,IndexError,struct.error) as exc:
            raise PatchError("select","range") from exc
        mismatch=False
        for i in range(0,size,4):
            own=current[i:i+4]
            src=original[i:i+4]
            if own==src:
                saw_original=True
            elif own in ALLOWED:
                mismatch=True
                saw_nop |= own==NOP
                saw_stub |= own in (STUB[:4],STUB[4:])
            else:
                raise PatchError("select","foreign")
        changed[key]=mismatch
        patches.append((address,current,original))
    return patches,changed,(saw_nop,saw_stub,saw_original)

def verify_private(owner:bytes,fixture:bytes):
    if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA:
        raise PatchError("auth","digest")
    patches,changed,observed=select_patches(owner,fixture)
    try:
        result=install(fixture,patches)
    except ValueError as exc:
        raise PatchError("apply","install") from exc
    for address,expected,original in patches:
        try:
            if text_at(result,address,len(original))!=original:
                raise PatchError("verify","span")
        except ValueError as exc:
            raise PatchError("verify","span") from exc
    if result[0xe0:0x100]!=fixture[0xe0:0x100]:
        raise PatchError("verify","header")
    try:
        reversed_image=install(
            result,[(address,original,expected)
                    for address,expected,original in patches])
    except ValueError as exc:
        raise PatchError("verify","reverse") from exc
    if reversed_image!=fixture:
        raise PatchError("verify","reverse")
    return result,changed,observed

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authenticated_owner",type=Path)
    parser.add_argument("prior_private_fixture",type=Path)
    parser.add_argument("new_private_fixture",type=Path)
    args=parser.parse_args()
    if args.new_private_fixture.exists() or args.new_private_fixture.is_symlink():
        print("V247_RESTORE_FAIL stage=output kind=exists")
        return 1
    try:
        result,changed,observed=verify_private(
            args.authenticated_owner.read_bytes(),
            args.prior_private_fixture.read_bytes())
        with args.new_private_fixture.open("xb") as stream:
            stream.write(result)
    except PatchError as exc:
        print("V247_RESTORE_FAIL stage="+exc.stage+" kind="+exc.kind)
        return 1
    except OSError:
        print("V247_RESTORE_FAIL stage=output kind=io")
        return 1
    except Exception:
        print("V247_RESTORE_FAIL stage=output kind=other")
        return 1
    nop,stub,original=observed
    print("V247_CALLBACK_RESTORE auth=1 cb_safe=1 nand_safe=1"
          +" cb_changed="+str(int(changed["cb"]))
          +" nand_changed="+str(int(changed["nand"]))
          +" nop="+str(int(nop))
          +" stub="+str(int(stub))
          +" original="+str(int(original))
          +" restored=1 reversible=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
