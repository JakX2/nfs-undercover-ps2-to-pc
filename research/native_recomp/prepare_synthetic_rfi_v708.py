import re,sys
from pathlib import Path
root=Path(sys.argv[1])
expected={0x8000400c:0x38a50001,0x80000548:0x4c000064}
seen=set()
for p in root.glob('*.cpp'):
    s=p.read_text();old=s
    for pc,w in expected.items():
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        hits=list(pat.finditer(s))
        if not hits:continue
        if len(hits)!=1 or pc in seen:raise ValueError('duplicate RFI/resume label')
        seen.add(pc)
        s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
    if s!=old:
        a='#include "runtime/cpu_context.h"'
        if s.count(a)!=1:raise ValueError('include')
        p.write_text(s.replace(a,a+'\n#include "rfi_test_v708.h"'))
if seen!=set(expected):raise ValueError('missing RFI/resume label')
print('V708_RFI_ROUTE labels=2')
