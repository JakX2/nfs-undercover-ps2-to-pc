#!/usr/bin/env python3
"""Authenticate the existing shared completion helper for the third ACK continuation."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from derive_ack_callback_paths_v1283 import path_lengths
from prepare_v667_si_dispatch import HANDLER,DISABLE,TIME,RESTORE,exact
from prepare_owner_second_time_v966 import plan as time_plan
from prepare_owner_second_shared_v988 import admit_shared_time
from prepare_owner_second_dispatch_v946 import reachable
from prepare_v975_second_time import render_time,render_shared
from prepare_v1169_third_ack import metadata as ack_metadata,render as render_ack,verify_label,verify_bus
from prepare_v1097_after_alarm import fmt,ACTIVE,inherited_hooks
from prepare_owner_callback_prefix_v797 import plan as prefix_plan
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_owner_callback_time_v802 import plan as callback_time_plan
from prepare_v813_callback_time import render as time_render
from prepare_owner_callback_frontier_v820 import plan as callback_frontier_plan
from prepare_v831_callback_frontier import render as frontier_render
from prepare_owner_wireless_v816 import plan as wireless_plan
from prepare_v847_wireless_wrapper import render as wireless_render
from audit_callback_frontiers_v799 import call_sites as wireless_calls
from prepare_owner_callback_after_setter_v842 import plan as suffix_plan
from prepare_v1124_postalarm_suffix import render as suffix_render
from prepare_v1134_postalarm_return import derive as return_derive,render as return_render
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_owner_scheduler_v722 import reachable as callback_reachable
from prepare_v625_ipc_client import audit_native,patch_return as patch_ipc_return
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v789_alarm_suffix import expectations as callback_expectations
from prepare_v1141_postalarm_handler import block_at,render as handler_render,patch_handler
from prepare_v868_handler_suffix import derive as handler_derive
from prepare_v672_si_ack_route import call_census
from prepare_v1146_postalarm_handler_return import geometry_return as handler_return_geometry,render as handler_return_render
from prepare_v738_handler_restore import audit_shared_alias
from prepare_v667_si_dispatch import DISPATCH
from prepare_v1152_held_epilogue import metadata as final_metadata,render as final_render,NEW as FINAL_ACTIVE
from prepare_v1097_after_alarm import SI
from prepare_v767_live_epilogue import geometry as final_geometry,ENTRY
from prepare_v1029_third_transfer import replace_body,include_once
from prepare_v928_leaf_finish import plan as leaf_plan,RETURN
from prepare_v922_irq_return import patch_label as legacy_leaf_patch
from make_v624_ipc_geometry import geometry as ipc_geometry,render as ipc_render,CALL as IPC_CALL,ROOT as IPC_ROOT,SPANS as IPC_SPANS,RETURN as IPC_RETURN
from audit_handler_third_v740 import edge as handler_edge
from prepare_v1246_ack_open import prepare as prepare_open_native
from prepare_v629_stm_open import geometry as stm_geometry,render as stm_render,expected_scopes as stm_scopes,BEGIN as STM_BEGIN,OSINIT as STM_OSINIT

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

def render(spans,edges,rows,msr,expected,callback_guard=True,paths=()):
    s=render_ack(spans,edges,rows).replace('namespace undercover::wii::v1167 {','namespace undercover::wii::v1175 {',1)
    old='inline constexpr std::array<AckMsrSite,0> msr{};\n'
    if s.count(old)!=1 or not s.endswith('}\n'):raise ValueError('ACK helper render')
    s=s.replace(old,f'inline constexpr std::array<AckMsrSite,{len(msr)}> msr{{{{'+','.join('{'+fmt(m)+'}' for m in msr)+'}};\n',1)
    path_array=('inline constexpr std::array<unsigned,'+str(len(paths))+'> callback_paths{'+
                ','.join(str(n)+'u' for n in paths)+'};\n') if paths else ''
    path_arg=',callback_paths' if paths else ''
    return (s[:-2]+'inline constexpr HeldAckHelperExpectation expected{'+fmt(expected)+',130u,6u,6u,2u};\n'
        +'inline constexpr bool callback_guard='+str(callback_guard).lower()+';\n'
        +'inline constexpr auto callback_words=v958::success_callback_words;\n'
        +'inline constexpr auto callback_sites=v958::success_callback_sites;\n'
        +path_array+'inline constexpr HeldAckCallbackExpectation callback_expected{callback_sites[0],0x4e800421u,71u,6u'+path_arg+'};\n'
        +'#ifdef UNDERCOVER_V1205_PRIVATE_ACK_RETURN\ninline constexpr unsigned return_loads=6;\ninline constexpr auto return_expected=v1132::expected;\n#endif\n'
        +'#ifdef UNDERCOVER_V1210_PRIVATE_ACK_HANDLER\ninline constexpr auto handler_rows=v1139::rows;\ninline constexpr auto handler_index=v1139::index;\ninline constexpr uint32_t handler_rd=v1139::rd,handler_wr=v1139::wr;\n#endif\n'
        +'#ifdef UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN\ninline constexpr auto handler_return_expected=v1145::expected;\n#endif\n}\n')

def verify_callback_metadata(dol,elf,spans,rows,old):
    candidate,words,sites=callback_expectations(dol,elf)
    if len(words)!=172 or len(sites)!=2 or sites[0]==sites[1]:
        raise ValueError('ACK callback geometry')
    call,_,w=handler_edge(HANDLER,exact(dol,elf,HANDLER,(spans[0][1]-HANDLER)//4),4)
    if [x for x in rows if x[0]==sites[0]]!=[(sites[0],0x4e800421,HANDLER,True)]:
        raise ValueError('ACK callback geometry')
    expected=(
        '#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1',
        f'inline constexpr uint32_t transfer_call=0x{call:08x}u,transfer_branch=0x{w:08x}u,transfer_callback=0x{candidate:08x}u;',
        'inline constexpr std::array<uint32_t,172> success_callback_words{'+fmt(words)+'};',
        'inline constexpr std::array<uint32_t,2> success_callback_sites{'+fmt(sites)+'};')
    if any(old.splitlines().count(line)!=1 for line in expected):
        raise ValueError('ACK callback metadata')
    return sites[0]

def verify_callback_guard(body,pc):
    block=block_at(body,pc,0x4e800421)
    guard=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x4e800421u,true);\n'
    observed=''.join(re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block))
    if observed==guard and block.count(guard)==1:return True
    # Existing post-alarm installers may already own this exact label.
    # Authenticate their conditional observer, not an arbitrary false hook.
    inherited={v for v in inherited_hooks(pc,0x4e800421).values()
               if ACTIVE in v and v.endswith('    else '+guard.lstrip())}
    if observed in inherited and block.count(observed)==1:return False
    raise ValueError('ACK callback guard')

def verify_prefix_metadata(dol,elf,old):
    roots,C,S,site,_,_=prefix_plan(dol,elf)
    candidate,words,sites=callback_expectations(dol,elf)
    prefix=roots[C][:-1];save=roots[S]
    if C!=candidate or len(prefix)!=6 or len(save)!=7 or tuple(prefix)!=tuple(words[:6]) or site!=C+16:
        raise ValueError('ACK prefix geometry')
    expected=['#define UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1',
              f'inline constexpr uint32_t third_postalarm_save_root=0x{S:08x}u;']
    for name,ws in (('third_postalarm_prefix',prefix),('third_postalarm_save',save),
                    ('third_postalarm_words',words),('third_postalarm_sites',sites)):
        expected.append(f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};')
    if any(old.splitlines().count(line)!=1 for line in expected):
        raise ValueError('ACK prefix metadata')
    return C,S,site,prefix,save

def verify_prefix_native(src,outer,meta):
    C,S,site,prefix,save=meta
    for addr,words in ((C,prefix),(S,save)):
        hits=[s for s in src.values() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:
            raise ValueError('ACK prefix owner')
        body=exact_function(hits[0],addr)
        rows={addr+4*i:(addr,w) for i,w in enumerate(words)}
        if audit_native([body],outer,rows)!=len(rows):raise ValueError('ACK prefix coverage')
        if addr==C:verify_direct(body,site,S)
        for pc,(_,w) in rows.items():verify_label(body,pc,w,False)

def verify_time_metadata(dol,elf,old,dest,host,prefix_meta):
    q,T,D,U,R,ts,leaves=callback_time_plan(dol,elf)
    roots,C,S,site,_,_=q
    resume=site+4;continuation=roots[C][(resume-C)//4:-1]
    prior_C,prior_S,prior_site,prior_prefix,prior_save=prefix_meta
    if (C,S,site)!=(prior_C,prior_S,prior_site) or tuple(roots[C][:(resume-C)//4+1])!=tuple(prior_prefix) or tuple(roots[S])!=tuple(prior_save):
        raise ValueError('ACK time predecessor')
    if len(roots[T])!=25 or len(leaves)!=3 or [x[1] for x in leaves]!=[D,U,R] or [x[4] for x in leaves]!=[1,2,3]:
        raise ValueError('ACK time geometry')
    if tuple(continuation)!=tuple(exact(dol,elf,C,172)[(resume-C)//4:(ts-C)//4+2]):
        raise ValueError('ACK time geometry')
    if old.splitlines().count('#define UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1')!=1 or 'UNDERCOVER_V1189_PRIVATE_ACK_TIME' in old:
        raise ValueError('ACK time mode')
    expected={'v813_private_callback_time.h':time_render(C,ts,continuation,T,roots[T],leaves),
              'wii_callback_time_v810.h':(host/'wii_callback_time_v810.h').read_text(),
              'wii_postack_os_leaf_v703.h':(host/'wii_postack_os_leaf_v703.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK time metadata')
    return roots,C,T,D,U,R,resume,ts,leaves

def verify_time_native(src,outer,meta):
    roots,C,T,D,U,R,resume,ts,leaves=meta
    callback_pcs={pc for pc in callback_reachable(C,roots[C]) if resume<=pc<=ts+4}
    if len(callback_pcs)!=13 or resume not in callback_pcs or ts+4 not in callback_pcs:
        raise ValueError('ACK time geometry')
    total=0
    for addr in (C,T,D,U,R):
        hits=[s for s in src.values() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:
            raise ValueError('ACK time owner')
        body=exact_function(hits[0],addr)
        labels=callback_pcs if addr==C else callback_reachable(addr,roots[addr])
        rows={pc:(addr,roots[addr][(pc-addr)//4]) for pc in labels}
        if audit_native([body],outer,rows)!=len(rows):raise ValueError('ACK time coverage')
        for a,t in ([(ts,T)] if addr==C else [(x[0],x[1]) for x in leaves] if addr==T else []):
            verify_direct(body,a,t)
        for pc,(_,w) in rows.items():verify_label(body,pc,w,False)
        total+=len(rows)
    if total-len(callback_pcs)!=45:raise ValueError('ACK time geometry')

def verify_frontier_metadata(dol,elf,old,dest,host,time_meta):
    q,seen,stops,A,B=callback_frontier_plan(dol,elf)
    base,T,D,U,R,ts,leaves=q;roots,C,S,site,_,_=base
    old_roots,old_C,old_T,old_D,old_U,old_R,old_resume,old_ts,old_leaves=time_meta
    if (C,T,D,U,R,site+4,ts,leaves)!=(old_C,old_T,old_D,old_U,old_R,old_resume,old_ts,old_leaves) or any(roots[x]!=old_roots[x] for x in (T,D,U,R)):
        raise ValueError('ACK frontier predecessor')
    original=exact(dol,elf,C,172);candidate,words,_=callback_expectations(dol,elf);resume=ts+4
    if candidate!=C or tuple(original)!=tuple(words) or len(original)!=172 or len(seen)!=27 or len(set(seen))!=27 or min(seen)!=resume or \
       sorted(o for o,_ in stops.values())!=[3,5] or {dst for _,dst in stops.values()}!={A,B} or A==B or \
       not set(stops).issubset(seen) or any(pc&3 or not resume<=pc<C+688 for pc in seen):
        raise ValueError('ACK frontier geometry')
    if old.splitlines().count('#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1')!=1 or 'UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER' in old:
        raise ValueError('ACK frontier mode')
    rows={pc:(C,original[(pc-C)//4]) for pc in seen}
    expected={'v831_private_callback_frontier.h':frontier_render(C,resume,rows,stops),
              'wii_callback_frontier_v829.h':(host/'wii_callback_frontier_v829.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK frontier metadata')
    return C,rows,stops

def verify_frontier_native(src,outer,meta):
    C,rows,stops=meta
    hits=[s for s in src.values() if owns_root(s,C)]
    if len(hits)!=1 or sum(entry_count(s,C) for s in src.values())!=1:raise ValueError('ACK frontier owner')
    body=exact_function(hits[0],C)
    if audit_native([body],outer,rows)!=len(rows):raise ValueError('ACK frontier coverage')
    for pc,(_,dst) in stops.items():verify_direct(body,pc,dst)
    for pc,(_,w) in rows.items():verify_label(body,pc,w,False)

def verify_wireless_metadata(dol,elf,old,dest,host,time_meta,frontier_meta):
    C,rows,stops=frontier_meta
    time_roots,old_C,T,D,TB,R,resume,ts,leaves=time_meta
    roots,A,B,U,L,guards=wireless_plan(dol,elf)
    if C!=old_C or (D,R)!=(DISABLE,RESTORE) or {o:dst for o,dst in stops.values()}!={3:A,5:B}:
        raise ValueError('ACK wireless predecessor')
    order=(A,B,U,D,R)
    if len(set(order))!=5 or L in order or [len(roots[x]) for x in order]!=[39,30,184,5,9] or any(tuple(roots[x])!=tuple(time_roots[x]) for x in (D,R)):
        raise ValueError('ACK wireless geometry')
    original=exact(dol,elf,C,172);lw=exact(dol,elf,L,1)[0]
    if len(original)!=172 or any(rows[pc]!=(C,original[(pc-C)//4]) for pc in stops):
        raise ValueError('ACK wireless geometry')
    edges=[(pc,original[(pc-C)//4],original[(pc+4-C)//4],o) for pc,(o,_) in sorted(stops.items())]
    if old.splitlines().count('#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1')!=1 or 'UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS' in old:
        raise ValueError('ACK wireless mode')
    expected={'v847_private_wireless_wrapper.h':wireless_render(roots,order,edges,L,lw),
              'wii_wireless_wrapper_v844.h':(host/'wii_wireless_wrapper_v844.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK wireless metadata')
    return roots,order,L,lw,C,original,stops

def verify_wireless_native(src,outer,meta):
    roots,order,L,lw,C,original,stops=meta
    def owner(addr):
        hits=[s for s in src.values() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('ACK wireless owner')
        return exact_function(hits[0],addr)
    def verify(addr,rows,edges):
        body=owner(addr)
        if audit_native([body],outer,rows)!=len(rows):raise ValueError('ACK wireless coverage')
        for pc,dst in edges:verify_direct(body,pc,dst)
        for pc,(_,w) in rows.items():verify_label(body,pc,w,False)
    labels=shared=direct=0
    for addr in order:
        rows={pc:(addr,roots[addr][(pc-addr)//4]) for pc in callback_reachable(addr,roots[addr])}
        calls=wireless_calls(addr,roots[addr])
        if any(k!=1 or dst not in roots for _,k,dst in calls):raise ValueError('ACK wireless edge')
        verify(addr,rows,[(pc,dst) for pc,_,dst in calls])
        labels+=len(rows);shared+=len(rows) if addr in order[-2:] else 0;direct+=len(calls)
    if audit_native([owner(L)],outer,{L:(L,lw)})!=1:raise ValueError('ACK wireless coverage')
    verify(C,{pc:(C,original[(pc-C)//4]) for pc in set(stops)|{pc+4 for pc in stops}},[(pc,dst) for pc,(_,dst) in stops.items()])
    if (labels,shared,direct+2)!=(267,14,18):raise ValueError('ACK wireless geometry')

def verify_suffix_metadata(dol,elf,old,dest,host,wireless_meta):
    roots,order,L,lw,prior_C,original,frontier=wireless_meta
    _,C,resume,seen,stops=suffix_plan(dol,elf,True)
    if C!=prior_C or {pc+4 for pc,(i,_) in frontier.items() if i==3}!={resume}:
        raise ValueError('ACK suffix predecessor')
    if len(seen)!=21 or len(set(seen))!=21 or resume not in seen or not set(stops).issubset(seen) or \
       sorted((i,k) for i,k,_ in stops.values())!=[(4,2),(13,1)] or any(pc&3 or not C<=pc<C+688 for pc in seen):
        raise ValueError('ACK suffix geometry')
    rows={pc:original[(pc-C)//4] for pc in seen}
    if old.splitlines().count('#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1')!=1 or 'UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX' in old:
        raise ValueError('ACK suffix mode')
    expected={'v1123_private_postalarm_suffix.h':suffix_render(C,resume,rows,stops),
              'wii_callback_suffix_v841.h':(host/'wii_callback_suffix_v841.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK suffix metadata')
    return C,rows,stops

def verify_suffix_native(src,outer,meta):
    C,rows,stops=meta
    hits=[s for s in src.values() if owns_root(s,C)]
    if len(hits)!=1 or sum(entry_count(s,C) for s in src.values())!=1:raise ValueError('ACK suffix owner')
    body=exact_function(hits[0],C)
    if audit_native([body],outer,{pc:(C,w) for pc,w in rows.items()})!=len(rows):raise ValueError('ACK suffix coverage')
    for pc,(i,k,dst) in stops.items():
        if k==1:verify_direct(body,pc,dst)
        else:verify_indirect(body,pc)
    for pc,w in rows.items():verify_label(body,pc,w,False)

def verify_return_metadata(dol,elf,old,dest,host,suffix_meta,callback_site):
    C,resume,rows,stops,words,call,R,caller,restore,tail,caller_word,callers=return_derive(dol,elf)
    if (C,rows,stops)!=suffix_meta or caller!=callback_site+4 or callers[0][:3]!=(callback_site,0x4e800421,6):
        raise ValueError('ACK return predecessor')
    if len(restore)!=7 or len(tail)!=4 or len(words)!=172 or restore[-1]!=0x4e800020 or tail[-1]!=0x4e800020:
        raise ValueError('ACK return geometry')
    if old.splitlines().count('#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1')!=1 or 'UNDERCOVER_V1205_PRIVATE_ACK_RETURN' in old:
        raise ValueError('ACK return mode')
    expected={'v1132_private_postalarm_return.h':return_render(call,R,caller,restore,tail,caller_word),
              'wii_callback_return_v846.h':(host/'wii_callback_return_v846.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK return metadata')
    return C,call,R,caller,restore,tail,caller_word,words[(call-C)//4]

def verify_return_dispatch_hook(body,caller,caller_word):
    block=block_at(body,caller,caller_word)
    hook=f'    undercover::wii::v958::postalarm_dispatch_resume(ctx,0x{caller:08x}u,0x{caller_word:08x}u);\n'
    tick='    ++ctx.inst_count;\n'
    # The dispatcher already advanced its tick. No additional executable
    # statement or conditional may appear between this observer and the
    # original caller label's own tick.
    if block.count('v958::postalarm_dispatch_resume(')!=1 or block.count(hook)!=1 or block.count(tick)!=1 or block.count(hook+tick)!=1:
        raise ValueError('ACK return dispatch')

def verify_return_native(src,outer,meta):
    C,call,R,caller,restore,tail,caller_word,call_word=meta
    for addr,rows in ((C,{call+4+4*i:w for i,w in enumerate(tail)}),
                      (R,{R+4*i:w for i,w in enumerate(restore)}),(HANDLER,{caller:caller_word})):
        hits=[s for s in src.values() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('ACK return owner')
        body=exact_function(hits[0],addr)
        checked={pc:(addr,w) for pc,w in rows.items()}
        if addr==C:
            verify_direct(body,call,R);verify_label(body,call,call_word,False);checked[call]=(addr,call_word)
        if addr==HANDLER:
            verify_resume_dispatch(outer,HANDLER,caller)
            verify_return_dispatch_hook(body,caller,caller_word)
        if audit_native([body],outer,checked)!=len(checked):raise ValueError('ACK return coverage')
        for pc,w in rows.items():verify_label(body,pc,w,False)

def verify_handler_metadata(dol,elf,old,dest,host,return_meta):
    words,sites,lanes,rd,wr,index=handler_derive(dol,elf)
    _,_,_,caller,_,_,caller_word,_=return_meta
    rows=lanes[0]
    if len(sites)!=2 or caller!=sites[0]+4 or caller!=index[0] or rows.get(caller)!=(caller_word,0,0):
        raise ValueError('ACK handler predecessor')
    if len(rows)!=52 or not caller<rd<wr or rd not in rows or wr not in rows or rows[rd][0]>>26!=32 or rows[wr][0]>>26!=36 or \
       sorted((o,k) for _,o,k in rows.values() if k)!=[(7,1),(8,1),(12,1)]:
        raise ValueError('ACK handler geometry')
    census=call_census(HANDLER,words)
    if any(census.get(pc,(0,0))!=(o,k) for pc,(_,o,k) in rows.items()):
        raise ValueError('ACK handler census')
    if old.splitlines().count('#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1')!=1 or 'UNDERCOVER_V1210_PRIVATE_ACK_HANDLER' in old:
        raise ValueError('ACK handler mode')
    expected={'v1139_private_postalarm_handler.h':handler_render(rows,rd,wr,index)}
    for n in ('wii_handler_suffix_guard_v868.h','wii_handler_index_branch_v911.h'):
        expected[n]=(host/n).read_text()
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK handler metadata')
    return rows,caller

def verify_handler_native(src,outer,meta):
    rows,caller=meta
    hits=[s for s in src.values() if owns_root(s,HANDLER)]
    if len(hits)!=1 or sum(entry_count(s,HANDLER) for s in src.values())!=1:raise ValueError('ACK handler owner')
    body=exact_function(hits[0],HANDLER)
    verify_resume_dispatch(outer,HANDLER,caller)
    if audit_native([body],outer,{pc:(HANDLER,w) for pc,(w,_,_) in rows.items()})!=len(rows):
        raise ValueError('ACK handler coverage')
    for pc,(w,o,k) in rows.items():
        verify_label(body,pc,w,False)
        if patch_handler(body,pc,w,o,k,caller)!=body:raise ValueError('ACK handler hook')

def verify_handler_return_metadata(dol,elf,old,dest,host,handler_meta):
    call,R,resume,restore,tail,w,branch,h,d=handler_return_geometry(dol,elf)
    rows,caller=handler_meta
    if rows.get(call)!=(branch,12,1) or set(rows)&{call+4+4*i for i in range(4)}:
        raise ValueError('ACK handler return predecessor')
    if len(restore)!=16 or len(tail)!=4 or restore[-1]!=0x4e800020 or tail[-1]!=0x4e800020:
        raise ValueError('ACK handler return geometry')
    if old.splitlines().count('#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1')!=1 or 'UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN' in old:
        raise ValueError('ACK handler return mode')
    expected={'v1145_private_postalarm_handler_return.h':handler_return_render(call,R,resume,restore,tail,w),
              'v919_private_handler_epilogue.h':h,'v920_private_handler_resume.h':d,
              'wii_callback_return_v846.h':(host/'wii_callback_return_v846.h').read_text()}
    for n,s in expected.items():
        path=dest/n
        if path.is_symlink() or not path.is_file() or path.read_text()!=s:raise ValueError('ACK handler return metadata')
    return call,R,resume,restore,tail,w,branch,caller

def verify_handler_return_dispatch_hook(body,pc,w):
    block=block_at(body,pc,w)
    hook=f'    undercover::wii::v958::postalarm_handler_dispatch_resume(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    tick='    ++ctx.inst_count;\n'
    if block.count('v958::postalarm_handler_dispatch_resume(')!=1 or block.count(hook)!=1 or block.count(tick)!=1 or block.count(hook+tick)!=1:
        raise ValueError('ACK handler return dispatch')

def verify_handler_return_native(src,outer,meta):
    call,R,resume,restore,tail,w,branch,caller=meta
    if audit_shared_alias(src.values(),outer,R,restore)!=16:raise ValueError('ACK handler return coverage')
    verify_resume_dispatch(outer,DISPATCH,resume)
    for addr,rows in ((HANDLER,{call+4+4*i:x for i,x in enumerate(tail)}),
                      (R,{R+4*i:x for i,x in enumerate(restore)}),(DISPATCH,{resume:w})):
        hits=[s for s in src.values() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:raise ValueError('ACK handler return owner')
        body=exact_function(hits[0],addr)
        checked={pc:(addr,x) for pc,x in rows.items()}
        if addr==HANDLER:
            verify_direct(body,call,R);verify_label(body,call,branch,False);checked[call]=(addr,branch)
        if addr==DISPATCH:verify_handler_return_dispatch_hook(body,resume,w)
        if audit_native([body],outer,checked)!=len(checked):raise ValueError('ACK handler return coverage')
        for pc,x in rows.items():
            verify_label(body,pc,x,False)
            if addr==HANDLER and patch_handler(body,pc,x,0,0,caller)!=body:raise ValueError('ACK handler return hook')

def verify_final_metadata(dol,elf,old,dest,host,handler_return_meta):
    ep,j,vectors,edges,entries,dw,prior=final_metadata(dol,elf)
    _,_,resume,_,_,w,_,_=handler_return_meta
    if j!=resume or ep.get(j)!=(DISPATCH,w):
        raise ValueError('ACK final predecessor')
    if len(entries)!=5 or len(set(entries))!=5 or len(edges)!=2 or set(ep)&set(vectors) or len(ep)<50 or sum(x==0x4c000064 for _,x in ep.values())!=1:
        raise ValueError('ACK final geometry')
    if old.splitlines().count('#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1')!=1 or 'UNDERCOVER_V1217_PRIVATE_ACK_FINAL' in old:
        raise ValueError('ACK final mode')
    expected={**prior,'v1151_private_held_epilogue.h':final_render(),
              'wii_live_epilogue_v762.h':(host/'wii_live_epilogue_v762.h').read_text(),
              'wii_external_return_v706.h':(host/'wii_external_return_v706.h').read_text()}
    for n,s in expected.items():
        h=dest/n
        if h.is_symlink() or not h.is_file() or h.read_text()!=s:raise ValueError('ACK final metadata')
    return ep,j,edges,entries

def verify_final_hook(body,pc,w,shared=False,first=False):
    block=block_at(body,pc,w)
    if shared or first:
        verify_label(body,pc,w,False)
        if first:verify_handler_return_dispatch_hook(body,pc,w)
        return
    tick='    ++ctx.inst_count;\n';arg=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    expected=f'    if({FINAL_ACTIVE}) undercover::wii::v958::before({arg},false);\n    else undercover::wii::v922::before({arg});\n'
    if block.count(tick)!=1 or block.count(SI)!=1 or block.count(expected)!=1 or \
       block.count('v958::before(')!=1 or block.count('v922::before(')!=1 or not block.index(tick)<block.index(SI)<block.index(expected):
        raise ValueError('ACK final hook')

def verify_final_native(src,outer,meta):
    ep,j,edges,entries=meta
    if audit_native(src.values(),outer,ep)!=len(ep):raise ValueError('ACK final coverage')
    def owner(a):
        hits=[s for s in src.values() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('ACK final owner')
        return exact_function(hits[0],a)
    verify_resume_dispatch(outer,DISPATCH,j)
    for a,links in edges:
        body=owner(a)
        for pc,dst in links:verify_direct(body,pc,dst)
    for a in set(entries)|{DISPATCH}:
        body=owner(a)
        for pc,(root,w) in ep.items():
            if root==a:verify_final_hook(body,pc,w,a in (DISABLE,RESTORE),pc==j)

def verify_resume_metadata(dol,elf,old,dest,final_meta):
    ep,j,resume,header,edges,entries=final_geometry(dol,elf)
    if resume not in ep or ep[resume][0]!=ENTRY or resume in final_meta[0] or j!=final_meta[1] or \
       {pc:x for pc,x in ep.items() if pc!=resume}!=final_meta[0]:
        raise ValueError('ACK resume predecessor')
    if old.count('#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n')!=1 or 'UNDERCOVER_V1220_PRIVATE_ACK_RESUME' in old:
        raise ValueError('ACK resume mode')
    h=dest/'v922_private_irq_return.h'
    if h.is_symlink() or not h.is_file() or h.read_text()!=header.replace('::v767','::v922'):
        raise ValueError('ACK resume metadata')
    return resume,ep[resume][1]

def patch_final_resume(body,pc,w):
    block=block_at(body,pc,w);arg=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    tick='    ++ctx.inst_count;\n'
    legacy=f'    undercover::wii::v922::resume({arg});\n'
    trace=r'    if \(nwii::runtime::g_trace_calls\) nwii::runtime::trace_call\(0x'+f'{pc:X}'+r', ctx\); // V616 native IRQ resume\n'
    if not re.match(trace+re.escape(tick),block,re.I) or block.count(tick)!=1 or block.count(SI)!=1 or \
       block.count(legacy)!=1 or block.count('v922::resume(')!=1 or 'v958::' in block or not block.index(tick)<block.index(SI)<block.index(legacy):
        raise ValueError('ACK resume hook')
    new=f'    if({FINAL_ACTIVE}) undercover::wii::v958::before({arg},false);\n    else '+legacy.lstrip()
    updated=block.replace(legacy,new,1)
    if body.count(block)!=1:raise ValueError('ACK resume hook')
    return body.replace(block,updated,1)

def prepare_resume_native(src,outer,meta):
    pc,w=meta
    hits=[p for p,s in src.items() if owns_root(s,ENTRY)]
    if len(hits)!=1 or sum(entry_count(s,ENTRY) for s in src.values())!=1:
        raise ValueError('ACK resume owner')
    p=hits[0];body=exact_function(src[p],ENTRY)
    verify_resume_dispatch(outer,ENTRY,pc)
    if audit_native([body],outer,{pc:(ENTRY,w)})!=1:raise ValueError('ACK resume coverage')
    out=patch_final_resume(body,pc,w)
    return p,include_once(replace_body(src[p],body,out),'#include "undercover/wii_second_ack_live_v958.h"')

def render_leaf(pc,w,caller_word):
    return ('#pragma once\n#include "wii_irq_leaf_finish_v927.h"\nnamespace undercover::wii::v1227 {\n'
            'inline constexpr IrqLeafFinishExpectation expected{'+fmt((pc,w,RETURN,caller_word))+'};\n}\n')

def verify_leaf_metadata(dol,elf,old,dest,resume_meta):
    pc,leaf,caller,caller_word=leaf_plan(dol,elf)
    if tuple(resume_meta)!=(pc,leaf[0]) or pc!=ENTRY+12 or len(leaf)!=2 or leaf[1]!=0x4e800020 or caller==ENTRY:
        raise ValueError('ACK leaf predecessor')
    if 'UNDERCOVER_V1227_PRIVATE_ACK_LEAF' in old or any((dest/n).exists() or (dest/n).is_symlink() for n in
        ('v1227_private_ack_leaf.h','wii_irq_leaf_finish_v927.h')):
        raise ValueError('ACK leaf destination')
    return pc,leaf[0],caller,caller_word

def patch_leaf_label(body,pc,w,caller=False):
    block=block_at(body,pc,w)
    if 'v958::' in block:raise ValueError('ACK leaf hook')
    # The original V928 installer already validates the scheduler prefix,
    # tick and caller's existing V616 pre-label trace. Reuse that check,
    # but activate only the new third-ACK observer, not the old leaf mode.
    checked=legacy_leaf_patch(body,pc,w,caller)
    arg=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    old=f'    undercover::wii::v922::{"resume" if caller else "before"}({arg});\n'
    new=f'    if({FINAL_ACTIVE}) undercover::wii::v958::before({arg},false);\n'
    if checked.count(old)!=1:raise ValueError('ACK leaf hook')
    return checked.replace(old,new,1)

def prepare_leaf_native(src,outer,meta,resume_edit):
    pc,w,caller,cw=meta
    labels={pc:(ENTRY,w),pc+4:(ENTRY,0x4e800020),RETURN:(caller,cw)}
    if audit_native(src.values(),outer,labels)!=3:raise ValueError('ACK leaf coverage')
    verify_resume_dispatch(outer,ENTRY,pc);verify_resume_dispatch(outer,caller,RETURN)
    edits={resume_edit[0]:resume_edit[1]}
    for a,label,word,is_caller in ((ENTRY,pc+4,0x4e800020,False),(caller,RETURN,cw,True)):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('ACK leaf owner')
        p=hits[0];s=edits.get(p,src[p]);body=exact_function(s,a)
        out=patch_leaf_label(body,label,word,is_caller)
        edits[p]=include_once(replace_body(s,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    return edits

def prepare_ipc_native(dol,elf,src,outer,leaf_meta,dest,host,old):
    _,_,caller,cw=leaf_meta
    g=ipc_geometry(dol,elf)
    rows,_,_,_=g
    if RETURN!=IPC_CALL or rows[0][:3]!=(IPC_ROOT,IPC_CALL+4,cw):raise ValueError('ACK IPC predecessor')
    n=dict(IPC_SPANS).get(IPC_ROOT)
    if n!=0xb4:raise ValueError('ACK IPC extent')
    code=exact(dol,elf,IPC_ROOT,n//4)
    if rows[0][3]!=code[0]:raise ValueError('ACK IPC identity')
    expected={IPC_CALL:(caller,cw),**{IPC_ROOT+4*i:(IPC_ROOT,w) for i,w in enumerate(code)}}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('ACK IPC coverage')
    owners=[exact_function(t,caller) for t in src.values() if owns_root(t,caller)]
    targets=[exact_function(t,IPC_ROOT) for t in src.values() if owns_root(t,IPC_ROOT)]
    if len(owners)!=1 or len(targets)!=1:raise ValueError('ACK IPC owner')
    verify_direct(owners[0],IPC_CALL,IPC_ROOT)
    trace=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{IPC_ROOT:X}) nwii::runtime::trace_call(0x{IPC_ROOT:X}, ctx);'
    if targets[0].count(trace)!=1:raise ValueError('ACK IPC entry trace')
    private=dest/'v1230_private_ack_ipc.h'
    if 'UNDERCOVER_V1230_PRIVATE_ACK_IPC' in old or private.exists() or private.is_symlink():raise ValueError('ACK IPC destination')
    files={private:ipc_render(*g)+'\n#include "wii_post_ack_ipc_join_v1229.h"\nnamespace undercover::wii::v1230 {inline constexpr IpcEntryJoinExpectation expected{'+fmt((IPC_CALL,IPC_ROOT,cw,code[0]))+'};}\n'}
    for name in ('wii_ipc_client_witness_v623.h','wii_ipc_entry_join_v930.h','wii_post_ack_ipc_join_v1229.h'):
        path=dest/name;data=(host/name).read_text()
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_text()!=data)):raise ValueError('ACK IPC destination')
        if not path.exists():files[path]=data
    return files

def prepare_ipc_complete_native(dol,elf,src,outer,leaf_meta,edits):
    _,_,caller,_=leaf_meta
    rows,_,_,ret=ipc_geometry(dol,elf)
    expected={pc+4*i:(pc,w) for pc,n in IPC_SPANS for i,w in enumerate(exact(dol,elf,pc,n//4))}
    expected[IPC_RETURN]=(caller,ret)
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('ACK IPC complete coverage')
    targets={r[0] for r in rows}
    if any(sum(entry_count(t,pc) for t in src.values())!=1 for pc in targets):raise ValueError('ACK IPC complete entry')
    # All seventeen direct edges must remain native, including shared OS leaves.
    for target,lr,_,_ in rows:
        site=lr-4
        hits=[t for t in src.values() if re.search(r'(?mi)^loc_'+f'{site:X}'+r': ;$',t)]
        if len(hits)!=1:raise ValueError('ACK IPC complete edge')
        verify_direct(hits[0],site,target)
    hits=[p for p,t in src.items() if owns_root(t,caller)]
    if len(hits)!=1:raise ValueError('ACK IPC complete owner')
    p=hits[0];s=edits.get(p,src[p]);body=exact_function(s,caller)
    new=patch_ipc_return(body,ret,IPC_RETURN)
    return {**edits,p:replace_body(s,body,new)}

def prepare_stm_native(dol,elf,src,outer,leaf_meta,edits,dest,host,old):
    _,_,caller,_=leaf_meta
    g=stm_geometry(dol,elf)
    bridge,body,stm,op,_,_=g
    if caller!=STM_OSINIT or STM_BEGIN!=IPC_RETURN:raise ValueError('ACK STM predecessor')
    scopes=stm_scopes(bridge,body,op)
    expected={pc:pair for name,group in scopes.items() if name!='post' for pc,pair in group.items()}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('ACK STM coverage')
    for target,lr,_,_ in (stm,op):
        owners=[exact_function(t,target) for t in src.values() if owns_root(t,target)]
        if len(owners)!=1 or sum(entry_count(t,target) for t in src.values())!=1:raise ValueError('ACK STM entry')
        site=lr-4
        hits=[t for t in src.values() if re.search(r'(?mi)^loc_'+f'{site:X}'+r': ;$',t)]
        if len(hits)!=1:raise ValueError('ACK STM edge')
        verify_direct(hits[0],site,target)
    owners=[p for p,t in src.items() if owns_root(t,caller)]
    if len(owners)!=1 or owners[0] not in edits:raise ValueError('ACK STM predecessor')
    body=exact_function(edits[owners[0]],caller)
    trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{STM_BEGIN:X}, ctx); // V625 IPC client return\n'
    label=f'loc_{STM_BEGIN:X}: ;\n    // 0x{STM_BEGIN:08X}: {bridge[0]:08X}\n'
    if body.count(trace)!=1 or body.count(label+trace+'    ++ctx.inst_count;\n')!=1:
        raise ValueError('ACK STM return trace')
    private=dest/'v1240_private_ack_stm.h'
    if 'UNDERCOVER_V1240_PRIVATE_ACK_STM' in old or private.exists() or private.is_symlink():raise ValueError('ACK STM destination')
    files={private:stm_render(g)+'\n#include "wii_post_ack_stm_join_v1239.h"\n'}
    for name in ('wii_stm_prefix_witness_v629.h','wii_post_ack_stm_join_v1239.h'):
        path=dest/name;data=(host/name).read_text()
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_text()!=data)):raise ValueError('ACK STM destination')
        if not path.exists():files[path]=data
    return files

def install(dol,elf,root,host,callback=False,prefix=False,time=False,frontier=False,wireless=False,suffix=False,returned=False,handler=False,handler_return=False,final=False,resumed=False,leaf=False,ipc=False,ipc_complete=False,stm=False,opened=False):
    if prefix and not callback:raise ValueError('ACK prefix mode')
    if time and not prefix:raise ValueError('ACK time mode')
    if frontier and not time:raise ValueError('ACK frontier mode')
    if wireless and not frontier:raise ValueError('ACK wireless mode')
    if suffix and not wireless:raise ValueError('ACK suffix mode')
    if returned and not suffix:raise ValueError('ACK return mode')
    if handler and not returned:raise ValueError('ACK handler mode')
    if handler_return and not handler:raise ValueError('ACK handler return mode')
    if final and not handler_return:raise ValueError('ACK final mode')
    if resumed and not final:raise ValueError('ACK resume mode')
    if leaf and not resumed:raise ValueError('ACK leaf mode')
    if ipc and not leaf:raise ValueError('ACK IPC mode')
    if ipc_complete and not ipc:raise ValueError('ACK IPC complete mode')
    if stm and not ipc_complete:raise ValueError('ACK STM mode')
    if opened and not stm:raise ValueError('ACK Open mode')
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
    callback_site=verify_callback_metadata(dol,elf,spans,rows,old) if callback else None
    callback_paths=path_lengths(rows,HANDLER,expected[0],callback_site) if callback else ()
    if callback and ('UNDERCOVER_V1180_PRIVATE_ACK_CALLBACK' in old or
        (dest/'wii_callback_identity_v796.h').is_symlink() or
        (dest/'wii_callback_identity_v796.h').read_text()!=(host/'wii_callback_identity_v796.h').read_text()):
        raise ValueError('ACK callback metadata')
    prefix_meta=verify_prefix_metadata(dol,elf,old) if prefix else None
    if prefix:
        h=dest/'wii_callback_prefix_v800.h'
        if h.is_symlink() or not h.is_file() or h.read_text()!=(host/h.name).read_text() or 'UNDERCOVER_V1184_PRIVATE_ACK_PREFIX' in old:
            raise ValueError('ACK prefix metadata')
    time_meta=verify_time_metadata(dol,elf,old,dest,host,prefix_meta) if time else None
    frontier_meta=verify_frontier_metadata(dol,elf,old,dest,host,time_meta) if frontier else None
    wireless_meta=verify_wireless_metadata(dol,elf,old,dest,host,time_meta,frontier_meta) if wireless else None
    suffix_meta=verify_suffix_metadata(dol,elf,old,dest,host,wireless_meta) if suffix else None
    return_meta=verify_return_metadata(dol,elf,old,dest,host,suffix_meta,callback_site) if returned else None
    handler_meta=verify_handler_metadata(dol,elf,old,dest,host,return_meta) if handler else None
    handler_return_meta=verify_handler_return_metadata(dol,elf,old,dest,host,handler_meta) if handler_return else None
    final_meta=verify_final_metadata(dol,elf,old,dest,host,handler_return_meta) if final else None
    resume_meta=verify_resume_metadata(dol,elf,old,dest,final_meta) if resumed else None
    leaf_meta=verify_leaf_metadata(dol,elf,old,dest,resume_meta) if leaf else None
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('ACK helper tree')
    src={x:x.read_text() for x in paths};outer=main.read_text()
    callback_guard=True
    if prefix_meta:verify_prefix_native(src,outer,prefix_meta)
    if time_meta:verify_time_native(src,outer,time_meta)
    if frontier_meta:verify_frontier_native(src,outer,frontier_meta)
    if wireless_meta:verify_wireless_native(src,outer,wireless_meta)
    if suffix_meta:verify_suffix_native(src,outer,suffix_meta)
    if return_meta:verify_return_native(src,outer,return_meta)
    if handler_meta:verify_handler_native(src,outer,handler_meta)
    if handler_return_meta:verify_handler_return_native(src,outer,handler_return_meta)
    if final_meta:verify_final_native(src,outer,final_meta)
    resume_edit=prepare_resume_native(src,outer,resume_meta) if resume_meta else None
    resume_edits=prepare_leaf_native(src,outer,leaf_meta,resume_edit) if leaf_meta else dict([resume_edit]) if resume_edit else {}
    ipc_files=prepare_ipc_native(dol,elf,src,outer,leaf_meta,dest,host,old) if ipc else {}
    if ipc_complete:resume_edits=prepare_ipc_complete_native(dol,elf,src,outer,leaf_meta,resume_edits)
    if stm:ipc_files.update(prepare_stm_native(dol,elf,src,outer,leaf_meta,resume_edits,dest,host,old))
    if opened:
        ios=root/'nWiiRuntime/src/hle/ios.cpp';cpu=root/'nWiiRuntime/include/runtime/cpu_context.h'
        if any(p.is_symlink() or not p.is_file() for p in (ios,cpu)):raise ValueError('ACK Open destination')
        resume_edits,open_files,new_ios,new_cpu=prepare_open_native(dol,elf,src,outer,resume_edits,dest,host,ios.read_text(),cpu.read_text(),old)
        if set(open_files)&set(ipc_files):raise ValueError('ACK Open destination')
        ipc_files.update(open_files);ipc_files[ios]=new_ios;ipc_files[cpu]=new_cpu
    for index,(a,end,_) in enumerate(spans):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('ACK helper owner')
        body=exact_function(src[hits[0]],a)
        if callback_site is not None and a==HANDLER:
            callback_guard=verify_callback_guard(body,callback_site)
            if prefix:verify_indirect(body,callback_site)
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
    # All checks are complete. Only the opt-in final resume redirects the
    # existing post-tick observer; no original instruction is modified.
    for path,content in resume_edits.items():path.write_text(content)
    if leaf_meta:
        (dest/'v1227_private_ack_leaf.h').write_text(render_leaf(leaf_meta[0],leaf_meta[1],leaf_meta[3]))
        (dest/'wii_irq_leaf_finish_v927.h').write_text((host/'wii_irq_leaf_finish_v927.h').read_text())
    for path,content in ipc_files.items():path.write_text(content)
    result.write_text(render(spans,edges,rows,msr,expected,callback_guard,callback_paths))
    extra='#define UNDERCOVER_V1175_PRIVATE_ACK_HELPER 1\n'
    if callback:extra+='#define UNDERCOVER_V1180_PRIVATE_ACK_CALLBACK 1\n'
    if prefix:extra+='#define UNDERCOVER_V1184_PRIVATE_ACK_PREFIX 1\n'
    if time:extra+='#define UNDERCOVER_V1189_PRIVATE_ACK_TIME 1\n'
    if frontier:extra+='#define UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER 1\n'
    if wireless:extra+='#define UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS 1\n'
    if suffix:extra+='#define UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX 1\n'
    if returned:extra+='#define UNDERCOVER_V1205_PRIVATE_ACK_RETURN 1\n'
    if handler:extra+='#define UNDERCOVER_V1210_PRIVATE_ACK_HANDLER 1\n'
    if handler_return:extra+='#define UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN 1\n'
    if final:extra+='#define UNDERCOVER_V1217_PRIVATE_ACK_FINAL 1\n'
    if resumed:extra+='#define UNDERCOVER_V1220_PRIVATE_ACK_RESUME 1\n'
    if leaf:extra+='#define UNDERCOVER_V1227_PRIVATE_ACK_LEAF 1\n'
    if ipc:extra+='#define UNDERCOVER_V1230_PRIVATE_ACK_IPC 1\n'
    if ipc_complete:extra+='#define UNDERCOVER_V1235_PRIVATE_ACK_IPC_COMPLETE 1\n'
    if stm:extra+='#define UNDERCOVER_V1240_PRIVATE_ACK_STM 1\n'
    if opened:extra+='#define UNDERCOVER_V1246_PRIVATE_ACK_OPEN 1\n'
    private.write_text(old.replace(macro,macro+extra,1))
    if callback:print('V1182_ACK_CALLBACK_METADATA installed=1 original_words=172 guarded_site=1 execution=0')
    if prefix:print('V1186_ACK_PREFIX_METADATA installed=1 original_prefix=6 original_save=7 native_edges=2 execution=0')
    if time:print('V1190_ACK_TIME_METADATA installed=1 callback_labels=13 shared_labels=45 native_edges=4 execution=0')
    if frontier:print('V1194_ACK_FRONTIER_METADATA installed=1 callback_labels=27 native_edges=2 execution=0')
    if wireless:print('V1198_ACK_WIRELESS_METADATA installed=1 wrapper_labels=267 shared_labels=14 direct_edges=18 callback_returns=2 execution=0')
    if suffix:print('V1203_ACK_SUFFIX_METADATA installed=1 callback_labels=21 direct_edges=1 indirect_edges=1 execution=0')
    if returned:print('V1207_ACK_RETURN_METADATA installed=1 restore_labels=7 tail_labels=4 handler_resume=1 outer_tick=1 execution=0')
    if handler:print('V1211_ACK_HANDLER_METADATA installed=1 labels=52 status_sites=2 original_frontiers=3 execution=0')
    if handler_return:print('V1215_ACK_HANDLER_RETURN_METADATA installed=1 restore_labels=16 tail_labels=4 dispatcher_resume=1 outer_tick=1 execution=0')
    if final:print(f'V1218_ACK_FINAL_METADATA installed=1 labels={len(final_meta[0])} original_rfi=1 separate_witness=1 execution=0')
    if resumed:print('V1221_ACK_RESUME_METADATA installed=1 original_label=1 outer_dispatch=1 legacy_preserved=1 execution=0')
    if leaf:print('V1228_ACK_LEAF_METADATA installed=1 original_labels=3 caller_dispatch=1 original_extract=1 execution=0')
    if ipc:print('V1230_ACK_IPC_METADATA installed=1 original_call=1 root_labels=45 entry_trace=1 cold_witness=1 execution=0')
    if ipc_complete:print('V1235_ACK_IPC_COMPLETE_METADATA installed=1 calls=17 spans=10 return_trace=1 execution=0')
    if stm:print('V1240_ACK_STM_METADATA installed=1 bridge_labels=7 prefix_labels=23 open_entry=1 direct_edges=2 execution=0')
    if opened:print('V1247_ACK_OPEN_METADATA installed=1 direct_edges=6 allocator_tail=1 cache=1 native_sc=1 execution=0')
    print(f'V1176_ACK_HELPER_ROUTE installed=1 native_labels={len(rows)} roots=7 direct_edges=8 msr_sites=2 bus_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);p.add_argument('--callback',action='store_true');p.add_argument('--prefix',action='store_true');p.add_argument('--time',action='store_true');p.add_argument('--frontier',action='store_true');p.add_argument('--wireless',action='store_true');p.add_argument('--suffix',action='store_true');p.add_argument('--returned',action='store_true');p.add_argument('--handler',action='store_true');p.add_argument('--handler-return',action='store_true');p.add_argument('--final',action='store_true');p.add_argument('--resumed',action='store_true');p.add_argument('--leaf',action='store_true');p.add_argument('--ipc',action='store_true');p.add_argument('--ipc-complete',action='store_true');p.add_argument('--stm',action='store_true');p.add_argument('--opened',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent,a.callback,a.prefix,a.time,a.frontier,a.wireless,a.suffix,a.returned,a.handler,a.handler_return,a.final,a.resumed,a.leaf,a.ipc,a.ipc_complete,a.stm,a.opened)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'ACK helper '+s for s in ('geometry','predecessor','MSR','return','edge','render','destination','identity','mode','metadata','tree','owner','coverage')}
        safe|={'ACK callback geometry','ACK callback metadata','ACK callback guard'}
        safe|={'ACK prefix '+s for s in ('geometry','metadata','owner','coverage','mode')}
        safe|={'ACK time '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode')}
        safe|={'ACK frontier '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode')}
        safe|={'ACK wireless '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode','edge')}
        safe|={'ACK suffix '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode')}
        safe|={'ACK return '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode','dispatch')}
        safe|={'ACK handler '+s for s in ('predecessor','geometry','census','metadata','owner','coverage','mode','hook')}
        safe|={'ACK handler return '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode','hook','dispatch')}
        safe|={'ACK final '+s for s in ('predecessor','geometry','metadata','owner','coverage','mode','hook')}
        safe|={'ACK resume '+s for s in ('predecessor','metadata','owner','coverage','mode','hook')}
        safe|={'ACK leaf '+s for s in ('predecessor','destination','owner','coverage','mode','hook')}
        safe|={'ACK IPC '+s for s in ('predecessor','extent','identity','coverage','owner','entry trace','destination','mode')}
        safe|={'ACK IPC complete '+s for s in ('coverage','entry','edge','owner','mode')}
        safe.add('native IPC return label')
        safe|={'ACK STM '+s for s in ('predecessor','coverage','entry','edge','return trace','destination','mode')}
        safe|={'ACK Open '+s for s in ('mode','destination','vector identity','IOS seam','IOS order','allocator tail','root word','geometry','coverage','entry','edge word','trace owner','shared extent')}
        safe|={'open SC label','source shape','ambiguous patch','roundtrip'}
        safe|={'STM spans','STM return','STM call geometry','STM alternate geometry','STM span geometry','path census','data geometry','data overlap'}
        safe|={'IRQ leaf shape','caller owner','IRQ return label','IRQ return tick','IRQ return scheduler'}
        safe|={'indirect label','indirect LR','indirect dispatch','indirect fallback'}
        safe|={'third ACK bus','third ACK hook','third ACK tick','held handler label','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
        print('V1176_ACK_HELPER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
