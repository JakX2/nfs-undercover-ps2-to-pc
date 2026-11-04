#!/usr/bin/env python3
"""Source-free PC-shaped 0xB3300000 texture-pack *synthetic test envelope*.

All names MUST start with SYNTH_; no original hashes, images, source chunks,
headers or materials are copied. This is deliberately NOT an installable native
Carbon PC texture pack. Only field widths/orders cross-checked by the existing
metadata parser are populated; unknown 0x33310001 / sampler / root header
fields are synthetic placeholders. Original 24-byte PC platform records were
separately confirmed to have zero bytes outside the DXT FOURCC. No disk writes or runtime claims.
"""
import struct
from synthetic_dxt1_texture_writer import encode_dxt1_mips
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array

MAX_PACK_TEXTURES = 16
MAX_SECTION_BYTES = 32 * 1024 * 1024


def _chunk(cid, payload):
    return struct.pack('<II', cid, len(payload)) + payload


def _validate_entry(row):
    if not isinstance(row, dict) or set(row) != {'hash','name','width','height','rgba','mip_levels'}:
        raise ValueError('Expected explicit synthetic texture fields')
    identity, name, w, h, levels = (row[x] for x in ('hash','name','width','height','mip_levels'))
    if type(identity) is not int or not 0 < identity <= 0xffffffff:
        raise ValueError('Invalid synthetic identity')
    if (not isinstance(name, bytes) or not name.startswith(b'SYNTH_') or
            len(name) > 150 or any(c < 32 or c > 126 for c in name)):
        raise ValueError('Only safe SYNTH_ ASCII names allowed')
    if (type(w) is not int or type(h) is not int or w > 1024 or h > 1024 or
            w < 1 or h < 1 or w&(w-1) or h&(h-1)):
        raise ValueError('Synthetic PC textures require power-of-two dimensions')
    if type(levels) is not int or not 1 <= levels <= min(max(w,h).bit_length(),16):
        raise ValueError('Invalid synthetic mip level count')
    if not isinstance(row['rgba'], (bytes,bytearray,memoryview)):
        raise ValueError('Expected source-free RGBA bytes')


def build_synthetic_pc_dxt1_pack(entries):
    """In-memory synthetic PC-shaped pack accepted by structural validators.

    The real Carbon PC texture resource may require many more initialized
    fields and correct placement/loader registration. Do not inject this data.
    """
    if (not isinstance(entries, (list,tuple)) or
            not 1 <= len(entries) <= MAX_PACK_TEXTURES):
        raise ValueError('Invalid synthetic texture count')
    for row in entries:
        _validate_entry(row)
    ordered=sorted(entries,key=lambda row:row['hash'])
    if len({row['hash'] for row in ordered})!=len(ordered):
        raise ValueError('Duplicate synthetic texture identity')
    indexes,descriptors,platform,images=[],bytearray(),bytearray(),bytearray()
    for row in ordered:
        identity,name,w,h,levels=(row[x] for x in ('hash','name','width','height','mip_levels'))
        dxt,spans=encode_dxt1_mips(row['rgba'],w,h,levels)
        # Use 16-byte image starts, preserving an explicit gap and disjointness.
        start=(len(images)+15)&~15
        images.extend(bytes(start-len(images)))
        images.extend(dxt)
        indexes.append(struct.pack('<II',identity,0))
        meta=bytearray(88)
        struct.pack_into('<I',meta,12,identity)
        struct.pack_into('<5I',meta,20,start,0,len(dxt),0,spans[0][3])
        struct.pack_into('<HH',meta,40,w,h)
        meta[44:48]=bytes((w.bit_length()-1,h.bit_length()-1,34,0))
        meta[50]=levels
        meta[51]=3  # synthetic candidate texture mode, NOT verified PC ABI
        # 89+n (n %4=3) is 4-byte aligned; one required terminator and padding.
        n=((len(name)+5)//4)*4-1
        descriptors.extend(meta+bytes((n,))+name+bytes(n-len(name)))
        plat=bytearray(24)
        plat[12:16]=b'DXT1'  # All other 20 bytes observed zero in 110 original PC records.
        platform.extend(plat)
    desc=_chunk(0xB3310000,
                _chunk(0x33310001,bytes(124)) +
                _chunk(0x33310002,b''.join(indexes)) +
                _chunk(0x33310004,descriptors) +
                _chunk(0x33310005,platform))
    framing=_chunk(0,bytes(48))+desc
    pix_pre=_chunk(0x33320001,bytes(24))+_chunk(0,bytes(80))
    # 0x33320002 payload starts 8 bytes past an absolute 128B boundary in
    # the original controls. Fill a synthetic unknown framing chunk to make
    # this true irrespective of descriptor length: then pad 120 bytes of 0x11.
    base_start=8+len(framing)+len(_chunk(0,bytes(80)))+8+len(pix_pre)+8
    extra=(8-base_start%128)%128
    filler=_chunk(0,bytes(80+extra))
    pixel=_chunk(0xB3320000,pix_pre+_chunk(0x33320002,bytes([0x11])*120+images))
    section=_chunk(0xB3300000,framing+filler+pixel)
    if len(section)>MAX_SECTION_BYTES:
        raise ValueError('Synthetic texture section exceeds safety bound')
    # Existing, separately developed Carbon PC metadata and aligned-span
    # validators must independently accept everything we emitted.
    records=parse_pack(section,'pc')['records']
    aligned,pad=aligned_pixel_array(section,records)
    if pad!=120 or set(records)!={row['hash'] for row in ordered}:
        raise ValueError('Internal PC texture envelope alignment/index mismatch')
    for row in ordered:
        meta=records[row['hash']]
        n=meta['image_bytes'];a=meta['image_offset']
        if len(aligned[a:a+n])!=n:
            raise ValueError('Internal synthetic image span mismatch')
    return section
