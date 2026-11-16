#!/usr/bin/env python3
"""Owner-private original __start -> __init_data DOL slicing.

No original machine code is included in this script. In owner mode, all guest
instructions come from the user's SHA-pinned original Wii DOL, except an
explicit synthetic sc/blr at 0x80004058. Wii debug/error service boundaries
remain inherited synthetic test callbacks from V21.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from make_icdc_slice_v21 import make as make_v21
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_initdata_slice_v22 import (
    ENTRY as DATA_INIT, END as DATA_END, TABLE, TABLE_LENGTH,
    check_code, get_section, parse_table, make_synthetic_table,
)

START = 0x8000403C
RETURN_PC = 0x80004058
REGISTER_INIT = 0x800041A8
HARDWARE = 0x800042E0
BLR = 0x4E800020
SC = 0x44000002
NOP = 0x60000000
SYNTH_DATA_DEST = 0x80036000


def synthetic_data_init():
    """Independently authored PPC body; zero one guest memory word and return.

    lis r8,0x8003 ; li r0,0 ; stw r0,0x6000(r8) ; blr
    """
    return struct.pack('>IIII', 0x3D008003, 0x38000000, 0x90086000, BLR)


def make(owner: Path | None):
    base = make_v21(owner)
    source = None
    if owner is not None:
        source = owner.read_bytes()
        if hashlib.sha256(source).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner DOL SHA-256 mismatch')
    first_offset = struct.unpack_from('>I', base, 0)[0]
    first_addr = struct.unpack_from('>I', base, 0x48)[0]
    first_size = struct.unpack_from('>I', base, 0x90)[0]
    if first_addr != START or first_size != HARDWARE + 36 - START:
        raise ValueError('unexpected V21 first section layout')
    first = bytearray(base[first_offset:first_offset + first_size])
    for i, target in enumerate((REGISTER_INIT, HARDWARE)):
        w = struct.unpack_from('>I', first, i * 4)[0]
        if linked_target(w, START + 4 * i) != target:
            raise ValueError('V21 startup prefix call target changed')
    if source is not None:
        # Exact original startup instructions from 0x80004044 to the third BL.
        prefix = get_text(source, START + 8, RETURN_PC - (START + 8))
        data_code = get_text(source, DATA_INIT, DATA_END - DATA_INIT)
        check_code(data_code)
        table = get_section(source, TABLE, TABLE_LENGTH)
        copy_rows, bss_rows = parse_table(table)
        if len(copy_rows) != 11 or len(bss_rows) != 3 or any(s != d for s,d,n in copy_rows):
            raise ValueError('owner original initialization table shape changed')
        if linked_target(struct.unpack_from('>I', prefix, len(prefix)-4)[0], RETURN_PC-4) != DATA_INIT:
            raise ValueError('original __start third call is not __init_data')
        # Hardware code is already in the V21 section; owner data slice may
        # not silently modify it when filling the neighboring text region.
        old_hardware = first[HARDWARE-START:HARDWARE-START+36]
        if data_code[HARDWARE-DATA_INIT:HARDWARE-DATA_INIT+36] != old_hardware:
            raise ValueError('owner __init_hardware differs between V21 and V22')
        resized = bytearray(NOP.to_bytes(4, 'big') * ((DATA_END-START)//4))
        resized[:len(first)] = first
        resized[DATA_INIT-START:DATA_END-START] = data_code
        resized[START+8-START:RETURN_PC-START] = prefix
        first = resized
    else:
        # Independent synthetic fixture: no game-derived instructions.
        # Re-use V21's independently written synthetic register/HW routines,
        # and introduce one four-instruction guest-memory-initializing leaf.
        first[DATA_INIT-START:DATA_INIT-START+16] = synthetic_data_init()
        first[START+8-START:RETURN_PC-START] = struct.pack('>5I',
            0x3800FFFF, 0x9421FFF8, 0x90010004, 0x90010000,
            0x480001E5) # original-free startup-shaped PPC assembly
        table = make_synthetic_table()
    first[RETURN_PC-START:RETURN_PC-START+8] = struct.pack('>II', SC, BLR)
    # Restrict execution after the third original BL. The synthetic stop is
    # conspicuous and ensures no code from the original fourth startup phase
    # can run in this bounded test.
    sections = [(START, bytes(first))]
    for i in range(1, 7):
        ofs, addr, length = (struct.unpack_from('>I',base,header+4*i)[0]
                             for header in (0,0x48,0x90))
        if not ofs or not length:
            raise ValueError('V21 section missing')
        sections.append((addr, base[ofs:ofs+length]))
    size = 256 + sum((len(payload)+3)&~3 for _, payload in sections) + len(table)
    result = bytearray(size)
    at = 256
    for i,(addr,contents) in enumerate(sections):
        for header,value in ((0,at),(0x48,addr),(0x90,len(contents))):
            struct.pack_into('>I',result,header+4*i,value)
        result[at:at+len(contents)] = contents
        at += (len(contents)+3)&~3
    # DOL data section is distinct from code: actual Wii runtime must copy
    # the relocation/BSS table to the guest MMU before calling run_game.
    for header,value in ((0x1c,at),(0x64,TABLE),(0xac,len(table))):
        struct.pack_into('>I',result,header,value)
    result[at:at+len(table)] = table
    struct.pack_into('>I',result,0xe0,START)
    return bytes(result)


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('destination',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    if args.destination.exists():
        ap.error('refusing to overwrite existing private test DOL')
    args.destination.write_bytes(make(args.owner_dol))
    print('V23 private startup->data DOL created (owner:', bool(args.owner_dol), ')')
