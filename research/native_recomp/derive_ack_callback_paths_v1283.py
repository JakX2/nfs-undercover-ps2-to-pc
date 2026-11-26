"""Derive bounded visit counts from authenticated handler-local CFG.

The helper-return label has already been counted. The frontier label is
included in each distance. No additional native call or guarded label is
permitted. The live strict branch witness still checks the actual path.
"""
LIMIT=256
def path_lengths(rows,owner,start,goal,limit=LIMIT):
    if not 1<=limit<=LIMIT or start==goal:raise ValueError('ACK callback path')
    table={}
    for pc,w,root,guard in rows:
        if root!=owner:continue
        if pc in table or pc&3:raise ValueError('ACK callback path')
        table[pc]=(w,guard)
    if start not in table or table[start][1] or table.get(goal)!=(0x4e800421,True):
        raise ValueError('ACK callback path')
    def successors(pc):
        w,guard=table[pc]
        if guard:return ()
        op=w>>26;xo=(w>>1)&1023
        if op in (16,18):
            if w&3:return ()
            m,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            dst=(pc+((w&m)^sign)-sign)&0xffffffff
            if op==18 or (w>>21)&20==20:return (dst,)
            return (pc+4,dst)
        if op==17 or op==19 and xo in (16,50,528) or op==31 and xo==146:return ()
        return (pc+4,)
    active={start};lengths=[]
    for n in range(1,limit+1):
        active={dst for pc in active for dst in successors(pc) if dst in table}
        if goal in active:
            lengths.append(n);active.remove(goal)
        active={pc for pc in active if not table[pc][1]}
        if not active:break
    if not lengths:raise ValueError('ACK callback path')
    return tuple(lengths)
