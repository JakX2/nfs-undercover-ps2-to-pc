#!/usr/bin/env python3
"""One complete-image execution, independently checked contiguous predecessor proofs.

Never infer a completed phase from a checkpoint count alone. All prior
auditors remain authoritative, and no original code or raw log is exported.
"""
import argparse,re
from pathlib import Path
import audit_v574_dsp_sc as sc
import audit_v581_dsp_return as dsp
import audit_v591_memory_init as mi
import audit_v603_boot_report as report
import audit_v609_arena_clear as arena
import audit_v616_irq_enable as irq
import audit_v625_ipc_client as ipc
from audit_v575_dsp_sc_frontier import frontier
MAX_LOG=ipc.MAX_LOG
SCOPES=(
    ('sc',(sc.SC,sc.GATE),sc.STAGES,sc.RESULT,sc.inspect),
    ('dsp',(dsp.PREFIX,),dsp.STAGES,dsp.RESULT,dsp.inspect),
    ('mi',(mi.PREFIX,mi.MAPPER),mi.STAGES,mi.RESULT,mi.inspect),
    ('report',(report.PREFIX,),report.EVENTS,report.RESULT,report.inspect),
    ('arena',(arena.PREFIX,),arena.EVENTS,arena.RESULT,arena.inspect),
    ('irq',(irq.PREFIX,),irq.EVENTS,irq.RESULT,irq.inspect),
    ('ipc',(ipc.PREFIX,),ipc.STAGES,ipc.RESULT,ipc.inspect),
)
# Only the explicit failure for the actual process exit code is diagnostic.
# Earlier scopes that fail before these phases retain their own audit rules.
DIAG=(
    (114,'dsp',rb'V581_DSP_RETURN_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2})',5),
    (115,'mi',rb'V591_MI_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2})',20),
    (116,'report',rb'V603_REPORT_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2}) reports=[0-9]{1,2} getters=[0-9]{1,2}',17),
    (117,'arena',rb'V609_ARENA_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2})',20),
    (119,'irq',rb'V616_IRQ_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2})',4),
    (120,'ipc',rb'V625_IPC_INVALID reason=([0-9]{1,2}) stage=([0-9]{1,2})',19),
)
def match_result(want,line):
    return line==want if isinstance(want,bytes) else want.fullmatch(line) is not None
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=raw.splitlines()
    fallback=any(l.startswith(b'V425_HARDWARE_FALLBACK') for l in lines)
    previous=-1;contiguous=not fallback;proofs={};counts={};first_failure=None
    indexed=[[(i,l) for i,l in enumerate(lines) if l.startswith(prefixes)]
             for _,prefixes,_,_,_ in SCOPES]
    for k,(name,_,events,result,auditor) in enumerate(SCOPES):
        pairs=indexed[k];rows=[l for _,l in pairs]
        n=0
        if contiguous and pairs and pairs[0][0]>previous:
            for a,b in zip(rows,events):
                if a!=b:break
                n+=1
        complete=False
        if contiguous and n==len(events) and len(rows)==len(events)+1 and match_result(result,rows[-1]):
            end=pairs[-1][0]
            # A later phase cannot start before this phase has returned,
            # and late duplicated/contradictory earlier evidence is rejected.
            if all(not p or p[0][0]>end for p in indexed[k+1:]):
                _,complete=auditor(b'\n'.join(lines[:end+1]),0)
                if complete:previous=end
        counts[name]=(n,len(events));proofs[name]=int(complete)
        if not complete:
            contiguous=False
            if first_failure is None:first_failure=name
    progress='V628_STARTUP_COUNTS '+' '.join(f'{k}={a}/{b}' for k,(a,b) in counts.items())
    prefix='V628_STARTUP_PREFIX '+' '.join(f'{k}={v}' for k,v in proofs.items())+' boot_verified=0'
    _,strict=ipc.inspect(raw,rc)
    ok=bool(rc==0 and strict and all(proofs.values()) and not fallback)
    diag=[]
    for exit_code,name,pattern,max_stage in DIAG:
        for l in lines:
            m=re.fullmatch(pattern,l)
            if m:diag.append((exit_code,name,int(m[1]),int(m[2]),max_stage))
    stop=None
    if len(diag)==1:
        exit_code,name,reason,stage,max_stage=diag[0]
        if rc==exit_code and name==first_failure and 0<reason<=99 and 0<=stage<=max_stage:
            stop=f'V628_STARTUP_STOP phase={name} reason={reason} stage={stage}'
    early,_=frontier(raw,rc)
    summary=f'V628_STARTUP_CENSUS rc={rc} fallback={int(fallback)} complete_ipc={int(ok)} boot_verified=0'
    return (early,progress,prefix,stop,summary),ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        rows,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V628_STARTUP_AUDIT inspected=0');return 1
    for row in rows:
        if row:print(row)
    print('V628_STARTUP_AUDIT inspected=1')
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
