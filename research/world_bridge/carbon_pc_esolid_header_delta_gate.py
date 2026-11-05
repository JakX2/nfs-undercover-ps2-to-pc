#!/usr/bin/env python3
"""V12: owner-original Carbon PC/PS2 paired eSolid header transform.

Matches 205/209 same-hash native Carbon controls exactly. Four special native
PC 0x00400016 version cases are classified, NOT fabricated. No game file IO.
The transform is an offline candidate, not a proven retail Carbon loader ABI.
"""
import struct


def inspect_header(header):
    if type(header) is not bytes or not 160 <= len(header) <= 512:
        raise ValueError('Invalid original serialized eSolid header')
    pad=0
    while pad<16 and header[pad:pad+4]==b'\x11'*4:pad+=4
    if pad not in (0,4,8,12) or header[pad:pad+12]!=bytes(12) or len(header)<pad+26:
        raise ValueError('Unsupported original eSolid header padding')
    version,identity,counts=struct.unpack_from('<III',header,pad+12)
    texture_count=header[pad+25]
    if version not in (0x16,0x800016,0x400016) or not identity or not 1<=texture_count<=127:
        raise ValueError('Unsupported serialized eSolid version/count/identity')
    return {'pad':pad,'version':version,'identity':identity,
            'triangles_candidate':counts&0xffff,'ps2_upper_count':counts>>16,
            'texture_count':texture_count,'length':len(header)-pad}


def normalize_ps2_header(header,expected_identity=None,expected_material_count=None,
                         expected_faces=None):
    """Only erase source PS2 upper16 at normalized +0x14; preserve all else.

    Special PS2 source version 0x800016 and native PC 0x400016 are intentionally
    unsupported here. Their correct mapping requires separate empirical proof.
    """
    d=inspect_header(header)
    if d['version']!=0x16 or not d['ps2_upper_count'] or not d['triangles_candidate']:
        raise ValueError('Unsupported PS2 header version/counters or already normalized')
    for expected,real,label in ((expected_identity,d['identity'],'model identity'),
                                (expected_material_count,d['texture_count'],'material count'),
                                (expected_faces,d['triangles_candidate'],'face count')):
        if expected is not None and (type(expected) is not int or expected!=real):
            raise ValueError('Original PS2 eSolid '+label+' mismatch')
    output=bytearray(header)
    struct.pack_into('<I',output,d['pad']+20,d['triangles_candidate'])
    result=bytes(output)
    if (len(result)!=len(header) or
            any(a!=b for i,(a,b) in enumerate(zip(header,result))
                if i not in (d['pad']+22,d['pad']+23)) or
            inspect_header(result)['identity']!=d['identity']):
        raise ValueError('PS2 header normalization modified an unexpected field')
    return result


def compare_same_model_headers(carbon_pc_header,carbon_ps2_header):
    pc=inspect_header(carbon_pc_header);ps=inspect_header(carbon_ps2_header)
    if (pc['identity']!=ps['identity'] or pc['texture_count']!=ps['texture_count'] or
            pc['length']!=ps['length']):
        raise ValueError('Native same-hash Carbon eSolid control metadata differs')
    candidate=normalize_ps2_header(carbon_ps2_header)[ps['pad']:]
    native=carbon_pc_header[pc['pad']:]
    if candidate==native:return 'exact'
    if (pc['version']==0x400016 and candidate[12:16]==struct.pack('<I',0x16) and
            candidate[:12]==native[:12] and candidate[16:]==native[16:]):
        return 'native_special_version_unresolved'
    raise ValueError('Unexplained Carbon PC versus PS2 original header difference')
