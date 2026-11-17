#!/usr/bin/env python3
"""Original-free HID4/FPSCR patch for the *already patched* V18+V20+V29 runtime.

The older direct-entry V30 patch expects an HID0 stub. Continuous __start
already has native HID0 from V18; patch only HID4 and FPSCR bit-operations,
and add HID0/HID4 to callback backups. Fail closed on unexpected upstream.
No owner PPC bytes, data, symbols or generated code are embedded here.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from apply_hid4_fp_v30 import FPSCR_OLD, FPSCR_NEW, RESTORE_OLD, SAVE_OLD

CTX=Path("nWiiRuntime/include/runtime/cpu_context.h")
RECOMP=Path("nWiiRecomp/src/recompiler.cpp")
IOS=Path("nWiiRuntime/src/hle/ios.cpp")

CONTEXT_OLD="  std::array<uint32_t, 4> pmc{};\n\n  struct BackupState {"
CONTEXT_NEW=("  std::array<uint32_t, 4> pmc{};\n"
             "  uint32_t hid4 = 0; // Wii HID4 guest-visible state\n"
             "\n  struct BackupState {")
BACKUP_OLD="    std::array<uint32_t, 4> pmc{};\n  };"
BACKUP_NEW=("    std::array<uint32_t, 4> pmc{};\n"
            "    uint32_t hid0 = 0;\n"
            "    uint32_t hid4 = 0;\n  };")

READ_OLD='''    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid0; // mfspr HID0\\n";
    } else if (spr == 287) {'''
READ_NEW='''    } else if (spr == 1011) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid4; // mfspr HID4\\n";
    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid0; // mfspr HID0\\n";
    } else if (spr == 287) {'''

WRITE_OLD='''    } else if (spr == 1017) {
      out << "    ctx.write_l2cr(ctx.gpr[" << rS << "]); // mtspr L2CR\\n";
    } else {'''
WRITE_NEW='''    } else if (spr == 1017) {
      out << "    ctx.write_l2cr(ctx.gpr[" << rS << "]); // mtspr L2CR\\n";
    } else if (spr == 1011) {
      out << "    ctx.hid4 = ctx.gpr[" << rS << "]; // mtspr HID4\\n";
    } else {'''

RESTORE_NEW=RESTORE_OLD+'\n    out << "                ctx.hid0 = bk.hid0; ctx.hid4 = bk.hid4;\\n";'
SAVE_NEW=SAVE_OLD+'\n  bk.hid0 = ctx.hid0; bk.hid4 = ctx.hid4;'

EDITS={
    CTX:[(CONTEXT_OLD,CONTEXT_NEW,1),(BACKUP_OLD,BACKUP_NEW,1)],
    RECOMP:[(READ_OLD,READ_NEW,1),(WRITE_OLD,WRITE_NEW,1),
            (FPSCR_OLD,FPSCR_NEW,1),(RESTORE_OLD,RESTORE_NEW,2)],
    IOS:[(SAVE_OLD,SAVE_NEW,2)]
}


def apply(root:Path)->str:
    cpu=(root/CTX).read_text(encoding="utf-8")
    if "uint32_t hid0 = 0; // Wii HID0, guest visible" not in cpu:
        raise ValueError("continuous HID4 patch requires preinstalled V18 HID0")
    updates={}
    done=[]
    for relative,replacements in EDITS.items():
        path=root/relative
        data=path.read_text(encoding="utf-8")
        updated=data
        for old,new,count in replacements:
            if updated.count(new)==count and updated.count(old)==(count if old in new else 0):
                done.append(True)
                continue
            if updated.count(old)!=count or updated.count(new)!=0:
                raise ValueError(f"{relative}: unknown, partial or ambiguous runtime patch")
            updated=updated.replace(old,new)
            done.append(False)
        updates[path]=updated
    if any(done) and not all(done):
        raise ValueError("mixed prepatched/unpatched Wii runtime refused atomically")
    if all(done):
        return "already applied"
    for path,updated in updates.items():
        path.write_text(updated,encoding="utf-8")
    return "installed"


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("upstream",type=Path)
    args=p.parse_args()
    print("V30 continuous original-free HID4/FPSCR patch:",apply(args.upstream))

if __name__=="__main__":
    main()
