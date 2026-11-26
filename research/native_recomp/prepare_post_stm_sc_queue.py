#!/usr/bin/env python3
"""Private queue witness expectations; no guest initialization or execution."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_report import queue_geometry,ROOT,EDGES
from prepare_post_stm_sc_version import plan as version_plan
from prepare_post_stm_sc_state import initial,overlap
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words

def plan(d,e):
    _,_,ranges,_=version_plan(d,e)
    rows,body,addr,obj,(start,site,queue)=queue_geometry(d,e)
    if set(rows)!=set(range(start,site+4,4)) or len(rows)!=3 or len(body)!=4 or direct_bl(rows[site],site)!=queue:
        raise ValueError('SC queue identity')
    if any(overlap(*obj,a,len(blob)) for a,blob in ranges):raise ValueError('SC queue version overlap')
    if site+4!=EDGES[5][0]:raise ValueError('SC queue next edge')
    caller=site+4;word=exact_words(d,e,caller,1)[0]
    if direct_bl(word,caller)!=EDGES[5][1]:raise ValueError('SC queue next edge')
    kind0,blob0=initial(d,addr,4);kind1,blob1=initial(d,addr+4,4)
    if kind0!=kind1:raise ValueError('SC queue initial kind')
    words=[(ROOT,pc,w) for pc,w in sorted(rows.items())]+[(queue,queue+4*i,w) for i,w in enumerate(body)]
    return (ROOT,start,queue,caller,word,addr),obj,words,(kind0,int(not any(blob0+blob1)))

def render(p):
    fields,obj,words,_=p
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f(row)+'}' for row in words)
    return ('#pragma once\n#include "wii_post_stm_sc_queue.h"\nnamespace post_stm_sc_queue_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+wr+'};\n'
        'inline constexpr undercover::wii::ScQueueExpectation expected{'+f(fields)+',undercover::wii::AllocatorRange{'+f(obj)+'},words};\n}\n')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('--out',type=Path);q=a.parse_args()
    safe={'size','SC queue identity','SC queue version overlap','SC queue next edge','SC queue initial kind'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.out:
            with (q.out/'private_post_stm_sc_queue.h').open('x') as out:out.write(render(p))
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_QUEUE_PROVENANCE verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    kind,zero=p[3]
    print(f'POST_STM_SC_QUEUE_PROVENANCE verified=1 caller_labels=3 leaf_labels=4 initial_kind={kind} initial_zero={zero} version_disjoint=1 next_console_edge=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
