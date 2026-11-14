#!/usr/bin/env python3
"""Original-free safety/rejection suite for V24's bounded DOL slicer/emitter."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_start_to_dbinit_v24 import make, START, DBINIT, DBPRINTF, OSINIT


def write32(data, offset, value):
    struct.pack_into('>I', data, offset, value)


def generate(emitter, dol, out, mode, succeed=False):
    before = list(out.iterdir()) if out.exists() else []
    p = subprocess.run([str(emitter), str(dol), str(out), mode],
                       capture_output=True, text=True, timeout=20)
    if succeed:
        assert p.returncode == 0, (p.stdout, p.stderr)
        assert (out/'output.cpp').is_file(), 'successful extraction missing output'
    else:
        assert p.returncode != 0, (mode, p.stdout, p.stderr)
        assert (list(out.iterdir()) if out.exists() else []) == before, 'rejected input wrote generated source'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('emitter', type=Path)
    ap.add_argument('--owner-dol', type=Path)
    args = ap.parse_args()
    args.emitter = args.emitter.resolve()
    count = 0
    with tempfile.TemporaryDirectory(prefix='v24_guards_') as d:
        root = Path(d)
        data = bytearray(make(None))
        original = root/'synthetic.dol'
        original.write_bytes(data)
        for mode in ('owner', 'unexpected', '', 'OWNER', 'synthetic '):
            out = root/'out'
            out.mkdir(exist_ok=True)
            generate(args.emitter, original, out, mode)
            count += 1
        out = root/'absent'
        generate(args.emitter, original, out, 'synthetic')
        count += 1
        out.mkdir()
        (out/'keep.txt').write_text('do not overwrite')
        generate(args.emitter, original, out, 'synthetic')
        assert (out/'keep.txt').read_text() == 'do not overwrite'
        count += 1
        (out/'keep.txt').unlink()
        def mutate(label, func):
            nonlocal count
            b = bytearray(data)
            func(b)
            path = root / (label + '.dol')
            path.write_bytes(b)
            generate(args.emitter, path, out, 'synthetic')
            count += 1
        # DOL header and bounded section metadata errors.
        mutate('entry_invalid', lambda b: write32(b, 0xe0, 0x80004040))
        mutate('text_offset_zero', lambda b: write32(b, 0, 0))
        mutate('text_size_huge', lambda b: write32(b, 0x90, 0x10000000))
        mutate('text_offset_header', lambda b: write32(b, 0, 0x80))
        mutate('text_unaligned', lambda b: write32(b, 0, 0x101))
        mutate('text_guest_unaligned', lambda b: write32(b, 0x48, 0x8000403d))
        mutate('text_guest_outside', lambda b: write32(b, 0x48, 0x7000403c))
        mutate('text_guest_overflow', lambda b: write32(b, 0x48, 0x817ffffc))
        mutate('data_size_huge', lambda b: write32(b, 0xac, 0x10000000))
        mutate('data_file_overlap', lambda b: write32(b, 0x1c, 0x100))
        mutate('data_guest_overlap', lambda b: write32(b, 0x64, 0x8000403c))
        mutate('second_code_offset_alias', lambda b: write32(b, 4, 0x100))
        # Find synthetic guest instruction locations through the section header.
        def patch_pc(b, pc, word):
            off = struct.unpack_from('>I', b, 0)[0]
            addr = struct.unpack_from('>I', b, 0x48)[0]
            write32(b, off + pc - addr, word)
        mutate('startup_wrong_register_call',lambda b:patch_pc(b,START,0x48000169))
        mutate('startup_wrong_data_call',lambda b:patch_pc(b,START+24,0x480001e1))
        mutate('startup_wrong_db_call',lambda b:patch_pc(b,0x80004058,0x48000001))
        mutate('startup_wrong_os_call',lambda b:patch_pc(b,0x8000405c,0x48000001))
        mutate('startup_missing_return',lambda b:patch_pc(b,0x80004060,0x60000000))
        def patch_db(b, addr, word):
            off = struct.unpack_from('>I', b, 0+4*6)[0]
            start = struct.unpack_from('>I', b, 0x48+4*6)[0]
            write32(b, off + addr - start, word)
        mutate('missing_db_blr',lambda b:patch_db(b,DBINIT+12,0x60000000))
        mutate('wrong_synthetic_store',lambda b:patch_db(b,DBINIT+8,0x60000000))
        def patch_os(b, addr, word):
            off = struct.unpack_from('>I', b, 0+4)[0]
            start = struct.unpack_from('>I', b, 0x48+4)[0]
            write32(b, off + addr - start, word)
        mutate('osinit_missing_stop',lambda b:patch_os(b,OSINIT,0x60000000))
        mutate('osinit_missing_return',lambda b:patch_os(b,OSINIT+4,0x60000000))
        mutate('debug_missing_stub',lambda b:patch_db(b,DBPRINTF,0x60000000))
        for n in (0,1,127,255,len(data)-1):
            path=root/f'truncated_{n}.dol'
            path.write_bytes(data[:n])
            generate(args.emitter, path, out, 'synthetic')
            count += 1
        if args.owner_dol:
            owner = args.owner_dol
            original_bytes = bytearray(owner.read_bytes())
            original_bytes[-1] ^= 1
            altered=root/'tampered_owner.dol'
            altered.write_bytes(original_bytes)
            try:
                make(altered)
                raise AssertionError('owner file SHA mismatch accepted')
            except ValueError:
                pass
            count += 1
            owner_private=root/'owner_private.dol'
            owner_private.write_bytes(make(owner))
            owner_data=bytearray(owner_private.read_bytes())
            def patch_owner(label, pc, word):
                nonlocal count
                b=bytearray(owner_data)
                off=struct.unpack_from('>I',b,0)[0]
                write32(b, off+pc-START,word)
                path=root/(label+'.dol')
                path.write_bytes(b)
                generate(args.emitter,path,out,'owner')
                count += 1
            patch_owner('owner_db_link_wrong',0x80004158,0x60000000)
            patch_owner('owner_os_link_wrong',0x8000415c,0x60000000)
            patch_owner('owner_alternative_boot_unguarded',0x800040c8,0x4bffff61)
            patch_owner('owner_indirect_boot_unguarded',0x800040dc,0x4e800021)
            # Original DBInit MUST contain all three guest stores.
            b=bytearray(owner_data)
            off=struct.unpack_from('>I',b,0x18)[0]
            write32(b,off+5*4,0x60000000)
            path=root/'owner_db_missing_store.dol'
            path.write_bytes(b)
            generate(args.emitter,path,out,'owner')
            count += 1
        print(f'PASS: {count} original-free V24 unsafe-input/owner-boundary rejections')


if __name__ == '__main__':
    main()
