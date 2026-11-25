#!/usr/bin/env python3
"""Redact compiler diagnostics; never print generated game code or paths."""
import re,sys
from pathlib import Path
p=Path(sys.argv[1]);fixture=sys.argv[2]
if p.stat().st_size>16*1024*1024:raise SystemExit(0)
for line in p.read_text(errors='replace').splitlines():
    m=re.search(r'([A-Za-z0-9_.-]+\.(?:h|cpp)):(\d+):\d+: (?:fatal )?error: (.*)',line)
    if m:
        own=m[1]==fixture
        categories=('parentheses','not declared','no member','no matching','expected','unused','redefinition','invalid','conversion','type-limits','sign-compare','narrowing','overflow')
        c=next((i+1 for i,k in enumerate(categories) if k in m[3]),0)
        print(f'V910_BUILD fixture={int(own)} line={m[2] if own else 0} category={c}')
