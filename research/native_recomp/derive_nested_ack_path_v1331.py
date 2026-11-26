"""Derive bounded interprocedural callback path censuses from private rows.

Only the unique observed handler-local call edge is admitted. Nested calls
must follow already authenticated direct edges; no indirect transfer,
syscall, arbitrary return or additional handler call is admitted.
"""
from derive_first_ack_call_v1330 import classify

def derive(rows,edges,msr,owner,start,goal,call_visit=19,ordinal=4,limit=256):
    if not 1<=call_visit<limit<=256 or not 1<=ordinal<=len(edges):
        raise ValueError('nested census limit')
    if classify(rows,edges,owner,start,call_visit+1)!=(ordinal,):
        raise ValueError('nested census candidate')
    table={}
    for pc,w,root,guard in rows:
        if pc in table or pc&3:raise ValueError('nested census identity')
        table[pc]=(w,root,guard)
    edge_map=dict(edges);msr_map=dict(msr)
    if len(edge_map)!=len(edges) or len(msr_map)!=len(msr):
        raise ValueError('nested census identity')
    site,dest=edges[ordinal-1]
    if table.get(goal)!=(0x4e800421,owner,True) or table[site][1]!=owner:
        raise ValueError('nested census frontier')
    # State before current instruction. Stack contains return addresses
    # and authenticated caller owners. Counter counts actual entered calls.
    active={(start,owner,(),0,0,False)}
    result=set()
    for visit in range(limit+1):
        nxt=set()
        for pc,root,stack,calls,writes,used in active:
            row=table.get(pc)
            if row is None or row[1]!=root:continue
            w,_,guard=row
            if pc==goal and not stack and used and calls:
                result.add((visit,calls,writes));continue
            if guard:continue
            op=w>>26;xo=(w>>1)&1023
            def add(dst,own=root,st=stack,n=calls,m=writes,u=used):
                if len(st)<=8 and n<=16 and m<=8:nxt.add((dst,own,st,n,m,u))
            if op==18 and w&3==1:
                dst=(pc+((w&0x03fffffc)^0x02000000)-0x02000000)&0xffffffff
                if edge_map.get(pc)!=dst or dst not in table or table[dst][1]!=dst:
                    continue
                if root==owner:
                    if used or pc!=site or visit!=call_visit:continue
                    add(dst,dst,stack+((pc+4,root),),calls+1,writes,True)
                elif stack:add(dst,dst,stack+((pc+4,root),),calls+1)
                continue
            if w==0x4e800020:
                if stack:
                    ret,caller=stack[-1];add(ret,caller,stack[:-1])
                continue
            if op==31 and xo==146:
                if msr_map.get(pc)==w:add(pc+4,m=writes+1)
                continue
            if op in (16,18):
                if w&3:continue
                mask,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
                dst=(pc+((w&mask)^sign)-sign)&0xffffffff
                if table.get(dst,(0,0,False))[1]!=root:continue
                add(dst)
                if op==16 and (w>>21)&20!=20:add(pc+4)
                continue
            if op==17 or (op==19 and xo in (16,50,528)):continue
            add(pc+4)
        if len(nxt)>20000 or len(result)>256:raise ValueError('nested census complexity')
        active=nxt
        if not active:break
    if not result:raise ValueError('nested census no route')
    return site,dest,tuple(sorted(result))
