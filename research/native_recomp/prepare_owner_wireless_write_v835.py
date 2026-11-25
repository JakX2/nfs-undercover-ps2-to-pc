#!/usr/bin/env python3
"""Join original wireless SRAM update to original immediate writes and deselect."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
from prepare_owner_wireless_select_v825 import plan as select_plan,header as select_header
from prepare_owner_exi_write_v828 import plan as transfer_plan
from prepare_owner_wireless_v816 import header as root_header,H,J
from prepare_owner_pair_v753 import alias,pair_shape
from audit_callback_frontiers_v799 import call_sites
from make_start_to_exi_transaction_v56 import IMM,SYNC,SELECT,DESELECT,PROBE,HWREV,UNMASK
from make_start_to_eximask_v53 import MASK
from prepare_owner_scheduler_v722 import reachable,ROOT,READ,rewrite
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
BLR=0x4e800020

def validate_overlaps(roots,aliases):
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    shared=0
    for i,(a,end) in enumerate(spans):
        for b,stop in spans[i+1:]:
            if b>=end:break
            if a not in aliases or b not in aliases or end!=stop or list(roots[a][(b-a)//4:])!=list(roots[b]):
                raise ValueError('shared suffix identity')
            shared+=1
    return shared

def plan(dol,elf):
    q,ss,sf,sn,sb,sd=select_plan(dol,elf)
    base,ls,lf,ln,lb,ld=q
    roots,A,B,U,L,guards=base
    t,ts,tf,tn,tb,td,console,revision=transfer_plan(dol,elf)
    sizes=parse_functions(elf);sites=call_sites(U,roots[U])
    immex=sites[5][2];unlock=sites[2][2]
    if sizes.get(immex)!=164 or sites[6][2]!=DESELECT or sites[7][2]!=unlock or sizes.get(DESELECT)!=256:
        raise ValueError('write geometry')
    if not {IMM,SYNC,immex,DESELECT,unlock,PROBE}.issubset(guards):raise ValueError('write guards')
    for a,ws in t.items():
        if a==H:continue
        if a in (IMM,SYNC):
            if roots.get(a)!=[BLR]:raise ValueError('transfer guard')
            roots[a]=ws
        elif a in roots:
            if list(roots[a])!=list(ws):raise ValueError('shared root')
        else:roots[a]=ws
    ex=exact(dol,elf,immex,41);es=call_sites(immex,ex)
    if len(es)!=4 or any(k!=1 for _,k,_ in es) or [a for _,_,a in es[1:3]]!=[IMM,SYNC]:
        raise ValueError('extended transfer edges')
    xs,xf=es[0][2],es[-1][2]
    xn=32-((exact(dol,elf,xs,1)[0]>>21)&31)
    if not 1<=xn<=18:raise ValueError('extended alias')
    xsave,xrestore=alias(dol,elf,xs,sizes,xn),alias(dol,elf,xf,sizes,xn)
    _,xb,xd=pair_shape(xsave,xrestore,xn)
    for a,ws in ((xs,xsave),(xf,xrestore)):
        if a in roots and list(roots[a])!=list(ws):raise ValueError('shared alias')
        roots[a]=ws
    dw=exact(dol,elf,DESELECT,64);ds=call_sites(DESELECT,dw)
    if len(ds)!=6 or any(k!=1 for _,k,_ in ds):
        raise ValueError('deselect edges')
    targets=[a for _,_,a in ds]
    if targets[:2]!=[DISABLE,RESTORE] or targets[2]!=targets[3] or targets[2] not in (MASK,UNMASK) or targets[4:]!=[RESTORE,PROBE]:
        raise ValueError('deselect dependencies')
    roots[immex]=ex;roots[DESELECT]=dw
    guards=tuple(a for a in guards if a not in (IMM,SYNC,immex,DESELECT))+(console,)
    if set(guards)!={unlock,PROBE,console}:raise ValueError('write guards')
    aliases={ls,lf,ss,sf,ts,tf,xs,xf}
    shared=validate_overlaps(roots,aliases)
    # A real SDK save/restore suffix is permitted to overlap only another
    # independently authenticated identical suffix, never general code.
    return (roots,A,B,U,L,guards),[(lf,ln,lb,ld),(sf,sn,sb,sd),(tf,tn,tb,td),(xf,xn,xb,xd)],aliases,revision,immex,unlock,shared

def header(p,out):
    base,restore,aliases,revision,immex,unlock,shared=p
    root_header(base,out)
    vals={'Imm':IMM,'Sync':SYNC,'ImmEx':immex,'Select':SELECT,'Deselect':DESELECT,'UnlockGuard':unlock,'Revision':HWREV,'RevisionRead':revision}
    from make_start_to_exi_transaction_v56 import IRQMASK
    vals['MaskHelper']=IRQMASK
    with out.open('a') as f:
        f.write('inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in vals.items())+';\n')
        f.write('struct RestoreRule{uint32_t root;unsigned count,base;int32_t disp;};\n')
        unique={row[0]:row for row in restore}
        f.write(f'inline constexpr std::array<RestoreRule,{len(unique)}> restore_rules{{{{'+','.join(
            f'RestoreRule{{0x{a:08x}u,{n}u,{b}u,{disp}}}' for a,n,b,disp in unique.values())+'}};\n')

def patch_analyzer(p,root):
    roots=p[0][0]
    # Ownership is relative to the actual root, not the lowest overlapping
    # instruction address. Analyzer block visitation is per function.
    root_patch=ROOT+'\n    const auto fixture_end=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a==0x{a:08x}u)return 0x{a+4*len(ws):08x}u;\n' for a,ws in sorted(roots.items())
    )+'      return 0;\n    };\n    const uint32_t fixture_limit=fixture_end(func_start);\n    if(!fixture_limit)continue;'
    read_patch='        if(current_pc<func_start||current_pc>=fixture_limit)break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('fixture ownership')
    old=f.read_text();new=rewrite(old,((ROOT,root_patch),(READ,read_patch)))
    if old!=new:f.write_text(new)

def install(p,root):
    roots,A,B,U,L,guards=p[0]
    paths=sorted(root.glob('*.cpp'))
    if not paths or any(f.is_symlink() or f.stat().st_size>4*1024*1024 for f in paths):raise ValueError('private output')
    src={f:f.read_text() for f in paths};main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    edits={};labels=0;edges=0
    for a,ws in roots.items():
        owners=[f for f,s in src.items() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('native owner')
        f=owners[0];original=exact_function(src[f],a)
        expected={pc:(a,ws[(pc-a)//4]) for pc in reachable(a,ws)}
        if audit_native([original],outer,expected)!=len(expected):raise ValueError('native coverage')
        for pc,k,dst in call_sites(a,ws):
            if k!=1 or dst not in roots:raise ValueError('native edge')
            verify_direct(original,pc,dst);edges+=1
        if a in guards:continue
        out=original
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            if len(list(pat.finditer(out)))!=1:raise ValueError('hook identity')
            out=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
            labels+=1
        edits[f]=replace_exact(edits.get(f,src[f]),original,out)
    for f,s in edits.items():
        s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n#include "rfi_test_v708.h"')
        f.write_text(s)
    print(f'V835_WRITE_NATIVE_ROUTE verified=1 labels={labels} edges={edges} shared_suffixes={p[-1]} execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:
            header(q,a.output);print(f'V835_WRITE_GEOMETRY verified=1 shared_suffixes={q[-1]} original_immex=1 original_deselect=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('shared suffix identity','write geometry','write guards','transfer guard','shared root','extended transfer edges','extended alias','shared alias','deselect edges','deselect dependencies','fixture ownership','private output','native owner','native coverage','native edge','hook identity','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V835_WRITE_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
