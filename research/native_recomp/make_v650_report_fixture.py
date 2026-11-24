#!/usr/bin/env python3
"""Private isolated outer report: actual original control flow, stub print sink.

The print sink is explicitly synthetic and only returns to the original
caller's resume. Never claim execution of the original output backend.
"""
import argparse,struct
from pathlib import Path
from make_v594_boot_report_geometry import START,END,REPORT,TARGETS
from prepare_v603_boot_report import expectations,patch_label
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v453_debug_leaf import data_at
from make_v626_ipc_fixture import assemble
from make_private_elf_symbol_map import parse_functions
from audit_v594_report_translation import check
from make_start_to_boot_report_v66 import DATA,STOP
ENTRY=0x805208f4
def build(dol,elf):
    exp,roots,labels,bctr=expectations(dol,elf)
    sizes=parse_functions(elf)
    blocks={ENTRY:exact_words(dol,elf,ENTRY,(STOP-ENTRY)//4+1),REPORT:(0x4e800020,)}
    pending=list(roots)
    while pending:
        pc=pending.pop()
        if pc in blocks:continue
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3 or len(blocks)>=32:raise ValueError('report closure')
        body=exact_words(dol,elf,pc,n//4);blocks[pc]=body
        for i,w in enumerate(body):
            if w>>26!=18:continue
            at=pc+4*i;disp=w&0x03fffffc
            if disp&0x02000000:disp-=0x04000000
            target=(disp if w&2 else at+disp)&0xffffffff
            if pc<=target<pc+n:continue
            if target not in blocks:
                if target not in sizes:raise ValueError('report external edge')
                pending.append(target)
    raw=bytearray(assemble(blocks,ENTRY))
    for i,(addr,n) in enumerate(DATA):
        data=data_at(dol,addr,n)
        for off,v in ((0x1c+4*i,len(raw)),(0x64+4*i,addr),(0xac+4*i,n)):struct.pack_into('>I',raw,off,v)
        raw.extend(data)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    f=lambda n:f'0x{n:08x}u'
    words={pc+4*i:w for pc,ws in blocks.items() for i,w in enumerate(ws) if pc!=REPORT}
    h=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v650 {\nstruct Word{uint32_t pc,word;};\n'
        'inline constexpr std::array<Word,'+str(len(words))+'> words{'+','.join('Word{'+f(pc)+','+f(w)+'}' for pc,w in sorted(words.items()))+'};\n}\n')
    return raw,csv,exp,h,labels,bctr
def install_traces(dol,elf,generated):
    _,_,labels,bctr=expectations(dol,elf)
    paths=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if not paths or any(p.is_symlink() for p in paths+[main]):raise ValueError('trace tree')
    check((p.read_text() for p in paths),main.read_text(),bctr,{p:labels[p] for p in (bctr,*TARGETS)})
    seen=set()
    for p in paths:
        s=p.read_text()
        for pc,w in labels.items():
            if f'loc_{pc:X}: ;' in s:
                if pc in seen:raise ValueError('duplicate trace')
                s=patch_label(s,pc,w);seen.add(pc)
        p.write_text(s)
    if seen!=set(labels):raise ValueError('trace coverage')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);p.add_argument('--trace',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        if a.trace:
            install_traces(d,e,a.out);print('V650_REPORT_TRACES verified=1');return 0
        raw,csv,exp,h,_,_=build(d,e)
        a.out.mkdir(mode=0o700)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'symbols.csv').write_text(csv)
        (a.out/'v603_private_report_expectations.h').write_text(exp);(a.out/'v650_private_words.h').write_text(h)
    except (OSError,ValueError,struct.error) as e:
        why=str(e) if str(e) in {'report closure','report external edge','fixture range','fixture overlap','fixture span','trace tree','duplicate trace','trace coverage','report trace label','report coverage','report case dispatch','report native label'} else 'geometry'
        print('V650_REPORT_FIXTURE accepted=0 reason='+why.replace(' ','_'));return 1
    print('V650_REPORT_FIXTURE accepted=1 exact_dol_elf=1 output_backend=0');return 0
if __name__=='__main__':raise SystemExit(main())
