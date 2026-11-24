#!/usr/bin/env python3
import re,sys
from pathlib import Path
def check(header,main):
    m=re.fullmatch(r'#pragma once\ninline constexpr uint32_t Resume=0x([0-9a-f]{8})u;\n',header)
    if not m:raise ValueError('resume header')
    pc=int(m[1],16)
    if pc not in range(0x805265c4,0x805265d4,4):raise ValueError('resume range')
    for addr in (0x805265c0,pc):
        rows=re.findall(r'(?mi)^[ \t]*case[ \t]+0x'+f'{addr:X}'+r'[ \t]*:[ \t]*([^\r\n]*)',main)
        if len(rows)!=1 or not re.fullmatch(r'func_805265C0\(ctx\);[ \t]*break;[ \t]*',rows[0]):raise ValueError('dispatcher resume')
if __name__=='__main__':
    try:check(Path(sys.argv[1]).read_text(),Path(sys.argv[2]).read_text())
    except (OSError,ValueError):print('V613_IRQ_DISPATCH verified=0');sys.exit(1)
    print('V613_IRQ_DISPATCH verified=1')
