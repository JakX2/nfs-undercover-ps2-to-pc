#!/usr/bin/env python3
"""V478: classify the authenticated post-BLR NAND frontier, never guess an edge.
The selected callback has returned. An obsolete LR-region stop may only
be retired for the exact original direct link observed at the frontier.
Otherwise report the failure category and preserve all existing guards.
"""
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import struct
import subprocess
from audit_v420_nand_sc_provenance import LINE
from derive_v437_nand_restored_frame import inspect,BEGIN,BLR,RESUME
from derive_v432_nand_nested_call import STOP,GUARD
from trace_v427_restored_function import abort_row,branch,MAX_LOG,MAX_CPP,STRINGS,ERROR
from repair_v424_nand_aot_placeholder import aot_entry
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v414_nand_resumed_coverage import classify
from resolve_v308_descendant_boundaries import resolve

CONTROL='V437_FRAME_RESULT rc=134 begins=1 blr=1 resume=1 nested=2 max_calls=44 unique=25 original=25 first_nonoriginal=none boot_verified=0'
OWN='    const bool owned=v437_region_owned&&!v437_frame.active();'
RESET='  nwii::runtime::v437_frame={};'
STATE='static undercover::wii::RestoredFrameWitness v437_frame{};'
STOP_ROW=re.compile(rb'V404_NAND_EXTENDED_STOP calls=44 owner=([01]) selected_return=([01]) parent_return=([01])')
MARK=b'V478_NAND_EDGE continued=1 call=44'
@dataclass(frozen=True)
class Frontier:
    pc:int
    lr:int
    word:int
    kind:str
    owned:int
    reason:str
    ready:bool
    prefix:tuple
def trace(raw):
    e=[]
    for line in raw.splitlines():
        if line.startswith(b'V420_CB_ENTRY'):
            m=LINE.fullmatch(line)
            if not m:raise ValueError('entry')
            row=(int(m[1]),*(int(m[i],16) for i in range(2,6)),*(int(m[i]) for i in range(6,11)))
            if row[0]!=len(e) or row[0]>192 or row[1]&3 or row[2]&3:raise ValueError('order')
            e.append(row)
    return tuple(e)
def terminal(owner,fixture,sizes,cpp,harness,raw):
    if inspect(raw,134,owner,fixture,sizes)!=CONTROL:raise ValueError('control')
    e=trace(raw)
    if len(e)!=45 or any(aot_entry(cpp,x[1])!=(1,1) for x in e):raise ValueError('AOT coverage')
    lines=raw.splitlines()
    if lines.index(RESUME)>=next(i for i,l in enumerate(lines) if l.startswith(b'V420_CB_ENTRY call=44 ')):raise ValueError('resume order')
    _,pc,lr,ew,lw,em,lm,resumed,_,_=e[-1]
    reason=abort_row(raw,harness,134)[0].split(' category=')[1].split()[0]
    stop=[m for l in lines if (m:=STOP_ROW.fullmatch(l))]
    owned=int(len(stop)==1 and stop[0][1]==b'1')
    kind='unknown';word=0;auth=False
    try:
        word=struct.unpack('>I',text_at(owner,lr-4,4))[0]
        k,target=branch(word,lr-4)
        kind=k if k in ('direct_link','conditional_link','indirect','direct_tail','return','other','syscall','conditional') else 'unknown'
        span=resolve(sizes,lr-4)
        # Match the actual immutable original caller word and ensure the
        # whole caller extent is still original in this reduced image.
        auth=(kind=='direct_link' and target==pc and span.length>0 and
              text_at(owner,span.entry,sizes[span.entry])==text_at(fixture,span.entry,sizes[span.entry]) and
              text_at(fixture,lr-4,4)==struct.pack('>I',word) and
              (not lm or lw==word) and classify(owner,fixture,sizes,pc)[0]=='original')
    except (ValueError,IndexError,KeyError,struct.error):pass
    region=0<=lr-e[0][1]<0x800
    ready=bool(owned and region and auth and not resumed and
               abort_row(raw,harness,134)[1].endswith('label=V402 extended original guest frontier incomplete'))
    return Frontier(pc,lr,word,kind,owned,reason,ready,e)
# Exact public source labels only. Never forward unknown exception strings.
GUARD_CLASSES={
    'V402 extended original guest frontier incomplete':'frontier',
    'V395 original NAND _isfsFuncCb did not reach its next guest call':'selected',
    'V396 original guest-selected ISFS callback did not reach next call':'callback_body',
    'V396 original ISFS-selected guest callee provenance lost':'provenance',
    'V396 original callback body next guest entry not verified':'body_entry',
    'V390 original NAND guest never left Hollywood ACK for next callee':'post_ack',
    'V399 original ISFS continuation classification incomplete':'return_order',
    'V400 original parent return-PC classification incomplete':'parent_return',
    'V401 original PPC linksite classification incomplete':'linksite',
    'V405 original guest post-48 call census incomplete':'call_census',
    'V413 bounded NAND context continuation incomplete':'context',
    'V437 restored callback BLR frame mismatch':'blr_frame',
    'V437 restored callback resume frame mismatch':'resume_frame',
    'interpreter fallback':'interpreter',
    'unexpected micro interpreter fallback':'micro',
}
EXIT_ROW=re.compile(rb'V410_NAND_GUEST_RUN_EXIT calls=([0-9]{1,3}) kind=([0-9]) running=([01]) mapped=([01]) matched_stop=([01]) v390=([01])')
STOP_ANY=re.compile(rb'V404_NAND_EXTENDED_STOP calls=([0-9]{1,3}) owner=([01]) selected_return=([01]) parent_return=([01])')
def diagnosis(raw,harness):
    if len(raw)>MAX_LOG:raise ValueError('diagnostic size')
    census,label=abort_row(raw,harness,134)
    ident=int(census.split(' public_id=')[1].split()[0])
    name=label.split(' label=',1)[1]
    guard=GUARD_CLASSES.get(name,'other' if ident else 'unknown')
    lines=raw.splitlines()
    stop=[STOP_ANY.fullmatch(l) for l in lines if l.startswith(b'V404_NAND_EXTENDED_STOP ')]
    exits=[EXIT_ROW.fullmatch(l) for l in lines if l.startswith(b'V410_NAND_GUEST_RUN_EXIT ')]
    if len(stop)>1 or len(exits)>1 or any(x is None for x in stop+exits):raise ValueError('diagnostic geometry')
    s=list(map(int,stop[0].groups())) if stop else [0,0,0,0]
    e=list(map(int,exits[0].groups())) if exits else [0,0,0,0,0,0]
    if s[0]>192 or e[0]>192:raise ValueError('diagnostic bounds')
    return (f'V485_NAND_DIAG guard={guard} id={ident:04d} stop={int(bool(stop))} '
            f'stop_calls={s[0]} owner={s[1]} selected={s[2]} parent={s[3]} '
            f'exit={int(bool(exits))} exit_calls={e[0]} kind={e[1]} running={e[2]} '
            f'mapped={e[3]} matched={e[4]} post_ack={e[5]} boot_verified=0')
# Correlate the actual private exception only with literal occurrences in
# committed public source. Publish a filename/line, never the exception text.
SOURCE_NAME=re.compile(r'[A-Za-z0-9_]{1,100}\.(?:py|cpp|h)\Z')
ACK_GUARD='V389 original NAND Hollywood flag ACK did not release native IRQ'
ACK_EVENT=re.compile(rb'V389_NAND_FLAG_ACK before=([01]) wrote=([01]) cleared=([01]) down=([01]) y1=([01]) guest=([01]) registered=([01])')
ACK_TRIAL=re.compile(rb'V389_NAND_FLAG_TRIAL y1=([01]) flag=([01]) completed=([01])')
PRE_TRIAL=re.compile(rb'V388_NAND_BOUNDED_TRIAL kind=([0-9]) calls=([0-9]{1,3}) stopped=([01]) completed=([01])')
POST_EVENT=re.compile(rb'V390_NAND_POST_ACK guest=([01]) clear=([01]) registered=([01]) masked=([01]) cache=([01]) context=([01])')
def ack_history(raw,harness):
    if len(raw)>MAX_LOG:raise ValueError('ACK history size')
    # This is a diagnostic only: the original trial guard remains intact.
    guard=int(abort_row(raw,harness,134)[1].endswith('label='+ACK_GUARD))
    lines=raw.splitlines()
    def one(prefix,pat):
        matches=[(i,pat.fullmatch(l)) for i,l in enumerate(lines) if l.startswith(prefix)]
        if len(matches)>1 or any(m is None for _,m in matches):raise ValueError('ACK history geometry')
        return matches[0] if matches else (-1,None)
    ai,a=one(b'V389_NAND_FLAG_ACK ',ACK_EVENT)
    pi,p=one(b'V388_NAND_BOUNDED_TRIAL ',PRE_TRIAL)
    ti,t=one(b'V389_NAND_FLAG_TRIAL ',ACK_TRIAL)
    qi,q=one(b'V390_NAND_POST_ACK ',POST_EVENT)
    event=int(a is not None and all(v==b'1' for v in a.groups()))
    prior=int(p is not None and p[1]==b'1' and p[3]==p[4]==b'1')
    trial=int(t is not None and t[1]==t[2]==b'1' and t[3]==b'0')
    post=int(q is not None and all(v==b'1' for v in q.groups()[:4]))
    order=int(0<=ai<qi<pi<ti)
    stale=int(guard and event and prior and trial and post and order)
    return f'V506_NAND_ACK_HISTORY guard={guard} event={event} post={post} prior={prior} failed_snapshot={trial} order={order} stale_candidate={stale} boot_verified=0'
def source_matches(raw,harness,host,names):
    if len(raw)>MAX_LOG or len(harness)>24_000_000:raise ValueError('provenance size')
    strings=sorted(set(STRINGS.findall(harness)))
    if len(strings)>9999:raise ValueError('catalog')
    known=next((s for s in ERROR.findall(raw.decode('utf-8',errors='replace')) if s in strings),None)
    ident=strings.index(known)+1 if known is not None else 0
    hits=[]
    if known and len(known)<=1024 and '\n' not in known and '\r' not in known:
        token='"'+known+'"'
        for name in sorted(set(names)):
            if not SOURCE_NAME.fullmatch(name) or name.startswith('test_') or name==Path(__file__).name:continue
            path=host/name
            if path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:continue
            content=path.read_text(encoding='utf-8',errors='replace')
            for i,line in enumerate(content.splitlines(),1):
                if token in line:
                    hits.append((name,i))
    return ident,hits
def source_provenance(raw,harness,host,names):
    ident,hits=source_matches(raw,harness,host,names)
    name,line=hits[0] if len(hits)==1 else ('none',0)
    return f'V492_NAND_SOURCE id={ident:04d} matches={min(len(hits),9999)} file={name} line={line} unique={int(len(hits)==1)} boot_verified=0'
def source_candidates(raw,harness,host,names):
    ident,hits=source_matches(raw,harness,host,names)
    # All emitted paths are from the tracked public source catalog, not
    # from raw logs. Report bounded ambiguity rather than suppressing it.
    if not 1<=len(hits)<=8:return ()
    return tuple(f'V499_NAND_CANDIDATE id={ident:04d} n={i+1} total={len(hits)} file={name} line={line} boot_verified=0'
                 for i,(name,line) in enumerate(hits))
def tracked_public_source(host):
    raw=subprocess.check_output(['git','-C',str(host),'ls-files','-z','--','*.py','*.cpp','*.h'],timeout=10)
    if len(raw)>2_000_000:raise ValueError('source catalog size')
    return raw.decode('utf-8').split('\0')
def row(p):
    return f'V478_NAND_FRONTIER calls=44 original=25 resumed=1 owner={p.owned} edge={p.kind} category={p.reason} ready={int(p.ready)} boot_verified=0'
def patch(harness,p):
    if not p.ready or 'v478_continued' in harness or any(harness.count(x)!=1 for x in (OWN,STATE,RESET,STOP,GUARD)):
        raise ValueError('route')
    replacement=f'''    const bool v478_exact=v437_region_owned&&v437_frame.stage()==3u&&
         !v478_continued&&v396_calls==43u&&addr==0x{p.pc:08x}u&&ctx.lr==0x{p.lr:08x}u&&
         !v413_context.restored();
    const bool owned=v437_region_owned&&!v437_frame.active()&&!v478_exact;
    if(v478_exact){{
      v478_continued=true;
      std::cout<<"V478_NAND_EDGE continued=1 call=44"<<std::endl;
    }}'''
    pairs=((STATE,STATE+'\nstatic bool v478_continued=false;'),(RESET,RESET+'\n  nwii::runtime::v478_continued=false;'),(OWN,replacement))
    out=harness
    for a,b in pairs:out=out.replace(a,b,1)
    back=out
    for a,b in reversed(pairs):back=back.replace(b,a,1)
    if back!=harness or out.count(STOP)!=1 or out.count(GUARD)!=1:raise ValueError('guards')
    return out
def outcome(raw,rc,owner,fixture,sizes,p):
    e=trace(raw)
    # Compare call identity and resume phase, not dynamic return-value
    # classifications after the edge has been permitted.
    key=lambda x:(x[0],x[1],x[2],x[7])
    if tuple(map(key,e[:45]))!=tuple(map(key,p.prefix)) or raw.splitlines().count(MARK)!=1:raise ValueError('prefix')
    lines=raw.splitlines();at=lines.index(MARK)
    if not lines.index(RESUME)<at<next(i for i,l in enumerate(lines) if l.startswith(b'V420_CB_ENTRY call=44 ')):raise ValueError('marker order')
    return inspect(raw,rc,owner,fixture,sizes).replace('V437_FRAME_RESULT','V478_FRAME_RESULT',1)+' continued=1'
def main():
    a=argparse.ArgumentParser(description=__doc__)
    for n in ('owner','elf','fixture','cpp','harness','control','output'):a.add_argument(n,type=Path)
    a.add_argument('--run-log',type=Path);a.add_argument('--run-rc',type=int);a=a.parse_args()
    def get(p,cap,as_text=False):
        if p.stat().st_size>cap:raise ValueError('size')
        return p.read_text(encoding='utf-8') if as_text else p.read_bytes()
    try:
        owner=get(a.owner,20_000_000);elf=get(a.elf,64_000_000)
        if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
        sizes=parse_functions(elf);fixture=get(a.fixture,20_000_000)
        harness=get(a.harness,24_000_000,True)
        p=terminal(owner,fixture,sizes,get(a.cpp,MAX_CPP,True),harness,get(a.control,MAX_LOG))
        print(row(p))
        print(diagnosis(get(a.control,MAX_LOG),harness))
        host=Path(__file__).resolve().parent
        names=tracked_public_source(host)
        raw=get(a.control,MAX_LOG)
        print(source_provenance(raw,harness,host,names))
        for candidate in source_candidates(raw,harness,host,names):print(candidate)
        print(ack_history(raw,harness))
        if not p.ready:
            if a.run_log is not None:raise ValueError('no authorized edge')
            print('V478_NAND_ROUTE installed=0 eligible=0');print('V478_NAND_AUDIT inspected=1');return 0
        new=patch(harness,p)
        if a.run_log is None:
            if a.run_rc is not None or a.output.exists() or a.output.is_symlink():raise ValueError('destination')
            with a.output.open('x',encoding='utf-8') as f:f.write(new)
            print('V478_NAND_ROUTE installed=1 eligible=1 guards_preserved=1')
        else:
            if a.run_rc is None or get(a.output,24_000_000,True)!=new:raise ValueError('harness identity')
            raw=get(a.run_log,MAX_LOG);print(outcome(raw,a.run_rc,owner,fixture,sizes,p))
            print(abort_row(raw,new,a.run_rc)[0].replace('V427_ABORT_CENSUS','V478_ABORT_CENSUS',1))
        print('V478_NAND_AUDIT inspected=1');return 0
    except (OSError,ValueError,IndexError,StopIteration,struct.error,UnicodeError,subprocess.SubprocessError):
        print('V478_NAND_AUDIT inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
