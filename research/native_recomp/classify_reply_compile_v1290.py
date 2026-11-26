#!/usr/bin/env python3
"""Fixed-category compiler diagnostic; never output private compiler text."""
import argparse,re
from pathlib import Path
PUBLIC={
    'test_native_scheduler_postack_v1256.cpp':'harness',
    'wii_reply_processor_v1280.h':'reply_witness',
    'wii_wake_ready_v1288.h':'wake_witness',
    'cpu_context.h':'runtime_context',
}
KINDS=(
    ('redeclaration',r'conflicting declaration|redeclaration of|redefinition of'),
    ('conversion',r'cannot convert|could not convert|invalid conversion|no known conversion'),
    ('overload',r'no matching function|no match for'),
    ('member',r'has no member named|is not a member of'),
    ('undeclared',r'was not declared in this scope'),
    ('include',r'No such file or directory'),
    ('link',r'undefined reference|multiple definition'),
    ('syntax',r'expected [^\n]* before|unterminated|missing terminating'),
    ('resource',r'Killed signal|out of memory|virtual memory exhausted'),
)
def classify(raw):
    if len(raw)>16*1024*1024:return 'oversize','other',0
    s=raw.decode('utf-8','replace')
    for row in s.splitlines():
        if 'error:' not in row and 'undefined reference' not in row and 'multiple definition' not in row:continue
        m=re.search(r'(?:^|/)([A-Za-z0-9_.-]+):(\d{1,4}):(?:\d{1,4}:)?\s*(?:fatal )?error:',row)
        part='other';line=0
        if m and m[1] in PUBLIC:
            part=PUBLIC[m[1]]
            # Only line numbers from independently authored public source.
            if part!='runtime_context':line=int(m[2])
        kind=next((k for k,pattern in KINDS if re.search(pattern,row)),'other')
        return kind,part,line
    return 'unknown','other',0
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);a=p.parse_args()
    try:
        if a.log.stat().st_size>16*1024*1024:kind,part,line='oversize','other',0
        else:kind,part,line=classify(a.log.read_bytes())
    except OSError:kind,part,line='unknown','other',0
    print(f'V1290_REPLY_COMPILE kind={kind} part={part} line={line}')
if __name__=='__main__':main()
