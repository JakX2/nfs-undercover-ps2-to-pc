#!/usr/bin/env python3
"""Bounded private instruction witness for the V424 restored function.

Only ordinal slots, branch categories, and authenticated public assertion
labels leave the owner runner. Never print a guest address or code word.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct
from repair_v424_nand_aot_placeholder import prepare, aot_entry, HEAD, MAX_CPP, result
from audit_v420_nand_sc_provenance import parse, LINE
from audit_v413_nand_context_resume import inspect as context_gate
from audit_v414_nand_resumed_coverage import classify, MAX_LOG
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

STEP=re.compile(rb'V427_NATIVE_STEP slot=([0-9]{1,2}) inst=([0-9]{1,20})')
PUBLIC=re.compile(r'[A-Za-z0-9 _.,:/()\-]{1,170}\Z')
STRINGS=re.compile(r'"((?:[^"\\]|\\.)*)"')
ERROR=re.compile(r'what\(\):\s+([^\r\n]+)')
LIMIT=64

def branch(word,pc):
    op=word>>26;lk=word&1
    if op in (16,18):
        mask,bits=(0xfffc,16) if op==16 else (0x03fffffc,26)
        delta=word&mask
        if delta&(1<<(bits-1)):delta-=1<<bits
        target=(delta if word&2 else pc+delta)&0xffffffff
        kind=('conditional_link' if lk else 'conditional') if op==16 else ('direct_link' if lk else 'direct_tail')
        return kind,target
    if op==19 and (word>>1)&1023 in (16,528):
        return ('return' if (word>>1)&1023==16 and not lk else 'indirect'),None
    return ('syscall' if op==17 else 'other'),None

def instrument(generated,pc,words):
    if len(words)!=15 or aot_entry(generated,pc)!=(1,1) or 'V427_NATIVE_STEP' in generated:raise ValueError('geometry')
    marker=f'nwii::runtime::trace_call(0x{pc:08x}, ctx)'
    at=generated.lower().index(marker);heads=list(HEAD.finditer(generated))
    start=max(h.start() for h in heads if h.start()<at)
    end=next((h.start() for h in heads if h.start()>at),len(generated))
    body=generated[start:end];updated=body
    for slot,word in enumerate(words):
        address=pc+slot*4
        pat=re.compile(r'(?m)^loc_'+f'{address:X}'+r': ;\n    // 0x'+f'{address:08X}'+r': '+f'{word:08X}'+r'\n',re.I)
        hits=list(pat.finditer(updated))
        if len(hits)!=1:raise ValueError('instruction_seam')
        # Logs only; no change to guest PC, GPR, memory or branch decisions.
        m=hits[0];extra=(f'    if (v427_steps < {LIMIT}u) {{ ++v427_steps; '
            f'std::fprintf(stderr, "V427_NATIVE_STEP slot={slot} inst=%llu\\n", '
            'static_cast<unsigned long long>(ctx.inst_count)); std::fflush(stderr); }\n')
        updated=updated[:m.end()]+extra+updated[m.end():]
    head=HEAD.match(updated)
    if not head:raise ValueError('function_seam')
    updated=updated[:head.end()]+'\n    static unsigned v427_steps=0u;'+updated[head.end():]
    # Verify the entire body is recoverable verbatim after removing observers.
    back=re.sub(r'(?m)^    if \(v427_steps < 64u\).*V427_NATIVE_STEP[^\n]*\n','',updated)
    back=back.replace('\n    static unsigned v427_steps=0u;','',1)
    if back!=body:raise ValueError('nonreversible')
    return '#include <cstdio>\n'+generated[:start]+updated+generated[end:]

def edges(owner,candidate,sizes,generated,pc,words,reader=text_at):
    targets={t for i,w in enumerate(words) for _,t in (branch(w,pc+4*i),) if t is not None and not pc<=t<pc+4*len(words)}
    counts=dict(original=0,nop=0,modified=0,missing=0,unknown=0)
    bodies=dispatch=0
    for t in sorted(targets):
        try:k,_=classify(owner,candidate,sizes,t,reader)
        except ValueError:k='unknown'
        counts[k]+=1
        a,b=aot_entry(generated,t);bodies+=a;dispatch+=b
    return ('V427_STATIC_EDGES external='+str(len(targets))+' '+' '.join(f'{k}={v}' for k,v in counts.items())+f' body={bodies} dispatch={dispatch} boot_verified=0')

def abort_row(raw,harness,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255 or len(harness)>24_000_000:raise ValueError('abort_geometry')
    strings=sorted(set(STRINGS.findall(harness)))
    if len(strings)>9999:raise ValueError('catalog')
    log=raw.decode('utf-8',errors='replace')
    known=next((s for s in ERROR.findall(log) if s in strings),None)
    ident=strings.index(known)+1 if known is not None else 0
    label=known if known is not None and PUBLIC.fullmatch(known) else 'other'
    if label=='interpreter fallback':category='interpreter'
    elif label=='unexpected micro interpreter fallback':category='micro'
    elif 'syscall' in label.lower():category='syscall'
    elif 'mmio' in label.lower():category='mmio'
    elif known is not None:category='public_guard'
    else:category='unknown'
    exception=next((v for k,v in (('std::runtime_error','runtime'),('std::logic_error','logic'),('std::out_of_range','range'),('std::bad_alloc','alloc')) if k in log),'unclassified')
    return (f'V427_ABORT_CENSUS rc={rc} public_id={ident:04d} known={int(ident!=0)} category={category} exception={exception} boot_verified=0',f'V427_PUBLIC_FAILURE id={ident:04d} label={label}')

def step_row(raw,rc,pc,words):
    if len(raw)>MAX_LOG or len(words)!=15 or not 0<=rc<=255:raise ValueError('trace_geometry')
    seen=False;steps=[];total=0
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            if int(m[2],16)==pc and not int(m[8]):seen=True
        if line.startswith(b'V427_NATIVE_STEP'):
            m=STEP.fullmatch(line)
            if not m:raise ValueError('step')
            slot,inst=map(int,m.groups());total+=1
            if slot>=len(words) or total>LIMIT:raise ValueError('step_bound')
            if seen:
                if steps and inst<steps[-1][1]:raise ValueError('step_order')
                steps.append((slot,inst))
    last=steps[-1][0] if steps else 0
    kind=branch(words[last],pc+last*4)[0] if steps else 'none'
    return f'V427_STEP_RESULT rc={rc} entered={int(seen)} steps={len(steps)} prior_steps={total-len(steps)} last_slot={last} last_kind={kind} boot_verified=0'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','baseline_cpp','baseline_log','candidate','candidate_cpp','candidate_log','harness','output'):p.add_argument(n,type=Path)
    p.add_argument('--trace-log',type=Path);p.add_argument('--trace-rc',type=int);a=p.parse_args()
    try:
        for path,limit in ((a.owner,20_000_000),(a.elf,64_000_000),(a.fixture,20_000_000),(a.candidate,20_000_000),(a.baseline_cpp,MAX_CPP),(a.candidate_cpp,MAX_CPP),(a.baseline_log,MAX_LOG),(a.candidate_log,MAX_LOG),(a.harness,24_000_000)):
            if path.stat().st_size>limit:raise ValueError('size')
        owner=a.owner.read_bytes();elf=a.elf.read_bytes();fixture=a.fixture.read_bytes();candidate=a.candidate.read_bytes();cpp=a.candidate_cpp.read_text(encoding='utf-8')
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        if not context_gate(a.baseline_log,0).endswith('verified=1 context_verified=1 interrupted_verified=1 boot_verified=0'):raise ValueError('control')
        sizes=parse_functions(elf);plan=prepare(owner,fixture,sizes,a.baseline_cpp.read_text(encoding='utf-8'),parse(a.baseline_log.read_bytes()))
        if plan.kind!='exact' or plan.size!=60 or plan.candidate!=candidate:raise ValueError('repair_identity')
        raw=a.candidate_log.read_bytes()
        if result(raw,134,plan.pc)!='V424_REPAIR_RESULT rc=134 kind=signal trials=1 complete=0 target_seen=1 resumed=0 status3=0 same_retry=0 max_calls=1 boot_verified=0':raise ValueError('abort_control')
        words=struct.unpack('>15I',text_at(owner,plan.pc,60));harness=a.harness.read_text(encoding='utf-8')
        patched=instrument(cpp,plan.pc,words)
        if a.trace_log is None:
            for row in abort_row(raw,harness,134):print(row)
            print(edges(owner,candidate,sizes,cpp,plan.pc,words))
            with a.output.open('x',encoding='utf-8') as f:f.write(patched)
            print('V427_STEP_ROUTE installed=1 words=15 read_only=1')
        else:
            if a.trace_rc is None or a.trace_log.stat().st_size>MAX_LOG or a.output.read_text(encoding='utf-8')!=patched:raise ValueError('trace_control')
            trace=a.trace_log.read_bytes();print(step_row(trace,a.trace_rc,plan.pc,words))
            for row in abort_row(trace,harness,a.trace_rc):print(row.replace('V427_ABORT_','V427_TRACE_ABORT_').replace('V427_PUBLIC_','V427_TRACE_PUBLIC_'))
        print('V427_STEP_AUDIT inspected=1');return 0
    except (OSError,ValueError,struct.error,IndexError,UnicodeError):
        print('V427_STEP_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
