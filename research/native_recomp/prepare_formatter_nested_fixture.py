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
from prepare_formatter_continuation_plan import plan as continuation_plan
from prepare_formatter_continuation_fixture import scope as continuation_scope
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at
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

def render_integers(contract):
    _,rows,end_pc,end_word=contract
    if not 1<=len(rows)<=8 or end_pc!=rows[0][0]+4*len(rows) or end_word==GUARD:
        raise ValueError('nested fixture caller integers')
    lines=['namespace formatter_caller_integer_private {']
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

def render_branch(contract,*,second=False):
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
    name='formatter_caller_second_branch_private' if second else 'formatter_caller_branch_private'
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

def expand(old,blocks,live,root):
    if set(blocks)!=set(old) or root not in old or any(live.get(a)!=ws for a,ws in old.items()):
        raise ValueError('nested fixture predecessor')
    if any(blocks[a]!=ws for a,ws in old.items() if a!=root) or len(blocks[root])<=len(old[root]):
        raise ValueError('nested fixture expansion')
    result={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in result.items()})
    return result

def extend(directory,p,*,post=None,partial=None,special=None,release=None,return_contract=None,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None):
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
    if caller_contract is not None:
        caller_blocks,info=caller_contract
        expanded={**expanded,**expand_caller(blocks,caller_blocks,info)}
        if byte_contract is not None:expanded={**expanded,**expand_byte(caller_blocks,*byte_contract)}
        if integer_contract is not None:expanded={**expanded,**expand_integers(byte_contract[0],integer_contract,byte_contract[1])}
        if branch_contract is not None:expanded={**expanded,**expand_branch(integer_contract[0],branch_contract,integer_contract)}
        if second_branch_contract is not None:expanded={**expanded,**expand_second_branch(branch_contract[0],branch_contract,second_branch_contract)}
        check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=60)
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
    with (directory/'private_formatter_nested.h').open('x') as out:out.write(header)
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    kind='guarded_instruction' if partial is not None else 'guarded_stack' if post is not None else 'guarded_control' if len(fields)==10 else 'guarded_load'
    print(f'FORMATTER_NESTED_FIXTURE verified=1 labels={len(final[2])} {kind}=1 new_roots=0')

def scope(d,e,sizes,p,*,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None):
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
        if owner==root or sizes.get(owner)!=4*len(final[owner]):
            raise ValueError('nested fixture caller extent')
        before[owner]=4*len(old[owner]);extra[owner]=sizes[owner]
    return check_spans({**dict(continuation_scope(d,e,before,prior)),root:sizes[root],**extra})

def install(directory,p,*,arrival=False,post=None,partial=None,special=None,release=None,return_contract=None,caller_contract=None,byte_contract=None,integer_contract=None,branch_contract=None,second_branch_contract=None):
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
    a.add_argument('--symbols',type=Path);modes=a.add_mutually_exclusive_group();modes.add_argument('--second',action='store_true');modes.add_argument('--third',action='store_true');modes.add_argument('--control',action='store_true');modes.add_argument('--arrival',action='store_true');modes.add_argument('--post-ctr',action='store_true');modes.add_argument('--partial',action='store_true');modes.add_argument('--special',action='store_true');modes.add_argument('--release',action='store_true');modes.add_argument('--return',dest='return_mode',action='store_true');modes.add_argument('--caller-arrival',action='store_true');modes.add_argument('--caller-byte',action='store_true');modes.add_argument('--caller-integers',action='store_true');modes.add_argument('--caller-branch',action='store_true');modes.add_argument('--caller-second-branch',action='store_true');q=a.parse_args()
    safe={'size','nested fixture instruction boundary','nested fixture return guard','nested fixture caller geometry','nested fixture caller expansion','nested fixture caller extent','nested fixture caller owner','nested fixture caller byte','nested fixture caller byte expansion','nested fixture caller integers','nested fixture caller integer overlap','nested fixture caller integer expansion','nested fixture caller branch','nested fixture caller branch expansion','nested fixture caller second branch','caller native branch body','caller native branch target','LR native body','nested fixture stack boundary','CTR analyzer geometry','CTR analyzer anchor','CTR destination trace','CTR native destination','completion local resume','completion outer resume','completion root dispatch','nested fixture arrival mode','CTR native body','nested fixture control owner','nested fixture control contract','nested fixture mode','nested fixture data contract','nested fixture predecessor','nested fixture expansion','nested fixture extent','nested fixture load boundary','nested fixture native hook','nested fixture coverage'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        with plan_cache_scope():
            p=plan(d,e,second=q.second,third=q.third,control=q.control or q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch)
            post=post_ctr_plan(d,e,previous=p[0][1],control=p[1]) if q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            partial=partial_plan(d,e,previous=p[0][1],control=p[1],post=post) if q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            special=None
            if q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch:
                special,info=special_plan(d,e,previous=p[0][1],control=p[1],post=post,partial=partial)
                if info[:2]!=('link',1):raise ValueError('nested fixture special provenance')
            release=release_plan(d,e,previous=p[0][1],control=p[1],post=post,partial=partial,special=special) if q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            return_contract=return_plan(d,e,release=release,previous=p[0][1]) if q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            caller_contract=caller_plan(d,e,release=release,previous=p[0][1],return_info=return_contract) if q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            byte_contract=byte_plan(d,e,arrival=caller_contract) if q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch else None
            integer_contract=None
            if q.caller_integers or q.caller_branch or q.caller_second_branch:
                integer_contract,_=integer_plan(d,e,byte=byte_contract)
                if integer_contract is None:raise ValueError('nested fixture caller integers')
            branch_contract=None
            second_branch_contract=None
            if q.caller_branch or q.caller_second_branch:
                branch_contract,second=branch_plan(d,e,byte=byte_contract,contract=integer_contract)
                if q.caller_second_branch:
                    second_branch_contract,_,_=second_branch_plan(d,e,byte=byte_contract,integer=integer_contract,first=branch_contract,second=second)
                    if second_branch_contract is None:raise ValueError('nested fixture caller second branch')
            if q.fixture:extend(q.fixture,p,post=post,partial=partial,special=special,release=release,return_contract=return_contract,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract);return 0
            if q.install:install(q.install,p,arrival=q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch,post=post,partial=partial,special=special,release=release,return_contract=return_contract,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract);return 0
            if q.analyzer:
                if not q.symbols:raise ValueError('nested fixture extent')
                source=analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),(p[0],release or special or partial or post) if post is not None else p,caller_contract=caller_contract,byte_contract=byte_contract,integer_contract=integer_contract,branch_contract=branch_contract,second_branch_contract=second_branch_contract))
                if q.arrival or q.post_ctr or q.partial or q.special or q.release or q.return_mode or q.caller_arrival or q.caller_byte or q.caller_integers or q.caller_branch or q.caller_second_branch:
                    fields=p[1][1];source=analyzer_local_edge(source,fields[0],fields[2],fields[7])
                q.analyzer.write_text(source)
                print('FORMATTER_NESTED_ANALYZER verified=1 expanded_root=1 new_roots=0');return 0
            if not render(p[1]) or (post is not None and not render(post,stack_boundary=True)) or (partial is not None and not render(partial,instruction_boundary=True)) or (special is not None and not render(special,instruction_boundary=True,special_boundary=True)) or (release is not None and not render(release,instruction_boundary=True,release_boundary=True)):raise ValueError('nested fixture extent')
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NESTED_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    kind='pre_control_hook' if q.control else 'pre_load_hook'
    print(f'FORMATTER_NESTED_PREP verified=1 labels={len(p[1][2])} {kind}=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
