"""Strict Windows full-image fourth-transfer caller continuation."""
import re
from audit_v777_transfer_return import RESULT as TRANSFER
from audit_v778_transfer_suffix import BOUNDARY, BLR, inspect as audit_suffix
from audit_v747_time_suffix import CONTROL, INVALID
from windows_transfer_return_v752 import inspect as audit_return, diagnostic as prior
from windows_startup_scope_v434 import MAX_LOG

def inspect(raw, rc, timed_out=False):
    if (type(raw) is not bytes or len(raw)>MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('transfer suffix log contract')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(TRANSFER,l)]
    return_ok=ok=False
    ordinal=kind=follow=blr=0
    if len(hits)==1:
        i=hits[0]
        before,tail=rows[:i+1],rows[i+1:]
        if not any(l.startswith(b'V778_') for l in before):
            _,return_ok=audit_return(b'\n'.join(before)+b'\n',0)
        boundary=(rc==126 and len(tail)==3 and
                  all(re.fullmatch(p,l) for p,l in zip((CONTROL,BOUNDARY,INVALID),tail)))
        terminal=(rc==0 and len(tail)==1 and re.fullmatch(BLR,tail[0]))
        if return_ok and not timed_out and (boundary or terminal):
            _,ok=audit_suffix(raw,rc)
            if ok and boundary:
                ordinal,kind,_,_,follow=map(int,re.fullmatch(BOUNDARY,tail[1]).groups())
            elif ok and terminal:
                blr=1
                follow=int(re.fullmatch(BLR,tail[0])[3])
    return (f'V753_WINDOWS_TRANSFER_SUFFIX return_verified={int(return_ok)} '
            f'suffix_verified={int(ok)} ordinal={ordinal} kind={kind} '
            f'follow={follow} blr_boundary={blr} '
            'next_instruction_executed=0 handler_return=0 boot_verified=0', bool(ok))

def diagnostic(line):
    return type(line) is bytes and (prior(line) or any(
        re.fullmatch(p,line) is not None for p in (CONTROL,BOUNDARY,INVALID,BLR)))
