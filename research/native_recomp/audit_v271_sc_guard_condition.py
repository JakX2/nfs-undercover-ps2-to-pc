#!/usr/bin/env python3
"""V271: decode real PowerPC conditions that skip status 1/0 helper stores.

SHA-verified private original ELF only. Branch BO/BI, register category,
relative address and comparison category may be logged. Original PPC words,
binary bytes and generated game code never leave private GitHub Actions.
"""
from pathlib import Path
import argparse
import hashlib
import sys
from audit_v264_osinit_retry_elf import HELPER,read_words
from audit_v268_sc_status_writers import access
from audit_v270_sc_writer_guards import classify as validate_prior
from audit_v243_original_callback_branch import branch_target
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from ppc_retry_edge import decode_bc


def guard_at(words:list[int],index:int)->dict[str,int]:
    pc=HELPER+4*index
    candidates=[]
    for i,word in enumerate(words[:index]):
        if word>>26!=16:continue
        src=HELPER+4*i
        dest=branch_target(src,word)
        if dest is not None and src<pc<dest<=HELPER+4*len(words):
            candidates.append((i,word,dest))
    if len(candidates)!=1:raise ValueError("guard_count")
    at,branch,dest=candidates[0]
    edge=decode_bc(branch)
    prev=words[at-1] if at else 0
    op=prev>>26
    cmptype=0
    field=-1
    ra=-1
    imm_class=-1
    if op in (10,11):
        cmptype=1 if op==11 else 2
        field=(prev>>23)&7
        ra=(prev>>16)&31
        imm_class={0:0,1:1,2:2,3:3}.get(prev&0xffff,4)
    elif op==31 and ((prev>>1)&1023) in (0,32):
        cmptype=3
        field=(prev>>23)&7
        ra=(prev>>16)&31
    return {
        "store_offset":index*4,"branch_offset":at*4,
        "target_offset":dest-HELPER,"bo":edge.bo,"bi":edge.bi,
        "cr_field":edge.cr_field,"cr_bit":edge.cr_bit,
        "ctr_decrement":int(edge.ctr_decrement),
        "cr_expected":-1 if edge.cr_expected is None else int(edge.cr_expected),
        "direct_cmp":int(cmptype!=0 and field==edge.cr_field),
        "cmp_kind":cmptype,"cmp_ra":ra,"cmp_imm_class":imm_class,
    }


def classify(words:list[int])->list[str]:
    validate_prior(words,HELPER)  # strictly one read, two direct byte stores
    stores=[i for i,w in enumerate(words) if access(w)=="byte_write"]
    reads=[i for i,w in enumerate(words) if access(w)=="byte_read"]
    if len(reads)!=1:
        raise ValueError("status_read")
    read_at=reads[0]
    read_rt=(words[read_at]>>21)&31
    rows=[]
    for rank,index in enumerate(stores,1):
        d=guard_at(words,index)
        d["read_rt"]=read_rt
        # Proven direct dataflow only if lbz rX,status is immediately
        # followed by the CR-producing comparison of the same rX.
        d["status_cmp"]=int(
            d["direct_cmp"]==1 and d["cmp_ra"]==read_rt and
            d["branch_offset"]==read_at*4+8)
        keys=("store_offset","branch_offset","target_offset","bo","bi",
              "cr_field","cr_bit","ctr_decrement","cr_expected",
              "direct_cmp","cmp_kind","cmp_ra","cmp_imm_class",
              "read_rt","status_cmp")
        rows.append(f"V271_SC_GUARD rank={rank} "+" ".join(
            f"{key}={d[key]}" for key in keys))
    return rows


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    fn=parse_functions(data)
    if len(fn)<25000:raise ValueError("symbols")
    length=fn.get(HELPER,0)
    if length<64 or length>32768 or length%4:
        raise ValueError("geometry")
    return classify(read_words(data,HELPER,length//4))


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: lines=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V271_GUARD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V271_GUARD_AUDIT verified=1")
    print("\n".join(lines))
    return 0

if __name__=="__main__":
    sys.exit(main())
