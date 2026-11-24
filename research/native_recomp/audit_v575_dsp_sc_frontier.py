#!/usr/bin/env python3
"""Audit strict startup result and bounded predecessor-prefix progress separately."""
import argparse,re
from importlib import import_module
from pathlib import Path
from audit_v574_dsp_sc import MAX_LOG,inspect as inspect_sc
SCOPES=(('si','audit_v529_si_discovery'),('sram','audit_v534_sram_read'),
        ('thread','audit_v549_thread_init'),('audio','audit_v556_audio_reset'),
        ('stage','audit_v559_dsp_stage'),('sc','audit_v574_dsp_sc'))
DIAG=(
    ('sram',re.compile(rb'V534_SRAM_INVALID reason=([0-9]{1,3}) stage=([0-9]{1,2}) completed=([0-9]{1,6})')),
    ('thread',re.compile(rb'V549_THREAD_INVALID reason=([0-9]{1,3}) stage=([0-9]{1,2})')),
    ('audio',re.compile(rb'V556_AUDIO_INVALID reason=([0-9]{1,3}) stage=([0-9]{1,2})')),
    ('stage',re.compile(rb'V559_DSP_STAGE_INVALID reason=([0-9]{1,3}) stage=([0-9]{1,2})')),
    ('sc',re.compile(rb'V574_DSP_SC_INVALID rejected=(1)')),
    ('dispatch',re.compile(rb'V572_SC_DIRECT_ONLY rejected=(1)')),
)
def frontier(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=raw.splitlines();progress=[];last=-1;contiguous=True
    for name,module in SCOPES:
        auditor=import_module(module)
        hits=[i for i,l in enumerate(lines) if l==auditor.RESULT]
        good=False
        if contiguous and len(hits)==1 and hits[0]>last:
            i=hits[0]
            _,good=auditor.inspect(b'\n'.join(lines[:i+1]),0)
            if good:last=i
        if not good:contiguous=False
        progress.append((name,int(good)))
    row='V575_DSP_SC_FRONTIER '+ ' '.join(f'{n}={v}' for n,v in progress)+' boot_verified=0'
    failures=[]
    for name,pattern in DIAG:
        for l in lines:
            m=pattern.fullmatch(l)
            if m:
                reason=int(m[1]);stage=int(m[2]) if m.lastindex>=2 else 0
                failures.append(f'V575_DSP_SC_BOUNDARY phase={name} reason={reason} stage={stage}')
    # Do not print unbounded or conflicting diagnostics. Strict final result
    # is independently evaluated against the full log and exit status.
    return row,failures[0] if len(failures)==1 else None
def inspect(raw,rc):
    row,diag=frontier(raw,rc);strict,ok=inspect_sc(raw,rc)
    return (row,diag,strict),ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        rows,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V575_DSP_SC_AUDIT inspected=0');return 1
    for row in rows:
        if row:print(row)
    print('V575_DSP_SC_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
