#!/usr/bin/env python3
"""Original-free V30 compatible-HID4 patch atomic and idempotency regressions."""
from pathlib import Path
import tempfile

from apply_hid4_continuous_v30 import (
    CTX, RECOMP, IOS, CONTEXT_OLD, CONTEXT_NEW,
    BACKUP_OLD, BACKUP_NEW, READ_OLD, READ_NEW,
    WRITE_OLD, WRITE_NEW, RESTORE_OLD, RESTORE_NEW,
    SAVE_OLD, SAVE_NEW, FPSCR_OLD, FPSCR_NEW, apply,
)

OLD={
    CTX:("  uint32_t hid0 = 0; // Wii HID0, guest visible\n"
         + CONTEXT_OLD + "\n" + BACKUP_OLD),
    RECOMP:(READ_OLD+"\n"+WRITE_OLD+"\n"+FPSCR_OLD+"\n"
            +RESTORE_OLD+"\n"+RESTORE_OLD),
    IOS:(SAVE_OLD+"\n"+SAVE_OLD),
}


def write(root,data):
    for path,content in data.items():
        p=root/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content,encoding="utf-8")


def snapshot(root):
    return {path:(root/path).read_text(encoding="utf-8") for path in OLD}


def rejected(root,data,description):
    write(root,data)
    previous=snapshot(root)
    try:
        apply(root)
    except ValueError:
        pass
    else:
        raise AssertionError(description+": malformed runtime accepted")
    assert snapshot(root)==previous,description+": partial mutation on failure"


def main():
    checks=0
    with tempfile.TemporaryDirectory(prefix="v30hid4_originalfree_") as temp:
        root=Path(temp)
        write(root,OLD)
        assert apply(root)=="installed"
        patched=snapshot(root)
        checks+=1
        for path in OLD:
            assert patched[path]!=OLD[path]
        checks+=1
        assert apply(root)=="already applied"
        assert snapshot(root)==patched
        checks+=2

        bad=dict(OLD)
        bad[CTX]=bad[CTX].replace("uint32_t hid0 = 0;","uint32_t hidden = 0;")
        rejected(root,bad,"requires earlier V18");checks+=1
        bad=dict(OLD)
        bad[CTX]=bad[CTX].replace(CONTEXT_OLD,CONTEXT_NEW)
        rejected(root,bad,"partial patch");checks+=1
        bad=dict(OLD)
        bad[RECOMP]=bad[RECOMP].replace(READ_OLD,READ_OLD+READ_OLD)
        rejected(root,bad,"ambiguous read anchor");checks+=1
        bad=dict(OLD)
        bad[RECOMP]=bad[RECOMP].replace(FPSCR_OLD,"unknown mtfsb format")
        rejected(root,bad,"unknown FPSCR emitter");checks+=1
        bad=dict(OLD)
        bad[RECOMP]=bad[RECOMP].replace(WRITE_OLD,"unknown L2 emitter")
        rejected(root,bad,"unknown after-V20 write emitter");checks+=1
        bad=dict(OLD)
        bad[IOS]=bad[IOS].replace(SAVE_OLD,SAVE_OLD+SAVE_OLD,1)
        rejected(root,bad,"ambiguous HLE backup");checks+=1
        bad=dict(OLD)
        bad[CTX]=bad[CTX].replace(BACKUP_OLD,"corrupted backup")
        rejected(root,bad,"unsafe partial CPUContext backup");checks+=1
        bad=dict(OLD)
        bad[RECOMP]=bad[RECOMP].replace(RESTORE_OLD,RESTORE_NEW,1)
        rejected(root,bad,"one of two callbacks prepatched");checks+=1
        bad=dict(OLD)
        bad[RECOMP]="// unrelated source-only comment\n"+bad[RECOMP]
        write(root,bad)
        assert apply(root)=="installed"
        assert snapshot(root)[RECOMP].startswith("// unrelated source-only comment")
        checks+=2
    print(f"PASS: {checks} V30 original-free compatible HID4/FPSCR patch guards")

if __name__=="__main__":
    main()
