#!/usr/bin/env python3
import argparse
from pathlib import Path
from audit_v574_dsp_sc import MARKERS as PRIOR,MAX_LOG,inspect as inspect_sc
from audit_v575_dsp_sc_frontier import frontier
PREFIX=b'V581_DSP_'
MARKERS=PRIOR+(PREFIX,)
STAGES=[f'V581_DSP_RETURN_STAGE n={i}'.encode() for i in range(1,6)]
RESULT=b'V581_DSP_RETURN_RESULT reset=2 dma=2 bytes=64 ack=2 mailbox=1 delay=1 restore=128 returned=1 firmware_executed=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_sc(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V581_DSP_RETURN_CENSUS rc={rc} sc={int(prior)} stages={n} firmware_executed=0 fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
        prefix,diag=frontier(raw,a.rc)
    except (OSError,ValueError):
        print('V581_DSP_RETURN_AUDIT inspected=0');return 1
    print(prefix)
    if diag:print(diag)
    # Permit only public bounded diagnostic markers, never raw private logs.
    import re
    bad=[l for l in raw.splitlines() if re.fullmatch(rb'V581_DSP_RETURN_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V581_DSP_PROFILE_INVALID rejected=1',l)]
    if len(bad)==1:print(bad[0].decode())
    print(row);print('V581_DSP_RETURN_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
