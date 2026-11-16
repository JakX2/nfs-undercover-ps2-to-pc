#!/usr/bin/env python3
"""Fail-closed V52 owner-private Wii OSInit→interrupt integration guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_mmio_v52 import make, INTERRUPT_STOP as OLD_IRQ_STOP, NEXT_STOP as INTERRUPT_STOP
from make_osinit_interrupt_bridge_v51 import OSINIT, INTERRUPT, MEMSET, FILL, PREVIOUS_STOP as NEW_OSINIT_STOP
from make_osinit_module_v49 import MODULE
from make_osinit_alarm_bridge_v48 import OLD_STOP as OLD_OSINIT_STOP
from make_osinit_syscall_bridge_v46 import (SAVE, RESTORE, EXCEPTION_RETURN_START,
                                             DEBUG_PRINT, SOURCE)
from make_alarm_v47 import ALARM, SET, GET, SHUTDOWN


def be32(raw, index):
    return struct.unpack_from('>I', raw, index)[0]


def mutate_word(raw, address):
    data = bytearray(raw)
    for section in range(7):
        offset = be32(data, section*4)
        base = be32(data, 0x48+section*4)
        length = be32(data, 0x90+section*4)
        if base <= address < base+length:
            index=offset+address-base
            struct.pack_into('>I', data,index,be32(data,index)^1)
            return data
    raise ValueError(f'guest mutation address not mapped: {address:08x}')


def rejects(gen: Path, case: str, blob: bytes, dir: Path):
    mutated = dir / (case+'.dol')
    mutated.write_bytes(blob)
    out = dir / 'out'
    out.mkdir(exist_ok=True)
    if list(out.iterdir()):
        raise AssertionError('unexpected preexisting output')
    r = subprocess.run([str(gen), str(mutated), str(out)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        raise AssertionError(f'mutated V52 private image accepted: {case}')
    if list(out.iterdir()):
        raise AssertionError(f'generator wrote private C++ before validation: {case}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_original_dol',type=Path)
    ap.add_argument('generator',type=Path)
    args=ap.parse_args()
    if not args.generator.is_file():
        ap.error('missing V52 original-free native generator')
    baseline=make(args.owner_original_dol)
    count=0
    with tempfile.TemporaryDirectory(prefix='v52_private_guards_') as tmp:
        home=Path(tmp)
        dirty=bytearray(args.owner_original_dol.read_bytes())
        dirty[-1]^=0x01
        dirty_path=home/'modified_original.dol'
        dirty_path.write_bytes(dirty)
        try:make(dirty_path)
        except ValueError:count+=1
        else:raise AssertionError('modified original owner game DOL passed SHA')
        addresses={
            OSINIT, OSINIT+0x10, OSINIT+0x34,OSINIT+0x38,
            OLD_OSINIT_STOP,NEW_OSINIT_STOP,NEW_OSINIT_STOP+4,
            0x805208B4,0x805208B8,0x805208BC,INTERRUPT,OLD_IRQ_STOP,INTERRUPT_STOP,
            ALARM,GET,SET,SHUTDOWN,
            0x80520CA8,0x80520D98,0x80520DA4,0x80520DB4,
            0x80520DB8,0x80520DBc,0x80520DC0,0x80520E50,
            0x805265AC,0x805265D4,0x8052A824,0x8052AE80,
            0x80523B1C, 0x80522320, 0x80522378,
            0x804B7920,0x804B7A00,0x80521D48,0x80521D60,
            0x80521D50,0x80521D68,
        }
        ranges=(
            (EXCEPTION_RETURN_START,0x1c),
            (ALARM,0x58),
            (MODULE,0x18),
            (SET,0x24),
            (SHUTDOWN,0x88),
            (SOURCE,0x80),
            (SAVE,0x34),
            (RESTORE,0x34),
            (0x80004338,0x50),
            (INTERRUPT,0x60),
            (FILL,0xE4),
            (0x80522320,0x2c),
            (0x80522378,0x34),
            (0x804E50A0,0x18),
            (DEBUG_PRINT,8),
        )
        for begin,length in ranges:
            addresses.update(range(begin,begin+length,4))
        for address in sorted(addresses):
            rejects(args.generator,f'ppc_{address:08x}',mutate_word(baseline,address),home)
            count+=1
        # Original handler-source *data* also belongs to the source-pinned
        # private DOL; this detects accidental template corruption.
        orig_off=be32(baseline,0x1c)
        for at in range(0,0x98,4):
            mutated=bytearray(baseline)
            idx=orig_off+at
            struct.pack_into('>I',mutated,idx,be32(mutated,idx)^1)
            rejects(args.generator,f'handler_data_{at:02x}',mutated,home)
            count+=1
        # Fail closed for both actual original MMIO write sites and every
        # intervening original instruction through the new terminal stop.
        for pc in (0x80526654,0x80526664,0x8052666c,0x80526670):
            if pc not in addresses:
                raise AssertionError('missing mandatory original hardware write source coverage')
        # Invalid metadata must be rejected *without* generated source output.
        mutations=(('entry',0xe0,0x8000403c),
                   ('section0_len',0x90,0x34cc),
                   ('section1_addr',0x4c,0x805265B0),
                   ('section1_len',0x94,0x48e8),
                   ('memcpy_plus_memset_len',0x9c,0x50),
                   ('restore_len',0x98,0x7c),
                   ('marker_len',0xa4,0x18),
                   ('data_addr',0x64,0x80030000),
                   ('data_len',0xac,0x90),
                   ('unexpected_extra_text',0x18,0x100),
                   ('unexpected_extra_data',0x20,0x100))
        for name,offset,new in mutations:
            mutated=bytearray(baseline)
            struct.pack_into('>I',mutated,offset,new)
            rejects(args.generator,name,mutated,home)
            count+=1
        dest=home/'dont_overwrite'
        dest.mkdir()
        marker=dest/'keep.txt'
        marker.write_text('preserve')
        valid=home/'valid_private.dol'
        valid.write_bytes(baseline)
        result=subprocess.run([str(args.generator),str(valid),str(dest)],
                              capture_output=True,text=True,timeout=30)
        if result.returncode==0 or marker.read_text()!='preserve':
            raise AssertionError('nonempty output directory overwritten')
        count+=1
        target=home/'owner_private_existing.dol'
        target.write_bytes(b'STAY')
        script=Path(__file__).with_name('make_osinit_mmio_v52.py')
        r=subprocess.run(['python3',str(script),str(args.owner_original_dol),str(target)],
                         capture_output=True,text=True,timeout=30)
        if r.returncode==0 or target.read_bytes()!=b'STAY':
            raise AssertionError('V52 owner-private image builder overwrote destination')
        count+=1
    print(f'PASS: V52 {count}/{count} original-code/SHA/DOL/output corruption guards')

if __name__=='__main__':
    main()
