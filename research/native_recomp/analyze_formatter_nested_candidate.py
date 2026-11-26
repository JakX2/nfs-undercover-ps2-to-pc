#!/usr/bin/env python3
"""Conditional symbolic probe of one initialized writable cell.

This does not establish a live value and never changes fixture memory.
The caller must validate the live bytes before any corresponding native path.
"""
import argparse,struct
from pathlib import Path
from audit_formatter_nested_read import plan as audit
from analyze_formatter_nested_path import plan as nested
from prepare_v419_full_start import MAX_DOL
from prepare_post_stm_sc_state import overlap
from prepare_post_stm_sc_disable import decision
from prepare_stm_final_return import plan as final_plan
from prepare_stm_event_return_geometry import plan as event_plan
from prepare_ipc_profile_geometry import layout
from prepare_ipc_dispatch_geometry import credit_object
from prepare_v1414_ipc_ring import ring_object
from prepare_post_stm_sc_version import plan as version_plan
from prepare_post_stm_sc_report_dependency_abi import plan as leaf_abi

def admit(record,addr,data,protected):
    kind,n,mapped,equal,covered,matches,writers=record
    if (kind,n,mapped,equal,covered,matches,writers)!=('writable',4,1,1,0,0,0):
        raise ValueError('candidate audit contract')
    if not isinstance(data,bytes) or len(data)!=4 or addr&3 or not 0x80000000<=addr<addr+4<=0x81800000:
        raise ValueError('candidate cell geometry')
    if any(overlap(addr,4,a,m) for a,m in protected):
        raise ValueError('candidate protected overlap')
    return addr,data

def candidate(d,e):
    record,addr,data=audit(d,e,details=True)
    _,_,ranges,_=version_plan(d,e)
    _,_,obj,*_=leaf_abi(d,e)
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3],final_plan(d,e)[1],
               *(x[3] for x in decision(d,e)[2]),*((a,len(blob)) for a,blob in ranges),obj]
    return admit(record,addr,data,protected)

def plan(d,e):
    return nested(d,e,candidate=candidate(d,e))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','candidate audit contract','candidate cell geometry','candidate protected overlap','nested candidate unused',
          'nested data range','nested data sections','nested data not immutable','nested data mapping','nested data identity','nested data cap',
          'formatter nested memory geometry','formatter nested state','formatter unknown arithmetic','formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance','formatter stack write provenance','formatter caller linkage provenance','formatter duplicate stack write','formatter update store','formatter indexed store provenance','formatter path bound','formatter frame identity','formatter other boundary','formatter update load','formatter compare','formatter branch','formatter CTR provenance','formatter CR provenance','formatter escape','formatter region cap','formatter boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        path,frame,sites,target_words,immutable_reads=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'FORMATTER_NESTED_CANDIDATE analyzed=0 reason=opcode category={k} ordinal={n} live_value_verified=0');return 1
        print('FORMATTER_NESTED_CANDIDATE analyzed=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input')+' live_value_verified=0')
        return 1
    print(f'FORMATTER_NESTED_CANDIDATE analyzed=1 conditional=1 visits={len(path)} unique={len(set(path))} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} target_words={target_words} immutable_reads={immutable_reads} candidate_cells=1 live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
