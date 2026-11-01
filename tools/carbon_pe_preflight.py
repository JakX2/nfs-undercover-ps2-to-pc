#!/usr/bin/env python3
"""V63: read-only PE32 address-map preflight for historical Carbon chunk loader.

The fixed virtual addresses below are PINNED to the independently reviewed
public XNFSModFiles Carbon_addresses.h source (Git blob
0720a4ccc79d5ffc132bb179322fc1554a394024, commit
de4164ac55620f38a173ddf855c28bd036e74883).

A mapped, executable PE section is merely a *prerequisite* for a hook.
It is NEVER code signature verification, correct-game-version evidence,
a callable-function ABI proof, or authorization to patch the executable.
This tool does not install, modify, inject into, or execute anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct

CARBON_XNFS_SOURCE={
    'repository':'xan1242/xnfsmodfiles',
    'commit':'de4164ac55620f38a173ddf855c28bd036e74883',
    'header_git_blob':'0720a4ccc79d5ffc132bb179322fc1554a394024',
    'loader_git_blob':'a0a9ed10724645ae5a1074ab5c971ea4d1f082fe',
}
# Source-derived virtual addresses from the 2017 public loader, NOT
# independently recovered from an original Carbon executable.
CARBON_HISTORICAL_VAS={
    'CreateResourceFile':0x006B32C0,
    'BeginLoading':0x006B5910,
    'Stage1JumpEntry':0x006B6D56,
    'Stage2CallEntry':0x006B7850,
}
IMAGE_SCN_MEM_EXECUTE=0x20000000


class PEError(ValueError):
    pass


def _u16(data,at):
    if at<0 or at+2>len(data):raise PEError('Truncated PE field')
    return struct.unpack_from('<H',data,at)[0]


def _u32(data,at):
    if at<0 or at+4>len(data):raise PEError('Truncated PE field')
    return struct.unpack_from('<I',data,at)[0]


def parse_pe32(data):
    """Interpret bounded PE32 headers only, no import resolution or disasm."""
    if len(data)<0x40 or data[:2]!=b'MZ':
        raise PEError('Not an MZ executable')
    pe=_u32(data,0x3C)
    if pe<0x40 or pe>1024*1024 or pe+24>len(data) or data[pe:pe+4]!=b'PE\x00\x00':
        raise PEError('Missing or out-of-bounds PE signature')
    coff=pe+4
    machine=_u16(data,coff)
    section_count=_u16(data,coff+2)
    optional_size=_u16(data,coff+16)
    if not 1<=section_count<=96 or optional_size<64:
        raise PEError('Invalid PE section count or optional header size')
    opt=coff+20
    if opt+optional_size>len(data):
        raise PEError('Optional header outside file')
    magic=_u16(data,opt)
    if magic!=0x10B:
        raise PEError('Expected PE32 optional header, not PE32+ or unknown')
    image_base=_u32(data,opt+28)
    image_size=_u32(data,opt+56)
    if image_size==0 or image_base==0 or image_base+image_size>0x100000000:
        raise PEError('Invalid 32-bit PE image range')
    section_start=opt+optional_size
    if section_start+section_count*40>len(data):
        raise PEError('Section table outside file')
    sections=[]
    for idx in range(section_count):
        at=section_start+idx*40
        raw_name=bytes(data[at:at+8])
        name=raw_name.partition(b'\x00')[0].decode('ascii','replace')
        vsize=_u32(data,at+8)
        rva=_u32(data,at+12)
        rawsize=_u32(data,at+16)
        rawstart=_u32(data,at+20)
        flags=_u32(data,at+36)
        if rva+max(vsize,rawsize)>image_size:
            raise PEError('Section exceeds declared image size')
        if rawsize and (rawstart>len(data) or rawsize>len(data)-rawstart):
            raise PEError('Section raw data exceeds file')
        sections.append({'name':name or f'section_{idx}',
                         'rva':rva,'virtual_size':vsize,
                         'raw_offset':rawstart,'raw_size':rawsize,
                         'executable':bool(flags & IMAGE_SCN_MEM_EXECUTE)})
    return {'machine':machine,'image_base':image_base,'image_size':image_size,
            'optional_header_magic':'PE32',
            'sections':sections}


def audit_address(pe,virtual_address):
    if not 0<=virtual_address<=0xFFFFFFFF:
        raise PEError('Virtual address outside 32-bit range')
    base=pe['image_base']
    rva=virtual_address-base
    answer={'virtual_address':f'0x{virtual_address:08X}',
            'rva':f'0x{rva:08X}' if 0<=rva<pe['image_size'] else None,
            'within_image':0<=rva<pe['image_size'],
            'section':None,'in_executable_section':False,
            'file_backed':False,'file_offset':None,
            'candidate_hook_location_only':True,
            'verified_function_or_hook_abi':False}
    if not answer['within_image']:
        return answer
    matches=[s for s in pe['sections']
             if s['rva']<=rva<s['rva']+max(s['virtual_size'],s['raw_size'])]
    if len(matches)!=1:
        answer['overlapping_or_missing_section']=len(matches)!=1
        return answer
    s=matches[0]
    d=rva-s['rva']
    answer['section']=s['name']
    answer['in_executable_section']=s['executable']
    if d<s['raw_size']:
        answer['file_backed']=True
        answer['file_offset']=s['raw_offset']+d
    return answer


def _file_identity(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def inspect_executable(path:Path,*,expected_sha256:str|None=None):
    """Hash, parse and rehash one read-only input handle (best effort)."""
    if expected_sha256 is not None:
        if (not isinstance(expected_sha256,str)
                or len(expected_sha256)!=64
                or any(c not in '0123456789abcdefABCDEF' for c in expected_sha256)):
            raise PEError('Expected SHA-256 must be exactly 64 hexadecimal digits')
        expected_sha256=expected_sha256.lower()
    with path.open('rb') as fh:
        before=os.fstat(fh.fileno())
        if before.st_size==0:
            raise PEError('Empty executable')
        with mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ) as data:
            digest=hashlib.sha256(data).hexdigest()
            if expected_sha256 is not None and digest!=expected_sha256:
                raise PEError('Executable SHA-256 mismatch')
            pe=parse_pe32(data)
            if pe['machine']!=0x14C:
                raise PEError('Not a 32-bit x86 PE executable')
            addresses={k:audit_address(pe,v)
                       for k,v in CARBON_HISTORICAL_VAS.items()}
            if hashlib.sha256(data).hexdigest()!=digest:
                raise PEError('Executable changed during preflight')
        after=os.fstat(fh.fileno())
        try: current=path.stat()
        except OSError as exc:
            raise PEError('Executable path vanished during preflight') from exc
        if (current.st_dev,current.st_ino)!=(after.st_dev,after.st_ino):
            raise PEError('Executable path replaced during preflight')
        if _file_identity(before)!=_file_identity(after):
            raise PEError('Executable metadata changed during preflight')
    all_mapped=all(v['within_image'] and v['file_backed'] and
                   v['in_executable_section'] for v in addresses.values())
    return {
        'schema':'v63-static-carbon-runtime-address-preflight-v1',
        'input_executable_sha256':digest,
        'input_file_size_bytes':before.st_size,
        'expected_executable_sha256_guard_applied':expected_sha256 is not None,
        'pe_machine':'i386',
        'pe_image_base':f"0x{pe['image_base']:08X}",
        'pe_image_size_bytes':pe['image_size'],
        'pe_section_count':len(pe['sections']),
        'historical_public_plugin':CARBON_XNFS_SOURCE,
        'historical_address_checks':addresses,
        'historical_addresses_in_executable_file_backed_sections':all_mapped,
        'historical_address_layout_compatible_prerequisite_only':all_mapped,
        'executable_version_authenticated_as_supported':False,
        'hook_bytes_or_instruction_boundaries_verified':False,
        'engine_function_ABI_verified':False,
        'resource_file_loader_runtime_verified':False,
        'world_scenery_registration_verified':False,
        'safe_to_install_or_patch':False,
        'read_only':True,'atomic_filesystem_snapshot':False,
        'warnings':[
            'Public XNFSModFiles address constants are from a 2017 project, not validated against this actual executable build.',
            'Address presence in an executable .text section does not prove correct instructions, function boundaries, or calling convention.',
            'The public plugin installs runtime detours and its old filename parser has unchecked input-length behavior; do not run it unchanged as a safety test.',
            'A resource-file load request does not demonstrate streaming-table registration, scenery placement, texture/material binding, collision, navigation or rendering.',
            'No original executable code bytes or private local paths are included in this report.',
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--executable',required=True,type=Path)
    p.add_argument('--expected-sha256')
    p.add_argument('--report',required=True,type=Path)
    args=p.parse_args()
    if args.report.exists() or args.report.resolve()==args.executable.resolve():
        p.error('Refusing to overwrite input or existing report')
    result=inspect_executable(args.executable,expected_sha256=args.expected_sha256)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,sort_keys=True)
        out.write('\n')
    print('V63 static-only:',sum(x['in_executable_section'] and x['file_backed']
          for x in result['historical_address_checks'].values()),
          'historical address locations map to file-backed executable sections.')
    print('No loader ABI or safe live patch established. No game file modified.')


if __name__=='__main__':
    main()
