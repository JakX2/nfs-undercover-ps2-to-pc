#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1])
if p.stat().st_size>16*1024*1024:raise SystemExit(0)
for line in p.read_text(errors='replace').splitlines():
    m=re.search(r'([A-Za-z0-9_.-]+\.(?:h|cpp)):(\d+):\d+: (?:fatal )?error: (.*)',line)
    if m:
        owner=m[1]=='test_owner_packet_choice_v881.cpp'
        categories=('parentheses','not declared','no member','no matching','expected','unused','redefinition','invalid','conversion')
        c=next((i+1 for i,k in enumerate(categories) if k in m[3]),0)
        print(f'V887_PACKET_BUILD fixture={int(owner)} line={m[2] if owner else 0} category={c}')
