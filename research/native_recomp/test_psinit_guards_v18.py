#!/usr/bin/env python3
"""Original-free V18 mutation/patch-safety regression; no game bytes needed."""
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import apply_hid_state_v18 as patch
import make_psinit_slice_v18 as maker


def set_op(b, header_index, instruction, value):
    where = struct.unpack_from('>I', b, header_index * 4)[0]
    struct.pack_into('>I', b, where + instruction * 4, value)


def verify_patch(source_root, tmp):
    # Reconstruct the original-free unpatched marker pattern in a disposable
    # miniature source tree, not by modifying the user's checkout.
    root = tmp / 'patch-test'
    for name in (patch.CONTEXT, patch.RECOMPILER):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        current = (source_root / name).read_text()
        if name == patch.CONTEXT:
            assert current.count(patch.CTX_AFTER) == 1
            current = current.replace(patch.CTX_AFTER, patch.CTX_BEFORE)
        else:
            assert current.count(patch.READ_AFTER) == 1
            assert current.count(patch.WRITE_AFTER) == 1
            current = current.replace(patch.READ_AFTER, patch.READ_BEFORE)
            current = current.replace(patch.WRITE_AFTER, patch.WRITE_BEFORE)
        path.write_text(current)
    assert patch.apply(root)
    assert not patch.apply(root)
    assert (root / patch.CONTEXT).read_text() == (source_root / patch.CONTEXT).read_text()
    assert (root / patch.RECOMPILER).read_text() == (source_root / patch.RECOMPILER).read_text()
    yield 'patch first apply, byte-parity and idempotence'

    # If *either* upstream file no longer matches, don't rewrite the other.
    old_ctx = (root / patch.CONTEXT).read_text()
    old_recomp = (root / patch.RECOMPILER).read_text()
    (root / patch.RECOMPILER).write_text(old_recomp.replace(patch.READ_AFTER, 'UNKNOWN-HID-READ-CASE'))
    try:
        patch.apply(root)
    except ValueError:
        pass
    else:
        raise AssertionError('patched source with mismatched recompiler marker')
    assert (root / patch.CONTEXT).read_text() == old_ctx
    yield 'unknown upstream revision rejects atomically'
    (root / patch.RECOMPILER).write_text(old_recomp)
    (root / patch.CONTEXT).write_text(old_ctx.replace(patch.CTX_AFTER,'UNKNOWN-CPU-CONTEXT-CASE'))
    try:
        patch.apply(root)
    except ValueError:
        pass
    else:
        raise AssertionError('patched source with mismatched CPU context marker')
    assert (root / patch.RECOMPILER).read_text() == old_recomp
    yield 'unknown context version rejects atomically'


def verify_generator(generator: Path, tmp: Path):
    original = bytearray(maker.make(None))
    def expect_bad(label, data, mode='synthetic'):
        dol=tmp / (label+'.dol')
        out=tmp / (label+'-out')
        dol.write_bytes(data)
        out.mkdir()
        p=subprocess.run([str(generator),str(dol),str(out),mode],capture_output=True,text=True,timeout=12)
        assert p.returncode != 0,(label,p.stdout,p.stderr)
        assert not list(out.iterdir()),f'partial generated output on rejection: {label}'

    cases = []
    def mut(label,section,op,word):
        d=bytearray(original)
        set_op(d,section,op,word)
        cases.append((label,d))
    mut('start_wrong_bl',0,0,0x48000001)
    mut('ps_wrong_hid_read',1,3,0x48000001)
    mut('ps_wrong_hid_write',1,5,0x48000001)
    mut('ps_wrong_ic',1,6,0x48000001)
    mut('ps_wrong_oris',1,4,0x64630000)
    mut('ps_wrong_gqr_zero',1,8,0x38600001)
    mut('ps_missing_sync',1,7,0x60000000)
    mut('ps_wrong_gqr_spr',1,9,0x60000000)
    mut('ps_no_blr',1,20,0x60000000)
    mut('hid2_mfspr_wrong',2,0,0x60000000)
    mut('hid2_mtspr_wrong',2,2,0x60000000)
    mut('ic_hid0_mfspr_wrong',3,0,0x60000000)
    mut('ic_hid0_mtspr_wrong',3,2,0x60000000)
    mut('ic_ori_wrong_bit',3,1,0x60840001)
    mut('ic_missing_blr',3,3,0x60000000)
    mut('fpr_stop_not_syscall',4,0,0x60000000)
    mut('cache_stop_not_syscall',5,0,0x60000000)
    mut('start_no_stop',0,2,0x60000000)
    d=bytearray(original)
    struct.pack_into('>I', d, 0xe0, maker.START+4)
    cases.append(('wrong_entry',d))
    d=bytearray(original)
    struct.pack_into('>I', d, 0x90, 0xfffffff8)
    cases.append(('oversized_text',d))
    for label,data in cases:
        expect_bad(label,data)
        yield label

    expect_bad('wrong_mode',original,'invalid')
    yield 'wrong generator mode'
    existing=tmp / 'already-exists.dol'
    existing.write_text('do not overwrite')
    p=subprocess.run([sys.executable,str(Path(maker.__file__)),str(existing)],capture_output=True,text=True)
    assert p.returncode and existing.read_text()=='do not overwrite'
    yield 'synthetic maker rejects pre-existing destination'
    out=tmp/'nonempty-out'
    out.mkdir()
    (out/'sentinel.txt').write_text('private')
    dol=tmp/'original-free-valid.dol'
    dol.write_bytes(original)
    p=subprocess.run([str(generator),str(dol),str(out),'synthetic'],capture_output=True,text=True)
    assert p.returncode and (out/'sentinel.txt').read_text()=='private'
    yield 'generator refuses overwriting any output'
    truncated=tmp/'truncated.dol'
    truncated.write_bytes(bytes(original[:100]))
    out=(tmp/'truncated-out')
    out.mkdir()
    p=subprocess.run([str(generator),str(truncated),str(out),'synthetic'],capture_output=True,text=True)
    assert p.returncode and not list(out.iterdir())
    yield 'truncated DOL rejected without output'


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Usage: test_psinit_guards_v18.py GENERATED_CPP_DRIVER PATCHED_NWII_ROOT')
    count=0
    with TemporaryDirectory(prefix='psinit-guards-') as t:
        tmp=Path(t)
        for _ in verify_patch(Path(sys.argv[2]),tmp):count+=1
        for _ in verify_generator(Path(sys.argv[1]).resolve(),tmp):count+=1
        bad_owner = tmp / 'bogus-original.dol'
        bad_owner.write_bytes(bytes(512))
        forbidden = tmp / 'must-not-create.dol'
        p = subprocess.run([sys.executable,str(Path(maker.__file__)),str(forbidden),
                            '--owner-dol',str(bad_owner)],capture_output=True,text=True)
        assert p.returncode and not forbidden.exists(), 'owner SHA guard failed'
        count += 1
    print(f'PASS: {count} original-free V18 loader/patch/extractor rejection checks')


if __name__=='__main__':main()
