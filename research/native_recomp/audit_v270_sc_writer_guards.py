#!/usr/bin/env python3
"""V270 owner-verified Wii SC helper status-write guard scan.

Classify the exact two original r13-3176 byte stores in 0x8052F830.
A forward branch that skips a store is a *static possible guard*;
no control-flow execution/reachability is assumed. No original PPC
words, disassembly or private ELF bytes are printed.
"""
import argparse
import hashlib
from pathlib import Path
import sys
from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import HELPER, read_words
from audit_v268_sc_status_writers import access
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions


def source_kind(word:int,rs:int)->tuple[int,int]:
    op=word>>26
    rt=(word>>21)&31
    ra=(word>>16)&31
    imm=word&0xffff
    if op==14 and rt==rs and ra==0:
        return 1,{0:0,1:1,2:2,3:3}.get(imm,4)
    if op in (32,33,34,35,40,41,42,43) and rt==rs:
        return 2,-1
    if (op==31 and ((word>>1)&1023)==444
            and ra==rs and rt==((word>>11)&31)):
        return 3,-1
    return 0,-1


def classify(words:list[int],start:int)->list[str]:
    if start!=HELPER or not 16<=len(words)<=8192:
        raise ValueError("geometry")
    reads=[i for i,w in enumerate(words) if access(w)=="byte_read"]
    stores=[i for i,w in enumerate(words) if access(w)=="byte_write"]
    if len(reads)!=1 or len(stores)!=2:
        raise ValueError("status_sites")
    result=[f"V270_SC_SITES reads=1 writes=2 read_offset={reads[0]*4} "
            f"store1_offset={stores[0]*4} store2_offset={stores[1]*4}"]
    for rank,at in enumerate(stores,1):
        word=words[at]
        rs=(word>>21)&31
        previous=words[at-1] if at else 0
        kind,value_class=source_kind(previous,rs)
        skip_cond=skip_direct=0
        for i,branch in enumerate(words[:at]):
            pc=start+4*i
            target=branch_target(pc,branch)
            if target is None or not pc<start+4*at<target<=start+4*len(words):
                continue
            if branch>>26==16:
                skip_cond+=1
            elif branch>>26==18:
                skip_direct+=1
        result.append(f"V270_SC_STORE rank={rank} offset={at*4} rs={rs} "
                      f"prev_kind={kind} prev_const={value_class} "
                      f"skip_cond={skip_cond} skip_direct={skip_direct}")
    return result


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    funcs=parse_functions(data)
    if len(funcs)<25000:raise ValueError("symbols")
    n=funcs.get(HELPER,0)
    if not 64<=n<=32768 or n%4:raise ValueError("geometry")
    return classify(read_words(data,HELPER,n//4),HELPER)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: lines=audit(a.owner_elf.read_bytes())
    except (ValueError,OSError):
        print("V270_GUARD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V270_GUARD_AUDIT verified=1")
    print("\n".join(lines))
    return 0


if __name__=="__main__":
    sys.exit(main())
