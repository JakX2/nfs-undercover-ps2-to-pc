#!/usr/bin/env python3
"""Owner-original V27 source-pin and fail-closed generated-DOL negative tests."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from make_execparams_v27 import make, ENTRY, COPY, STOP, word


def patch(blob, index, address, opcode):
    import struct
    offset = word(blob, 4*index)
    base = word(blob, 0x48+4*index)
    length = word(blob, 0x90+4*index)
    if not base <= address < base+length:
        raise ValueError('test patch address out of section')
    struct.pack_into('>I', blob, offset+address-base, opcode)


def rejects(generator, path, output):
    before = tuple(output.iterdir()) if output.exists() else ()
    proc = subprocess.run([str(generator), str(path), str(output)],
                          capture_output=True, text=True, timeout=25)
    assert proc.returncode != 0, (path, proc.stdout[-200:], proc.stderr[-400:])
    assert (tuple(output.iterdir()) if output.exists() else ()) == before, 'rejected input created output'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('owner_dol',type=Path)
    parser.add_argument('generator',type=Path)
    args=parser.parse_args()
    checks=0
    with tempfile.TemporaryDirectory(prefix='v27_guards_') as tmp:
        root=Path(tmp)
        owner=bytearray(args.owner_dol.read_bytes())
        owner[-1] ^= 1
        bad=root/'bad_owner.dol'; bad.write_bytes(owner)
        try:
            make(bad)
        except ValueError:
            checks+=1
        else:
            raise AssertionError('mutated original owner DOL was accepted')
        original=make(args.owner_dol)
        output=root/'out';output.mkdir()
        def invalid(name,fn):
            nonlocal checks
            image=bytearray(original)
            fn(image)
            path=root/(name+'.dol');path.write_bytes(image)
            rejects(args.generator,path,output)
            checks+=1
        for name,idx,addr,opcode in (
            ('exec_entry',0,ENTRY,0x60000000),
            ('exec_source',0,ENTRY+4,0x60000000),
            ('exec_copy_size',0,ENTRY+16,0x60000000),
            ('exec_tail',0,ENTRY+20,0x60000000),
            ('exec_zero_constant',0,ENTRY+24,0x60000000),
            ('exec_zero_store',0,ENTRY+28,0x60000000),
            ('memcpy_return',1,COPY+76,0x60000000),
            ('stop_syscall',2,STOP,0x60000000),
            ('stop_return',2,STOP+4,0x60000000),
        ):
            invalid(name,lambda image, i=idx,a=addr,o=opcode:patch(image,i,a,o))
        invalid('wrong_entry',lambda b:__import__('struct').pack_into('>I',b,0xe0,STOP))
        invalid('short_text',lambda b:__import__('struct').pack_into('>I',b,0x90,4))
        invalid('overlap_text',lambda b:__import__('struct').pack_into('>I',b,0x48+4,ENTRY))
        invalid('truncated_image',lambda b:b.__delitem__(slice(-24,None)))
        (output/'keep.txt').write_text('sentinel')
        rejects(args.generator,root/'exec_entry.dol',output)
        assert (output/'keep.txt').read_text()=='sentinel'
        checks+=1
    print(f'PASS: {checks} V27 original SHA/fixture mutation/overwrite guards')


if __name__=='__main__':
    main()
