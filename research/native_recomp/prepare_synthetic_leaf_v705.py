import sys,re,shutil
from pathlib import Path
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
HOST=Path(__file__).resolve().parent
H=0x80004000;D=0x80005000;T=0x80006000;R=0x80007000
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
roots={H:[bl(H,D),bl(H+4,T),0x38600000,bl(H+12,R),0x60000000,0x4e800020],
       D:[0x7c0000a6,0x7c000124,0x38600000,0x4e800020],
       T:[0x7c8c42e6,0x7c6d42e6,0x4e800020],R:[0x7c0000a6,0x7c000124,0x4e800020]}
def install(root,inc):
    paths=list(root.glob('*.cpp'));original={p:p.read_text() for p in paths}
    main=(root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')).read_text()
    outer=main[main.index('extern "C" void run_game('):]
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    assert audit_native(original.values(),outer,expected)==16
    seen=set()
    for p,s in original.items():
        if f'void func_{H:X}(CPUContext& ctx) {{' in s:
            for a,b in ((H,D),(H+4,T),(H+12,R)):verify_direct(exact_function(s,H),a,b)
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('leaf hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    leaf_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=original[p]:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('include')
            p.write_text(s.replace(anchor,anchor+'\n#include "leaf_test.h"'))
    if seen!=set(expected):raise ValueError('leaf hook coverage')
    dest=inc/'undercover';dest.mkdir(parents=True)
    shutil.copyfile(HOST/'wii_postack_os_leaf_v703.h',dest/'wii_postack_os_leaf_v703.h')
    shutil.copyfile(HOST/'leaf_test_v705.h',inc/'leaf_test.h')
    print('V705_PATCH native_labels=16 direct_edges=3')
if __name__=='__main__':install(Path(sys.argv[1]),Path(sys.argv[2]))
