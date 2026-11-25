"""Separate local and outer native resume dispatch verification."""
import re
from prepare_v726_handler_return import verify_resume_dispatch

def verify_callback_resume(main, body, owner, pc):
    marker = 'extern "C" void run_game('
    if main.count(marker) != 1:
        raise ValueError('outer dispatcher extent')
    outer = main.split(marker, 1)[1]
    local = body.split(marker, 1)[0]
    verify_resume_dispatch(outer, owner, pc)
    rows = re.findall(r'(?mi)^[ \t]*case[ \t]+0x'+f'{pc:X}'+r'[ \t]*:[ \t]*([^\r\n]*)', local)
    if len(rows) != 1 or not re.fullmatch(r'goto[ \t]+loc_'+f'{pc:X}'+r';[ \t]*', rows[0], re.I):
        raise ValueError('local resume dispatcher identity')
