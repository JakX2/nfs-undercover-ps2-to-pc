"""Export only a unique, adjacent, bounded IRQ entry refusal after exit 119."""
import re
from audit_v603_boot_report import MAX_LOG
PAT=re.compile(rb'V661_IRQ_BEGIN refusal=([0-9]{1,4}) pending=([0-9]{1,10})')
FAIL=b'V616_IRQ_INVALID reason=1 stage=0'
def diagnostic(raw,rc):
    if rc!=119 or len(raw)>MAX_LOG:return None
    lines=raw.splitlines()
    hits=[(i,PAT.fullmatch(l)) for i,l in enumerate(lines) if l.startswith(b'V661_IRQ_BEGIN')]
    failures=[i for i,l in enumerate(lines) if l==FAIL]
    if len(hits)!=1 or len(failures)!=1 or hits[0][0]!=failures[0]+1 or not hits[0][1]:return None
    refusal,pending=map(int,hits[0][1].groups())
    if not (1<=refusal<=1024 and pending<=0xffffffff):return None
    if refusal!=1024 and bool(refusal&32)!=bool(pending):return None
    return lines[hits[0][0]].decode('ascii')
