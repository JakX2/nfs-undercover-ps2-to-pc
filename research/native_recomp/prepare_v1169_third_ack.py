#!/usr/bin/env python3
"""Authenticate existing second-ACK labels for a bounded third completion ACK."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import HANDLER,exact
from prepare_owner_second_ack_v955 import plan
from prepare_owner_second_dispatch_v946 import reachable
from prepare_v958_second_ack import render as render_base
from prepare_v1161_held_dispatch import render as render_dispatch
from prepare_v1141_postalarm_handler import block_at
from prepare_v1097_after_alarm import SI,ACTIVE,inherited_hooks,fmt
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count

def verify_label(body,pc,w):
    block=block_at(body,pc,w)
    tick='    ++ctx.inst_count;\n';arg=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    if block.count(tick)!=1 or block.count(SI)!=1 or block.index(tick)>block.index(SI):
        raise ValueError('third ACK tick')
    plain=f'    undercover::wii::v958::before({arg},false);\n'
    guard=f'    undercover::wii::v958::before({arg},true);\n'
    allowed={plain,guard,f'    if({ACTIVE}) '+plain.lstrip()}
    allowed|={s for s in inherited_hooks(pc,w).values() if ACTIVE in s}
    observed=''.join(re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block))
    if observed not in allowed or block.count(observed)!=1 or block.index(observed)<block.index(SI):
        raise ValueError('third ACK hook')

def metadata(dol,elf):
    roots,_,indirect,_,_,_,guard,extra=plan(dol,elf)
    if len(extra)!=3:raise ValueError('third ACK geometry')
    ordered=(HANDLER,extra[0][1],extra[1][1])
    if len(set(ordered))!=3:raise ValueError('third ACK geometry')
    rows=[]
    for a in ordered:
        raw=exact(dol,elf,a,len(roots[a]))
        for pc in sorted(reachable(a,roots[a],guard,indirect)):
            w=raw[(pc-a)//4]
            # The actual bounded completion proof enters only save and
            # completion. A nested helper call is deliberately a refusal.
            refused=pc in guard or pc==extra[2][0]
            rows.append((pc,w,a,refused))
    if len({pc for pc,_,_,_ in rows})!=len(rows):raise ValueError('third ACK geometry')
    spans=[(a,a+4*len(roots[a]),int(i==1)) for i,a in enumerate(ordered)]
    edges=[(site,dst) for site,dst,_,_,_ in extra[:2]]
    if any(not any(p==site and a==HANDLER and not g for p,_,a,g in rows) for site,_ in edges):
        raise ValueError('third ACK geometry')
    return spans,edges,rows,render_base(roots,extra)

def render(spans,edges,rows):
    return ('#pragma once\n#include "wii_held_pending_epilogue_v1149.h"\nnamespace undercover::wii::v1167 {\n'
        +f'inline constexpr std::array<AckCallSpan,{len(spans)}> spans{{{{'+','.join('{'+fmt((a,e))+f',{s}u'+'}' for a,e,s in spans)+'}};\n'
        +f'inline constexpr std::array<AckCallEdge,{len(edges)}> edges{{{{'+','.join('{'+fmt(row)+'}' for row in edges)+'}};\n'
        +'inline constexpr std::array<AckMsrSite,0> msr{};\n'
        +f'inline constexpr std::array<ThirdAckNativeLabel,{len(rows)}> labels{{{{'+','.join('{'+fmt((pc,w,a))+','+str(g).lower()+'}' for pc,w,a,g in rows)+'}};\n}\n')

def verify_bus(s):
    read='if(v958::next_device.stage()!=3u||!v958::held_epilogue.ack_read(active_->controller_,off,value))v958::reject_held_epilogue();'
    write='if(v958::next_device.stage()!=3u||!v958::held_epilogue.ack_write(active_->controller_,*off,value))v958::reject_held_epilogue();'
    old_read='!v958::next_device.read(active_->controller_,off,value)'
    old_write='!v958::next_device.write(active_->controller_,*off,value)'
    if any(s.count(x)!=1 for x in (read,write,old_read,old_write)) or not s.index(read)<s.index(old_read)<s.index(write)<s.index(old_write):
        raise ValueError('third ACK bus')
    if s.count('#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK\n')!=3 or s.count('if(v958::third_ack_active())')!=3:
        raise ValueError('third ACK bus')

def install(dol,elf,root,host):
    spans,edges,rows,base=metadata(dol,elf)
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    result=dest/'v1167_private_third_ack.h';bus=dest/'wii_si_binding_v512.h'
    expected={'v1158_private_held_dispatch.h':render_dispatch()}
    for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
              'wii_second_completion_ack_v950.h','wii_bounded_ack_call_route_v956.h'):
        expected[n]=(host/n).read_text()
    if dest.is_symlink() or result.exists() or result.is_symlink() or any(x.is_symlink() or not x.is_file() for x in
        (private,bus,*[dest/n for n in expected])):
        raise ValueError('third ACK destination')
    if any((dest/n).read_text()!=value for n,value in expected.items()):raise ValueError('third ACK identity')
    verify_bus(bus.read_text())
    old=private.read_text();macro='#define UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1167_PRIVATE_THIRD_ACK' in old:raise ValueError('third ACK mode')
    # The base V958 header is extended by later installers. Authenticate
    # all original base metadata rows independently, not just the macro.
    for line in base.splitlines():
        if 'inline constexpr ' in line and old.count(line+'\n')!=1:raise ValueError('third ACK metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('third ACK tree')
    src={x:x.read_text() for x in paths};outer=main.read_text()
    for index,(a,_,_) in enumerate(spans):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('third ACK owner')
        body=exact_function(src[hits[0]],a)
        expected_rows={pc:(a,w) for pc,w,owner,_ in rows if owner==a}
        if audit_native([body],outer,expected_rows)!=len(expected_rows):raise ValueError('third ACK coverage')
        if index==0:
            for pc,target in edges:verify_direct(body,pc,target)
        for pc,(_,w) in expected_rows.items():
            try:verify_label(body,pc,w)
            except ValueError:
                print(f'V1169_ACK_HOOK_REFUSAL root={index} index={(pc-a)//4}')
                raise
    # No generated instruction is changed; the existing hook already
    # calls the same runtime route. Only install private validated data.
    result.write_text(render(spans,edges,rows))
    private.write_text(old.replace(macro,macro+'#define UNDERCOVER_V1167_PRIVATE_THIRD_ACK 1\n',1))
    print(f'V1169_THIRD_ACK_ROUTE installed=1 native_labels={len(rows)} guard_labels={sum(g for _,_,_,g in rows)} direct_edges=2 bus_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'third ACK '+s for s in ('tick','hook','geometry','bus','destination','identity','mode','metadata','tree','owner','coverage')}
        safe|={'held handler label','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
        print('V1169_THIRD_ACK_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
