#!/usr/bin/env python3
"""Require one original boot-report body and its seven native dispatcher cases."""
import argparse,re,struct
from pathlib import Path
from make_v594_boot_report_geometry import START,END,TARGETS,geometry
from prepare_v419_full_start import words_at
LABEL=re.compile(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n')
def check(shards,main,bctr,expected):
    seen=dict.fromkeys((bctr,*TARGETS),0)
    owner=None
    for s in shards:
        # Restrict proof to exact generated function boundaries.
        defs=list(re.finditer(r'(?m)^void (fn_[0-9A-Fa-f]+|func_[0-9A-Fa-f]+)\(CPUContext& ctx\) \{',s))
        for i,m in enumerate(defs):
            body=s[m.end():defs[i+1].start() if i+1<len(defs) else len(s)]
            labels=list(LABEL.finditer(body))
            for j,l in enumerate(labels):
                pc=int(l[1],16)
                if pc not in seen:continue
                seen[pc]+=1
                if int(m[1].split('_')[1],16)!=START or int(l[2],16)!=pc or int(l[3],16)!=expected[pc]:
                    raise ValueError('report label ownership')
                if owner is not None and owner!=m[1]:raise ValueError('report function identity')
                owner=m[1]
                block=body[l.end():labels[j+1].start() if j+1<len(labels) else len(body)]
                if 'interpret_step' in block or 'micro_interpret' in block or '++ctx.inst_count;' not in block:raise ValueError('report native label')
                if pc==bctr and 'ctx.pc = ctx.ctr; return;' not in block:raise ValueError('computed native branch')
    if not owner or any(n!=1 for n in seen.values()):raise ValueError('report coverage')
    for pc in TARGETS:
        needle=f'case 0x{pc:X}: {owner}(ctx); break;'
        if main.count(needle)!=1:raise ValueError('report case dispatch')
    return True
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        dol=a.dol.read_bytes();bctr,_=geometry(dol,a.elf.read_bytes())
        expected={pc:words_at(dol,pc,1)[0] for pc in (bctr,*TARGETS)}
        shards=sorted(a.generated.glob('output_*.cpp'));main=a.generated/'main_output.cpp'
        if len(shards)<20 or any(p.is_symlink() or p.stat().st_size>64*1024*1024 for p in [*shards,main]):raise ValueError('full image')
        check((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),bctr,expected)
    except (OSError,ValueError,UnicodeError,struct.error) as e:
        reasons={'report label ownership','report function identity','report native label','computed native branch','report coverage','report case dispatch','full image'}
        print('V594_REPORT_TRANSLATION rejected=1 reason='+ (str(e).replace(' ','_') if str(e) in reasons else 'geometry'));return 1
    print('V594_REPORT_TRANSLATION owner=1 cases=7 root=1 computed=1 fallback=0 link=0 execution=0 boot_verified=0');return 0
if __name__=='__main__':raise SystemExit(main())
