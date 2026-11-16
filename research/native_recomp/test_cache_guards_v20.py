#!/usr/bin/env python3
"""Source-only V20 malformed-DOL and patch-safety regression suite."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path

from apply_l2cr_v20 import apply as patch, CONTEXT, EMITTER
from make_cache_slice_v20 import make, CACHE, L2_READ, MSR_READ, IC_ENABLE, DC_ENABLE


def _u32(blob, offset):
    return struct.unpack_from('>I', blob, offset)[0]


def map_guest(blob, address):
    for i in range(7):
        offset, base, size = (_u32(blob, x + 4*i) for x in (0,0x48,0x90))
        if offset and base <= address < base + size:
            return offset + address - base
    raise ValueError('fixture address missing')


def set_word(blob, address, opcode):
    struct.pack_into('>I', blob, map_guest(blob,address), opcode)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('generator',type=Path)
    ap.add_argument('patched_upstream',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    assert args.generator.is_file()
    checks=0
    with tempfile.TemporaryDirectory(prefix='v20_guards_') as scratch:
        tmp=Path(scratch)
        original=make(None)
        def fail(blob,mode='synthetic'):
            nonlocal checks
            output=tmp/'result';output.mkdir()
            path=tmp/'invalid.dol';path.write_bytes(blob)
            p=subprocess.run([str(args.generator),str(path),str(output),mode],
                             capture_output=True,text=True,timeout=10)
            assert p.returncode!=0, f'generator accepted invalid fixture {checks}: {p.stdout}'
            assert not list(output.iterdir()),'rejected generation left proprietary outputs'
            checks+=1
            path.unlink();output.rmdir()
        def change_word(addr,code):
            b=bytearray(original);set_word(b,addr,code);fail(bytes(b))
        fail(original[:255])
        fail(original[:-1])
        b=bytearray(original);struct.pack_into('>I',b,0xe0,0x80000000);fail(bytes(b))
        b=bytearray(original);struct.pack_into('>I',b,0,0x00);fail(bytes(b))
        b=bytearray(original);struct.pack_into('>I',b,0x90,0xff000000);fail(bytes(b))
        b=bytearray(original);struct.pack_into('>I',b,0x48,0x100);fail(bytes(b))
        b=bytearray(original);struct.pack_into('>I',b,4,_u32(b,0));fail(bytes(b))
        b=bytearray(original);struct.pack_into('>I',b,0x90,0);fail(bytes(b))
        # Source-only synthetic L2CR helper corruption.
        change_word(L2_READ,0x60000000)
        change_word(L2_READ+4,0x60000000)
        change_word(MSR_READ,0x60000000)
        change_word(CACHE+80,0x60000000)
        change_word(IC_ENABLE,0x60000000)
        change_word(DC_ENABLE,0x60000000)
        fail(original,mode='untrusted')
        # Present but nonempty destination must never be touched.
        output=tmp/'nonempty';output.mkdir();(output/'keep').write_text('do not overwrite')
        path=tmp/'valid.dol';path.write_bytes(original)
        p=subprocess.run([str(args.generator),str(path),str(output),'synthetic'],
                         capture_output=True,text=True,timeout=10)
        assert p.returncode!=0 and (output/'keep').read_text()=='do not overwrite'
        checks+=1
        output_missing=tmp/'missing-dir'
        p=subprocess.run([str(args.generator),str(path),str(output_missing),'synthetic'],
                         capture_output=True,text=True,timeout=10)
        assert p.returncode!=0 and not output_missing.exists()
        checks+=1
        # Original DOL is not needed: any wrong SHA must be rejected before
        # source bytes are extracted or copied to a private temporary DOL.
        bad_owner=tmp/'not_original.dol';bad_owner.write_bytes(original)
        try:
            make(bad_owner)
            raise AssertionError('owner DOL without expected SHA accepted')
        except ValueError:
            checks+=1
        # Source patch tests use only two copied TEXT files; no upstream edits.
        root=tmp/'upstream'
        (root/CONTEXT).parent.mkdir(parents=True)
        (root/EMITTER).parent.mkdir(parents=True)
        for file in (CONTEXT,EMITTER):
            (root/file).write_bytes((args.patched_upstream/file).read_bytes())
        assert patch(root) is False
        checks+=1
        # A changed emitter must fail without altering CPUContext.
        old=(root/CONTEXT).read_bytes()
        emitter=(root/EMITTER)
        emitter.write_text(emitter.read_text().replace('ctx.read_l2cr(); // mfspr L2CR',
                                                      'ctx.stale_l2cr(); // mfspr L2CR'))
        try:
            patch(root)
            raise AssertionError('conflicting emitter patch accepted')
        except ValueError:
            assert (root/CONTEXT).read_bytes()==old
            checks+=1
        if args.owner_dol:
            # Owner mode only; never write or print the proprietary bytecode.
            from make_cache_slice_v20 import validate_original, get_text, CACHE_BYTES
            blob=bytearray(args.owner_dol.read_bytes())
            cache=get_text(blob,CACHE,CACHE_BYTES)
            bad=bytearray(cache);bad[-4:]=b'\0\0\0\0'
            try:
                validate_original(bytes(bad),b'')
                raise AssertionError('original __OSCacheInit last BLR not validated')
            except ValueError:
                checks+=1
    print(f'PASS: {checks} V20 original-free guard and idempotence tests')


if __name__=='__main__':
    main()
