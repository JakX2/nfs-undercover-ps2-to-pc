#!/usr/bin/env python3
"""Original-free atomic-validation, idempotency and fail-closed V30 HID/FP patch tests."""
import argparse
import tempfile
from pathlib import Path

from apply_hid4_fp_v30 import (CTX, RECOMP, IOS, CONTEXT_OLD, CONTEXT_NEW,
                                 BACKUP_OLD, BACKUP_NEW, READ_OLD, READ_NEW,
                                 WRITE_OLD, WRITE_NEW, FPSCR_OLD, FPSCR_NEW, RESTORE_OLD, RESTORE_NEW,
                                 SAVE_OLD, SAVE_NEW, apply)

EDITS = {
    CTX: [(CONTEXT_OLD, CONTEXT_NEW, 1), (BACKUP_OLD, BACKUP_NEW, 1)],
    RECOMP: [(READ_OLD, READ_NEW, 1), (WRITE_OLD, WRITE_NEW, 1), (FPSCR_OLD, FPSCR_NEW, 1),
             (RESTORE_OLD, RESTORE_NEW, 2)],
    IOS: [(SAVE_OLD, SAVE_NEW, 2)],
}


def read_files(root):
    return {file: (root/file).read_text(encoding='utf-8') for file in EDITS}


def write_files(root, data):
    for file, content in data.items():
        target=root/file;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content, encoding='utf-8')


def check_reject(root, source, label):
    write_files(root, source)
    try:
        apply(root)
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise AssertionError(label + ': accepted malformed emitter')
    for file in source:
        assert (root/file).read_text(encoding='utf-8') == source[file], \
               label + ': changed source on rejected patch'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('upstream',type=Path)
    args=ap.parse_args()
    actual=read_files(args.upstream)
    fresh={}
    for file,original in actual.items():
        raw=original
        for old,new,count in reversed(EDITS[file]):
            assert raw.count(new)==count, 'upstream is not a V30-installed baseline'
            raw=raw.replace(new,old)
        fresh[file]=raw
    checks=0
    with tempfile.TemporaryDirectory(prefix='v30_hid_guards_') as folder:
        root=Path(folder)
        write_files(root,fresh)
        assert apply(root)=='installed'
        assert read_files(root)==actual
        checks+=2
        assert apply(root)=='already applied'
        assert read_files(root)==actual
        checks+=2
        bad=dict(fresh)
        bad[RECOMP]=bad[RECOMP].replace(READ_OLD,READ_OLD.replace('HID0 (stub)', 'HID0 (unknown)'))
        check_reject(root,bad,'unknown mfspr layout');checks+=1
        bad=dict(fresh)
        bad[RECOMP]=bad[RECOMP].replace(WRITE_OLD,WRITE_OLD+WRITE_OLD)
        check_reject(root,bad,'ambiguous mtspr match');checks+=1
        bad=dict(fresh)
        bad[CTX]=bad[CTX].replace(CONTEXT_OLD,CONTEXT_NEW)
        check_reject(root,bad,'partial CPUContext patch');checks+=1
        bad=dict(fresh)
        bad[IOS]=bad[IOS].replace(SAVE_OLD,SAVE_OLD+SAVE_OLD,1)
        check_reject(root,bad,'duplicate IOS backup');checks+=1
        bad=dict(fresh)
        bad[RECOMP]=bad[RECOMP].replace(RESTORE_OLD,RESTORE_NEW,1)
        check_reject(root,bad,'partial callback restore patch');checks+=1
        bad=dict(fresh)
        bad[CTX]=bad[CTX].replace(BACKUP_OLD,BACKUP_OLD.replace('hid4','xyz') if 'hid4' in BACKUP_OLD else BACKUP_OLD.replace('pmc','xyz'))
        check_reject(root,bad,'unknown backup layout');checks+=1
        bad=dict(fresh)
        bad[RECOMP]=bad[RECOMP].replace(FPSCR_OLD,FPSCR_OLD.replace('ignored', 'ignoredX'))
        check_reject(root,bad,'unknown FPSCR instruction layout');checks+=1
        bad=dict(fresh)
        bad[RECOMP]='// independent source comment\n'+bad[RECOMP]
        # This harmless trailing comment isn't an anchor, so should NOT be rejected.
        write_files(root,bad)
        assert apply(root)=='installed', 'overly broad patch rejected unrelated change'
        checks+=1
        assert (root/RECOMP).read_text().count('independent source comment')==1
        checks+=1
        write_files(root,fresh)
        (root/IOS).unlink()
        try:apply(root)
        except FileNotFoundError:checks+=1
        else:raise AssertionError('missing IOS file was accepted')
        for file in (CTX,RECOMP):
            assert (root/file).read_text()==fresh[file], 'prevalidation wrote partial source'
    print(f'PASS: {checks} V30 HID0/HID4/FPSCR patch safety/idempotency checks')


if __name__=='__main__':main()
