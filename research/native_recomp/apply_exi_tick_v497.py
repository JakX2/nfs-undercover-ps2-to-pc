#!/usr/bin/env python3
"""Opt-in EXI scheduler tick at the V438 native instruction-label boundary."""
import argparse
from pathlib import Path
from apply_native_tick_v438 import LABEL_TICK
from apply_irq_bootstrap_v475 import rewrite
EMITTER=Path('nWiiRecomp/src/recompiler.cpp')
CONTEXT=Path('nWiiRuntime/include/runtime/cpu_context.h')
# Preserve existing instruction-count ordering and all native labels.
EMIT_NEW=LABEL_TICK+'\n  out << "    ctx.exi_instruction_boundary();\\n";'
HEADER='#include "undercover/wii_irq_bank_binding_v481.h"'
# A standalone method is added to CPUContext, not MMU.
STRUCT='struct CPUContext {'
METHOD=STRUCT+'\n  void exi_instruction_boundary() { undercover::wii::ExiTickBinding::advance(inst_count); }'
def emitter(source):
    return rewrite(source,((LABEL_TICK,EMIT_NEW),))
def runtime(root,host):
    ctx=root/CONTEXT;dest=root/'nWiiRuntime/include/undercover'
    if ctx.is_symlink() or dest.is_symlink() or not (dest/'wii_exi_controller_v489.h').is_file():raise ValueError('predecessor')
    out=rewrite(ctx.read_text(encoding='utf-8'),((HEADER,HEADER+'\n#include "undercover/wii_exi_tick_binding_v497.h"'),(STRUCT,METHOD)))
    changes={ctx:out.encode()}
    for name in ('wii_exi_mx_device_v494.h','wii_exi_endpoint_scheduler_v495.h','wii_exi_tick_binding_v497.h'):
        path=dest/name;data=(host/name).read_bytes()
        if path.is_symlink() or (path.exists() and path.read_bytes()!=data):raise ValueError('header conflict')
        changes[path]=data
    for path,data in changes.items():
        if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=('emitter','runtime'));a=p.parse_args()
    try:
        if a.phase=='emitter':
            path=a.root/EMITTER
            if path.is_symlink():raise ValueError('symlink')
            path.write_text(emitter(path.read_text(encoding='utf-8')),encoding='utf-8')
        else:runtime(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V497_EXI_TICK installed=0');return 1
    print(f'V497_EXI_TICK installed=1 phase={a.phase} opt_in=1');return 0
if __name__=='__main__':raise SystemExit(main())
