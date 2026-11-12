#!/usr/bin/env python3
"""Source-private PS2 Undercover texture-ID -> parser-valid PC DXT5 pack candidate.

This DOES NOT register textures with the Carbon game runtime and is NOT a
native installable texture archive. Unknown retail headers and PC sampler/
material semantics remain unvalidated. Never distribute owner game bytes.
No public JSON output contains hashes, names, RGBA, image payloads or paths.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import struct

from texture_metadata_pixel_bridge import parse_pack, mip_size, MAX_SECTION
from texture_pixel_base_alignment import aligned_pixel_array
from undercover_to_pc_dxt5_bridge import decode_undercover_source
from synthetic_dxt5_texture_writer import encode_dxt5_mips
from pc_dxt_reference_decode import decode_dxt_base
from pc_texture_header_overlay_gate import _source_image_span

MAX_DONORS = 512
MAX_OUTPUT = 32*1024*1024


def _chunk(tag, payload):
    return struct.pack('<II', tag, len(payload)) + payload


def _ids(value, label):
    if not isinstance(value, (set, frozenset)):
        raise ValueError(label+' must be a private identity set')
    if not value or any(type(n) is not int or not 0 < n <= 0xffffffff for n in value):
        raise ValueError('Invalid '+label+' identity')
    return value


def audit_registration_coverage(used_material_ids, source_ps2_sections, carbon_ids=None):
    """Compare private identity sets, exposing only safe aggregate counts."""
    used = _ids(used_material_ids,'source material')
    if not isinstance(source_ps2_sections,dict) or set(source_ps2_sections) != {241,3401}:
        raise ValueError('Expected both original source PS2 RB texture sections')
    images = {}
    for section in (241,3401):
        raw = source_ps2_sections[section]
        if not isinstance(raw,bytes):
            raise ValueError('Private PS2 section must be complete bytes')
        data = parse_pack(raw,'ps2')['records']
        aligned_pixel_array(raw,data)
        if len(data) > MAX_DONORS:
            raise ValueError('Too many PS2 donor entries')
        images[section] = set(data)
    available=images[241] | images[3401]
    if carbon_ids is not None and (not isinstance(carbon_ids,(set,frozenset)) or
                                   any(type(h) is not int or not 0<h<=0xffffffff for h in carbon_ids)):
        raise ValueError('Invalid private Carbon PC identity set')
    pc=set() if carbon_ids is None else set(carbon_ids)
    return {'scope':'OFFLINE_SOURCE_IDENTITY_PRESENCE_NOT_RUNTIME_REGISTRATION',
            'used_distinct_material_identities':len(used),
            'source_241_image_identities':len(images[241]),
            'source_3401_image_identities':len(images[3401]),
            'source_image_identities_shared':len(images[241]&images[3401]),
            'source_image_identities_combined':len(available),
            'used_identities_with_source_images':len(used & available),
            'used_identities_without_source_images':len(used - available),
            'used_identities_with_carbon_rb_images':len(used & pc) if carbon_ids is not None else None,
            'complete_material_image_coverage':used <= available,
            'missing_identities_are_not_fabricated':True,
            'runtime_identity_registration':'UNVERIFIED'}


def _padded_name(name):
    if (not isinstance(name,bytes) or not 1 <= len(name) <= 240 or
            any(c<32 or c>126 for c in name)):
        raise ValueError('Invalid original source ASCII texture name')
    n=((len(name)+5)//4)*4-1
    if n>255:
        raise ValueError('Original name exceeds PC descriptor byte field')
    return bytes((n,))+name+bytes(n-len(name))


def _assemble_pc_dxt5_entries(entries):
    """Build synthetic-header but real-ID native-shaped DXT5 texture root.

    Entries are private (hash, name, width, height, mip_levels, DXT5 bytes).
    The images are strictly validated against independent mip-size equations.
    """
    if not isinstance(entries,(tuple,list)) or not 1<=len(entries)<=MAX_DONORS:
        raise ValueError('Invalid private entry count')
    if any(len(row)!=6 for row in entries):
        raise ValueError('Invalid private entry tuple')
    ordered=sorted(entries,key=lambda row:row[0])
    identities=[row[0] for row in ordered]
    if any(type(h) is not int or not 0 < h <= 0xffffffff for h in identities) or len(set(identities))!=len(identities):
        raise ValueError('Duplicate or invalid private texture identity')
    index=[];metadata=bytearray();platform=bytearray();images=bytearray()
    sizes=Counter()
    for h,name,w,hh,levels,packed in ordered:
        if (type(w) is not int or type(hh) is not int or not 1<=w<=8192 or not 1<=hh<=8192 or
                w&(w-1) or hh&(hh-1) or type(levels) is not int or
                not 1<=levels<=min(16,max(w,hh).bit_length())):
            raise ValueError('Invalid PC candidate dimensions/mip count')
        if not isinstance(packed,bytes) or len(packed)!=mip_size(w,hh,38,levels):
            raise ValueError('Encoded DXT5 bytes disagree with PC mip equation')
        start=(len(images)+15)&~15
        images.extend(bytes(start-len(images)));images.extend(packed)
        index.append(struct.pack('<II',h,0))
        info=bytearray(88)
        struct.pack_into('<I',info,12,h)
        struct.pack_into('<5I',info,20,start,0,len(packed),0,mip_size(w,hh,38,1))
        struct.pack_into('<HH',info,40,w,hh)
        info[44:48]=bytes((w.bit_length()-1,hh.bit_length()-1,38,0))
        info[50]=levels
        info[51]=3 # UNVERIFIED candidate mode, not native Carbon registration proof.
        metadata.extend(info+_padded_name(name))
        pc_platform=bytearray(24);pc_platform[12:16]=b'DXT5'
        platform.extend(pc_platform)
        sizes[levels]+=1
    desc=_chunk(0xB3310000, _chunk(0x33310001, bytes(124)) +
                _chunk(0x33310002,b''.join(index))+
                _chunk(0x33310004,bytes(metadata))+
                _chunk(0x33310005,bytes(platform)))
    beginning=_chunk(0,bytes(48))+desc
    pix_prefix=_chunk(0x33320001,bytes(24))+_chunk(0,bytes(80))
    base_start=8+len(beginning)+len(_chunk(0,bytes(80)))+8+len(pix_prefix)+8
    extra=(8-base_start%128)%128
    filler=_chunk(0,bytes(80+extra))
    pixel=_chunk(0xB3320000,pix_prefix+_chunk(0x33320002,bytes([0x11])*120+bytes(images)))
    output=_chunk(0xB3300000,beginning+filler+pixel)
    if len(output)>MAX_OUTPUT:
        raise ValueError('Candidate PC texture root is too large')
    reread=parse_pack(output,'pc')['records']
    aligned,pad=aligned_pixel_array(output,reread)
    if (pad!=120 or set(reread)!=set(identities) or
            len(reread)!=len(entries) or any(reread[h]['codec']!=38 for h in identities)):
        raise ValueError('PC image index/metadata/alignment readback failed')
    for h,name,w,hh,levels,packed in ordered:
        meta=reread[h]
        if (meta['name'] != name or meta['width']!=w or meta['height']!=hh or
                meta['mip_levels']!=levels or meta['image_bytes']!=len(packed)):
            raise ValueError('PC native texture identity/descriptor readback failed')
        a,b=_source_image_span(output,meta)
        if output[a:b]!=packed:
            raise ValueError('PC texture image span readback differs')
        # First BC3 mip must decode as valid RGBA with explicit alpha.
        decoded=decode_dxt_base(packed[:meta['base_image_bytes']],w,hh,b'DXT5')
        if len(decoded)!=4*w*hh:
            raise ValueError('PC DXT5 base-level decode size mismatch')
    return output, {'pc_candidate_texture_identities':len(entries),
                    'pc_candidate_section_bytes':len(output),
                    'pc_candidate_dxt5_image_bytes':sum(len(row[5]) for row in entries),
                    'pc_candidate_alpha_codec':'DXT5',
                    'pc_candidate_mip_level_counts':dict(sorted(sizes.items())),
                    'all_names_identities_and_encoded_spans_read_back':True,
                    'unknown_pc_descriptor_and_sampler_headers':'SYNTHETIC_UNVERIFIED'}


def build_private_dxt5_candidate(source_section, used_material_ids=None,
                                 mip_levels=4, max_textures=MAX_DONORS):
    """In-memory 4/8bpp PS2 → DXT5 candidate with original IDs and names.

    A caller may optionally constrain to actually referenced material identities;
    any unresolved used identities are COUNTED and BLOCK complete registration.
    max_textures is a bounded deliberate partial-audit option, not silent discard.
    """
    if not isinstance(source_section,bytes):
        raise ValueError('Expected private source section bytes')
    if type(mip_levels) is not int or not 1<=mip_levels<=16:
        raise ValueError('Invalid requested mip count')
    if type(max_textures) is not int or not 1<=max_textures<=MAX_DONORS:
        raise ValueError('Unsafe max texture count')
    source=parse_pack(source_section,'ps2')['records']
    aligned_pixel_array(source_section,source)
    if len(source)>MAX_DONORS:
        raise ValueError('Too many source texture records')
    used=None if used_material_ids is None else _ids(used_material_ids,'source material')
    donors=sorted(source)
    chosen=[h for h in donors if used is None or h in used]
    if not chosen:
        raise ValueError('No source image matched private material usage')
    selected=chosen[:max_textures]
    entries=[];bit_depth=Counter();changed_mip_policy=0
    for h in selected:
        ordinal=donors.index(h)
        rgba,w,hh,bits,_flag=decode_undercover_source(source_section,ordinal)
        levels=min(mip_levels,max(w,hh).bit_length())
        changed_mip_policy+=levels!=mip_levels
        packed,spans=encode_dxt5_mips(rgba,w,hh,levels)
        if spans[0][3]!=mip_size(w,hh,38,1):
            raise ValueError('DXT5 base mip equation mismatch')
        entries.append((h,source[h]['name'],w,hh,levels,packed))
        bit_depth[bits]+=1
    blob,info=_assemble_pc_dxt5_entries(entries)
    missing=set() if used is None else used-set(source)
    report={'scope':'OFFLINE_PC_SHAPED_TEXTURE_ROOT_NOT_GAME_REGISTERED',
            'original_source_texture_count':len(source),
            'source_material_ids_supplied':used is not None,
            'source_material_ids_absent_from_this_pack':len(missing) if used is not None else None,
            'source_donors_requested':len(chosen),
            'source_donors_converted':len(entries),
            'partial_ordinal_batch':len(entries)!=len(chosen),
            'requested_mip_levels':mip_levels,
            'sources_capped_to_smaller_mip_chain':changed_mip_policy,
            'source_indexed_bits':dict(sorted(bit_depth.items())),
            'complete_material_identity_coverage':used is not None and not missing and len(entries)==len(chosen),
            'runtime_registration':'UNVERIFIED', 'safe_for_direct_game_install':False,
            **info}
    return blob,report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--undercover-ps2-tracks-zip',type=Path,required=True)
    parser.add_argument('--source-section',type=int,choices=(241,3401),default=3401)
    parser.add_argument('--mip-levels',type=int,default=4)
    parser.add_argument('--max-textures',type=int,default=MAX_DONORS)
    args=parser.parse_args()
    # CRC check both original source sections; derive used material identities
    # from original PS2 strip table references in memory only, never emit IDs.
    from undercover_ra_texture_presence_gate import (
        _owner_archive, _member_bytes, _fingerprint, parse_stream_section_rows,
        used_material_ids_from_original_rb, MAX_SMALL_BUN, MAX_RB_STREAM)
    import zipfile
    original=_owner_archive(args.undercover_ps2_tracks_zip)
    snapshot=_fingerprint(original)
    with zipfile.ZipFile(original) as archive:
        bun=_member_bytes(archive,'TRACKS/L2RB.BUN',MAX_SMALL_BUN)
        stream=_member_bytes(archive,'TRACKS/STREAML2RB.BUN',MAX_RB_STREAM)
    _,rows=parse_stream_section_rows(bun,len(stream))
    if not {241,3401} <= rows.keys():
        raise ValueError('Original Undercover source sections missing from table')
    sections={s:stream[slice(*rows[s])] for s in (241,3401)}
    used={s:used_material_ids_from_original_rb(sections[s]) for s in sections}
    union=used[241] | used[3401]
    coverage=audit_registration_coverage(union,sections)
    _private,report=build_private_dxt5_candidate(
        sections[args.source_section],used_material_ids=union,
        mip_levels=args.mip_levels,max_textures=args.max_textures)
    if _fingerprint(original)!=snapshot:
        raise ValueError('Original archive changed during private read-only conversion')
    print(json.dumps({'registration_coverage':coverage,'candidate':report,
                      'original_zip_crc_verified':True,'original_owner_archive_unchanged':True},
                     indent=2))


if __name__=='__main__':
    main()
