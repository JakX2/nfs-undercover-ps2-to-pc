#!/usr/bin/env python3
"""No-response completion followed by a real, unexecuted handler call."""
import argparse,re
from pathlib import Path
from audit_second_irq_output_v1016 import public_line
import audit_v1015_error_completion as error
import audit_v995_success_frontier as frontier
import audit_v975_second_time as time
import audit_v986_transfer_frontier as transfer
import audit_v989_shared_time as shared
import audit_v958_second_ack as ack
import audit_v967_post_ack as post
DIRECT=b'V1021_ERROR_FRONTIER branch=4 visits=78 handler_time=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
INDIRECT=b'V1021_ERROR_FRONTIER branch=6 visits=71 handler_time=0 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=16 stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
TAGS=frontier.TAGS+(b'V1009_',b'V1014_',b'V1015_',b'V1021_')
MAX_LOG=shared.old.old.old.capture.MAX_LOG
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l==error.RESULT]
    ok=False;branch=admitted=category=0
    if rc==0 and len(hits)==1:
        i=hits[0]
        prior,base,_=error.inspect(b'\n'.join(rows[:i+1]),0)
        tail=[l for l in rows[i+1:] if l.startswith(TAGS)]
        if base and 'no_response=1' in prior and not any(l.startswith(b'V1021_') for l in rows[:i+1]):
            if len(tail)==2 and tail[0]==INDIRECT:
                m=re.fullmatch(frontier.RESULT,tail[1])
                if m and 1<=int(m[1])<=4 and int(m[3])==71:
                    ok=True;branch=6;category=int(m[1]);admitted=int(category==2 and m[2]==b'1')
            elif len(tail)==3 and tail[1]==DIRECT:
                t=re.fullmatch(time.RESULT,tail[0]);m=re.fullmatch(transfer.RESULT,tail[2])
                if t and m and 1<=int(t[1])<78 and 1<=int(m[6])<78 and int(t[1])+int(m[6])<78 and int(m[5])==int(all(int(v) for v in m.groups()[:4])):
                    ok=True;branch=4;admitted=int(m[5])
    return f'V1021_ERROR_CENSUS verified={int(ok)} branch={branch} admitted={admitted} target_class={category} call_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1021_ERROR_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(ack.BEGIN,error.RESULT,DIRECT,INDIRECT),(FAULT,frontier.RESULT,frontier.FAULT,time.RESULT,transfer.RESULT,shared.DETAIL,shared.DIAG,shared.RESULT,post.RESULT,ack.RESULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
