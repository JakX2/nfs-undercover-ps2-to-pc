#!/usr/bin/env python3
"""Allowlisted private C++ compile diagnostics; never output original code."""
import re,sys
from pathlib import Path
p=Path(sys.argv[1])
if p.stat().st_size>16*1024*1024:raise SystemExit(0)
names=('wii_transfer_return_v774.h','wii_transfer_prefix_binding_v768.h','wii_si_ack_binding_v672.h','wii_si_handler_return_binding_v726.h','wii_si_binding_v512.h','wii_postack_transfer_device_v771.h','wii_si_type_scheduler_v514.h','wii_si_os_leaf_binding_v709.h','v777_private_transfer_return.h')
pattern=re.compile(r'([A-Za-z0-9_.-]+\.(?:h|cpp)):(\d+):\d+: (?:fatal )?error: (.*)')
seen=set()
for line in p.read_text(errors='replace').splitlines():
    m=pattern.search(line)
    if not m:continue
    source=names.index(m[1])+1 if m[1] in names else 0
    kinds=('not declared','no member','no matching','expected','redefinition','incomplete type','cannot convert','invalid','ambiguous','too many','not a member')
    kind=next((i+1 for i,k in enumerate(kinds) if k in m[3]),0)
    row=(source,int(m[2]) if source else 0,kind)
    if row not in seen and len(seen)<32:
        seen.add(row);print(f'V779_TRANSFER_SYNTAX source={row[0]} line={row[1]} category={row[2]}')
