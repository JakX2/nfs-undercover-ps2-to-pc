#!/usr/bin/env python3
"""Install opt-in SI type scheduling after the existing V497 native tick and V512 MMIO."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_exi_tick_v497 import EMITTER, CONTEXT, EMIT_NEW
SI_EMIT=EMIT_NEW+'\n  out << "    ctx.si_instruction_boundary();\\n";'
INCLUDE='#include "undercover/wii_si_binding_v512.h"'
METHOD='  void exi_instruction_boundary() { undercover::wii::ExiTickBinding::advance(inst_count); }'
def apply(root,phase,host):
    if phase=='emitter':
        path=root/EMITTER
        if path.is_symlink():raise ValueError('source symlink')
        data=rewrite(path.read_text(encoding='utf-8'),((EMIT_NEW,SI_EMIT),))
        if data!=path.read_text(encoding='utf-8'):path.write_text(data,encoding='utf-8')
        return
    path=root/CONTEXT
    dest=root/'nWiiRuntime/include/undercover'
    header=dest/'wii_si_type_scheduler_v514.h'
    if any(p.is_symlink() for p in (path,dest,header)) or not (dest/'wii_si_binding_v512.h').is_file():
        raise ValueError('predecessor')
    content=(host/header.name).read_bytes()
    if header.exists() and header.read_bytes()!=content:raise ValueError('header conflict')
    data=rewrite(path.read_text(encoding='utf-8'),(
        (INCLUDE,INCLUDE+'\n#include "undercover/wii_si_type_scheduler_v514.h"'),
        (METHOD,METHOD+'\n  void si_instruction_boundary() { undercover::wii::SiTickBinding::advance(inst_count); }'))).encode()
    for p,c in ((path,data),(header,content)):
        if not p.exists() or p.read_bytes()!=c:p.write_bytes(c)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=('emitter','runtime'));a=p.parse_args()
    try:apply(a.root,a.phase,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V515_SI_TICK installed=0');return 1
    print(f'V515_SI_TICK installed=1 phase={a.phase} opt_in=1');return 0
if __name__=='__main__':raise SystemExit(main())
