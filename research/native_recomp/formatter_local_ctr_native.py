"""Audit the pinned NWiiRecomp native local CTR transfer form."""
import re
from prepare_v1337_open_completion import ensure_resume

def verify_ctr_body(body,site):
    # The original bctr must remain a native indirect transfer, never an
    # interpreter fallback, replacement direct jump, or forced destination.
    label=r'(?mi)^loc_'+f'{site:X}'+r': ;\n    // 0x'+f'{site:08X}'+r': 4E800420\n'
    hits=list(re.finditer(label,body))
    if len(hits)!=1:raise ValueError('CTR native body')
    rest=body[hits[0].end():]
    if not rest.startswith('    ++ctx.inst_count;\n    ctx.pc = ctx.ctr; return;\n'):
        raise ValueError('CTR native body')
    return True

def verify_blr_body(body,site):
    # The pinned emitter uses the same unconditional native return form as
    # bctr, selecting LR instead. Only the exact original blr is admitted.
    label=r'(?mi)^loc_'+f'{site:X}'+r': ;\n    // 0x'+f'{site:08X}'+r': 4E800020\n'
    hits=list(re.finditer(label,body))
    if len(hits)!=1 or not body[hits[0].end():].startswith('    ++ctx.inst_count;\n    ctx.pc = ctx.lr; return;\n'):
        raise ValueError('LR native body')
    return True

def verify_forward_branch_body(body,pc,w):
    """Match the pinned emitter's exact local CR-only forward branch."""
    op=w>>26;bo=(w>>21)&31;bi=(w>>16)&31
    if op not in (16,18) or w&3 or op==16 and not bo&4:
        raise ValueError('caller native branch body')
    n=16 if op==16 else 26
    disp=w&((1<<n)-4);disp=(disp^(1<<(n-1)))-(1<<(n-1))
    target=pc+disp
    if target<=pc+4:raise ValueError('caller native branch body')
    condition='' if op==18 or bo&16 else ('!' if not bo&8 else '')+f'ctx.cr[{bi//4}].'+('lt','gt','eq','so')[bi%4]
    line=f'    if ({condition}) goto loc_{target:X};\n' if condition else f'    goto loc_{target:X};\n'
    label=r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n'
    hits=list(re.finditer(label,body))
    if len(hits)!=1 or not body[hits[0].end():].startswith('    ++ctx.inst_count;\n'+line):
        raise ValueError('caller native branch body')
    if len(re.findall(r'(?mi)^loc_'+f'{target:X}'+r': ;$',body))!=1:
        raise ValueError('caller native branch target')
    return True

def ensure_ctr_resume(main,body,owner,site,destination):
    if site==destination or destination==owner or destination&3:raise ValueError('CTR native destination')
    verify_ctr_body(body,site)
    labels=re.findall(r'(?mi)^loc_'+f'{destination:X}'+r': ;$',body)
    if len(labels)!=1:raise ValueError('CTR native destination')
    return ensure_resume(main,body,owner,destination)

def analyzer_local_edge(source,owner,site,destination):
    if any(a&3 for a in (owner,site,destination)) or not owner<site<owner+383*4 or not owner<destination<owner+383*4 or site==destination:
        raise ValueError('CTR analyzer geometry')
    anchor='    block_queue.push(func_start);'
    if source.count(anchor)!=1 or 'verified local CTR edge' in source:raise ValueError('CTR analyzer anchor')
    # This adds a block, not a function root. Source words and ownership are
    # independently authenticated by the private contract and span adapter.
    line=(f'\n    if(func_start==0x{owner:08x}u) {{ block_queue.push(0x{destination:08x}u); '
          f'local_jump_targets.insert(0x{destination:08x}u); }} // verified local CTR edge')
    return source.replace(anchor,anchor+line,1)

def trace_ctr_destination(source,pc,w,*,caller=False):
    label=r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n'
    pat=re.compile(label+r'    \+\+ctx\.inst_count;\n    formatter_nested_before\(ctx,0x'+f'{pc:08x}u,0x{w:08x}u'+r'\);')
    hits=list(pat.finditer(source))
    if len(hits)!=1:raise ValueError('CTR destination trace')
    pos=hits[0].start()+len(re.match(label,source[hits[0].start():])[0])
    comment='caller return label' if caller else 'original CTR destination'
    line=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx); // {comment}\n'
    if line in source:raise ValueError('CTR destination trace')
    return source[:pos]+line+source[pos:]
