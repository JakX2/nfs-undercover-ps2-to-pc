#!/usr/bin/env python3
"""Bounded private caller integer path; no unknown operand is concretized.

Each admitted instruction carries its exact constant register inputs.
The native witness independently predicts effects, including CR with live
XER.SO, and stops before the next original label. No branches are admitted.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_integer import after_byte
from audit_formatter_partial_integer import classify
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope
MASK=0xffffffff
CAP=8
def signed(v,bits=32):return (v^(1<<(bits-1)))-(1<<(bits-1))
def mask(mb,me):
    return sum(1<<(31-i) for i in range(32) if (mb<=i<=me if mb<=me else i>=mb or i<=me))
def rot(v,n):return ((v<<n)|(v>>(32-n)))&MASK

def step(w,gp,*,saved_mask=0,allow_stack_copy=False,allow_stack_relative=False):
    if len(gp)!=32:raise ValueError('caller integer registers')
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    name,reads,writes,_,carry,xer,oe=classify(w)
    if not 0<=saved_mask<=MASK or saved_mask&0x3fff or carry or xer or oe or any(r not in (0,*range(3,13)) and not (r>=14 and saved_mask&(1<<r)) for r in writes):
        raise ValueError('caller integer effects')
    if not (op in (10,11,14,15,20,21,23,24,25,26,27,28,29) or
            op==31 and xo in (0,32,28,40,266,316,444,922,954)):
        raise ValueError('caller integer opcode')
    if (op in (10,11) and w&0x00600000) or (op==31 and xo in (0,32) and w&0x00600001) or (op==31 and xo in (922,954) and rb):
        raise ValueError('caller integer encoding')
    # Opt-in provenance-only modeling of PPC mr (or rA,rS,rS).
    # No concrete guest stack pointer is synthesized, and callers which
    # construct native numeric witnesses must retain their original gate.
    if (allow_stack_copy and op==31 and xo==444 and not w&1 and
            rs==rb and isinstance(gp[rs],tuple) and len(gp[rs])==2 and
            gp[rs][0]=='stack' and type(gp[rs][1]) is int):
        if ra not in (0,*range(3,13)):
            raise ValueError('caller integer effects')
        out=list(gp)
        out[ra]=gp[rs]
        return tuple(out),()
    # Opt-in symbolic addi/addis of one authenticated stack-relative token.
    # No numeric stack base is guessed and no guest memory is accessed.
    # This mirrors the bounded volatile-register part of the native predictor.
    if (allow_stack_relative and op in (14,15) and ra != 0 and
            isinstance(gp[ra],tuple) and len(gp[ra])==2 and
            gp[ra][0]=='stack' and type(gp[ra][1]) is int):
        if rs not in (0,*range(3,13)):
            raise ValueError('caller integer effects')
        offset=gp[ra][1]
        delta=signed(w&0xffff,16)*(65536 if op==15 else 1)
        result=offset+delta
        if not (-0x01800000<offset<0x01800000 and
                -0x01800000<result<0x01800000):
            raise ValueError('caller integer inputs')
        out=list(gp)
        out[rs]=('stack',result)
        return tuple(out),()
    if any(gp[r][0]!='const' or not 0<=gp[r][1]<=MASK for r in reads):
        raise ValueError('caller integer inputs')
    inputs=tuple((r,gp[r][1]) for r in sorted(set(reads)))
    v=lambda r:gp[r][1]
    imm=signed(w&0xffff,16)
    out=list(gp);result=None
    if op in (14,15):result=(v(ra) if ra else 0)+(imm<<(16 if op==15 else 0))
    elif op in (10,11) or op==31 and xo in (0,32):pass # no GPR write
    elif op in (24,25,26,27,28,29):
        n=(w&0xffff)<<(16 if op&1 else 0)
        result=v(rs)|n if op<26 else v(rs)^n if op<28 else v(rs)&n
    elif op in (20,21,23):
        sh=v(rb)&31 if op==23 else rb;m=mask((w>>6)&31,(w>>1)&31)
        n=rot(v(rs),sh)&m
        result=(v(ra)&~m)|n if op==20 else n
    elif xo in (444,28,316):result=v(rs)|v(rb) if xo==444 else v(rs)&v(rb) if xo==28 else v(rs)^v(rb)
    elif xo in (922,954):
        bits=16 if xo==922 else 8
        result=signed(v(rs)&((1<<bits)-1),bits)
    elif xo in (266,40):result=v(ra)+v(rb) if xo==266 else v(rb)-v(ra)
    else:raise ValueError('caller integer opcode')
    if result is not None:
        if len(writes)!=1:raise ValueError('caller integer effects')
        out[writes[0]]=('const',result&MASK)
    elif writes:raise ValueError('caller integer effects')
    return tuple(out),inputs

def extend(byte,words,gp,initial,*,cap=CAP,saved_mask=0):
    blocks,info=byte
    owner,caller,load,call,_,_,start,w=info
    live,_=after_byte(info,gp,initial)
    if not 1<=cap<=CAP or owner&3 or caller&3 or start!=caller+4 or caller<=owner:
        raise ValueError('caller integer geometry')
    i=(start-owner)//4;body=blocks.get(owner,())
    if not 2<=i<len(body)-1 or i+1>=len(words) or body[i-2]!=call or body[i-1]!=load or body[i]!=w or words[i]!=w or body[i+1]!=GUARD:
        raise ValueError('caller integer boundary')
    if any(x!=GUARD and (j>=len(words) or words[j]!=x) for j,x in enumerate(body)):
        raise ValueError('caller integer history')
    rows=[];reason='cap'
    for j in range(i,min(i+cap,len(words)-1)):
        try:next_gp,inputs=step(words[j],live,saved_mask=saved_mask)
        except ValueError as ex:
            reason=str(ex);break
        if j>i and j<len(body) and body[j]!=GUARD:raise ValueError('caller integer overlap')
        rows.append((owner+4*j,words[j],inputs))
        live=next_gp
    if not rows:return None,reason
    end=i+len(rows)
    if words[end]==GUARD or end<len(body) and body[end]!=GUARD or end+1<len(body) and body[end+1]!=GUARD:
        raise ValueError('caller integer overlap')
    out=list(body)+[GUARD]*max(0,end+2-len(body))
    for j in range(i+1,end+1):out[j]=words[j]
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return (expanded,tuple(rows),owner+4*end,words[end]),reason

def plan(d,e,*,byte=None):
    if byte is None:byte=byte_plan(d,e)
    owner=byte[1][0];size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4:raise ValueError('caller integer extent')
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    saved_mask=continuation_plan(d,e)[6]
    if saved_mask.bit_count()!=16 or saved_mask&0x3fff:raise ValueError('caller integer effects')
    return extend(byte,exact_words(d,e,owner,size//4),trace[-1][2],entry[1],saved_mask=saved_mask)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller integer registers','caller integer effects','caller integer opcode','caller integer encoding','caller integer inputs','caller integer geometry','caller integer boundary','caller integer history','caller integer overlap','caller integer extent','caller integer state','caller integer byte'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if reason not in safe|{'cap'}:raise ValueError('caller integer opcode')
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_INTEGER_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    if contract is None:
        print(f'FORMATTER_CALLER_INTEGER_CONTRACT verified=1 admitted=0 refusal={reason.replace(" ","_")} original_execution=0');return 0
    _,rows,_,w=contract
    print(f'FORMATTER_CALLER_INTEGER_CONTRACT verified=1 admitted={len(rows)} constant_inputs={sum(len(x[2]) for x in rows)} next_family={boundary_shape(w)} stop_reason={reason.replace(" ","_")} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
