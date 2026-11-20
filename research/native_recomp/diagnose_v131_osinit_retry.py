#!/usr/bin/env python3
"""V131 SHA-pinned original Wii OSInit retry condition classification.

Public output is only bounded PPC control-flow metadata, not original words.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,target,text_at
CALL=0x8052096C
CMP=CALL+4
CONDITION=CALL+8
EXIT_CALL=CALL+12
EXPECTED_CALLEE=0x8052F830

def branch16_dest(word:int,pc:int)->int:
    if word>>26!=16 or (word&1):
        raise ValueError("V131 original conditional branch shape differs")
    displacement=word&0xFFFC
    if displacement&0x8000:displacement-=0x10000
    return (displacement if word&2 else pc+displacement)&0xFFFFFFFF

def analyze(words:tuple[int,int,int,int])->dict[str,int]:
    if len(words)!=4 or words[1]>>26!=10:
        raise ValueError("V131 original CMPLI window differs")
    if target(words[0],CALL,True)!=EXPECTED_CALLEE:
        raise ValueError("V131 first OSInit retry callsite differs")
    follow=target(words[3],EXIT_CALL,True)
    cmpword=words[1]
    bo=(words[2]>>21)&31
    bi=(words[2]>>16)&31
    reg=(cmpword>>16)&31
    bf=(cmpword>>23)&7
    compare_imm=cmpword&0xFFFF
    compare_zero=int(compare_imm==0)
    test_eq=int(bi==bf*4+2 and not (bo&16))
    return dict(cmp_reg=reg,cmp_field=bf,compare_imm=compare_imm,compare_zero=compare_zero,
                branch_bo=bo,branch_bi=bi,branch_target=branch16_dest(words[2],CONDITION),
                retry_back=int(branch16_dest(words[2],CONDITION)==CALL),
                tests_equal=test_eq,retry_on_equal=int(test_eq and bool(bo&8)),
                next_call=follow)

def report(d:dict[str,int])->str:
    fields=("cmp_reg","cmp_field","compare_imm","compare_zero","branch_bo","branch_bi",
            "retry_back","tests_equal","retry_on_equal")
    return "V131_OSINIT_RETRY "+" ".join(f"{k}={d[k]}" for k in fields)+(
         f" branch_target={d['branch_target']:08x} next_call={d['next_call']:08x}")

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha_authenticated_original_dol",type=Path)
    args=parser.parse_args()
    try:
        raw=args.sha_authenticated_original_dol.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V131 Wii owner authentication mismatch")
        words=struct.unpack(">IIII",text_at(raw,CALL,16))
        result=analyze(words)
    except Exception:
        print("V131_OSINIT_RETRY result=failed")
        return 1
    print(report(result))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
