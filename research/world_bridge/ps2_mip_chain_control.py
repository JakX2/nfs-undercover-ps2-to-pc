#!/usr/bin/env python3
"""Strict in-memory PS2 indexed mip-chain boundaries and original-UC controls.

A 0x33310004 mip-image span is a concatenation of separately sized levels.
This module does not infer GPU texture state or a native PC material writer.
It checks each level's byte boundaries and explicitly decodes the known PS2
base-layout candidates; it rejects unsupported small-level transfer mappings.
Original source images, names, hashes and pixel buffers never leave the audit.
"""
from collections import Counter
from pathlib import Path
from statistics import mean

from texture_metadata_pixel_bridge import parse_pack, mip_size
from texture_pixel_base_alignment import aligned_pixel_array
from texture_visual_pair_gate import _platform_flags, _palette
from ps2_texture_layout_candidates import decode_indices, palette_rgba, indices_to_rgba, MAX_PIXELS
from ps2_ct16_transfer_candidate import decode_ct16_psmt4
from pc_dxt_reference_decode import compare_rgba_nearest
from undercover_ps2_texture_layout_coverage import SECTION_IDS, _bounds, MAX_SMALL_BUN, MAX_STREAM


def split_mip_chain(raw_image, width, height, bits, levels):
    """Return immutable (w,h,raw_level) tuples with no implicit padding.

    A redundant repetition of the 1x1 level is not silently accepted: it is
    not a new dimension level and has no source-backed interpretation here.
    """
    if (bits not in (4,8) or not all(type(v) is int and v > 0 for v in (width,height,levels))
            or width & (width-1) or height & (height-1) or
            width*height > MAX_PIXELS or levels > max(width,height).bit_length()):
        raise ValueError('Unsupported indexed mip dimensions or count')
    if not isinstance(raw_image,(bytes,bytearray,memoryview)):
        raise ValueError('Image must be bytes-like')
    expected = mip_size(width,height,bits,levels)
    if len(raw_image) != expected:
        raise ValueError('Mip chain length disagrees with exact byte budget')
    result=[];cursor=0
    for level in range(levels):
        w=max(1,width>>level);h=max(1,height>>level)
        n=mip_size(w,h,bits,1)
        result.append((w,h,bytes(raw_image[cursor:cursor+n])))
        cursor+=n
    if cursor!=len(raw_image):raise ValueError('Mip payload length mismatch')
    return tuple(result)


def decode_mip_chain(raw_image, meta, flag):
    """Explicit source-flag based decoding, no layout selection or fallback."""
    levels=split_mip_chain(raw_image,meta['width'],meta['height'],meta['codec'],meta['mip_levels'])
    result=[]
    for w,h,level_bytes in levels:
        bits=meta['codec']
        if flag==0:
            indices=decode_indices(level_bytes,w,h,bits,'linear')
        elif flag==1 and bits==8:
            indices=decode_indices(level_bytes,w,h,bits,'ct32_transfer')
        elif flag==1 and bits==4:
            indices=decode_ct16_psmt4(level_bytes,w,h)
        else:
            raise ValueError('Unverified PS2 mip swizzle flag or codec')
        if len(indices)!=w*h:raise ValueError('Decoded mip index count disagrees')
        result.append((w,h,indices))
    return tuple(result)


def analyze_undercover_mip_sections(sections):
    if type(sections) is not dict or set(sections)!=set(SECTION_IDS):
        raise ValueError('Require both original Undercover source sections')
    rows={};per_section={};records={};flags={};pixels={}
    for section in SECTION_IDS:
        blob=sections[section]
        rec=parse_pack(blob,'ps2')['records']
        px,pad=aligned_pixel_array(blob,rec)
        fl=_platform_flags(blob,rec)
        decoded={};level_hist=Counter();levels_total=0
        for identity,meta in rec.items():
            img_start,img_size=meta['image_offset'],meta['image_bytes']
            levels=decode_mip_chain(px[img_start:img_start+img_size],meta,fl[identity])
            pal=palette_rgba(_palette(px,meta),meta['codec'],
                             'csm1' if meta['codec']==8 else 'linear','raw','rgba')
            decoded[identity]=tuple((w,h,indices_to_rgba(idx,pal,meta['codec'])) for w,h,idx in levels)
            level_hist[meta['mip_levels']]+=1
            levels_total+=len(levels)
        rows[section]=decoded;records[section]=rec;flags[section]=fl;pixels[section]=px
        per_section[str(section)]={'texture_records':len(rec),
                                   'decoded_mip_buffers':levels_total,
                                   'non_base_mip_buffers':levels_total-len(rec),
                                   'records_by_mip_count':{str(k):v for k,v in sorted(level_hist.items())},
                                   'pixel_alignment_bytes':pad}
    if set(records[241])!=set(records[3401]):
        raise ValueError('Section identity sets disagree')
    same_size=[]
    for identity in records[241]:
        a,b=records[241][identity],records[3401][identity]
        if (a['name'],a['codec'],a['tile_mode'])!=(b['name'],b['codec'],b['tile_mode']):
            raise ValueError('Source mip-chain identity metadata conflict')
        # Only compare mip levels of matching dimensions across the two
        # independent source texture variants. Skip other pairs honestly.
        aa=rows[241][identity];bb=rows[3401][identity]
        for w,h,rgba_a in aa:
            for wb,hb,rgba_b in bb:
                if (w,h)!=(wb,hb):continue
                metric=compare_rgba_nearest(rgba_a,w,h,rgba_b,wb,hb)
                same_size.append(metric)
    return {'sections':per_section,
            'total_source_texture_records':sum(z['texture_records'] for z in per_section.values()),
            'total_decoded_mip_buffers':sum(z['decoded_mip_buffers'] for z in per_section.values()),
            'total_non_base_mip_buffers':sum(z['non_base_mip_buffers'] for z in per_section.values()),
            'same_size_cross_variant_mip_pairs':len(same_size),
            'mean_rgb_mae_same_size_mips':round(mean(s['mean_absolute_rgb_error'] for s in same_size),4) if same_size else None,
            'maximum_rgb_mae_same_size_mips':round(max(s['mean_absolute_rgb_error'] for s in same_size),4) if same_size else None,
            'mean_alpha_mae_same_size_mips':round(mean(s['mean_absolute_alpha_error'] for s in same_size),4) if same_size else None,
            'verdict':'MIP BYTE-BOUNDARY AND SOURCE-PAIR CONSISTENCY ONLY: no native PC texture writer or runtime sampling/blending proof'}


def analyze_original_archive(path):
    import zipfile
    if not Path(path).is_file():raise ValueError('Missing Undercover archive')
    with zipfile.ZipFile(path) as z:
        bun='TRACKS/L2RB.BUN';stream='TRACKS/STREAML2RB.BUN'
        if not 0<z.getinfo(bun).file_size<=MAX_SMALL_BUN or not 0<z.getinfo(stream).file_size<=MAX_STREAM:
            raise ValueError('Unbounded original stream member')
        header=z.read(bun);data=z.read(stream)
    bounds=_bounds(header,len(data),SECTION_IDS)
    return analyze_undercover_mip_sections({s:data[o:o+n] for s,(o,n) in bounds.items()})


def main():
    import argparse,json
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(analyze_original_archive(args.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
