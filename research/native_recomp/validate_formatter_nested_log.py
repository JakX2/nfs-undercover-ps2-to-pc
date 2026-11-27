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

ARRIVAL_TRIAL=re.compile(r'FORMATTER_ARRIVAL_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 transfer_executed=1 destination_arrival=1 destination_body=0 deferred=1 reply=0 visits=77')
ARRIVAL_TOTAL='FORMATTER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 transfer_executed=8 destination_arrival=8 destination_body=0 deferred=8 reply=0 visits=616 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

POST_CTR_TRIAL=re.compile(r'FORMATTER_POST_CTR_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=8 stores=13 nonvolatile=3 authenticated_loads=(5) local_transfer=1 stack_stop=1 unresolved_load=0 deferred=1 reply=0 visits=84')
POST_CTR_TOTAL=re.compile(r'FORMATTER_POST_CTR_NATIVE owner=1 trials=8 native_prefix=8 loads=64 stores=104 nonvolatile=24 authenticated_loads=([0-9]{2}) local_transfer=8 stack_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=672 ios_steps=5 fallback=0 complete_image=0 boot_verified=0')

PARTIAL_TRIAL=re.compile(r'FORMATTER_PARTIAL_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 instruction_stop=1 deferred=1 reply=0 visits=95')
PARTIAL_TOTAL='FORMATTER_PARTIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 instruction_stop=8 deferred=8 reply=0 visits=760 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

SPECIAL_TRIAL=re.compile(r'FORMATTER_SPECIAL_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 instruction_stop=1 deferred=1 reply=0 visits=96')
SPECIAL_TOTAL='FORMATTER_SPECIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 instruction_stop=8 deferred=8 reply=0 visits=768 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

RELEASE_TRIAL=re.compile(r'FORMATTER_RELEASE_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 return_stop=1 return_executed=0 deferred=1 reply=0 visits=97')
RELEASE_TOTAL='FORMATTER_RELEASE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 return_stop=8 return_executed=0 deferred=8 reply=0 visits=776 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

RETURN_TRIAL=re.compile(r'FORMATTER_RETURN_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_arrival=1 caller_body=0 caller_guard=1 deferred=1 reply=0 visits=98')
RETURN_TOTAL='FORMATTER_RETURN_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_arrival=8 caller_body=0 caller_guard=8 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

CALLER_ARRIVAL_TRIAL=re.compile(r'FORMATTER_CALLER_ARRIVAL_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_label=1 caller_body=0 caller_guard=0 deferred=1 reply=0 visits=98')
CALLER_ARRIVAL_TOTAL='FORMATTER_CALLER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_label=8 caller_body=0 caller_guard=0 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

CALLER_BYTE_TRIAL=re.compile(r'FORMATTER_CALLER_BYTE_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits=99')
CALLER_BYTE_TOTAL='FORMATTER_CALLER_BYTE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits=792 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'

def integer_markers(count):
    if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=8:raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_INTEGERS_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={99+count}')
    total=f'FORMATTER_CALLER_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={792+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_INTEGERS',trial,total

def branch_markers(count):
    if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=8:raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_BRANCH_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branch=1 fallthrough=1 alternate_guard=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={100+count}')
    total=f'FORMATTER_CALLER_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=8 fallthrough=8 alternate_guard=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={800+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_BRANCH',trial,total

def second_branch_markers(count):
    if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=8:raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_SECOND_BRANCH_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=2 fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={101+count}')
    total=f'FORMATTER_CALLER_SECOND_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=16 fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={808+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_SECOND_BRANCH',trial,total

def post_integer_markers(count,post):
    if any(not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=8 for n in (count,post)):raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_POST_INTEGERS_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=2 post_integers={post} fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={101+count+post}')
    total=f'FORMATTER_CALLER_POST_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=16 post_integers={8*post} fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={808+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_POST_INTEGERS',trial,total

def third_branch_markers(count,post):
    if any(not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=8 for n in (count,post)):raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_THIRD_BRANCH_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=3 post_integers={post} fallthrough=2 taken=1 alternate_checks=3 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={102+count+post}')
    total=f'FORMATTER_CALLER_THIRD_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=24 post_integers={8*post} fallthrough=16 taken=8 alternate_checks=24 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={816+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_THIRD_BRANCH',trial,total

def fourth_branch_markers(count,post):
    if any(not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=8 for n in (count,post)):raise ValueError('native integer count')
    trial=re.compile(f'FORMATTER_CALLER_FOURTH_BRANCH_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=4 post_integers={post} fallthrough=3 taken=1 alternate_checks=4 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={103+count+post}')
    total=f'FORMATTER_CALLER_FOURTH_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=32 post_integers={8*post} fallthrough=24 taken=8 alternate_checks=32 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={824+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return 'FORMATTER_CALLER_FOURTH_BRANCH',trial,total

def mixed_markers(count,post,integers,taken,fallthrough,*,byte=False):
    if any(not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=8 for n in (count,post)):raise ValueError('native integer count')
    if any(not isinstance(n,int) or isinstance(n,bool) or not 0<=n<=16 for n in (integers,taken,fallthrough)) or not 1<=integers+taken+fallthrough<=16:raise ValueError('native mixed count')
    tag='FORMATTER_CALLER_MIXED_BYTE' if byte else 'FORMATTER_CALLER_MIXED'
    trial_extra=' mixed_byte_verified=1' if byte else ''
    total_extra=' mixed_bytes_verified=8' if byte else ''
    trial=re.compile(f'{tag}_TRIAL n=([0-7]) native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=4 post_integers={post} mixed_integers={integers} mixed_taken={taken} mixed_fallthrough={fallthrough}{trial_extra} next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={103+count+post+integers+taken+fallthrough+int(byte)}')
    total=f'{tag}_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=32 post_integers={8*post} mixed_integers={8*integers} mixed_taken={8*taken} mixed_fallthrough={8*fallthrough}{total_extra} next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={824+8*(count+post+integers+taken+fallthrough+int(byte))} ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return tag,trial,total

def verify(lines,*,second=False,third=False,control=False,arrival=False,post_ctr=False,partial=False,special=False,release=False,return_mode=False,caller_arrival=False,caller_byte=False,caller_integers=False,caller_branch=False,caller_second_branch=False,caller_post_integers=False,caller_third_branch=False,caller_fourth_branch=False,caller_mixed=False,caller_mixed_byte=False,integer_count=None,post_integer_count=None,mixed_integers=None,mixed_taken=None,mixed_fallthrough=None):
    if sum((second,third,control,arrival,post_ctr,partial,special,release,return_mode,caller_arrival,caller_byte,caller_integers,caller_branch,caller_second_branch,caller_post_integers,caller_third_branch,caller_fourth_branch,caller_mixed,caller_mixed_byte))>1:raise ValueError('native mode')
    mixed_mode=caller_mixed or caller_mixed_byte
    tag,trial,total=markers(second)
    if third:tag,trial,total='FORMATTER_THIRD',THIRD_TRIAL,None
    if control:tag,trial,total='FORMATTER_CONTROL',CONTROL_TRIAL,CONTROL_TOTAL
    if arrival:tag,trial,total='FORMATTER_ARRIVAL',ARRIVAL_TRIAL,ARRIVAL_TOTAL
    if post_ctr:tag,trial,total='FORMATTER_POST_CTR',POST_CTR_TRIAL,None
    if partial:tag,trial,total='FORMATTER_PARTIAL',PARTIAL_TRIAL,PARTIAL_TOTAL
    if special:tag,trial,total='FORMATTER_SPECIAL',SPECIAL_TRIAL,SPECIAL_TOTAL
    if release:tag,trial,total='FORMATTER_RELEASE',RELEASE_TRIAL,RELEASE_TOTAL
    if return_mode:tag,trial,total='FORMATTER_RETURN',RETURN_TRIAL,RETURN_TOTAL
    if caller_arrival:tag,trial,total='FORMATTER_CALLER_ARRIVAL',CALLER_ARRIVAL_TRIAL,CALLER_ARRIVAL_TOTAL
    if caller_byte:tag,trial,total='FORMATTER_CALLER_BYTE',CALLER_BYTE_TRIAL,CALLER_BYTE_TOTAL
    if caller_integers:tag,trial,total=integer_markers(integer_count)
    elif caller_branch:tag,trial,total=branch_markers(integer_count)
    elif caller_second_branch:tag,trial,total=second_branch_markers(integer_count)
    elif caller_post_integers:tag,trial,total=post_integer_markers(integer_count,post_integer_count)
    elif caller_third_branch:tag,trial,total=third_branch_markers(integer_count,post_integer_count)
    elif caller_fourth_branch:tag,trial,total=fourth_branch_markers(integer_count,post_integer_count)
    elif mixed_mode:tag,trial,total=mixed_markers(integer_count,post_integer_count,mixed_integers,mixed_taken,mixed_fallthrough,byte=caller_mixed_byte)
    elif integer_count is not None:raise ValueError('native mode')
    if not (caller_post_integers or caller_third_branch or caller_fourth_branch or mixed_mode) and post_integer_count is not None:raise ValueError('native mode')
    if not mixed_mode and any(n is not None for n in (mixed_integers,mixed_taken,mixed_fallthrough)):raise ValueError('native mode')
    details=None;third_total=None
    trials=set();cells={};aggregate=None;native=False
    for line in lines:
        line=line.rstrip('\r\n')
        if line.startswith(tag+'_TRIAL '):
            m=trial.fullmatch(line)
            if not m or int(m[1]) in trials:raise ValueError('native trial')
            if third or post_ctr:
                current=tuple(map(int,m.groups()[1:]))
                if details is not None and details!=current:raise ValueError('native trial details')
                details=current
            trials.add(int(m[1]))
        elif line.startswith('FORMATTER_NESTED_CELL_TRIAL '):
            if control or arrival or post_ctr or partial or special or release or return_mode or caller_arrival or caller_byte or caller_integers or caller_branch or caller_second_branch or caller_post_integers or caller_third_branch or caller_fourth_branch or mixed_mode:raise ValueError('unexpected cell observation')
            m=CELL.fullmatch(line)
            if not m or int(m[1]) in cells:raise ValueError('cell trial')
            v=tuple(map(int,m.groups()[1:]))
            if v[2] and v[0]!=v[1] or v[0] and v[1] and not v[2]:
                raise ValueError('cell consistency')
            cells[int(m[1])]=v
        elif line.startswith('FORMATTER_NESTED_CELL_NATIVE '):
            if control or arrival or post_ctr or partial or special or release or return_mode or caller_arrival or caller_byte or caller_integers or caller_branch or caller_second_branch or caller_post_integers or caller_third_branch or caller_fourth_branch or mixed_mode:raise ValueError('unexpected cell observation')
            m=CELL_TOTAL.fullmatch(line)
            if not m or aggregate is not None:raise ValueError('cell aggregate')
            aggregate=tuple(map(int,m.groups()))
        elif line.startswith(tag+'_NATIVE '):
            if native:raise ValueError('native aggregate')
            if third or post_ctr:
                m=(POST_CTR_TOTAL if post_ctr else THIRD_TOTAL).fullmatch(line)
                if not m:raise ValueError('native aggregate')
                third_total=tuple(map(int,m.groups()))
                total=line
            elif line!=total:raise ValueError('native aggregate')
            native=True
        elif line.startswith('FORMATTER_NESTED_REFUSAL '):
            raise ValueError('native refusal')
    if trials!=set(range(8)) or not native or (not (control or arrival or post_ctr or partial or special or release or return_mode or caller_arrival or caller_byte or caller_integers or caller_branch or caller_second_branch or caller_post_integers or caller_third_branch or caller_fourth_branch or mixed_mode) and set(cells)!=trials):
        raise ValueError('trial coverage')
    if (third or post_ctr) and third_total!=tuple(8*v for v in details):raise ValueError('native totals')
    if control or arrival or post_ctr or partial or special or release or return_mode or caller_arrival or caller_byte or caller_integers or caller_branch or caller_second_branch or caller_post_integers or caller_third_branch or caller_fourth_branch or mixed_mode:return (total,)
    if aggregate!=tuple(sum(v[i] for v in cells.values()) for i in range(3)):
        raise ValueError('cell totals')
    return (f'FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match={aggregate[0]} live_match={aggregate[1]} sample_equal={aggregate[2]} endpoint_only=1 guest_loads=0 guest_writes=0',total)

def main():
    a=argparse.ArgumentParser();a.add_argument('log',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--second',action='store_true');m.add_argument('--third',action='store_true');m.add_argument('--control',action='store_true');m.add_argument('--arrival',action='store_true');m.add_argument('--post-ctr',action='store_true');m.add_argument('--partial',action='store_true');m.add_argument('--special',action='store_true');m.add_argument('--release',action='store_true');m.add_argument('--return',dest='return_mode',action='store_true');m.add_argument('--caller-arrival',action='store_true');m.add_argument('--caller-byte',action='store_true');m.add_argument('--caller-integers',action='store_true');m.add_argument('--caller-branch',action='store_true');m.add_argument('--caller-second-branch',action='store_true');m.add_argument('--caller-post-integers',action='store_true');m.add_argument('--caller-third-branch',action='store_true');m.add_argument('--caller-fourth-branch',action='store_true');m.add_argument('--caller-mixed',action='store_true');m.add_argument('--caller-mixed-byte',action='store_true');a.add_argument('--integer-count',type=int);a.add_argument('--post-integer-count',type=int);a.add_argument('--mixed-integers',type=int);a.add_argument('--mixed-taken',type=int);a.add_argument('--mixed-fallthrough',type=int);q=a.parse_args()
    safe={'unexpected cell observation','native mode','native integer count','native mixed count','native trial details','native totals','native trial','cell trial','cell consistency','cell aggregate','native aggregate','native refusal','trial coverage','cell totals'}
    try:
        if q.log.stat().st_size>16*1024*1024:raise ValueError('log size')
        with q.log.open(encoding='utf-8',errors='replace') as f:result=verify(f,second=q.second,third=q.third,control=q.control,arrival=q.arrival,post_ctr=q.post_ctr,partial=q.partial,special=q.special,release=q.release,return_mode=q.return_mode,caller_arrival=q.caller_arrival,caller_byte=q.caller_byte,caller_integers=q.caller_integers,caller_branch=q.caller_branch,caller_second_branch=q.caller_second_branch,caller_post_integers=q.caller_post_integers,caller_third_branch=q.caller_third_branch,caller_fourth_branch=q.caller_fourth_branch,caller_mixed=q.caller_mixed,caller_mixed_byte=q.caller_mixed_byte,integer_count=q.integer_count,post_integer_count=q.post_integer_count,mixed_integers=q.mixed_integers,mixed_taken=q.mixed_taken,mixed_fallthrough=q.mixed_fallthrough)
    except (ValueError,OSError) as ex:
        print('FORMATTER_NESTED_LOG verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'input'));return 1
    print(*result,sep='\n');return 0
if __name__=='__main__':raise SystemExit(main())
