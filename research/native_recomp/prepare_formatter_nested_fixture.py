#!/usr/bin/env python3
"""Private finite nested fixture. The unresolved load is an observed stop."""
import argparse,struct
from pathlib import Path
from private_plan_cache import plan_cache_scope
from prepare_formatter_nested_contract import plan as nested_plan
from prepare_formatter_second_contract import plan as second_plan
from prepare_formatter_third_contract import plan as third_plan
from prepare_formatter_control_contract import plan as control_plan
from prepare_formatter_post_ctr_contract import plan as post_ctr_plan
from prepare_formatter_partial_native_contract import plan as partial_plan
from prepare_formatter_special_contract import plan as special_plan
from prepare_formatter_release_contract import plan as release_plan
from prepare_formatter_return_contract import plan as return_plan
from prepare_formatter_caller_arrival_contract import plan as caller_plan
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan
from prepare_formatter_caller_branch_contract import plan as branch_plan
from prepare_formatter_caller_second_branch_contract import plan as second_branch_plan
from prepare_formatter_caller_post_integer_contract import plan as post_integer_plan
from prepare_formatter_caller_third_branch_contract import plan as third_branch_plan
from prepare_formatter_caller_fourth_branch_contract import plan as fourth_branch_plan
from prepare_formatter_caller_mixed_contract import plan as mixed_plan
from prepare_formatter_caller_mixed_byte_contract import plan as mixed_byte_plan
from audit_formatter_caller_after_mixed_byte import plan as post_mixed_plan
from prepare_formatter_caller_stack_move_contract import plan as stack_move_plan
from audit_formatter_caller_after_stack_move import plan as final_integer_plan
from prepare_formatter_caller_next_entry_contract import plan as next_entry_plan
from prepare_formatter_next_entry_report_byte_contract import plan as report_byte_plan
from prepare_formatter_report_compare_fixture import (
    plan as report_compare_plan, promote as promote_report_compare,
    render as render_report_compare,
)
from prepare_formatter_report_stack_copy_fixture import (
    plan as report_copy_plan, render as render_report_copy,
)
from prepare_formatter_report_immediate_fixture import (
    plan as report_immediate_plan, render as render_report_immediate,
)
from prepare_formatter_report_signext_fixture import (
    plan as report_signext_plan, render as render_report_signext,
)
from audit_formatter_partial_copy import boundary_shape
from prepare_formatter_continuation_plan import plan as continuation_plan
from prepare_formatter_continuation_fixture import scope as continuation_scope
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from formatter_local_ctr_native import verify_ctr_body,verify_blr_body,ensure_ctr_resume,analyzer_local_edge,trace_ctr_destination,verify_forward_branch_body
from prepare_v680_si_helper import exact_function,verify_direct

def plan(d,e,*,second=False,third=False,control=False):
    if sum((second,third,control))>1:raise ValueError('nested fixture mode')
    prior=continuation_plan(d,e,details=True)
    first=nested_plan(d,e,previous=prior[1])
    if not (second or third or control):return prior,first
    two=second_plan(d,e,previous=prior[1],first=first)
    if second:return prior,two
    three=third_plan(d,e,previous=prior[1],second=two)
    return prior,control_plan(d,e,previous=prior[1],third=three) if control else three

def render(contract,*,stack_boundary=False,instruction_boundary=False,special_boundary=False,release_boundary=False):
    if release_boundary and (not instruction_boundary or special_boundary):raise ValueError('nested fixture instruction boundary')
    if special_boundary and not instruction_boundary:raise ValueError('nested fixture instruction boundary')
    _,fields,rows,access,slots,known=contract
    root,caller,target,word,frame,addr,width,*control=fields
    if control and (len(control)!=3 or addr or width or word!=0x4e800420):raise ValueError('nested fixture control contract')
    if stack_boundary and (control or width!=4 or addr%4 or not -44<=addr<=-4):raise ValueError('nested fixture stack boundary')
    if instruction_boundary and (stack_boundary or control or addr or width):raise ValueError('nested fixture instruction boundary')
    namespace='formatter_release_private' if release_boundary else 'formatter_special_private' if special_boundary else 'formatter_partial_private' if instruction_boundary else 'formatter_post_ctr_private' if stack_boundary else 'formatter_nested_private'
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+fmt((root,pc,w))+'}' for pc,w in rows)
    values={pc:int.from_bytes(data,'big') for pc,_,data in known}
    if len(values)!=len(known) or any(sum(site[0]==pc and not site[3] and not site[4] and site[2]==at and site[1]==len(data) for site in access)!=1 for pc,at,data in known):
        raise ValueError('nested fixture data contract')
    if any(not stack and not write and pc not in values for pc,_,_,stack,write in access):
        raise ValueError('nested fixture data contract')
    ar=','.join('undercover::wii::ScFormatterAccess{'+fmt((pc,n))+','+str(at)+','+str(stack).lower()+','+str(write).lower()+
                (','+fmt((values[pc],)) if pc in values else '')+'}' for pc,n,at,stack,write in access)
    sr=','.join('undercover::wii::StmFinalSlot{'+str(at)+','+str(reg)+'u}' for at,reg in slots)
    boundary='{0u,0u,false,0,true}' if instruction_boundary else '{0u,4u,true,'+str(addr)+'}' if stack_boundary else '{'+fmt((addr,width))+'}'
    return ('#pragma once\n#include "wii_post_stm_sc_formatter.h"\nnamespace '+namespace+' {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> path'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::ScFormatterAccess,{len(access)}> accesses'+'{'+ar+'};\n'
        f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+sr+'};\n'
        'inline constexpr undercover::wii::ScFormatterExpectation expected{'+fmt((root,caller,target,word,frame))+',path,accesses,slots,'+boundary+(',{'+fmt(control)+'}' if control else '')+'};\n}\n')

def render_return(contract):
    owner,caller,guard,_,_=contract
    if owner==caller or owner&3 or caller&3 or caller<=owner or guard!=GUARD:
        raise ValueError('nested fixture return guard')
    return ('namespace formatter_return_private {\n'
            f'inline constexpr uint32_t owner=0x{owner:08x}u,caller=0x{caller:08x}u,guard=0x{guard:08x}u;\n'
            '}\n')

def render_caller(info):
    owner,caller,word,call=info
    if owner==caller or owner&3 or caller&3 or caller<=owner or word==GUARD or call>>26!=18 or call&3!=1:
        raise ValueError('nested fixture caller geometry')
    return ('namespace formatter_caller_private {\n'
            f'inline constexpr uint32_t owner=0x{owner:08x}u,caller=0x{caller:08x}u,word=0x{word:08x}u,call=0x{call:08x}u;\n'
            '}\n')

def expand_caller(old,blocks,info):
    owner,caller,word,call=info
    if set(old)!=set(blocks) or owner not in old or caller<=owner or caller&3 or owner&3:
        raise ValueError('nested fixture caller geometry')
    i=(caller-owner)//4
    body=old[owner];out=blocks[owner]
    if not 1<=i<len(body) or body[i]!=GUARD or body[i-1]!=call or word==GUARD:
        raise ValueError('nested fixture caller geometry')
    expected=list(body)+[GUARD]*max(0,i+2-len(body));expected[i]=word
    if tuple(expected)!=out or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_byte(info):
    owner,caller,word,call,offset,value,next_pc,next_word=info
    if next_pc!=caller+4 or next_word==GUARD or not 8<=offset<704 or not 0<=value<=255:
        raise ValueError('nested fixture caller byte')
    return ('namespace formatter_caller_byte_private {\n'
            f'inline constexpr int32_t offset={offset};\n'
            f'inline constexpr uint8_t value={value}u;\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            '}\n')

def expand_byte(old,blocks,info):
    owner,caller,word,call,offset,value,next_pc,next_word=info
    render_byte(info)
    if set(old)!=set(blocks) or owner not in old or caller<=owner or caller&3 or owner&3:
        raise ValueError('nested fixture caller byte')
    i=(caller-owner)//4
    body=old[owner]
    if not 1<=i<len(body)-1 or body[i-1]!=call or body[i]!=word or body[i+1]!=GUARD:
        raise ValueError('nested fixture caller byte')
    expected=list(body)+[GUARD]*max(0,i+3-len(body));expected[i+1]=next_word
    if tuple(expected)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller byte expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_integers(contract,*,post_branch=False):
    _,rows,end_pc,end_word=contract
    if not 1<=len(rows)<=8 or end_pc!=rows[0][0]+4*len(rows) or end_word==GUARD:
        raise ValueError('nested fixture caller integers')
    lines=['namespace formatter_caller_post_integer_private {' if post_branch else 'namespace formatter_caller_integer_private {']
    entries=[]
    for i,(pc,w,inputs) in enumerate(rows):
        if pc&3 or pc!=rows[0][0]+4*i or w==GUARD or len(inputs)>3 or len({r for r,_ in inputs})!=len(inputs) or any(not 0<=r<32 or not 0<=v<=0xffffffff for r,v in inputs):
            raise ValueError('nested fixture caller integers')
        values=','.join(f'undercover::wii::CallerIntegerInput{{{r}u,0x{v:08x}u}}' for r,v in inputs)
        lines.append(f'inline constexpr std::array<undercover::wii::CallerIntegerInput,{len(inputs)}> inputs_{i}'+'{'+values+'};')
        entries.append(f'undercover::wii::ScCallerIntegerStep{{0x{pc:08x}u,0x{w:08x}u,inputs_{i}}}')
    lines.append(f'inline constexpr std::array<undercover::wii::ScCallerIntegerStep,{len(rows)}> path'+'{'+','.join(entries)+'};')
    lines.append(f'inline constexpr uint32_t end_pc=0x{end_pc:08x}u,end_word=0x{end_word:08x}u;')
    return '\n'.join(lines+['}',''])

def expand_integers(old,contract,info):
    blocks,rows,end_pc,end_word=contract
    owner,_,_,_,_,_,start,w=info
    render_integers(contract)
    if set(old)!=set(blocks) or owner not in old or start<=owner or start&3 or rows[0][:2]!=(start,w):
        raise ValueError('nested fixture caller integers')
    i=(start-owner)//4;end=(end_pc-owner)//4;body=old[owner]
    if not 0<=i<len(body)-1 or body[i]!=w:
        raise ValueError('nested fixture caller integers')
    # Only the actual newly admitted labels and their next guard must be
    # empty. Other authenticated labels from earlier, disjoint paths stay.
    if any(body[j]!=GUARD for j in range(i+1,min(end+2,len(body)))):
        raise ValueError('nested fixture caller integer overlap')
    expected=list(body)+[GUARD]*max(0,end+2-len(body))
    for j,(_,word,_) in enumerate(rows):expected[i+j]=word
    expected[end]=end_word
    if tuple(expected)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller integer expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_branch(contract,*,second=False,third=False,fourth=False):
    if sum((second,third,fourth))>1:raise ValueError('nested fixture caller branch')
    _,(owner,size,pc,w,taken,chosen,cword,other)=contract
    if owner&3 or not 8<=size<=65536 or size%4 or not isinstance(taken,bool) or w>>26 not in (16,18) or w&3 or cword==GUARD:
        raise ValueError('nested fixture caller branch')
    if any(a&3 or not owner<=a<owner+size for a in (pc,chosen,other)) or min(chosen,other)!=pc+4 or max(chosen,other)<=pc+4:
        raise ValueError('nested fixture caller branch')
    if w>>26==16 and not (w>>21)&4 or w>>26==18 and not taken:
        raise ValueError('nested fixture caller branch')
    n=16 if w>>26==16 else 26
    disp=w&((1<<n)-4);disp=(disp^(1<<(n-1)))-(1<<(n-1))
    if pc+disp!=(chosen if taken else other):raise ValueError('nested fixture caller branch')
    name='formatter_caller_fourth_branch_private' if fourth else 'formatter_caller_third_branch_private' if third else 'formatter_caller_second_branch_private' if second else 'formatter_caller_branch_private'
    return (f'namespace {name} {{\n'
            f'inline constexpr uint32_t owner=0x{owner:08x}u,owner_size={size}u,pc=0x{pc:08x}u,word=0x{w:08x}u;\n'
            f'inline constexpr bool taken={str(taken).lower()};\n'
            f'inline constexpr uint32_t next_pc=0x{chosen:08x}u,next_word=0x{cword:08x}u,other_pc=0x{other:08x}u;\n'
            '}\n')

def expand_branch(old,contract,integer):
    blocks,(owner,size,pc,w,taken,chosen,cword,other)=contract
    render_branch(contract)
    if set(old)!=set(blocks) or owner not in old or integer[2:]!=(pc,w):
        raise ValueError('nested fixture caller branch')
    i,j,k=((a-owner)//4 for a in (pc,chosen,other));body=old[owner]
    if not 0<=i<len(body) or body[i]!=w or j<len(body) and body[j]!=GUARD or k<len(body) and body[k]!=GUARD:
        raise ValueError('nested fixture caller branch')
    expected=list(body)+[GUARD]*max(0,max(j+1,k)+1-len(body));expected[j]=cword
    if len(expected)*4>size or tuple(expected)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller branch expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def expand_second_branch(old,first,second):
    _,a=first;_,b=second
    if a[:2]!=b[:2] or a[4] or not b[4] or a[5:7]!=b[2:4] or a[7]==b[5]:
        raise ValueError('nested fixture caller second branch')
    expanded=expand_branch(old,second,(None,(),a[5],a[6]))
    if expanded[a[0]][(a[7]-a[0])//4]!=GUARD:
        raise ValueError('nested fixture caller second branch')
    return expanded

def expand_post_integers(old,contract,first,second):
    blocks,rows,end,w=contract;_,info=second
    owner,size,_,_,_,start,start_word,other=info
    render_integers(contract,post_branch=True)
    if set(old)!=set(blocks) or owner not in old or rows[0][:2]!=(start,start_word) or not owner<start<=end<owner+size:
        raise ValueError('nested fixture caller post integers')
    i=(start-owner)//4;j=(end-owner)//4;body=old[owner]
    if not 0<=i<len(body) or body[i]!=start_word or any(body[k]!=GUARD for k in range(i+1,min(j+2,len(body)))):
        raise ValueError('nested fixture caller post integer overlap')
    if any(start<=a<=end for a in (first[1][7],other)):
        raise ValueError('nested fixture caller post integer guard')
    expected=list(body)+[GUARD]*max(0,j+2-len(body))
    for k,(_,word,_) in enumerate(rows):expected[i+k]=word
    expected[j]=w
    if len(expected)*4>size or tuple(expected)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller post integer expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def expand_third_branch(old,first,second,post,third):
    _,a=first;_,b=second;_,c=third
    if a[:2]!=b[:2] or b[:2]!=c[:2] or c[4] or c[2:4]!=post[2:] or c[5] in (a[7],b[7]):
        raise ValueError('nested fixture caller third branch')
    expanded=expand_branch(old,third,post)
    if any(expanded[c[0]][(v[7]-c[0])//4]!=GUARD for v in (a,b)):
        raise ValueError('nested fixture caller third branch')
    return expanded

def expand_fourth_branch(old,first,second,third,fourth):
    _,a=first;_,b=second;_,c=third;_,d=fourth
    if any(v[:2]!=d[:2] for v in (a,b,c)) or c[5:7]!=d[2:4] or d[5] in (a[7],b[7],c[7]):
        raise ValueError('nested fixture caller fourth branch')
    expanded=expand_branch(old,fourth,(None,(),c[5],c[6]))
    if any(expanded[d[0]][(v[7]-d[0])//4]!=GUARD for v in (a,b,c)):
        raise ValueError('nested fixture caller fourth branch')
    return expanded

def render_mixed(contract):
    _,rows,end,w=contract
    if not 1<=len(rows)<=16 or end&3 or w==GUARD:raise ValueError('nested fixture caller mixed')
    lines=['namespace formatter_caller_mixed_private {'];entries=[]
    for i,(pc,word,inputs,nxt,other,taken) in enumerate(rows):
        if pc&3 or nxt&3 or nxt<=pc or nxt!=(rows[i+1][0] if i+1<len(rows) else end) or word==GUARD:
            raise ValueError('nested fixture caller mixed')
        if len(inputs)>3 or len({r for r,_ in inputs})!=len(inputs) or any(not 0<=r<32 or not 0<=v<=0xffffffff for r,v in inputs):
            raise ValueError('nested fixture caller mixed')
        if other is None:
            if taken is not None or nxt!=pc+4:raise ValueError('nested fixture caller mixed')
        else:
            if inputs or not isinstance(taken,bool) or other&3 or other==nxt:
                raise ValueError('nested fixture caller mixed')
            # Check the exact encoded forward edge, independently of planner.
            render_branch((None,(pc,max(nxt,other)-pc+4,pc,word,taken,nxt,w,other)))
        values=','.join(f'undercover::wii::CallerIntegerInput{{{r}u,0x{v:08x}u}}' for r,v in inputs)
        lines.append(f'inline constexpr std::array<undercover::wii::CallerIntegerInput,{len(inputs)}> inputs_{i}'+'{'+values+'};')
        entries.append(f'undercover::wii::ScCallerMixedStep{{0x{pc:08x}u,0x{word:08x}u,inputs_{i},0x{nxt:08x}u,0x{(other or 0):08x}u,{str(bool(taken)).lower()}}}')
    lines.append(f'inline constexpr std::array<undercover::wii::ScCallerMixedStep,{len(rows)}> path'+'{'+','.join(entries)+'};')
    lines.append(f'inline constexpr uint32_t end_pc=0x{end:08x}u,end_word=0x{w:08x}u;')
    return '\n'.join(lines+['}',''])

def expand_mixed(old,contract,branches):
    if len(branches)!=4:raise ValueError('nested fixture caller mixed')
    infos=[b[1] for b in branches];owner,size=infos[-1][:2]
    if any(v[:2]!=(owner,size) for v in infos):raise ValueError('nested fixture caller mixed')
    return expand_mixed_segment(old,contract,owner,size,infos[-1][5:7],{v[7] for v in infos})

def expand_mixed_segment(old,contract,owner,size,entry,guards):
    blocks,rows,end,w=contract
    render_mixed(contract)
    if set(old)!=set(blocks) or owner not in old or rows[0][:2]!=entry:
        raise ValueError('nested fixture caller mixed')
    body=old[owner];out=list(body);guards=set(guards)
    def inside(a):return a is not None and not a&3 and owner<=a<owner+size
    def at(a):
        j=(a-owner)//4
        return out[j] if j<len(out) else GUARD
    def fill(a,v):
        j=(a-owner)//4
        out.extend([GUARD]*max(0,j+1-len(out)));out[j]=v
    if any(not inside(a) or at(a)!=GUARD for a in guards):raise ValueError('nested fixture caller mixed guard')
    for i,(pc,word,_,nxt,other,_) in enumerate(rows):
        if not inside(pc) or not inside(nxt) or at(pc)!=word or nxt in guards or at(nxt)!=GUARD:
            raise ValueError('nested fixture caller mixed overlap')
        if other is not None:
            if not inside(other) or at(other)!=GUARD:raise ValueError('nested fixture caller mixed guard')
            fill(other,GUARD);guards.add(other)
        fill(nxt,rows[i+1][1] if i+1<len(rows) else w)
        if (nxt-owner)//4+1>=len(out):out.append(GUARD)
    if len(out)*4>size or tuple(out)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller mixed expansion')
    if any(at(a)!=GUARD for a in guards):raise ValueError('nested fixture caller mixed guard')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def expand(old,blocks,live,root):
    if set(blocks)!=set(old) or root not in old or any(live.get(a)!=ws for a,ws in old.items()):
        raise ValueError('nested fixture predecessor')
    if any(blocks[a]!=ws for a,ws in old.items() if a!=root) or len(blocks[root])<=len(old[root]):
        raise ValueError('nested fixture expansion')
    result={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in result.items()})
    return result

def render_mixed_byte(contract):
    _,(owner,pc,w,offset,value,next_pc,next_word)=contract
    rt=(w>>21)&31
    if owner&3 or pc&3 or pc<owner or next_pc!=pc+4 or next_word==GUARD or not 8<=offset<704 or not 0<=value<=255:
        raise ValueError('nested fixture caller mixed byte')
    if rt not in (0,*range(3,13)) or not (w>>26==34 or w>>26==31 and (w>>1)&1023==87 and not w&1):
        raise ValueError('nested fixture caller mixed byte')
    return ('namespace formatter_caller_mixed_byte_private {\n'
            f'inline constexpr int32_t offset={offset};\n'
            f'inline constexpr uint8_t value={value}u;\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            '}\n')

def expand_mixed_byte(old,mixed,contract,branches):
    blocks,(owner,pc,w,_,_,next_pc,next_word)=contract
    render_mixed_byte(contract)
    if len(branches)!=4 or set(old)!=set(blocks) or old!=mixed[0] or mixed[2:]!=(pc,w) or owner not in old:
        raise ValueError('nested fixture caller mixed byte')
    infos=[b[1] for b in branches];size=infos[-1][1]
    if any(v[:2]!=(owner,size) for v in infos) or next_pc+8>owner+size:
        raise ValueError('nested fixture caller mixed byte')
    guards={v[7] for v in infos}|{row[4] for row in mixed[1] if row[4] is not None}
    body=old[owner];i=(pc-owner)//4
    if i>=len(body) or body[i]!=w or next_pc in guards or any(j<len(body) and body[j]!=GUARD for j in (i+1,i+2)):
        raise ValueError('nested fixture caller mixed byte overlap')
    if any(a&3 or not owner<=a<owner+4*len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('nested fixture caller mixed byte guard')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=next_word
    if len(out)*4>size or tuple(out)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller mixed byte expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_post_mixed(contract):
    return render_mixed(contract).replace('namespace formatter_caller_mixed_private','namespace formatter_caller_post_mixed_private')

def expand_post_mixed(old,byte,mixed,contract,branches):
    if len(branches)!=4 or old!=byte[0]:raise ValueError('nested fixture caller post mixed')
    infos=[b[1] for b in branches];owner,size=infos[-1][:2]
    if byte[1][0]!=owner or byte[1][1:3]!=mixed[2:] or any(v[:2]!=(owner,size) for v in infos):
        raise ValueError('nested fixture caller post mixed')
    guards={v[7] for v in infos}|{row[4] for row in mixed[1] if row[4] is not None}
    return expand_mixed_segment(old,contract,owner,size,byte[1][-2:],guards)

def render_stack_move(contract):
    _,(owner,size,pc,w,offset,next_pc,next_word)=contract
    rs,ra,rb=(w>>21)&31,(w>>16)&31,(w>>11)&31
    if owner&3 or pc&3 or not 8<=size<=65536 or size&3 or not owner<=pc<next_pc<owner+size-4 or next_pc!=pc+4 or next_word==GUARD:
        raise ValueError('nested fixture caller stack move')
    if w>>26!=31 or (w>>1)&1023!=444 or w&1 or rs!=rb or ra==rs or ra not in (0,*range(3,13)) or not -0x01800000<offset<0x01800000:
        raise ValueError('nested fixture caller stack move')
    return ('namespace formatter_caller_stack_move_private {\n'
            f'inline constexpr int32_t offset={offset};\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            '}\n')

def expand_stack_move(old,post_mixed,mixed,contract,branches):
    blocks,(owner,size,pc,w,_,next_pc,next_word)=contract
    render_stack_move(contract)
    if len(branches)!=4 or old!=post_mixed[0] or post_mixed[2:]!=(pc,w) or set(old)!=set(blocks) or owner not in old:
        raise ValueError('nested fixture caller stack move')
    infos=[b[1] for b in branches]
    if any(v[:2]!=(owner,size) for v in infos):raise ValueError('nested fixture caller stack move')
    guards={v[7] for v in infos}|{row[4] for rows in (mixed[1],post_mixed[1]) for row in rows if row[4] is not None}
    body=old[owner];i=(pc-owner)//4
    if i>=len(body) or body[i]!=w or next_pc in guards or any(j<len(body) and body[j]!=GUARD for j in (i+1,i+2)):
        raise ValueError('nested fixture caller stack move overlap')
    if any(a&3 or not owner<=a<owner+4*len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('nested fixture caller stack move guard')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=next_word
    if len(out)*4>size or tuple(out)!=blocks[owner] or any(blocks[a]!=ws for a,ws in old.items() if a!=owner):
        raise ValueError('nested fixture caller stack move expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_final_integer(contract):
    _,rows,end,w=contract
    if len(rows)!=1 or rows[0][1]>>26!=14 or rows[0][4] is not None or len(rows[0][2])>1 or w>>26!=18 or w&3!=1:
        raise ValueError('nested fixture caller final integer')
    return render_mixed(contract).replace('namespace formatter_caller_mixed_private','namespace formatter_caller_final_integer_private')

def expand_final_integer(old,move,mixed,post_mixed,contract,branches):
    render_final_integer(contract)
    if len(branches)!=4 or old!=move[0]:raise ValueError('nested fixture caller final integer')
    owner,size,_,_,_,pc,w=move[1]
    infos=[b[1] for b in branches]
    if any(v[:2]!=(owner,size) for v in infos):raise ValueError('nested fixture caller final integer')
    guards={v[7] for v in infos}|{row[4] for rows in (mixed[1],post_mixed[1]) for row in rows if row[4] is not None}
    return expand_mixed_segment(old,contract,owner,size,(pc,w),guards)

def render_next_entry(contract):
    _,(owner,size,pc,w,dst,entry,ret)=contract
    if owner&3 or pc&3 or dst&3 or not 8<=size<=65536 or size&3 or not owner<=pc<ret<owner+size or ret!=pc+4 or dst>=owner or w>>26!=18 or w&3!=1 or direct_bl(w,pc)!=dst or entry==GUARD or boundary_shape(entry)!='load':
        raise ValueError('nested fixture caller next entry')
    return ('namespace formatter_caller_next_entry_private {\n'
            f'inline constexpr uint32_t target=0x{dst:08x}u,word=0x{entry:08x}u,return_pc=0x{ret:08x}u;\n'
            '}\n')

def verify_next_entry_trace(source,dst):
    trace=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{dst:X}) nwii::runtime::trace_call(0x{dst:X}, ctx);'
    label=f'loc_{dst:08X}: ;'
    if source.count(trace)!=1 or source.count(label)!=1 or source.index(trace)>source.index(label):
        raise ValueError('nested fixture caller next entry trace')

def expand_next_entry(old,final_integer,contract):
    blocks,(owner,size,pc,w,dst,entry,ret)=contract
    render_next_entry(contract)
    if old!=final_integer[0] or final_integer[2:]!=(pc,w) or owner not in old or dst in old or set(blocks)!=set(old)|{dst}:
        raise ValueError('nested fixture caller next entry')
    body=old[owner];j=(pc-owner)//4
    if j+1>=len(body) or body[j:j+2]!=(w,GUARD) or blocks[dst]!=(entry,GUARD) or any(blocks[a]!=ws for a,ws in old.items()):
        raise ValueError('nested fixture caller next entry expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

def render_report_byte(entry,contract):
    render_next_entry(entry)
    _,(_,_,_,_,dst,entry_word,ret)=entry
    _,info=contract
    if len(info)!=8:raise ValueError('nested fixture report byte')
    pc,w,parent_offset,report_offset,value,next_pc,next_word,return_pc=info
    op,rt,xo=w>>26,(w>>21)&31,(w>>1)&1023
    if (pc!=dst or w!=entry_word or return_pc!=ret or next_pc!=pc+4 or
            not (op==34 or (op==31 and xo==87 and not w&1)) or
            rt not in (0,*range(3,13)) or
            not 8<=report_offset<128 or parent_offset!=736+report_offset or
            type(value) is not int or not 0<=value<=255 or
            next_word==GUARD or boundary_shape(next_word)!='integer'):
        raise ValueError('nested fixture report byte')
    return ('namespace formatter_caller_report_byte_private {\n'
            f'inline constexpr uint32_t pc=0x{pc:08x}u,word=0x{w:08x}u,next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u,return_pc=0x{return_pc:08x}u;\n'
            f'inline constexpr int32_t parent_offset={parent_offset};\n'
            f'inline constexpr uint32_t report_offset={report_offset}u;\n'
            f'inline constexpr uint8_t value={value}u;\n'
            '}\n')

def expand_report_byte(old,entry,contract):
    render_report_byte(entry,contract)
    blocks,(pc,w,_,_,_,_,next_word,_)=contract
    if (old!=entry[0] or set(blocks)!=set(old) or old.get(pc)!=(w,GUARD) or
            blocks.get(pc)!=(w,next_word,GUARD) or
            any(blocks[a]!=ws for a,ws in old.items() if a!=pc)):
        raise ValueError('nested fixture report byte expansion')
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    return blocks

_COMPARE_EXPANSION_STAGES = frozenset({
    'begin', 'base_joined', 'caller_joined', 'callee_joined',
    'byte_joined', 'compare_joined', 'copy_joined', 'spans_checked',
    'census_checked', 'image_rebuilt', 'header_rendered',
})


def private_compare_checkpoint(stage):
    """Fixed stage labels only, never original words, addresses or state."""
    if stage not in _COMPARE_EXPANSION_STAGES:
        raise ValueError('nested fixture diagnostic stage')
    print(f'FORMATTER_NESTED_119_STAGE stage={stage}', flush=True)


def public_nested_refusal(error, safe):
    """Preserve privacy while separating span conflicts from unknown input."""
    reason = str(error)
    if type(error) is ValueError and reason == 'prefix ownership':
        return 'nested_fixture_span_overlap'
    return reason.replace(' ', '_') if type(error) is ValueError and reason in safe else 'private_input'


def compare_extension(prior, byte_contract, compare_contract):
    """Admit only a local guard move in one existing authenticated callee."""
    candidate, fields = promote_report_compare(
        byte_contract, compare_contract[1][3], compare_contract[1][4:6])
    if compare_contract != (candidate, fields):
        raise ValueError('nested fixture report compare contract')
    root = fields[0]
    # The private comparison contract may cover only a subset of the
    # already authenticated roots. It may never introduce a new root.
    if not set(candidate).issubset(prior) or root not in prior:
        raise ValueError('nested fixture report compare root set')
    if prior[root] != (candidate[root][0], candidate[root][1], GUARD):
        raise ValueError('nested fixture report compare predecessor')
    if candidate[root] != (*prior[root][:2], fields[3], GUARD):
        raise ValueError('nested fixture report compare contract')
    if any(prior[at] != words for at,words in candidate.items() if at != root):
        raise ValueError('nested fixture report compare sibling')
    # Preserve all previously validated original roots that are outside
    # this callee-specific symbolic contract. Validate final ownership.
    merged={**prior,**candidate}
    check_spans({address:4*len(words) for address,words in merged.items()})
    return merged, fields


def copy_extension(prior, compare_contract, copy_contract):
    """Preserve every verified root while moving the 120 boundary by 4 bytes."""
    if (not isinstance(copy_contract, tuple) or len(copy_contract) != 2 or
            not isinstance(copy_contract[1], tuple) or len(copy_contract[1]) != 9):
        raise ValueError('nested fixture report copy contract')
    blocks, info = copy_contract
    root, pc, word, next_pc, next_word, rs, ra, offset, ret = info
    compare_blocks, compare_info = compare_contract
    if (root != compare_info[0] or (pc, word) != compare_info[2:4] or
            ret != compare_info[6] or next_pc != pc+4 or
            root not in prior or root not in blocks or
            not set(blocks).issubset(prior) or
            prior[root] != compare_blocks[root] or
            blocks[root] != (*prior[root][:3], next_word, GUARD)):
        raise ValueError('nested fixture report copy predecessor')
    render_report_copy(copy_contract)
    if any(prior[at] != words for at,words in blocks.items() if at != root):
        raise ValueError('nested fixture report copy sibling')
    merged = {**prior, **blocks}
    check_spans({address:4*len(words) for address,words in merged.items()})
    return merged, info



def immediate_extension(prior, copy_contract, immediate_contract):
    """Move the private 121 guard, without widening any authenticated root."""
    if (not isinstance(immediate_contract, tuple) or
            len(immediate_contract) != 2 or
            not isinstance(immediate_contract[1], tuple) or
            len(immediate_contract[1]) != 8):
        raise ValueError('nested fixture report immediate contract')
    blocks, info = immediate_contract
    root, pc, word, next_pc, next_word, dst, value, ret = info
    copy_blocks, copy_info = copy_contract
    if (root != copy_info[0] or (pc, word) != copy_info[3:5] or
            ret != copy_info[8] or next_pc != pc + 4 or
            root not in prior or root not in blocks or
            not set(blocks).issubset(prior) or
            prior[root] != copy_blocks[root] or
            blocks[root] != (*prior[root][:4], next_word, GUARD)):
        raise ValueError('nested fixture report immediate predecessor')
    render_report_immediate(immediate_contract)
    if any(prior[at] != words for at,words in blocks.items() if at != root):
        raise ValueError('nested fixture report immediate sibling')
    merged = {**prior, **blocks}
    check_spans({address: 4 * len(words) for address, words in merged.items()})
    return merged, info


def signext_extension(prior, immediate_contract, signext_contract):
    """Move only the authenticated 122 guard, preserving sibling roots."""
    if (not isinstance(signext_contract, tuple) or
            len(signext_contract) != 2 or
            not isinstance(signext_contract[1], tuple) or
            len(signext_contract[1]) != 9):
        raise ValueError('nested fixture report signext contract')
    blocks, info = signext_contract
    root, pc, word, next_pc, next_word, dst, before, after, ret = info
    immediate_blocks, immediate_info = immediate_contract
    if (root != immediate_info[0] or
            (pc, word) != immediate_info[3:5] or
            ret != immediate_info[7] or next_pc != pc + 4 or
            dst != immediate_info[5] or before != immediate_info[6] or
            root not in prior or root not in blocks or
            not set(blocks).issubset(prior) or
            prior[root] != immediate_blocks[root] or
            blocks[root] != (*prior[root][:5], next_word, GUARD)):
        raise ValueError('nested fixture report signext predecessor')
    render_report_signext(signext_contract)
    if any(prior[at] != words for at,words in blocks.items() if at != root):
        raise ValueError('nested fixture report signext sibling')
    merged = {**prior, **blocks}
    check_spans({address: 4 * len(words) for address, words in merged.items()})
    return merged, info


def extend(directory,p,*,post=None,partial=None,special=None,release=None,return_contract=None,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None,post_integer_contract=None,third_branch_contract=None,fourth_branch_contract=None,mixed_contract=None,mixed_byte_contract=None,post_mixed_contract=None,stack_move_contract=None,final_integer_contract=None,next_entry_contract=None,report_byte_contract=None,compare_contract=None,copy_contract=None,immediate_contract=None,signext_contract=None,stage_trace=False):
    if stage_trace:private_compare_checkpoint('begin')
    if signext_contract is not None and immediate_contract is None:raise ValueError('nested fixture mode')
    if immediate_contract is not None and copy_contract is None:raise ValueError('nested fixture mode')
    if copy_contract is not None and compare_contract is None:raise ValueError('nested fixture mode')
    if compare_contract is not None and report_byte_contract is None:raise ValueError('nested fixture mode')
    if report_byte_contract is not None and next_entry_contract is None:raise ValueError('nested fixture mode')
    if next_entry_contract is not None and final_integer_contract is None:raise ValueError('nested fixture mode')
    if final_integer_contract is not None and stack_move_contract is None:raise ValueError('nested fixture mode')
    if stack_move_contract is not None and post_mixed_contract is None:raise ValueError('nested fixture mode')
    if post_mixed_contract is not None and mixed_byte_contract is None:raise ValueError('nested fixture mode')
    if mixed_byte_contract is not None and mixed_contract is None:raise ValueError('nested fixture mode')
    if mixed_contract is not None and fourth_branch_contract is None:raise ValueError('nested fixture mode')
    if fourth_branch_contract is not None and third_branch_contract is None:raise ValueError('nested fixture mode')
    if third_branch_contract is not None and post_integer_contract is None:raise ValueError('nested fixture mode')
    if post_integer_contract is not None and second_branch_contract is None:raise ValueError('nested fixture mode')
    if second_branch_contract is not None and branch_contract is None:raise ValueError('nested fixture mode')
    if branch_contract is not None and integer_contract is None:raise ValueError('nested fixture mode')
    if integer_contract is not None and byte_contract is None:raise ValueError('nested fixture mode')
    if byte_contract is not None and caller_contract is None:raise ValueError('nested fixture mode')
    if caller_contract is not None and return_contract is None:raise ValueError('nested fixture mode')
    if return_contract is not None and release is None:raise ValueError('nested fixture mode')
    if release is not None and special is None:raise ValueError('nested fixture mode')
    if special is not None and partial is None:raise ValueError('nested fixture mode')
    if partial is not None and post is None:raise ValueError('nested fixture mode')
    prior,contract=p;old=prior[1][0];final=release or special or partial or post or contract;blocks,fields,*_=final;root=fields[0]
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    expanded=expand(old,blocks,live,root)
    if stage_trace:private_compare_checkpoint('base_joined')
    if caller_contract is not None:
        caller_blocks,info=caller_contract
        expanded={**expanded,**expand_caller(blocks,caller_blocks,info)}
        if byte_contract is not None:expanded={**expanded,**expand_byte(caller_blocks,*byte_contract)}
        if integer_contract is not None:expanded={**expanded,**expand_integers(byte_contract[0],integer_contract,byte_contract[1])}
        if branch_contract is not None:expanded={**expanded,**expand_branch(integer_contract[0],branch_contract,integer_contract)}
        if second_branch_contract is not None:expanded={**expanded,**expand_second_branch(branch_contract[0],branch_contract,second_branch_contract)}
        if post_integer_contract is not None:expanded={**expanded,**expand_post_integers(second_branch_contract[0],post_integer_contract,branch_contract,second_branch_contract)}
        if third_branch_contract is not None:expanded={**expanded,**expand_third_branch(post_integer_contract[0],branch_contract,second_branch_contract,post_integer_contract,third_branch_contract)}
        if fourth_branch_contract is not None:expanded={**expanded,**expand_fourth_branch(third_branch_contract[0],branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract)}
        if mixed_contract is not None:expanded={**expanded,**expand_mixed(fourth_branch_contract[0],mixed_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))}
        if mixed_byte_contract is not None:expanded={**expanded,**expand_mixed_byte(mixed_contract[0],mixed_contract,mixed_byte_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))}
        if post_mixed_contract is not None:expanded={**expanded,**expand_post_mixed(mixed_byte_contract[0],mixed_byte_contract,mixed_contract,post_mixed_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))}
        if stack_move_contract is not None:expanded={**expanded,**expand_stack_move(post_mixed_contract[0],post_mixed_contract,mixed_contract,stack_move_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))}
        if final_integer_contract is not None:expanded={**expanded,**expand_final_integer(stack_move_contract[0],stack_move_contract,mixed_contract,post_mixed_contract,final_integer_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))}
        if stage_trace:private_compare_checkpoint('caller_joined')
        if next_entry_contract is not None:
            if next_entry_contract[1][4] in live:raise ValueError('nested fixture caller next entry overlap')
            expanded={**expanded,**expand_next_entry(final_integer_contract[0],final_integer_contract,next_entry_contract)}
            if stage_trace:private_compare_checkpoint('callee_joined')
            if report_byte_contract is not None:
                expanded={**expanded,**expand_report_byte(next_entry_contract[0],next_entry_contract,report_byte_contract)}
                if stage_trace:private_compare_checkpoint('byte_joined')
                if compare_contract is not None:
                    candidate,_=compare_extension(expanded,report_byte_contract,compare_contract)
                    expanded=candidate
                    if stage_trace:private_compare_checkpoint('compare_joined')
                    if copy_contract is not None:
                        candidate,_=copy_extension(expanded,compare_contract,copy_contract)
                        expanded=candidate
                        if stage_trace:private_compare_checkpoint('copy_joined')
                        if immediate_contract is not None:
                            candidate,_=immediate_extension(expanded,copy_contract,immediate_contract)
                            expanded=candidate
                            if signext_contract is not None:
                                candidate,_=signext_extension(expanded,immediate_contract,signext_contract)
                                expanded=candidate
        check_spans({a:4*len(ws) for a,ws in expanded.items()})
        if stage_trace:private_compare_checkpoint('spans_checked')
    # The previously authenticated formatter image has 58 CSV roots
    # plus two vector roots. Admit exactly one new authenticated callee.
    root_limit=60
    if next_entry_contract is not None:
        if len(live)!=58 or len(expanded)!=59:
            raise ValueError('nested fixture caller next entry root census')
        root_limit=61
        print('FORMATTER_NESTED_ROOT_CENSUS verified=1 prior=60 expanded=61 new_roots=1')
    if stage_trace:private_compare_checkpoint('census_checked')
    new=rebuild(raw,expanded,max_roots=root_limit)
    if stage_trace:private_compare_checkpoint('image_rebuilt')
    header=render(contract)
    if post is not None:header+=render(post,stack_boundary=True)
    if partial is not None:header+=render(partial,instruction_boundary=True)
    if special is not None:header+=render(special,instruction_boundary=True,special_boundary=True)
    if release is not None:header+=render(release,instruction_boundary=True,release_boundary=True)
    if return_contract is not None:header+=render_return(return_contract)
    if caller_contract is not None:header+=render_caller(caller_contract[1])
    if byte_contract is not None:header+=render_byte(byte_contract[1])
    if integer_contract is not None:header+=render_integers(integer_contract)
    if branch_contract is not None:header+=render_branch(branch_contract)
    if second_branch_contract is not None:header+=render_branch(second_branch_contract,second=True)
    if post_integer_contract is not None:header+=render_integers(post_integer_contract,post_branch=True)
    if third_branch_contract is not None:header+=render_branch(third_branch_contract,third=True)
    if fourth_branch_contract is not None:header+=render_branch(fourth_branch_contract,fourth=True)
    if mixed_contract is not None:header+=render_mixed(mixed_contract)
    if mixed_byte_contract is not None:header+=render_mixed_byte(mixed_byte_contract)
    if post_mixed_contract is not None:header+=render_post_mixed(post_mixed_contract)
    if stack_move_contract is not None:header+=render_stack_move(stack_move_contract)
    if final_integer_contract is not None:header+=render_final_integer(final_integer_contract)
    if next_entry_contract is not None:header+=render_next_entry(next_entry_contract)
    if report_byte_contract is not None:header+=render_report_byte(next_entry_contract,report_byte_contract)
    if compare_contract is not None:header+=render_report_compare(compare_contract)
    if copy_contract is not None:header+=render_report_copy(copy_contract)
    if immediate_contract is not None:header+=render_report_immediate(immediate_contract)
    if signext_contract is not None:header+=render_report_signext(signext_contract)
    if stage_trace:private_compare_checkpoint('header_rendered')
    with (directory/'private_formatter_nested.h').open('x') as out:out.write(header)
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    kind='guarded_instruction' if partial is not None else 'guarded_stack' if post is not None else 'guarded_control' if len(fields)==10 else 'guarded_load'
    print(f'FORMATTER_NESTED_FIXTURE verified=1 labels={len(final[2])} {kind}=1 new_roots={int(next_entry_contract is not None)}')

def scope(d,e,sizes,p,*,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None,post_integer_contract=None,third_branch_contract=None,fourth_branch_contract=None,mixed_contract=None,mixed_byte_contract=None,post_mixed_contract=None,stack_move_contract=None,final_integer_contract=None,next_entry_contract=None,report_byte_contract=None,compare_contract=None,copy_contract=None,immediate_contract=None,signext_contract=None):
    if signext_contract is not None and immediate_contract is None:raise ValueError('nested fixture mode')
    if immediate_contract is not None and copy_contract is None:raise ValueError('nested fixture mode')
    if copy_contract is not None and compare_contract is None:raise ValueError('nested fixture mode')
    if compare_contract is not None and report_byte_contract is None:raise ValueError('nested fixture mode')
    if report_byte_contract is not None and next_entry_contract is None:raise ValueError('nested fixture mode')
    if next_entry_contract is not None and final_integer_contract is None:raise ValueError('nested fixture mode')
    if final_integer_contract is not None and stack_move_contract is None:raise ValueError('nested fixture mode')
    if stack_move_contract is not None and post_mixed_contract is None:raise ValueError('nested fixture mode')
    if post_mixed_contract is not None and mixed_byte_contract is None:raise ValueError('nested fixture mode')
    if mixed_byte_contract is not None and mixed_contract is None:raise ValueError('nested fixture mode')
    if mixed_contract is not None and fourth_branch_contract is None:raise ValueError('nested fixture mode')
    if fourth_branch_contract is not None and third_branch_contract is None:raise ValueError('nested fixture mode')
    if third_branch_contract is not None and post_integer_contract is None:raise ValueError('nested fixture mode')
    if post_integer_contract is not None and second_branch_contract is None:raise ValueError('nested fixture mode')
    if second_branch_contract is not None and branch_contract is None:raise ValueError('nested fixture mode')
    if branch_contract is not None and integer_contract is None:raise ValueError('nested fixture mode')
    if integer_contract is not None and byte_contract is None:raise ValueError('nested fixture mode')
    if byte_contract is not None and caller_contract is None:raise ValueError('nested fixture mode')
    prior,contract=p;old=prior[1][0];blocks,fields,*_=contract;root=fields[0]
    if set(blocks)!=set(old) or sizes.get(root)!=4*len(blocks[root]):
        raise ValueError('nested fixture extent')
    before={**sizes,root:4*len(old[root])}
    extra={}
    if caller_contract is not None:
        caller_blocks,info=caller_contract;owner=info[0]
        final=expand_caller(blocks,caller_blocks,info)
        if byte_contract is not None:final=expand_byte(final,*byte_contract)
        if integer_contract is not None:final=expand_integers(final,integer_contract,byte_contract[1])
        if branch_contract is not None:final=expand_branch(final,branch_contract,integer_contract)
        if second_branch_contract is not None:final=expand_second_branch(final,branch_contract,second_branch_contract)
        if post_integer_contract is not None:final=expand_post_integers(final,post_integer_contract,branch_contract,second_branch_contract)
        if third_branch_contract is not None:final=expand_third_branch(final,branch_contract,second_branch_contract,post_integer_contract,third_branch_contract)
        if fourth_branch_contract is not None:final=expand_fourth_branch(final,branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract)
        if mixed_contract is not None:final=expand_mixed(final,mixed_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))
        if mixed_byte_contract is not None:final=expand_mixed_byte(final,mixed_contract,mixed_byte_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))
        if post_mixed_contract is not None:final=expand_post_mixed(final,mixed_byte_contract,mixed_contract,post_mixed_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))
        if stack_move_contract is not None:final=expand_stack_move(final,post_mixed_contract,mixed_contract,stack_move_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))
        if final_integer_contract is not None:final=expand_final_integer(final,stack_move_contract,mixed_contract,post_mixed_contract,final_integer_contract,(branch_contract,second_branch_contract,third_branch_contract,fourth_branch_contract))
        if owner==root or sizes.get(owner)!=4*len(final[owner]):
            raise ValueError('nested fixture caller extent')
        before[owner]=4*len(old[owner]);extra[owner]=sizes[owner]
        if next_entry_contract is not None:
            final=expand_next_entry(final,final_integer_contract,next_entry_contract)
            dst=next_entry_contract[1][4]
            if report_byte_contract is not None:
                final=expand_report_byte(final,next_entry_contract,report_byte_contract)
                if compare_contract is not None:
                    final,_=compare_extension(final,report_byte_contract,compare_contract)
                    if copy_contract is not None:
                        final,_=copy_extension(final,compare_contract,copy_contract)
                        if immediate_contract is not None:
                            final,_=immediate_extension(final,copy_contract,immediate_contract)
                            if signext_contract is not None:
                                final,_=signext_extension(final,immediate_contract,signext_contract)
            extent=28 if signext_contract is not None else 24 if immediate_contract is not None else 20 if copy_contract is not None else 16 if compare_contract is not None else 12 if report_byte_contract is not None else 8
            if dst in old or sizes.get(dst)!=extent or 4*len(final[dst])!=extent:raise ValueError('nested fixture caller next entry extent')
            before.pop(dst);extra[dst]=extent
    return check_spans({**dict(continuation_scope(d,e,before,prior)),root:sizes[root],**extra})

def install(directory,p,*,arrival=False,post=None,partial=None,special=None,release=None,return_contract=None,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None,post_integer_contract=None,third_branch_contract=None,fourth_branch_contract=None,mixed_contract=None,mixed_byte_contract=None,post_mixed_contract=None,stack_move_contract=None,final_integer_contract=None,next_entry_contract=None,report_byte_contract=None,compare_contract=None,copy_contract=None,immediate_contract=None,signext_contract=None):
    if signext_contract is not None and immediate_contract is None:raise ValueError('nested fixture mode')
    if immediate_contract is not None and copy_contract is None:raise ValueError('nested fixture mode')
    if copy_contract is not None and compare_contract is None:raise ValueError('nested fixture mode')
    if compare_contract is not None and report_byte_contract is None:raise ValueError('nested fixture mode')
    if report_byte_contract is not None and next_entry_contract is None:raise ValueError('nested fixture mode')
    if next_entry_contract is not None and final_integer_contract is None:raise ValueError('nested fixture mode')
    if final_integer_contract is not None and stack_move_contract is None:raise ValueError('nested fixture mode')
    if stack_move_contract is not None and post_mixed_contract is None:raise ValueError('nested fixture mode')
    if post_mixed_contract is not None and mixed_byte_contract is None:raise ValueError('nested fixture mode')
    if mixed_byte_contract is not None and mixed_contract is None:raise ValueError('nested fixture mode')
    if mixed_contract is not None and fourth_branch_contract is None:raise ValueError('nested fixture mode')
    if fourth_branch_contract is not None and third_branch_contract is None:raise ValueError('nested fixture mode')
    if third_branch_contract is not None and post_integer_contract is None:raise ValueError('nested fixture mode')
    if post_integer_contract is not None and second_branch_contract is None:raise ValueError('nested fixture mode')
    if second_branch_contract is not None and branch_contract is None:raise ValueError('nested fixture mode')
    if branch_contract is not None and integer_contract is None:raise ValueError('nested fixture mode')
    if integer_contract is not None and byte_contract is None:raise ValueError('nested fixture mode')
    if byte_contract is not None and caller_contract is None:raise ValueError('nested fixture mode')
    if caller_contract is not None and return_contract is None:raise ValueError('nested fixture mode')
    if return_contract is not None and release is None:raise ValueError('nested fixture mode')
    if release is not None and special is None:raise ValueError('nested fixture mode')
    if special is not None and partial is None:raise ValueError('nested fixture mode')
    if partial is not None and (post is None or not arrival):raise ValueError('nested fixture mode')
    _,contract=p
    _,fields,rows,*_=(release or special or partial or post or contract);root,_,target,word,*_=fields
    control_fields=contract[1]
    files=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in files}
    expected={pc:(root,w) for pc,w in rows}
    if target in expected:raise ValueError('nested fixture load boundary')
    expected[target]=(root,word)
    main=directory/'main_output.cpp';main_text=main.read_text()
    if arrival:
        if len(control_fields)!=10:raise ValueError('nested fixture arrival mode')
        dst,dword,_=control_fields[7:]
        if post is None:
            if dst in expected:raise ValueError('nested fixture arrival mode')
            expected[dst]=(root,dword)
        elif expected.get(dst)!=(root,dword):raise ValueError('nested fixture arrival mode')
    if caller_contract is not None:
        _,(owner,caller,cword,call)=caller_contract
        if caller in expected or owner==root:raise ValueError('nested fixture caller geometry')
        expected[caller]=(owner,cword)
        if byte_contract is not None:
            _,info=byte_contract
            if info[:4]!=(owner,caller,cword,call):raise ValueError('nested fixture caller byte')
            render_byte(info)
            next_pc,next_word=info[-2:]
            if next_pc in expected:raise ValueError('nested fixture caller byte')
            expected[next_pc]=(owner,next_word)
            if integer_contract is not None:
                _,rows,end_pc,end_word=integer_contract
                render_integers(integer_contract)
                if rows[0][:2]!=(next_pc,next_word):raise ValueError('nested fixture caller integers')
                for pc,w,_ in rows[1:]:
                    if pc in expected:raise ValueError('nested fixture caller integers')
                    expected[pc]=(owner,w)
                if end_pc in expected:raise ValueError('nested fixture caller integers')
                expected[end_pc]=(owner,end_word)
                if branch_contract is not None:
                    _,info=branch_contract
                    render_branch(branch_contract)
                    if info[0]!=owner or info[2:4]!=(end_pc,end_word) or info[5] in expected:
                        raise ValueError('nested fixture caller branch')
                    expected[info[5]]=(owner,info[6])
                    if second_branch_contract is not None:
                        _,second_info=second_branch_contract
                        render_branch(second_branch_contract,second=True)
                        if second_info[:2]!=info[:2] or second_info[2:4]!=info[5:7] or second_info[5] in expected:
                            raise ValueError('nested fixture caller second branch')
                        expected[second_info[5]]=(owner,second_info[6])
                        if post_integer_contract is not None:
                            _,rows,end,w=post_integer_contract
                            render_integers(post_integer_contract,post_branch=True)
                            if rows[0][:2]!=second_info[5:7]:raise ValueError('nested fixture caller post integers')
                            for pc,word,_ in rows[1:]:
                                if pc in expected:raise ValueError('nested fixture caller post integers')
                                expected[pc]=(owner,word)
                            if end in expected:raise ValueError('nested fixture caller post integers')
                            expected[end]=(owner,w)
                            if third_branch_contract is not None:
                                _,third_info=third_branch_contract
                                render_branch(third_branch_contract,third=True)
                                if third_info[:2]!=second_info[:2] or third_info[2:4]!=(end,w) or third_info[5] in expected:
                                    raise ValueError('nested fixture caller third branch')
                                expected[third_info[5]]=(owner,third_info[6])
                                if fourth_branch_contract is not None:
                                    _,fourth_info=fourth_branch_contract
                                    render_branch(fourth_branch_contract,fourth=True)
                                    if fourth_info[:2]!=third_info[:2] or fourth_info[2:4]!=third_info[5:7] or fourth_info[5] in expected:
                                        raise ValueError('nested fixture caller fourth branch')
                                    expected[fourth_info[5]]=(owner,fourth_info[6])
                                    if mixed_contract is not None:
                                        _,rows,end,w=mixed_contract
                                        render_mixed(mixed_contract)
                                        if rows[0][:2]!=fourth_info[5:7]:raise ValueError('nested fixture caller mixed')
                                        for pc,word,*_ in rows[1:]:
                                            if pc in expected:raise ValueError('nested fixture caller mixed')
                                            expected[pc]=(owner,word)
                                        if end in expected:raise ValueError('nested fixture caller mixed')
                                        expected[end]=(owner,w)
                                        if mixed_byte_contract is not None:
                                            render_mixed_byte(mixed_byte_contract)
                                            _,info=mixed_byte_contract
                                            if info[:3]!=(owner,end,w) or info[5] in expected:raise ValueError('nested fixture caller mixed byte')
                                            expected[info[5]]=(owner,info[6])
                                            if post_mixed_contract is not None:
                                                render_post_mixed(post_mixed_contract)
                                                _,post_rows,post_end,post_word=post_mixed_contract
                                                if post_rows[0][:2]!=info[-2:]:raise ValueError('nested fixture caller post mixed')
                                                for at,word,*_ in post_rows[1:]:
                                                    if at in expected:raise ValueError('nested fixture caller post mixed')
                                                    expected[at]=(owner,word)
                                                if post_end in expected:raise ValueError('nested fixture caller post mixed')
                                                expected[post_end]=(owner,post_word)
                                                if stack_move_contract is not None:
                                                    render_stack_move(stack_move_contract)
                                                    _,info=stack_move_contract
                                                    if info[:1]!=(owner,) or info[2:4]!=(post_end,post_word) or info[5] in expected:raise ValueError('nested fixture caller stack move')
                                                    expected[info[5]]=(owner,info[6])
                                                    if final_integer_contract is not None:
                                                        render_final_integer(final_integer_contract)
                                                        _,rows,end,w=final_integer_contract
                                                        if rows[0][:2]!=info[-2:] or end in expected:raise ValueError('nested fixture caller final integer')
                                                        expected[end]=(owner,w)
                                                        if next_entry_contract is not None:
                                                            render_next_entry(next_entry_contract)
                                                            _,info=next_entry_contract
                                                            if info[0]!=owner or info[2:4]!=(end,w) or info[4] in expected:raise ValueError('nested fixture caller next entry')
                                                            expected[info[4]]=(info[4],info[5])
                                                        if report_byte_contract is not None:
                                                            expand_report_byte(next_entry_contract[0],next_entry_contract,report_byte_contract)
                                                            ri=report_byte_contract[1]
                                                            if ri[5] in expected:raise ValueError('nested fixture report byte expansion')
                                                            expected[ri[5]]=(ri[0],ri[6])
                                                            if compare_contract is not None:
                                                                candidate,fields=promote_report_compare(report_byte_contract,compare_contract[1][3],compare_contract[1][4:6])
                                                                if compare_contract!=(candidate,fields) or fields[2] in expected:
                                                                    raise ValueError('nested fixture report compare expansion')
                                                                expected[fields[2]]=(fields[0],fields[3])
                                                                if copy_contract is not None:
                                                                    ci=copy_contract[1]
                                                                    if (ci[0]!=fields[0] or ci[1:3]!=fields[2:4] or
                                                                            ci[3] in expected):
                                                                        raise ValueError('nested fixture report copy expansion')
                                                                    expected[ci[3]]=(ci[0],ci[4])
                                                                    if immediate_contract is not None:
                                                                        ii=immediate_contract[1]
                                                                        if (ii[0]!=ci[0] or ii[1:3]!=ci[3:5] or
                                                                                ii[3] in expected):
                                                                            raise ValueError('nested fixture report immediate expansion')
                                                                        expected[ii[3]]=(ii[0],ii[4])
                                                                        if signext_contract is not None:
                                                                            si=signext_contract[1]
                                                                            if (si[0]!=ii[0] or si[1:3]!=ii[3:5] or
                                                                                    si[5:7]!=ii[5:7] or si[8]!=ii[7] or
                                                                                    si[3] in expected):
                                                                                raise ValueError('nested fixture report signext expansion')
                                                                            expected[si[3]]=(si[0],si[4])
    audit_native(sources.values(),main_text,expected)
    if len(control_fields)==10:
        owners=[]
        for source in sources.values():
            try:owners.append(exact_function(source,root))
            except ValueError:pass
        if len(owners)!=1:raise ValueError('nested fixture control owner')
        site=control_fields[2]
        verify_ctr_body(owners[0],site)
        if return_contract is not None:verify_blr_body(owners[0],target)
        if arrival:main_text,_=ensure_ctr_resume(main_text,owners[0],root,site,dst)
    if caller_contract is not None:
        bodies=[]
        for source in sources.values():
            try:bodies.append(exact_function(source,owner))
            except ValueError:pass
        if len(bodies)!=1:raise ValueError('nested fixture caller owner')
        verify_direct(bodies[0],caller-4,root)
        if branch_contract is not None:
            _,info=branch_contract
            verify_forward_branch_body(bodies[0],info[2],info[3])
        if second_branch_contract is not None:
            _,info=second_branch_contract
            verify_forward_branch_body(bodies[0],info[2],info[3])
        if third_branch_contract is not None:
            _,info=third_branch_contract
            verify_forward_branch_body(bodies[0],info[2],info[3])
        if fourth_branch_contract is not None:
            _,info=fourth_branch_contract
            verify_forward_branch_body(bodies[0],info[2],info[3])
        if mixed_contract is not None:
            for pc,w,_,_,other,_ in mixed_contract[1]:
                if other is not None:verify_forward_branch_body(bodies[0],pc,w)
        if post_mixed_contract is not None:
            for pc,w,_,_,other,_ in post_mixed_contract[1]:
                if other is not None:verify_forward_branch_body(bodies[0],pc,w)
        if next_entry_contract is not None:
            _,info=next_entry_contract
            verify_direct(bodies[0],info[2],info[4])
            target_bodies=[]
            for source in sources.values():
                try:target_bodies.append(exact_function(source,info[4]))
                except ValueError:pass
            if len(target_bodies)!=1:raise ValueError('nested fixture caller next entry trace')
            verify_next_entry_trace(target_bodies[0],info[4])
        main_text,_=ensure_resume(main_text,bodies[0],owner,caller)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('nested fixture native hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','formatter_nested_before'))
            if arrival and pc==dst:s=trace_ctr_destination(s,pc,w)
            if caller_contract is not None and pc==caller:s=trace_ctr_destination(s,pc,w,caller=True)
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('nested fixture native hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid formatter_nested_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('nested fixture coverage')
    for file,s in changed.items():file.write_text(s)
    if arrival:main.write_text(main_text)
    kind='partial_hook' if partial is not None else 'post_ctr_hook' if post is not None else 'arrival_hook' if arrival else 'pre_control_hook' if len(fields)==10 else 'pre_load_hook'
    print(f'FORMATTER_NESTED_TRANSLATION verified=1 labels={len(rows)} {kind}=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);modes=a.add_mutually_exclusive_group();modes.add_argument('--second',action='store_true');modes.add_argument('--third',action='store_true');modes.add_argument('--control',action='store_true');modes.add_argument('--arrival',action='store_true');modes.add_argument('--post-ctr',action='store_true');modes.add_argument('--partial',action='store_true');modes.add_argument('--special',action='store_true');modes.add_argument('--release',action='store_true');modes.add_argument('--return',dest='return_mode',action='store_true');modes.add_argument('--caller-arrival',action='store_true');modes.add_argument('--caller-byte',action='store_true');modes.add_argument('--caller-integers',action='store_true');modes.add_argument('--caller-branch',action='store_true');modes.add_argument('--caller-second-branch',action='store_true');modes.add_argument('--caller-post-integers',action='store_true');modes.add_argument('--caller-third-branch',action='store_true');modes.add_argument('--caller-fourth-branch',action='store_true');modes.add_argument('--caller-mixed',action='store_true');modes.add_argument('--caller-mixed-byte',action='store_true');modes.add_argument('--caller-post-mixed',action='store_true');modes.add_argument('--caller-stack-move',action='store_true');modes.add_argument('--caller-final-integer',action='store_true');modes.add_argument('--caller-next-entry',action='store_true');modes.add_argument('--caller-report-byte',action='store_true');modes.add_argument('--caller-report-compare',action='store_true');modes.add_argument('--caller-report-copy',action='store_true');modes.add_argument('--caller-report-immediate',action='store_true');modes.add_argument('--caller-report-signext',action='store_true');q=a.parse_args()
    if q.caller_report_signext:q.caller_report_immediate=True
    if q.caller_report_immediate:q.caller_report_copy=True
    if q.caller_report_copy:q.caller_report_compare=True
    if q.caller_report_compare:q.caller_report_byte=True
    if q.caller_report_byte:q.caller_next_entry=True
    if q.caller_next_entry:q.caller_final_integer=True
    if q.caller_final_integer:q.caller_stack_move=True
    if q.caller_stack_move:q.caller_post_mixed=True
    if q.caller_post_mixed:q.caller_mixed_byte=True
    if q.caller_mixed_byte:q.caller_mixed=True
    safe={'size','nested fixture instruction boundary','nested fixture return guard','nested fixture caller geometry','nested fixture caller expansion','nested fixture caller extent','nested fixture caller owner','nested fixture caller byte','nested fixture caller byte expansion','nested fixture caller integers','nested fixture caller integer overlap','nested fixture caller integer expansion','nested fixture caller branch','nested fixture caller branch expansion','nested fixture caller second branch','nested fixture caller post integers','nested fixture caller post integer overlap','nested fixture caller post integer guard','nested fixture caller post integer expansion','nested fixture caller third branch','nested fixture caller fourth branch','nested fixture caller mixed','nested fixture caller mixed guard','nested fixture caller mixed overlap','nested fixture caller mixed expansion','nested fixture caller mixed byte','nested fixture caller mixed byte overlap','nested fixture caller mixed byte guard','nested fixture caller mixed byte expansion','nested fixture caller post mixed','nested fixture caller stack move','nested fixture caller stack move overlap','nested fixture caller stack move guard','nested fixture caller stack move expansion','nested fixture caller final integer','nested fixture caller next entry','nested fixture caller next entry trace','nested fixture caller next entry expansion','nested fixture caller next entry overlap','nested fixture caller next entry extent','nested fixture caller next entry root census','fixture geometry','fixture range','fixture span','fixture overlap','completion roundtrip','nested fixture report byte','nested fixture report byte expansion','nested fixture report compare expansion','nested fixture report compare contract','nested fixture report compare root set','nested fixture report compare predecessor','nested fixture report compare sibling','nested fixture report copy contract','nested fixture report copy predecessor','nested fixture report copy sibling','nested fixture report copy expansion','nested fixture report immediate contract','nested fixture report immediate predecessor','nested fixture report immediate sibling','nested fixture report immediate expansion','nested fixture report signext contract','nested fixture report signext predecessor','nested fixture report signext sibling','nested fixture report signext expansion','caller native branch body','caller native branch target','LR native body','nested fixture stack boundary','CTR analyzer geometry','CTR analyzer anchor','CTR destination trace','CTR native destination','completion local resume','completion outer resume','completion root dispatch','nested fixture arrival mode','CTR native body','nested fixture control owner','nested fixture control contract','nested fixture mode','nested fixture data contract','nested fixture predecessor','nested fixture expansion','nested fixture extent','nested fixture load boundary','nested fixture native hook','nested fixture coverage'}
    phase='inputs'
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        with plan_cache_scope():
            phase='base_plan'
            p=plan(d,e,second=q.second,third=q.third,control=q.control or q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed)
            post=post_ctr_plan(d,e,previous=p[0][1],control=p[1]) if q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            partial=partial_plan(d,e,previous=p[0][1],control=p[1],post=post) if q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            special=None
            if q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                special,info=special_plan(d,e,previous=p[0][1],control=p[1],post=post,partial=partial)
                if info[:2]!=('link',1):raise ValueError('nested fixture special provenance')
            release=release_plan(d,e,previous=p[0][1],control=p[1],post=post,partial=partial,special=special) if q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            return_contract=return_plan(d,e,release=release,previous=p[0][1]) if q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            phase='caller_plan'
            caller_contract=caller_plan(d,e,release=release,previous=p[0][1],return_info=return_contract) if q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            byte_contract=byte_plan(d,e,arrival=caller_contract) if q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed else None
            integer_contract=None
            if q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                integer_contract,_=integer_plan(d,e,byte=byte_contract)
                if integer_contract is None:raise ValueError('nested fixture caller integers')
            branch_contract=None
            second_branch_contract=None
            if q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                branch_contract,second=branch_plan(d,e,byte=byte_contract,contract=integer_contract)
                if q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                    second_branch_contract,_,_=second_branch_plan(d,e,byte=byte_contract,integer=integer_contract,first=branch_contract,second=second)
                    if second_branch_contract is None:raise ValueError('nested fixture caller second branch')
            post_integer_contract=None
            third_branch_contract=None
            if q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                post_integer_contract,edge,_=post_integer_plan(d,e,byte=byte_contract,integer=integer_contract,first=branch_contract,second=second_branch_contract)
                if q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                    third_branch_contract,_,_=third_branch_plan(d,e,byte=byte_contract,integer=integer_contract,first=branch_contract,second=second_branch_contract,post=post_integer_contract,edge=edge)
                    if third_branch_contract is None:raise ValueError('nested fixture caller third branch')
            fourth_branch_contract=None
            mixed_contract=None
            mixed_byte_contract=None
            post_mixed_contract=None
            stack_move_contract=None
            final_integer_contract=None
            next_entry_contract=None
            report_byte_contract=None
            report_byte_state=None
            if q.caller_fourth_branch or q.caller_mixed:
                phase='mixed_plan'
                prior=dict(byte=byte_contract,integer=integer_contract,first=branch_contract,second=second_branch_contract,post=post_integer_contract,third=third_branch_contract)
                fourth_branch_contract,_,_=fourth_branch_plan(d,e,**prior)
                if fourth_branch_contract is None:raise ValueError('nested fixture caller fourth branch')
                if q.caller_mixed:
                    mixed_contract,_,_,_=mixed_plan(d,e,fourth=fourth_branch_contract,**prior)
                    if not mixed_contract[1]:raise ValueError('nested fixture caller mixed')
                    if q.caller_mixed_byte:mixed_byte_contract=mixed_byte_plan(d,e)
                    if q.caller_post_mixed:
                        post_mixed_contract,_,_,_=post_mixed_plan(d,e)
                        if not post_mixed_contract[1]:raise ValueError('nested fixture caller post mixed')
                        if q.caller_stack_move:stack_move_contract,_,_,_=stack_move_plan(d,e)
                        if q.caller_final_integer:
                            phase='final_integer_plan'
                            final_integer_contract,_,_,_=final_integer_plan(d,e)
                            phase='next_entry_plan'
                            if q.caller_next_entry:next_entry_contract,_,_,_=next_entry_plan(d,e)
                            if q.caller_report_byte:
                                if q.caller_report_compare:
                                    report_byte_state=report_byte_plan(d,e,with_live=True)
                                    report_byte_contract=report_byte_state[0]
                                else:
                                    report_byte_contract=report_byte_plan(d,e)
            compare_contract=report_compare_plan(
                d,e,predecessor=report_byte_state) if q.caller_report_compare else None
            copy_contract=report_copy_plan(d,e,predecessor=report_byte_state,compare=compare_contract) if q.caller_report_copy else None
            immediate_contract=report_immediate_plan(d,e,predecessor=report_byte_state,compare=compare_contract,copy=copy_contract) if q.caller_report_immediate else None
            signext_contract=report_signext_plan(d,e,predecessor=report_byte_state,compare=compare_contract,copy=copy_contract,immediate=immediate_contract) if q.caller_report_signext else None
            phase='fixture_expansion'
            if q.fixture:extend(q.fixture,p,post=post,partial=partial,special=special,release=release,return_contract=return_contract,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract,post_integer_contract=post_integer_contract,third_branch_contract=third_branch_contract,fourth_branch_contract=fourth_branch_contract,mixed_contract=mixed_contract,mixed_byte_contract=mixed_byte_contract,post_mixed_contract=post_mixed_contract,stack_move_contract=stack_move_contract,final_integer_contract=final_integer_contract,next_entry_contract=next_entry_contract,report_byte_contract=report_byte_contract,compare_contract=compare_contract,copy_contract=copy_contract,immediate_contract=immediate_contract,signext_contract=signext_contract,stage_trace=q.caller_report_compare);return 0
            phase='native_install'
            if q.install:install(q.install,p,arrival=q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed,post=post,partial=partial,special=special,release=release,return_contract=return_contract,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract,post_integer_contract=post_integer_contract,third_branch_contract=third_branch_contract,fourth_branch_contract=fourth_branch_contract,mixed_contract=mixed_contract,mixed_byte_contract=mixed_byte_contract,post_mixed_contract=post_mixed_contract,stack_move_contract=stack_move_contract,final_integer_contract=final_integer_contract,next_entry_contract=next_entry_contract,report_byte_contract=report_byte_contract,compare_contract=compare_contract,copy_contract=copy_contract,immediate_contract=immediate_contract,signext_contract=signext_contract);return 0
            phase='analyzer_expansion'
            if q.analyzer:
                if not q.symbols:raise ValueError('nested fixture extent')
                source=analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),(p[0],release or special or partial or post) if post is not None else p,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract,post_integer_contract=post_integer_contract,third_branch_contract=third_branch_contract,fourth_branch_contract=fourth_branch_contract,mixed_contract=mixed_contract,mixed_byte_contract=mixed_byte_contract,post_mixed_contract=post_mixed_contract,stack_move_contract=stack_move_contract,final_integer_contract=final_integer_contract,next_entry_contract=next_entry_contract,report_byte_contract=report_byte_contract,compare_contract=compare_contract,copy_contract=copy_contract,immediate_contract=immediate_contract,signext_contract=signext_contract))
                if q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch or q.caller_post_integers or q.caller_third_branch or q.caller_fourth_branch or q.caller_mixed:
                    fields=p[1][1];source=analyzer_local_edge(source,fields[0],fields[2],fields[7])
                q.analyzer.write_text(source)
                print(f'FORMATTER_NESTED_ANALYZER verified=1 expanded_root=1 new_roots={int(next_entry_contract is not None)}');return 0
            if not render(p[1]) or (post is not None and not render(post,stack_boundary=True)) or (partial is not None and not render(partial,instruction_boundary=True)) or (special is not None and not render(special,instruction_boundary=True,special_boundary=True)) or (release is not None and not render(release,instruction_boundary=True,release_boundary=True)):raise ValueError('nested fixture extent')
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        # A fixed, public phase label identifies the refusing component, but
        # never prints original addresses, instruction words or exception data.
        assert phase in {'inputs','base_plan','caller_plan','mixed_plan',
                         'final_integer_plan','next_entry_plan',
                         'fixture_expansion','native_install','analyzer_expansion'}
        reason=public_nested_refusal(ex,safe)
        print(f'FORMATTER_NESTED_PREP verified=0 reason={reason} phase={phase}');return 1
    kind='pre_control_hook' if q.control else 'pre_load_hook'
    print(f'FORMATTER_NESTED_PREP verified=1 labels={len(p[1][2])} {kind}=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
