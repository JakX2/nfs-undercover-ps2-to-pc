#!/usr/bin/env python3
"""Authenticate the private submit-header-return to queue-entry corridor."""
import argparse,struct
from pathlib import Path
from make_v651_open_fixture import submit_geometry,SUBMIT
from make_start_to_ipc_submit_v72 import EDGES
from apply_open_roots_v645 import irq_spans
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
CALLS=EDGES[2:4]
RESUME,DISABLE=CALLS[0]
QUEUE_CALL,QUEUE=CALLS[1]

def derive(d,e):
    roots,_=submit_geometry(d,e)
    irq={a:exact_words(d,e,a,n//4) for a,n in irq_spans(d,e)}
    body=roots[SUBMIT]
    if not SUBMIT<RESUME<QUEUE_CALL<SUBMIT+4*len(body) or QUEUE_CALL-RESUME>512:
        raise ValueError('queue corridor')
    words={pc:(SUBMIT,body[(pc-SUBMIT)//4]) for pc in range(RESUME,QUEUE_CALL+4,4)}
    if {pc:direct_bl(w,pc) for pc,(_,w) in words.items() if w>>26==18 and w&3==1}!=dict(CALLS):
        raise ValueError('queue corridor edges')
    helper=irq[DISABLE]
    words.update({pc:(DISABLE,helper[(pc-DISABLE)//4]) for pc in reachable(DISABLE,helper)})
    if sum(w>>26==31 and (w>>1)&1023==146 for a,w in words.values() if a==DISABLE)!=1:
        raise ValueError('nested disable shape')
    edges=[(dst,site+4,words[site][1],exact_words(d,e,dst,1)[0]) for site,dst in CALLS]
    return words,edges

def render(p):
    words,edges=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    return ('#pragma once\n#include "wii_ioctl_submit_queue_v1409.h"\nnamespace v1410 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt((a,pc,w))+'}' for pc,(a,w) in sorted(words.items()))+'};\n'
      'inline constexpr undercover::wii::IoctlSubmitQueueExpectation expected{'+fmt((SUBMIT,))+','+
      ','.join('undercover::wii::VectorEdge{'+fmt(row)+'}' for row in edges)+',words};\n}\n')

def audit(root,p):
    words,edges=p
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,(root/'main_output.cpp').read_text(),{**words,QUEUE:(QUEUE,edges[1][3])})
    for site,dst in CALLS:
        owners=[s for s in sources if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('queue call owner')
        verify_direct(owners[0],site,dst)
    for pc,(a,w) in words.items():
        hook=f'    {"v1270_before" if a==DISABLE else "v1344_before"}(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources)!=1:raise ValueError('queue prior hook')
    trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{RESUME:X}, ctx); // V625 IPC client return'
    if sum(s.count(trace) for s in sources)!=1:raise ValueError('queue resume trace')
    print(f'V1410_QUEUE_TRANSLATION verified=1 labels={len(words)+1} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--audit',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.audit:audit(q.out,p);return 0
        with (q.out/'v1410_private_ioctl_queue.h').open('x') as f:f.write(render(p))
        words,_=p
        stores=sum(w>>26 in (36,37,38,39,44,45,47,52,53,54,55,60,61) or
                   w>>26==31 and (w>>1)&1023 in (150,151,183,215,247,407,439,661,725,662,918,663,695,727,759,983,1014)
                   for a,w in words.values() if a==SUBMIT)
        print(f'V1410_QUEUE_GEOMETRY verified=1 submit_labels={sum(a==SUBMIT for a,w in words.values())} disable_labels={sum(a==DISABLE for a,w in words.values())} static_stores={stores}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','queue corridor','queue corridor edges','nested disable shape','queue call owner','queue prior hook','queue resume trace',
          'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
          'helper direct native call','helper native return edge','reachable fallthrough','reachable external conditional'}
        print('V1410_QUEUE_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
