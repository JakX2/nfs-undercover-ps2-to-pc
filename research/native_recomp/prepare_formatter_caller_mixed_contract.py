#!/usr/bin/env python3
"""Bounded mixed caller path after four observed branch edges.

Admit constant-input register operations and proved forward local branches.
The boundary is an original label, not a synthesized executed instruction.
Never replace an earlier alternate guard or historical admitted label.
"""
import argparse,struct
from collections import Counter
from pathlib import Path
from audit_formatter_caller_fourth_branch import plan as fourth_audit
from prepare_formatter_caller_fourth_branch_contract import extend as fourth_extend
from prepare_formatter_caller_integer_contract import step
from audit_formatter_caller_branch import condition_effect,branch
from audit_formatter_partial_integer import classify
from audit_formatter_partial_copy import boundary_shape
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

CAP=16
def extend(fourth,words,gp,cr,saved_mask,earlier_guards,*,cap=CAP,integer_step=step):
    blocks,info=fourth;owner,size,previous,_,_,start,start_word,other=info
    if not 1<=cap<=CAP or len(gp)!=32 or len(cr)!=32 or owner&3 or size!=4*len(words) or not 8<=size<=65536:
        raise ValueError('mixed caller geometry')
    def inside(a):return a is not None and not a&3 and owner<=a<owner+size
    if not inside(start) or not inside(previous) or start<=previous or not inside(other):
        raise ValueError('mixed caller geometry')
    body=blocks.get(owner,());i=(start-owner)//4
    if i>=len(body) or body[i]!=start_word or words[i]!=start_word:
        raise ValueError('mixed caller predecessor')
    if any(v!=GUARD and (j>=len(words) or words[j]!=v) for j,v in enumerate(body)):
        raise ValueError('mixed caller history')
    guards=set(earlier_guards)|{other}
    if start in guards or any(not inside(a) or (a-owner)//4>=len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('mixed caller predecessor')
    out=list(body);live=tuple(gp);cr=tuple(cr);pc=start;rows=[];reason='cap'
    def at(a):
        j=(a-owner)//4
        return out[j] if j<len(out) else GUARD
    def fill(a,v):
        j=(a-owner)//4
        if j>=len(out):out.extend([GUARD]*(j+1-len(out)))
        out[j]=v
    for _ in range(cap):
        w=words[(pc-owner)//4]
        if w==GUARD:raise ValueError('mixed caller boundary')
        kind,ctr,taken,back,dst,chosen=branch(pc,w,cr,owner,size)
        if kind in ('conditional','direct'):
            if ctr or taken is None or back or dst is None or chosen is None or dst<=pc+4:
                reason='branch provenance';break
            alternate=pc+4 if taken else dst
            if not inside(alternate) or alternate==chosen or at(alternate)!=GUARD:
                reason='branch alternate';break
            nxt=chosen;new_gp=live;new_cr=cr;row=(pc,w,(),nxt,alternate,taken)
        else:
            try:new_gp,proof=integer_step(w,live,saved_mask=saved_mask)
            except ValueError as ex:reason=str(ex);break
            new_cr=condition_effect(w,live,new_gp,cr)
            nxt=pc+4;alternate=None;row=(pc,w,proof,nxt,None,None)
        if not inside(nxt) or nxt<=pc or nxt in guards or at(nxt)!=GUARD:
            reason='next label conflict';break
        j=(nxt-owner)//4
        if words[j]==GUARD or j+1>=len(words):
            reason='next label boundary';break
        # Keep the new alternate guard, including a target beyond the
        # existing synthetic extent. Do not change any historical word.
        if alternate is not None:
            fill(alternate,GUARD);guards.add(alternate)
        fill(nxt,words[j])
        if j+1>=len(out):out.append(GUARD)
        rows.append(row);live=new_gp;cr=new_cr;pc=nxt
    if any(at(a)!=GUARD for a in guards):raise ValueError('mixed caller guard')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(v) for a,v in expanded.items()})
    return (expanded,tuple(rows),pc,words[(pc-owner)//4]),reason,live,cr

def plan(d,e,*,fourth=None,**prior):
    third,words,proof,gp,cr,saved_mask=fourth_audit(d,e,with_state=True,**prior)
    verified,reason,_=fourth_extend(third,words,proof)
    if verified is None or fourth is not None and fourth!=verified:raise ValueError('mixed caller predecessor')
    fourth=verified
    return extend(fourth,words,gp,cr,saved_mask,proof[2])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','mixed caller geometry','mixed caller predecessor','mixed caller history','mixed caller boundary','mixed caller guard','branch provenance','branch alternate','next label conflict','next label boundary','caller integer registers','caller integer effects','caller integer opcode','caller integer encoding','caller integer inputs','cap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,_,cr=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if reason not in safe:raise ValueError('mixed caller boundary')
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_MIXED_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    _,rows,_,w=contract
    counts=Counter(classify(x[1])[0] for x in rows if x[4] is None)
    taken=sum(x[5] is True for x in rows);fallthrough=sum(x[5] is False for x in rows)
    print(f'FORMATTER_CALLER_MIXED_CONTRACT verified=1 admitted={len(rows)} integers={sum(counts.values())} branches={taken+fallthrough} taken={taken} fallthrough={fallthrough} constant_inputs={sum(len(x[2]) for x in rows)} next_family={boundary_shape(w)} stop_reason={reason.replace(" ","_")} established_cr_bits={sum(x is not None for x in cr)} original_execution=0')
    for name,count in sorted(counts.items()):print(f'FORMATTER_CALLER_MIXED_FAMILY family={name} count={count}')
    return 0
if __name__=='__main__':raise SystemExit(main())
