"""Bounded reporting diagnostic; no private code, raw addresses or data."""
import re
from audit_v603_boot_report import MAX_LOG
PAT=re.compile(rb'V643_REPORT_DIAG mask=([0-9]{1,3}) class=([0-9]{1,2}) call_offset=([0-9]{1,3}) format_offset=([0-9]{1,3})')
FAIL=re.compile(rb'V603_REPORT_INVALID reason=8 stage=2 reports=([0-9]) getters=([0-6])')
def diagnostic(raw,rc):
    if rc!=116 or len(raw)>MAX_LOG:return None
    lines=raw.splitlines()
    hits=[(i,PAT.fullmatch(l)) for i,l in enumerate(lines) if l.startswith(b'V643_REPORT_DIAG')]
    failures=[i for i,l in enumerate(lines) if FAIL.fullmatch(l)]
    if len(hits)!=1 or len(failures)!=1 or hits[0][0]!=failures[0]+1 or not hits[0][1]:return None
    mask,kind,call,fmt=map(int,hits[0][1].groups())
    if not 1<=mask<=127 or not 0<=kind<=36 or call not in (*range(0,333,4),512) or not (0<=fmt<496 or fmt==512):return None
    return lines[hits[0][0]].decode('ascii')
