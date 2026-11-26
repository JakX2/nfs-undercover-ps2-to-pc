"""Generic finite continuation construction for synthetic/owner fixture tests."""
from prepare_v419_full_start import direct_bl
from prepare_post_stm_sc_join import GUARD,check_spans

def extend_guarded(blocks,owner,start,rows,target,entry_word):
    """Expand only unexecuted guard slots, never an existing native label.

    The continuation has one authenticated final direct call. Its return
    address is retained as a guard, and the callee is entry-only.
    """
    if owner not in blocks or target in blocks or target==owner or not rows or len(rows)>128:
        raise ValueError('continuation ownership')
    body=blocks[owner]
    pcs=[pc for pc,_ in rows]
    if pcs[0]!=start or len(set(pcs))!=len(pcs) or any(pc<owner or pc&3 for pc in pcs):
        raise ValueError('continuation labels')
    offsets=[(pc-owner)//4 for pc in pcs]
    if max(offsets)>=16384 or offsets[0]>=len(body) or body[offsets[0]]!=GUARD:
        raise ValueError('continuation start')
    if any(i<len(body) and body[i]!=GUARD for i in offsets):
        raise ValueError('continuation overlap')
    if any(w==GUARD for _,w in rows) or direct_bl(rows[-1][1],pcs[-1])!=target:
        raise ValueError('continuation final call')
    ret=offsets[-1]+1
    if ret in offsets or (ret<len(body) and body[ret]!=GUARD):
        raise ValueError('continuation return guard')
    extended=list(body)+[GUARD]*max(0,max(max(offsets)+1,ret)+1-len(body))
    for i,(_,w) in zip(offsets,rows):extended[i]=w
    out={**blocks,owner:tuple(extended),target:(entry_word,GUARD)}
    check_spans({a:4*len(ws) for a,ws in out.items()})
    return out

def saved_mask(slots):
    regs=[r for _,r in slots if r!=32]
    if any(not 14<=r<=31 for r in regs) or len(set(regs))!=len(regs):
        raise ValueError('continuation saved registers')
    return sum(1<<r for r in regs)
