#!/usr/bin/env python3
"""V326: third-generation original NAND code-coverage census.

Read the authenticated Wii DOL/ELF, private V310 candidate, and its
AOT C++ only inside owner CI. V325 confirmed the nine original direct
callees of 0x805195EC. Reuse V323's exact/interior window guard without
printing instructions, generated code, paths or guest data.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from analyze_v323_second_descendants import inspect as inspect_original

TARGETS=(
    0x8051906C,0x8051AD3C,0x805265D4,
    0x8051905C,0x8051AFE0,0x805222C0,
    0x805265AC,0x805293B0,0x8052A430
)

def inspect(owner:bytes,elf:bytes,fixture:bytes,generated:str,**kwargs)->list[str]:
    return inspect_original(
        owner,elf,fixture,generated,
        targets=TARGETS,prefix="V326",depth="THIRD",**kwargs
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_v310_dol",type=Path)
    p.add_argument("private_v310_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        rows=inspect(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.private_v310_dol.read_bytes(),
            a.private_v310_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError,IndexError):
        print("V326_THIRD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(rows))
    print("V326_THIRD_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
