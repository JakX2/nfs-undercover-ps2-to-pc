#!/usr/bin/env python3
"""Authenticate the existing shared completion helper for the third ACK continuation."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import HANDLER,DISABLE,TIME,RESTORE,exact
from prepare_owner_second_time_v966 import plan as time_plan
from prepare_owner_second_shared_v988 import admit_shared_time
from prepare_owner_second_dispatch_v946 import reachable
from prepare_v975_second_time import render_time,render_shared
from prepare_v1169_third_ack import metadata as ack_metadata,render as render_ack,verify_label,verify_bus
from prepare_v1097_after_alarm import fmt
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count

def compatible(old_spans,old_edges,old_rows,spans,edges,rows,msr,expected):
    if len(spans)!=7 or len(edges)!=8 or len(msr)!=2 or spans[:3]!=old_spans or edges[:2]!=old_edges:
        raise ValueError('ACK helper geometry')
    table={pc:(w,a,g) for pc,w,a,g in rows}
    if len(table)!=len(rows):raise ValueError('ACK helper geometry')
    for pc,w,a,g in old_rows:
        v=table.get(pc)
        if v is None or v[:2]!=(w,a) or (not g and v[2]):raise ValueError('ACK helper predecessor')
    for pc,w in msr:
        if pc not in table or table[pc][0]!=w or table[pc][2]:raise ValueError('ACK helper MSR')
    pc,w=expected
    if table.get(pc)!=(w,spans[0][0],False) or pc!=edges[1][0]+4:
        raise ValueError('ACK helper return')
    for pc,a in edges:
        if pc not in table or table[pc][2] or a not in {s[0] for s in spans}:raise ValueError('ACK helper edge')

def metadata(dol,elf):
    old_spans,old_edges,old_rows,base=ack_metadata(dol,elf)
    q,site,msr,_=time_plan(dol,elf)
    roots,_,indirect,_,_,_,guard,extra=q
    if len(extra)!=7:raise ValueError('ACK helper geometry')
    prior=render_time(base,roots,extra,site,msr)
    shared=admit_shared_time(dol,elf,roots,guard,extra)
    extra=(*extra,shared)
    prior=render_shared(prior,extra,shared[0])
    ordered=(HANDLER,*(d for _,d,_,_,_ in extra[:3]),DISABLE,TIME,RESTORE)
    if len(set(ordered))!=7:raise ValueError('ACK helper geometry')
    rows=[]
    for a in ordered:
        raw=exact(dol,elf,a,len(roots[a]))
        rows.extend((pc,raw[(pc-a)//4],a,pc in guard) for pc in sorted(reachable(a,roots[a],guard,indirect)))
    spans=[(a,a+4*len(roots[a]),int(i==1)) for i,a in enumerate(ordered)]
    edges=[(s,d) for s,d,_,_,_ in extra]
    pc=edges[1][0]+4
    expected=(pc,exact(dol,elf,pc,1)[0])
    compatible(old_spans,old_edges,old_rows,spans,edges,rows,msr,expected)
    return spans,edges,rows,msr,expected,render_ack(old_spans,old_edges,old_rows),prior

def render(spans,edges,rows,msr,expected):
    s=render_ack(spans,edges,rows).replace('namespace undercover::wii::v1167 {','namespace undercover::wii::v1175 {',1)
    old='inline constexpr std::array<AckMsrSite,0> msr{};\n'
    if s.count(old)!=1 or not s.endswith('}\n'):raise ValueError('ACK helper render')
    s=s.replace(old,f'inline constexpr std::array<AckMsrSite,{len(msr)}> msr{{{{'+','.join('{'+fmt(m)+'}' for m in msr)+'}};\n',1)
    return s[:-2]+'inline constexpr HeldAckHelperExpectation expected{'+fmt(expected)+',130u,6u,6u,2u};\n}\n'

def install(dol,elf,root,host):
    spans,edges,rows,msr,expected,ack,prior=metadata(dol,elf)
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    result=dest/'v1175_private_ack_helper.h';bus=dest/'wii_si_binding_v512.h'
    sources={'v1167_private_third_ack.h':ack}
    for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
              'wii_second_completion_ack_v950.h','wii_bounded_ack_call_route_v956.h'):
        sources[n]=(host/n).read_text()
    if dest.is_symlink() or result.exists() or result.is_symlink() or any(x.is_symlink() or not x.is_file() for x in
        (private,bus,*[dest/n for n in sources])):
        raise ValueError('ACK helper destination')
    if any((dest/n).read_text()!=s for n,s in sources.items()):raise ValueError('ACK helper identity')
    verify_bus(bus.read_text())
    old=private.read_text();macro='#define UNDERCOVER_V1167_PRIVATE_THIRD_ACK 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1175_PRIVATE_ACK_HELPER' in old:raise ValueError('ACK helper mode')
    for line in prior.splitlines():
        if 'inline constexpr ' in line and old.count(line+'\n')!=1:raise ValueError('ACK helper metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('ACK helper tree')
    src={x:x.read_text() for x in paths};outer=main.read_text()
    for index,(a,end,_) in enumerate(spans):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('ACK helper owner')
        body=exact_function(src[hits[0]],a)
        expected_rows={pc:(a,w) for pc,w,owner,_ in rows if owner==a}
        if audit_native([body],outer,expected_rows)!=len(expected_rows):raise ValueError('ACK helper coverage')
        for pc,dst in edges:
            if a<=pc<end:verify_direct(body,pc,dst)
        for pc,w,owner,refused in rows:
            if owner!=a:continue
            try:verify_label(body,pc,w,refused)
            except ValueError:
                print(f'V1176_ACK_HELPER_HOOK_REFUSAL root={index} index={(pc-a)//4}')
                raise
    # No new emitted hook or instruction. The existing generated V958
    # observer owns all authenticated roots at the original scheduler tick.
    result.write_text(render(spans,edges,rows,msr,expected))
    private.write_text(old.replace(macro,macro+'#define UNDERCOVER_V1175_PRIVATE_ACK_HELPER 1\n',1))
    print(f'V1176_ACK_HELPER_ROUTE installed=1 native_labels={len(rows)} roots=7 direct_edges=8 msr_sites=2 bus_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'ACK helper '+s for s in ('geometry','predecessor','MSR','return','edge','render','destination','identity','mode','metadata','tree','owner','coverage')}
        safe|={'third ACK bus','third ACK hook','third ACK tick','held handler label','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
        print('V1176_ACK_HELPER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
