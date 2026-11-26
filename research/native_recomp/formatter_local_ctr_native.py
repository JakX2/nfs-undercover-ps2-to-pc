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

def ensure_ctr_resume(main,body,owner,site,destination):
    if site==destination or destination==owner or destination&3:raise ValueError('CTR native destination')
    verify_ctr_body(body,site)
    labels=re.findall(r'(?mi)^loc_'+f'{destination:X}'+r': ;$',body)
    if len(labels)!=1:raise ValueError('CTR native destination')
    return ensure_resume(main,body,owner,destination)
