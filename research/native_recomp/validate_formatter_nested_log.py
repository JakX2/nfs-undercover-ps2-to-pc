#!/usr/bin/env python3
"""Check only allowlisted aggregate markers; never echo private diagnostics."""
import argparse,re
from pathlib import Path

CELL=re.compile(r'FORMATTER_NESTED_CELL_TRIAL n=([0-7]) cold_match=([01]) live_match=([01]) sample_equal=([01]) guest_load=0')
CELL_TOTAL=re.compile(r'FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match=([0-8]) live_match=([0-8]) sample_equal=([0-8]) endpoint_only=1 guest_loads=0 guest_writes=0')
def markers(second):
    tag='FORMATTER_SECOND' if second else 'FORMATTER_NESTED'
    visits,loads=(44,2) if second else (35,1)
    conditional=' conditional_load=1' if second else ''
    trial=re.compile(fr'{tag}_TRIAL n=([0-7]) native_prefix=1 frame=48 loads={loads} stores=12 nonvolatile=3{conditional} pre_load_stop=1 deferred=1 reply=0 visits={visits}')
    total=(f'{tag}_NATIVE owner=1 trials=8 native_prefix=8 loads={8*loads} stores=96 nonvolatile=24'
        +(' conditional_loads=8' if second else '')
        +f' pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits={8*visits} ios_steps=5 fallback=0 complete_image=0 boot_verified=0')
    return tag,trial,total

THIRD_TRIAL=re.compile(r'FORMATTER_THIRD_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=5 stores=13 nonvolatile=([3-9]|1[0-8]) authenticated_loads=([3-5]) conditional_loads=2 pre_load_stop=1 deferred=1 reply=0 visits=74')
THIRD_TOTAL=re.compile(r'FORMATTER_THIRD_NATIVE owner=1 trials=8 native_prefix=8 loads=40 stores=104 nonvolatile=([0-9]{2,3}) authenticated_loads=([0-9]{2}) conditional_loads=16 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=592 ios_steps=5 fallback=0 complete_image=0 boot_verified=0')

CONTROL_TRIAL=re.compile(r'FORMATTER_CONTROL_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 pre_transfer_stop=1 transfer_executed=0 deferred=1 reply=0 visits=76')
CONTROL_TOTAL='FORMATTER_CONTROL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 pre_transfer_stop=8 transfer_executed=0 deferred=8 reply=0 visits=608 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

def verify(lines,*,second=False,third=False,control=False):
    if sum((second,third,control))>1:raise ValueError('native mode')
    tag,trial,total=markers(second)
    if third:tag,trial,total='FORMATTER_THIRD',THIRD_TRIAL,None
    if control:tag,trial,total='FORMATTER_CONTROL',CONTROL_TRIAL,CONTROL_TOTAL
    details=None;third_total=None
    trials=set();cells={};aggregate=None;native=False
    for line in lines:
        line=line.rstrip('\r\n')
        if line.startswith(tag+'_TRIAL '):
            m=trial.fullmatch(line)
            if not m or int(m[1]) in trials:raise ValueError('native trial')
            if third:
                current=tuple(map(int,m.groups()[1:]))
                if details is not None and details!=current:raise ValueError('native trial details')
                details=current
            trials.add(int(m[1]))
        elif line.startswith('FORMATTER_NESTED_CELL_TRIAL '):
            if control:raise ValueError('unexpected cell observation')
            m=CELL.fullmatch(line)
            if not m or int(m[1]) in cells:raise ValueError('cell trial')
            v=tuple(map(int,m.groups()[1:]))
            if v[2] and v[0]!=v[1] or v[0] and v[1] and not v[2]:
                raise ValueError('cell consistency')
            cells[int(m[1])]=v
        elif line.startswith('FORMATTER_NESTED_CELL_NATIVE '):
            if control:raise ValueError('unexpected cell observation')
            m=CELL_TOTAL.fullmatch(line)
            if not m or aggregate is not None:raise ValueError('cell aggregate')
            aggregate=tuple(map(int,m.groups()))
        elif line.startswith(tag+'_NATIVE '):
            if native:raise ValueError('native aggregate')
            if third:
                m=THIRD_TOTAL.fullmatch(line)
                if not m:raise ValueError('native aggregate')
                third_total=tuple(map(int,m.groups()))
                total=line
            elif line!=total:raise ValueError('native aggregate')
            native=True
        elif line.startswith('FORMATTER_NESTED_REFUSAL '):
            raise ValueError('native refusal')
    if trials!=set(range(8)) or not native or (not control and set(cells)!=trials):
        raise ValueError('trial coverage')
    if control:return (total,)
    if third and third_total!=tuple(8*v for v in details):raise ValueError('native totals')
    if aggregate!=tuple(sum(v[i] for v in cells.values()) for i in range(3)):
        raise ValueError('cell totals')
    return (f'FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match={aggregate[0]} live_match={aggregate[1]} sample_equal={aggregate[2]} endpoint_only=1 guest_loads=0 guest_writes=0',total)

def main():
    a=argparse.ArgumentParser();a.add_argument('log',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--second',action='store_true');m.add_argument('--third',action='store_true');m.add_argument('--control',action='store_true');q=a.parse_args()
    safe={'unexpected cell observation','native mode','native trial details','native totals','native trial','cell trial','cell consistency','cell aggregate','native aggregate','native refusal','trial coverage','cell totals'}
    try:
        if q.log.stat().st_size>16*1024*1024:raise ValueError('log size')
        with q.log.open(encoding='utf-8',errors='replace') as f:result=verify(f,second=q.second,third=q.third,control=q.control)
    except (ValueError,OSError) as ex:
        print('FORMATTER_NESTED_LOG verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'input'));return 1
    print(*result,sep='\n');return 0
if __name__=='__main__':raise SystemExit(main())
