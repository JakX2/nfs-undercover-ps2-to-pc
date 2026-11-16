#!/usr/bin/env python3
"""Original-free negative tests: malformed startup slices never emit C++ files."""
import struct
import subprocess
import sys
from pathlib import Path


def fail_extract(executable: Path, dol: Path, root: Path, tag: str,
                 mode: str = 'synthetic'):
    out = root / ('out_' + tag)
    out.mkdir()
    p = subprocess.run([str(executable), str(dol), str(out), mode],
                       text=True, capture_output=True, timeout=20)
    assert p.returncode != 0, (tag, p.stdout, p.stderr)
    assert list(out.iterdir()) == [], (tag, 'rejected input wrote output files')


def mutate(base: bytes, root: Path, name: str, at: int, word: int) -> Path:
    copy = bytearray(base)
    struct.pack_into('>I', copy, at, word)
    target = root / (name + '.dol')
    target.write_bytes(copy)
    return target


def main():
    if len(sys.argv) != 5:
        raise SystemExit('Usage: tests.py GENERATOR SYNTHETIC_DOL WORKDIR BUILDER_PY')
    generator, synthetic, root, builder = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
    raw = synthetic.read_bytes()
    off = lambda i: struct.unpack_from('>I', raw, 4*i)[0]
    # ENTRY=first text, REGS=second text, HW=third text, service stubs 4-6.
    entry, regs, hw, service0, service1, service2 = [off(i) for i in range(6)]
    checks=0
    for tag, pos, word in [
        ('entry_wrong_bl1',entry,0x48000001),
        ('entry_wrong_bl2',entry+4,0x48000001),
        ('entry_stop_missing',entry+8,0x60000000),
        ('entry_missing_blr',entry+12,0x60000000),
        ('regs_missing_blr',regs+4,0x60000000),
        ('hw_mfmsr',hw,0x60000000),
        ('hw_ori_msr_bit',hw+4,0x60e74000),
        ('hw_mtmsr',hw+8,0x60000000),
        ('hw_mflr',hw+12,0x60000000),
        ('hw_bl_service_1',hw+16,0x48000001),
        ('hw_bl_service_2',hw+20,0x48000001),
        ('hw_bl_service_3',hw+24,0x48000001),
        ('hw_mtlr',hw+28,0x60000000),
        ('hw_missing_blr',hw+32,0x60000000),
        ('first_service_no_sc',service0,0x60000000),
        ('second_service_no_sc',service1,0x60000000),
        ('third_service_no_sc',service2,0x60000000),
        ('first_service_no_blr',service0+4,0x60000000),
        ('wrong_entrypoint',0xe0,0x80004040),
        ('unaligned_text',0x48,0x8000403d),
        ('oversized_section',0x90,0x10000000),
        ('missing_service_slot',0x14,0),
    ]:
        path = mutate(raw,root,tag,pos,word)
        fail_extract(generator,path,root,tag)
        checks+=1
    nonempty=root/'nonempty'
    nonempty.mkdir()
    (nonempty/'no-overwrite').write_text('sentinel')
    p=subprocess.run([str(generator),str(synthetic),str(nonempty),'synthetic'],
                     capture_output=True,text=True,timeout=20)
    assert p.returncode!=0 and (nonempty/'no-overwrite').read_text()=='sentinel'
    checks+=1
    fail_extract(generator,synthetic,root,'wrong_mode',mode='unverified')
    checks+=1
    tampered=root/'tampered_owner.dol'
    tampered.write_bytes(raw)
    target=root/'refused_owner.dol'
    p=subprocess.run([sys.executable,str(builder),str(target),'--owner-dol',str(tampered)],
                     capture_output=True,text=True,timeout=20)
    assert p.returncode!=0 and not target.exists(), 'owner SHA pin bypassed'
    checks+=1
    existing=root/'existing.dol'
    existing.write_bytes(b'unchanged')
    p=subprocess.run([sys.executable,str(builder),str(existing)],
                     capture_output=True,text=True,timeout=20)
    assert p.returncode!=0 and existing.read_bytes()==b'unchanged'
    checks+=1
    print(f'PASS: {checks} original-free unsafe startup input and output rejection checks')


if __name__ == '__main__': main()
