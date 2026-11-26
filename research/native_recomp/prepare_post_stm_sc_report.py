#!/usr/bin/env python3
"""Private census of the original report prologue and subsequent SC queue call."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_version import plan as version_plan,REPORT,ROOT,EDGES
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import first_region,category
from audit_handler_suffix_v728 import target
from restore_post_stm_v89 import SIZE
from prepare_stm_event_return_geometry import object_at,plan as event_plan
from prepare_stm_final_return import plan as final_plan
from prepare_post_stm_sc_disable import decision
from prepare_ipc_profile_geometry import layout
from prepare_ipc_dispatch_geometry import credit_object
from prepare_v1414_ipc_ring import ring_object
from prepare_post_stm_sc_state import overlap

def report_trace(root,words):
    rows,backs,_,stops=first_region(root,words,root)
    if backs or len(stops)!=1 or stops[0][1]!=1:raise ValueError('SC report boundary')
    # The version thunk established CR6=0. Only use that fact for
    # a CR-only branch on this exact bit; no guessed condition flags.
    pc=root;seen=[];sp=0;slots=[];fp=0;known_cr6=True
    while True:
        if pc not in rows or pc in seen:raise ValueError('SC report path')
        w=rows[pc];seen.append(pc);op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31
        if pc==stops[0][0]:break
        disp=((w&0xffff)^0x8000)-0x8000
        if op==37 and rs==ra==1:
            if sp or not -512<=disp<=-8 or disp%8:raise ValueError('SC report frame')
            sp=disp;slots.append((sp,4))
        elif op in (36,38,44,47,54) and ra==1:
            if not sp:raise ValueError('SC report frame')
            n={36:4,38:1,44:2,47:4*(32-rs),54:8}[op]
            at=sp+disp
            if at<sp+4 or at+n>8 or at%min(n,4) or any(overlap(at,n,a,m) for a,m in slots):
                raise ValueError('SC report slot')
            slots.append((at,n));fp+=int(op==54)
        elif op==16 and w&3==0:
            bo=(w>>21)&31;bi=(w>>16)&31
            if bo&16:pc=target(pc,w);continue
            if not known_cr6 or bi!=6 or not bo&4:raise ValueError('SC report branch')
            pc=target(pc,w) if not bo&8 else pc+4
            continue
        elif op==18 and not w&3:pc=target(pc,w);continue
        elif category(w)=='integer':
            # Comparisons/record forms can invalidate the incoming CR bit.
            if op in (10,11,12,13,28,29) or op==31 and (xo in (0,32,144) or w&1):
                known_cr6=False
        else:raise ValueError('SC report opcode')
        pc+=4
    if not sp:raise ValueError('SC report frame')
    return rows,tuple(seen),tuple(slots),fp,-sp,stops[0][3]

def report_prefix(root,words):
    rows,seen,slots,fp,frame,dst=report_trace(root,words)
    return len(rows),len(seen),len(slots),fp,frame,dst

def queue_plan(d,e):
    caller=EDGES[3][0]+4;site,root=EDGES[4]
    body=exact_words(d,e,ROOT,SIZE//4)
    rows,backs,stores,stops=first_region(ROOT,body,caller)
    if backs or stores or len(stops)!=1 or stops[0][0]!=site or stops[0][3]!=root:
        raise ValueError('SC queue boundary')
    gp={i:EXPECTED_GPRS[i] for i in (2,13)}
    for pc,w in sorted(rows.items()):
        if pc==site:continue
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31
        if op not in (14,15) or (ra and ra not in gp):raise ValueError('SC queue argument')
        imm=((w&0xffff)^0x8000)-0x8000
        gp[rs]=((gp[ra] if ra else 0)+(imm<<(16 if op==15 else 0)))&0xffffffff
    addr=gp.get(3,0)
    if not addr or addr&3:raise ValueError('SC queue address')
    obj=object_at(d,e,addr,4)
    if object_at(d,e,addr+4,4)!=obj or not obj[0]<=addr<addr+8<=obj[0]+obj[1]:
        raise ValueError('SC queue object')
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3],final_plan(d,e)[1],
               *(x[3] for x in decision(d,e)[2])]
    if any(overlap(*obj,*p) for p in protected):raise ValueError('SC queue overlap')
    size=parse_functions(e).get(root,0)
    if size!=16:raise ValueError('SC queue extent')
    ws=exact_words(d,e,root,size//4)
    if ws[-1]!=0x4e800020:raise ValueError('SC queue return')
    known={};cells=set()
    for w in ws[:-1]:
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;disp=((w&0xffff)^0x8000)-0x8000
        if op==14 and ra==0 and rs!=3 and disp==0:known[rs]=0
        elif op==36 and ra==3 and known.get(rs)==0 and disp in (0,4):cells.add(disp)
        else:raise ValueError('SC queue opcode')
    if cells!={0,4}:raise ValueError('SC queue stores')
    return len(rows),len(ws),len(cells)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('--queue',action='store_true');q=a.parse_args()
    safe={'size','SC report boundary','SC report path','SC report frame','SC report slot','SC report branch','SC report opcode','SC report extent',
          'SC queue boundary','SC queue argument','SC queue address','SC queue object','SC queue overlap','SC queue extent','SC queue return','SC queue opcode','SC queue stores'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();version_plan(d,e)
        if q.queue:
            caller,leaf,stores=queue_plan(d,e)
            print(f'POST_STM_SC_QUEUE_GEOMETRY verified=1 caller_labels={caller} leaf_labels={leaf} zero_stores={stores} object_disjoint=1 original_execution=0');return 0
        sizes=parse_functions(e);size=sizes.get(REPORT,0)
        if not 16<=size<=4096 or size%4:raise ValueError('SC report extent')
        ws=exact_words(d,e,REPORT,size//4)
        labels,visits,slots,fp,frame,dst=report_prefix(REPORT,ws)
        n=sizes.get(dst,0)
        if not 4<=n<=4096 or n%4:raise ValueError('SC report boundary')
        exact_words(d,e,dst,1)
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_'+('QUEUE' if q.queue else 'REPORT')+'_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_GEOMETRY verified=1 static_labels={labels} cr6_clear_visits={visits} stack_store_sites={slots} fp_stores={fp} frame_bytes={frame} next_root_words={n//4} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
