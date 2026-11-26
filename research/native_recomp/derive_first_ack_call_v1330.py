"""Bounded first-call census for the authenticated third SI ACK handler.

Counts start after an already visited helper-return label, just as the
live observer does. Stop at the first direct call, guard or other control
transfer. Never publish original instruction words or addresses.
"""
def first_calls(rows,edges,owner,start,limit=256):
    if not 1<=limit<=256:raise ValueError('call census limit')
    table={}
    for pc,w,root,guard in rows:
        if root!=owner:continue
        if pc in table or pc&3:raise ValueError('call census identity')
        table[pc]=(w,guard)
    if start not in table or table[start][1]:raise ValueError('call census start')
    known={}
    for i,(pc,dst) in enumerate(edges,1):
        if pc in known:raise ValueError('call census edge')
        known[pc]=(i,dst)
    def target(pc,w):
        m,s=(0xfffc,0x8000) if w>>26==16 else (0x03fffffc,0x02000000)
        return (pc+((w&m)^s)-s)&0xffffffff
    def walk(pc):
        w,g=table[pc];op=w>>26;xo=(w>>1)&1023
        if g:return (),None
        if op==18 and w&3==1:
            if pc not in known or known[pc][1]!=target(pc,w):raise ValueError('call census edge')
            return (),known[pc][0]
        if op in (16,18):
            if w&3:return (),None
            dst=target(pc,w)
            return ((dst,) if op==18 or (w>>21)&20==20 else (pc+4,dst)),None
        if op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):return (),None
        return (pc+4,),None
    active={start};out=set()
    for n in range(limit+1):
        next_active=set()
        for pc in active:
            successors,edge=walk(pc)
            if edge is not None:out.add((n,edge))
            else:next_active.update(dst for dst in successors if dst in table)
        active=next_active
        if not active:break
    return tuple(sorted(out))

def classify(rows,edges,owner,start,refusal_visit):
    if not 2<=refusal_visit<=256:raise ValueError('call census refusal')
    paths=first_calls(rows,edges,owner,start,refusal_visit-1)
    return tuple(edge for n,edge in paths if n==refusal_visit-1)
