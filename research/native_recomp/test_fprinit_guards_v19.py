#!/usr/bin/env python3
"""Original-free V19 callgraph corruption, patch atomicity and owner SHA guards."""
import struct
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import apply_fpscr_v19 as patch
import make_fprinit_slice_v19 as maker


def verify_patch(root: Path, temp: Path):
    fake=temp/'patch-fixture'
    for name in [patch.CONTEXT, patch.RECOMPILER]:
        path=fake/name
        path.parent.mkdir(parents=True,exist_ok=True)
        current=(root/name).read_text()
        if name==patch.CONTEXT:
            assert current.count(patch.CTX_AFTER)==1
            path.write_text(current.replace(patch.CTX_AFTER,patch.CTX_BEFORE))
        else:
            assert current.count(patch.EMIT_AFTER)==1
            path.write_text(current.replace(patch.EMIT_AFTER,patch.EMIT_BEFORE))
    assert patch.apply(fake)
    assert not patch.apply(fake)
    for name in [patch.CONTEXT, patch.RECOMPILER]:
        assert (fake/name).read_text()==(root/name).read_text()
    yield 'patch applies byte-exact and idempotently'
    original_a=(fake/patch.CONTEXT).read_text()
    original_b=(fake/patch.RECOMPILER).read_text()
    (fake/patch.RECOMPILER).write_text(original_b.replace(patch.EMIT_AFTER,'BROKEN_FPSCR_EMIT'))
    try:
        patch.apply(fake)
        raise AssertionError('accepted unknown emitter revision')
    except ValueError:
        assert (fake/patch.CONTEXT).read_text()==original_a
    yield 'unknown recompiler source fails without modifying CPU context'
    (fake/patch.RECOMPILER).write_text(original_b)
    (fake/patch.CONTEXT).write_text(original_a.replace(patch.CTX_AFTER,'BROKEN_FPSCR_CONTEXT'))
    try:
        patch.apply(fake)
        raise AssertionError('accepted unknown CPUContext revision')
    except ValueError:
        assert (fake/patch.RECOMPILER).read_text()==original_b
    yield 'unknown context source fails without modifying emitter'


def mutate(section,index,word):
    b=bytearray(maker.make(None))
    offset=struct.unpack_from('>I',b,4*section)[0]
    struct.pack_into('>I',b,offset+index*4,word)
    return b


def guard(binary: Path, temp: Path):
    base=maker.make(None)
    cases=[
        ('start_wrong_branch',mutate(0,0,0x48000001)),
        ('psinit_missing_return',mutate(1,20,0x60000000)),
        ('hid_read_missing_mfspr',mutate(2,0,0x60000000)),
        ('ic_hid0_write_wrong',mutate(3,2,0x60000000)),
        ('fpr_psq_missing',mutate(4,2,0x60000000)),
        ('fpr_ps_copy_missing',mutate(4,3,0x60000000)),
        ('fpr_scalar_lfd_missing',mutate(4,36,0x60000000)),
        ('fpr_scalar_copy_missing',mutate(4,37,0x60000000)),
        ('fpr_mtfsf_missing',mutate(4,68,0x60000000)),
        ('fpr_mtfsf_wrong_mask',mutate(4,68,(63<<26)|(0xf0<<17)|(711<<1))),
        ('fpr_return_missing',mutate(4,69,0x60000000)),
        ('cache_stop_missing',mutate(5,0,0x60000000)),
    ]
    broken=bytearray(base)
    struct.pack_into('>I',broken,0x90+4*4,0xfffffff0)
    cases.append(('fpr_oversized_section',broken))
    broken=bytearray(base)
    struct.pack_into('>I',broken,0xe0,0x80004040)
    cases.append(('unexpected_entry',broken))
    for name,raw in cases:
        path=temp/f'{name}.dol'; out=temp/f'{name}_generated'
        path.write_bytes(raw);out.mkdir()
        proc=subprocess.run([str(binary),str(path),str(out),'synthetic'],
                            capture_output=True,text=True,timeout=25)
        assert proc.returncode, (name,proc.stdout,proc.stderr)
        assert list(out.iterdir())==[],('bad generator emitted output',name)
        yield name
    # Additional malformed input modes and destination guards.
    valid=temp/'valid.dol';valid.write_bytes(base)
    bad=temp/'bad_mode';bad.mkdir()
    p=subprocess.run([str(binary),str(valid),str(bad),'badmode'],capture_output=True,text=True)
    assert p.returncode and not list(bad.iterdir())
    yield 'invalid generator mode'
    nonempty=temp/'existing_output';nonempty.mkdir()
    (nonempty/'sentinel').write_text('preserve this')
    p=subprocess.run([str(binary),str(valid),str(nonempty),'synthetic'],capture_output=True,text=True)
    assert p.returncode and (nonempty/'sentinel').read_text()=='preserve this'
    yield 'refuses non-empty output directory'
    dest=temp/'already_exists.dol';dest.write_bytes(b'do not overwrite')
    p=subprocess.run([sys.executable,str(Path(maker.__file__)),str(dest)],capture_output=True,text=True)
    assert p.returncode and dest.read_bytes()==b'do not overwrite'
    yield 'refuses overwriting DOL destination'
    bad_owner=temp/'not_owner.dol';bad_owner.write_bytes(bytes(512))
    dest=temp/'forbidden.dol'
    p=subprocess.run([sys.executable,str(Path(maker.__file__)),str(dest),'--owner-dol',str(bad_owner)],capture_output=True,text=True)
    assert p.returncode and not dest.exists()
    yield 'rejects owner DOL SHA mismatch'
    invalid=temp/'short.dol';invalid.write_bytes(base[:100])
    out=temp/'short_output';out.mkdir()
    p=subprocess.run([str(binary),str(invalid),str(out),'synthetic'],capture_output=True,text=True)
    assert p.returncode and not list(out.iterdir())
    yield 'rejects truncated DOL'


def main():
    if len(sys.argv)!=3:
        raise SystemExit('Usage: test_fprinit_guards_v19.py GENERATOR PATCHED_UPSTREAM')
    count=0
    with TemporaryDirectory(prefix='v19-fpr-guards-') as name:
        temp=Path(name)
        for message in verify_patch(Path(sys.argv[2]),temp):count+=1
        for message in guard(Path(sys.argv[1]).resolve(),temp):count+=1
    print(f'PASS: {count} original-free V19 patch / input / callgraph rejection assertions')


if __name__=='__main__':main()
