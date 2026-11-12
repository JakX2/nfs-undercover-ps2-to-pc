#!/usr/bin/env python3
"""Bounded read-only Undercover PS2 texture layout/address coverage audit.

Consumes original owner-supplied regular TRACKS.zip, retaining only two
sections (241, 3401). Returns *aggregate counts only*: no texture names,
actual hash values, source images, palette bytes or decoded pictures.

This validates a base-level buffer decode and palette lookup, NOT visual
fidelity, original alpha/UV semantics or a native Carbon PC texture writer.
"""
from collections import Counter
import json
import struct
from pathlib import Path
import zipfile

from texture_original_archive_pair_audit import _bounds
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from texture_visual_pair_gate import _base, _palette, _platform_flags
from ps2_texture_layout_candidates import decode_indices, palette_rgba, indices_to_rgba
from ps2_ct16_transfer_candidate import decode_ct16_psmt4

MAX_SMALL_BUN = 8 * 1024 * 1024
MAX_STREAM = 128 * 1024 * 1024
SECTION_IDS = (241, 3401)


def analyze_sections(sections):
    """Read-only reusable section audit with no original identifiers in result."""
    if set(sections) != set(SECTION_IDS):
        raise ValueError('Must supply both original Undercover texture sections')
    result = {}
    all_hashes = []
    for sec in SECTION_IDS:
        blob=sections[sec]
        records = parse_pack(blob, 'ps2')['records']
        pixels, padding = aligned_pixel_array(blob, records)
        flags = _platform_flags(blob, records)
        modes=Counter()
        all_hashes.append(set(records))
        for identity, meta in records.items():
            bits=meta['codec']
            flag=flags[identity]
            raw=_base(pixels, meta)
            if flag == 0:
                indices=decode_indices(raw,meta['width'],meta['height'],bits,'linear')
            elif flag == 1 and bits == 4:
                indices=decode_ct16_psmt4(raw,meta['width'],meta['height'])
            elif flag == 1 and bits == 8:
                indices=decode_indices(raw,meta['width'],meta['height'],8,'ct32_transfer')
            else:
                raise ValueError('Unsupported texture format or source swizzle flag')
            pal=palette_rgba(_palette(pixels,meta),bits,'csm1' if bits==8 else 'linear', 'double','rgba')
            color=indices_to_rgba(indices,pal,bits)
            if len(color) != meta['width']*meta['height']*4:
                raise ValueError('Source texture color-buffer size mismatch')
            modes[(bits,flag)]+=1
        result[str(sec)]={
            'source_texture_records':len(records),
            'base_image_rgba_buffer_decoded':len(records),
            'pixel_alignment_pad_bytes':padding,
            'four_bit_swizzled':modes[(4,1)],
            'eight_bit_swizzled':modes[(8,1)],
            'four_bit_linear':modes[(4,0)],
            'eight_bit_linear':modes[(8,0)],
        }
    return {'sections':result,
            'total_source_records':sum(r['source_texture_records'] for r in result.values()),
            'total_decoded_base_images':sum(r['base_image_rgba_buffer_decoded'] for r in result.values()),
            'shared_source_texture_identities':len(all_hashes[0]&all_hashes[1]),
            'limit':'Decoding coverage only. Visual fidelity, alpha semantics, all mips, native PC texture writing and runtime UNVERIFIED.'}


def analyze_original_archive(path):
    """Safely locate 241/3401 in the original owner-supplied Undercover ZIP."""
    if not Path(path).is_file():
        raise ValueError('Missing original Undercover PS2 archive')
    with zipfile.ZipFile(path) as z:
        bun='TRACKS/L2RB.BUN'; stream='TRACKS/STREAML2RB.BUN'
        if not 0 < z.getinfo(bun).file_size <= MAX_SMALL_BUN or not 0 < z.getinfo(stream).file_size <= MAX_STREAM:
            raise ValueError('Original Undercover stream exceeds source bound')
        header=z.read(bun)
        data=z.read(stream) # zipfile verifies CRC for the complete member
    bounds=_bounds(header,len(data),SECTION_IDS)
    return analyze_sections({s:data[o:o+n] for s,(o,n) in bounds.items()})


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(analyze_original_archive(args.undercover_ps2_zip),indent=2))


if __name__=='__main__': main()
