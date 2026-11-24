#!/usr/bin/env python3
"""Continue the exact restored callback's first nested call, not an LR-range guess."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
from trace_v427_restored_function import branch,step_row,abort_row,edges,STEP,LINE,MAX_LOG,MAX_CPP
from repair_v424_nand_aot_placeholder import prepare,result,aot_entry
from audit_v420_nand_sc_provenance import parse
from audit_v413_nand_context_resume import inspect as context_gate
from audit_v414_nand_resumed_coverage import classify,TRIAL
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

OWNED='''    const bool owned=ctx.lr>=v395_next_pc&&
         ctx.lr-v395_next_pc<0x800u&&(ctx.lr&3u)==0u;'''
STOP='if(owned||v396_calls==192u){'
GUARD='check(v404_completed,"V402 extended original guest frontier incomplete");'
MARK=b'V432_NESTED_CONTINUE exact=1 call=1'
FAILURE='V402 extended original guest frontier incomplete'

# No assumption that an LR in a 2 KiB region proves a return. The exact
# recovered branch edge must be both present in the original and observed.
def first_edge(raw,pc,words):
    if len(raw)>MAX_LOG or len(words)!=15:raise ValueError('control geometry')
    kind,target=branch(words[5],pc+20)
    if kind!='direct_link' or target is None or pc<=target<pc+60 or not 0x80400000<=target<0x80600000:raise ValueError('branch')
    entries=[];slots=[]
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            entries.append((int(m[1]),int(m[2],16),int(m[3],16),int(m[8])))
        elif line.startswith(b'V427_NATIVE_STEP'):
            m=STEP.fullmatch(line)
            if not m:raise ValueError('step')
            if len(entries)!=1:raise ValueError('step order')
            slots.append(int(m[1]))
    if len(entries)!=2 or entries[0][0:2]!=(0,pc) or entries[0][3]!=0 or entries[1]!=(1,target,pc+24,0) or slots!=list(range(6)):raise ValueError('nested edge')
    return target,pc+24

def patch(source,pc,target,lr):
    if not all(0x80400000<=a<0x80600000 and not a&3 for a in (pc,target,lr)) or lr!=pc+24 or pc<=target<pc+60:raise ValueError('edge geometry')
    if any(source.count(a)!=1 for a in (OWNED,STOP,GUARD,'V420_CB_ENTRY call=','V413_CONTEXT_TRIAL complete=')) or 'V432_NESTED_CONTINUE' in source:raise ValueError('source seam')
    replacement=OWNED.replace('const bool owned','const bool v432_region_owned')+f'''
    const bool v432_exact_nested=v432_region_owned&&v396_calls==0u&&
         v395_next_pc==0x{pc:08x}u&&addr==0x{target:08x}u&&ctx.lr==0x{lr:08x}u&&
         v398_site_seen==0u&&v400_parent_site==0u&&!v413_context.restored();
    const bool owned=v432_region_owned&&!v432_exact_nested;
    if(v432_exact_nested)std::cout<<"V432_NESTED_CONTINUE exact=1 call=1"<<std::endl;'''
    out=source.replace(OWNED,replacement,1)
    if out.replace(replacement,OWNED,1)!=source or out.count(STOP)!=1 or out.count(GUARD)!=1:raise ValueError('route')
    return out

def audit(raw,rc,pc,target,lr):
    # Reuse the existing partial-progress parser; don't demand the old
    # retry route after restoring the real code. Keep every old guard.
    base=result(raw,rc,pc).replace('V424_REPAIR_RESULT','V432_NESTED_RESULT',1)
    active=False;pending=False;retired=0
    for line in raw.splitlines():
        if line.startswith(b'V432_NESTED_CONTINUE'):
            if line!=MARK or not active or pending:raise ValueError('retirement')
            pending=True
        elif line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            call=int(m[1]);addr=int(m[2],16);back=int(m[3],16);resumed=int(m[8])
            if call==0:
                if pending:raise ValueError('incomplete retirement')
                active=addr==pc and not resumed
            elif call==1 and pending:
                if (addr,back,resumed)!=(target,lr,0):raise ValueError('retired edge mismatch')
                retired+=1;pending=False;active=False
            else:
                if pending:raise ValueError('retired edge order')
                active=False
        elif line==TRIAL:
            if pending:raise ValueError('incomplete retirement')
            active=False
    if pending or retired>16:raise ValueError('retirement bound')
    return base+f' retired_exact={retired}'

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','baseline_cpp','baseline_log','candidate','candidate_cpp','candidate_log','trace_log','harness','output'):p.add_argument(n,type=Path)
    p.add_argument('--run-log',type=Path);p.add_argument('--run-rc',type=int);a=p.parse_args()
    try:
        for path,limit in ((a.owner,20_000_000),(a.elf,64_000_000),(a.fixture,20_000_000),(a.candidate,20_000_000),(a.baseline_cpp,MAX_CPP),(a.candidate_cpp,MAX_CPP),(a.baseline_log,MAX_LOG),(a.candidate_log,MAX_LOG),(a.trace_log,MAX_LOG),(a.harness,24_000_000)):
            if path.stat().st_size>limit:raise ValueError('size')
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.fixture.read_bytes();candidate=a.candidate.read_bytes();cpp=a.candidate_cpp.read_text(encoding='utf-8');harness=a.harness.read_text(encoding='utf-8')
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        if not context_gate(a.baseline_log,0).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):raise ValueError('baseline')
        sizes=parse_functions(elf);plan=prepare(owner,fixture,sizes,a.baseline_cpp.read_text(encoding='utf-8'),parse(a.baseline_log.read_bytes()))
        if plan.kind!='exact' or plan.size!=60 or plan.candidate!=candidate or aot_entry(cpp,plan.pc)!=(1,1):raise ValueError('repair')
        raw=a.candidate_log.read_bytes();trace=a.trace_log.read_bytes();words=struct.unpack('>15I',text_at(owner,plan.pc,60))
        if result(raw,134,plan.pc)!='V424_REPAIR_RESULT rc=134 kind=signal trials=1 complete=0 target_seen=1 resumed=0 status3=0 same_retry=0 max_calls=1 boot_verified=0':raise ValueError('candidate control')
        if step_row(trace,134,plan.pc,words)!='V427_STEP_RESULT rc=134 entered=1 steps=6 prior_steps=0 last_slot=5 last_kind=direct_link boot_verified=0':raise ValueError('trace control')
        for log in (raw,trace):
            if not abort_row(log,harness,134)[1].endswith('label='+FAILURE):raise ValueError('guard control')
        target,lr=first_edge(trace,plan.pc,words)
        if classify(owner,candidate,sizes,target)[0]!='original' or aot_entry(cpp,target)!=(1,1):raise ValueError('callee coverage')
        updated=patch(harness,plan.pc,target,lr)
        if a.run_log is None:
            with a.output.open('x',encoding='utf-8') as f:f.write(updated)
            print('V432_NESTED_ROUTE installed=1 exact_edge=1 old_guards=1 cap=192')
        else:
            if a.run_rc is None or a.run_log.stat().st_size>MAX_LOG or a.output.read_text(encoding='utf-8')!=updated:raise ValueError('run control')
            raw=a.run_log.read_bytes();print(audit(raw,a.run_rc,plan.pc,target,lr))
            for row in abort_row(raw,updated,a.run_rc):print(row.replace('V427_','V432_',1))
            print(context_gate(a.run_log,a.run_rc).replace('V413_CONTEXT_CENSUS','V432_CONTEXT_CENSUS',1))
        print('V432_NESTED_AUDIT inspected=1');return 0
    except (OSError,ValueError,struct.error,IndexError,UnicodeError):
        print('V432_NESTED_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
