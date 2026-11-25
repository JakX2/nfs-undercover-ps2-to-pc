#!/usr/bin/env python3
"""Report compiler error category and source line without private generated text."""
import re,sys
from pathlib import Path
p=Path(sys.argv[1])
if p.stat().st_size>8*1024*1024:raise SystemExit(1)
rows=p.read_text(errors='replace').splitlines()
for l in rows:
    m=re.search(r'(test_owner_transfer_v765\.cpp|output(?:_[0-9]+)?\.cpp|owner_transfer_input\.h):([0-9]+):[0-9]+: (?:(?:fatal )?error|warning): (.*)',l)
    if not m:continue
    msg=m[3];kind=next((i for i,k in enumerate(('expected','not declared','no member','ambiguous','no matching','undefined','invalid','unused','comparison','cannot convert'),1) if k in msg),0)
    flag=re.search(r'\[-W(?:error=)?([a-z-]+)\]',msg)
    flags={'type-limits':1,'sign-compare':2,'address':3,'unused-variable':4,'conversion':5}
    warning=flags.get(flag[1],0) if flag else 0
    print(f'V768_TRANSFER_BUILD_DIAG source={1 if m[1].startswith("test_") else 2 if m[1].startswith("output") else 3} line={int(m[2])} category={kind} flag={warning}')
