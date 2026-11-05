#!/usr/bin/env python3
"""Read-only Carbon PC executable preflight for public XNFSModFiles hook sites.

Checks third-party address-to-PE mappings against an audited owner-original
NFSC.exe. NEVER loads an ASI, modifies an executable/installation, or claims
engine ABI compatibility, model registration, or rendering.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

REFERENCE_ADDRESSES = {
    'create_resource': 0x006B32C0,
    'begin_loading': 0x006B5910,
    'preinit_cave': 0x006B6D56,
    'preinit_resume': 0x006B6D76,
    'postinit_cave': 0x006B7850,
}
AUDITED_EXE_SHA256 = 'baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3'
MAX_EXE_BYTES = 64 * 1024 * 1024
MAX_SECTION_HEADERS = 64
MIN_SPAN = 16


def inspect_exe(blob, addresses=None):
    if (type(blob) is not bytes or not 512 <= len(blob) <= MAX_EXE_BYTES or
            blob[:2] != b'MZ'):
        raise ValueError('Not a bounded 32-bit Windows PE executable')
    if addresses is None:
        addresses = REFERENCE_ADDRESSES
    if (not isinstance(addresses, dict) or not addresses or
            any(not isinstance(name, str) or not name or type(addr) is not int or addr <= 0
                for name, addr in addresses.items())):
        raise ValueError('Malformed external loader address set')
    offset = struct.unpack_from('<I', blob, 0x3c)[0]
    if not 64 <= offset <= len(blob) - 24 or blob[offset:offset+4] != b'PE\x00\x00':
        raise ValueError('Missing bounded PE signature')
    machine, nsections, opt_size = (struct.unpack_from('<H', blob, offset+k)[0] for k in (4, 6, 20))
    opt = offset + 24
    if (machine != 0x14c or not 1 <= nsections <= MAX_SECTION_HEADERS or
            opt_size < 96 or opt + opt_size > len(blob) or
            struct.unpack_from('<H',blob,opt)[0] != 0x10b):
        raise ValueError('Unsupported PE architecture, header or section count')
    image_base = struct.unpack_from('<I', blob, opt+28)[0]
    table = opt + opt_size
    if table + nsections*40 > len(blob):
        raise ValueError('Truncated PE section header table')
    sections = []
    for i in range(nsections):
        at=table+i*40
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', blob, at+8)
        characteristics = struct.unpack_from('<I', blob, at+36)[0]
        if (virtual_size <= 0 or raw_size <= 0 or
                raw_offset > len(blob) or raw_size > len(blob)-raw_offset):
            raise ValueError('Invalid PE section span')
        sections.append((rva, virtual_size, raw_offset, raw_size, characteristics))
    resolved = {}
    for key, address in addresses.items():
        rva=address-image_base
        mapped=[]
        for start, virtual_size, file_start, raw_size, flags in sections:
            if (flags & 0x20000000) and start <= rva and rva-start <= min(virtual_size,raw_size)-MIN_SPAN:
                off=file_start+(rva-start)
                if blob[off:off+MIN_SPAN] != bytes(MIN_SPAN):
                    mapped.append(off)
        if len(mapped) != 1:
            raise ValueError('External loader hook site is not unique executable code')
        resolved[key] = mapped[0]
    return {
        'scope': 'READ_ONLY_THIRD_PARTY_CARBON_LOADER_ADDRESS_COMPATIBILITY_NOT_EXECUTION',
        'pe32_x86': True,
        'image_base_matches_external_addresses': image_base == 0x400000,
        'external_addresses_examined': len(addresses),
        'all_external_addresses_in_executable_section': True,
        'all_external_addresses_nonzero_machine_code': True,
        'matches_owner_audited_original_nfsc_sha256': (
            hashlib.sha256(blob).hexdigest() == AUDITED_EXE_SHA256),
        'code_injection_performed': False,
        'runtime_compatibility_verified': False,
        'custom_bundle_loaded': False,
        'native_scenery_registration_verified': False,
    }


def audit_file(path):
    p = Path(path).absolute()
    if (any(x.is_symlink() for x in (p,*p.parents)) or not p.is_file() or
            not 512 <= p.stat().st_size <= MAX_EXE_BYTES):
        raise ValueError('Owner NFSC.exe missing or unsafe to inspect')
    before=p.stat()
    blob=p.read_bytes()
    result=inspect_exe(blob)
    after=p.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Owner executable changed during read-only preflight')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--carbon-exe',required=True)
    args=ap.parse_args()
    print(json.dumps(audit_file(args.carbon_exe),indent=2))


if __name__=='__main__':
    main()
