"""Bounded private post-alarm label census, no original words in public output."""
from audit_handler_suffix_v728 import target
def collect_after_alarm(root,original,translated,guards,start):
    end=root+4*len(original)
    if len(original)!=len(translated) or not 1<=len(original)<=1024 or root&3 or start&3 or not root<=start<end:
        raise ValueError('third alarm suffix extent')
    calls=[root+4*i for i,w in enumerate(original) if (w>>26==18 and w&3==1) or w==0x4e800421]
    ordinals={pc:i+1 for i,pc in enumerate(calls)}
    rows={};todo=[start]
    while todo:
        pc=todo.pop()
        if pc in rows:continue
        if pc&3 or not root<=pc<end:raise ValueError('third alarm suffix extent')
        if len(rows)>=256:raise ValueError('third alarm suffix geometry')
        w=original[(pc-root)//4];emitted=translated[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        # Refusal labels are terminal diagnostics even when the original
        # instruction is a call, conditional branch, or other system op.
        if pc in guards:
            if emitted!=0x4e800020:raise ValueError('third alarm suffix guard')
            rows[pc]=(emitted,0,0);continue
        if emitted!=w:raise ValueError('third alarm suffix word')
        if pc in ordinals:
            ordinal=ordinals[pc]
            if ordinal>12:raise ValueError('third alarm suffix call')
            rows[pc]=(w,ordinal,2 if w==0x4e800421 else 1);continue
        if w==0x4e800020:
            rows[pc]=(w,0,0);continue
        if (op==19 and xo in (16,50,528)) or (op==31 and xo==146) or op==17:
            raise ValueError('third alarm suffix boundary')
        rows[pc]=(w,0,0)
        if op in (16,18):
            if w&3:raise ValueError('third alarm suffix boundary')
            dest=target(pc,w)
            if not root<=dest<end or dest&3:raise ValueError('third alarm suffix extent')
            todo.append(dest)
            if op==18:continue
        todo.append(pc+4)
    if not rows or not any(k or w==0x4e800020 for w,_,k in rows.values()):
        raise ValueError('third alarm suffix geometry')
    return rows
