#!/usr/bin/env python3
"""Emit only bounded counts/booleans on failure, never raw private log data."""
import argparse,re
from pathlib import Path
from audit_v534_sram_read import MAX_LOG,RESULT as SRAM,STAGES
from audit_v529_si_discovery import RESULT as DISC
from audit_v581_dsp_return import RESULT as DSP
from audit_v591_memory_init import RESULT as MI
from audit_v603_boot_report import RESULT as REPORT
from audit_v609_arena_clear import RESULT as ARENA
FAULT=re.compile(rb'V534_SRAM_INVALID reason=([1-7]) stage=(0|[1-9]|1[0-2])(?: completed=([0-2]))?')
def diagnostic(raw,rc,audit):
    if len(raw)>MAX_LOG or not 0<=rc<=255 or not 0<=audit<=255:raise ValueError('geometry')
    if not rc and not audit:return None
    rows=raw.splitlines()
    stages=[x for x in rows if x.startswith(b'V534_SRAM_STAGE ')]
    n=0
    for x,y in zip(stages,STAGES):
        if x!=y:break
        n+=1
    faults=[x for x in rows if x.startswith(b'V534_SRAM_INVALID')]
    m=FAULT.fullmatch(faults[0]) if rc==108 and len(faults)==1 else None
    reason=int(m[1]) if m else 0
    completed=int(m[3] or 0) if m else 0
    exact=lambda value:int(rows.count(value)==1)
    regex=lambda value:int(sum(bool(value.fullmatch(x)) for x in rows)==1)
    return f'V1225_COLD_FAILURE rc={rc} audit={audit} discovery={exact(DISC)} sram={exact(SRAM)} sram_stages={n} sram_reason={reason} sram_completed={completed} dsp={exact(DSP)} mi={exact(MI)} report={regex(REPORT)} arena={regex(ARENA)}'
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);p.add_argument('audit',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row=diagnostic(a.log.read_bytes(),a.rc,a.audit)
    except (OSError,ValueError):
        print('V1225_COLD_FAILURE inspected=0');return 0
    if row:print(row)
    return 0
if __name__=='__main__':raise SystemExit(main())
