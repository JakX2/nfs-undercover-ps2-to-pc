#!/usr/bin/env python3
"""Read-only cross-variant PS2 color/alpha consistency audit (sections 241/3401).

Undercover has no matching native PC reference artwork in the inspected sample.
Two independently indexed original PS2 versions of each texture, however, give
an internal cross-section reference. Decode BOTH using their own flagged layout,
palette and dimensions, then compare on the lower-resolution pixel-centre grid.

This is a consistency control, not ground truth for the GS runtime, UV/sampler
modes, alpha blending, small mip levels or a PC DXT encoder. No game assets,
identities, source names, hashes or per-texture scores leave the public report.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from texture_visual_pair_gate import _base, _palette, _platform_flags
from ps2_texture_layout_candidates import decode_indices, palette_rgba, indices_to_rgba
from ps2_ct16_transfer_candidate import decode_ct16_psmt4
from pc_dxt_reference_decode import compare_rgba_nearest
from undercover_ps2_texture_layout_coverage import (
    SECTION_IDS, _bounds, MAX_SMALL_BUN, MAX_STREAM,
)


def _color(pixels, meta, flag, *, force_linear=False):
    bits=meta['codec']
    raw=_base(pixels,meta)
    if force_linear or flag == 0:
        indices=decode_indices(raw,meta['width'],meta['height'],bits,'linear')
    elif flag == 1 and bits == 4:
        indices=decode_ct16_psmt4(raw,meta['width'],meta['height'])
    elif flag == 1 and bits == 8:
        indices=decode_indices(raw,meta['width'],meta['height'],bits,'ct32_transfer')
    else:
        raise ValueError('Unsupported PS2 format or swizzle flag; refusing to guess')
    pal=palette_rgba(_palette(pixels,meta),bits,
                     'csm1' if bits==8 else 'linear','raw','rgba')
    return indices_to_rgba(indices,pal,bits)


def _summarize(scores):
    if not scores:return None
    return {'pairs':len(scores),
            'mean_rgb_mae':round(mean(row['rgb'] for row in scores),4),
            'median_rgb_mae':round(median(row['rgb'] for row in scores),4),
            'maximum_rgb_mae':round(max(row['rgb'] for row in scores),4),
            'pairs_below_10_rgb_mae':sum(row['rgb']<10 for row in scores),
            'pairs_below_20_rgb_mae':sum(row['rgb']<20 for row in scores),
            'mean_alpha_mae':round(mean(row['alpha'] for row in scores),4),
            'mean_linear_baseline_rgb_mae':round(mean(row['linear'] for row in scores),4),
            'matching_unmodified_source_palettes':sum(row['same_palette'] for row in scores)}


def compare_variant_sections(sections):
    if type(sections) is not dict or set(sections) != set(SECTION_IDS):
        raise ValueError('Require both Undercover source sections 241/3401')
    records={};pixels={};flags={};pads={}
    for section in SECTION_IDS:
        records[section]=parse_pack(sections[section],'ps2')['records']
        pixels[section],pads[section]=aligned_pixel_array(sections[section],records[section])
        flags[section]=_platform_flags(sections[section],records[section])
    large,small=records[241],records[3401]
    if set(large)!=set(small) or len(large)<2:
        raise ValueError('Original variant source identity sets disagree')
    groups=defaultdict(list);modes=Counter()
    for identity in sorted(large):
        a,b=large[identity],small[identity]
        if (a['name'],a['codec'],a['tile_mode'])!=(b['name'],b['codec'],b['tile_mode']):
            raise ValueError('Cross-section name, format or mode identity conflict')
        if (a['width'],a['height'])!=(2*b['width'],2*b['height']):
            raise ValueError('Cross-section dimensions not exactly 2x in both axes')
        if flags[241][identity] not in (0,1) or flags[3401][identity] not in (0,1):
            raise ValueError('Unsupported PS2 swizzle flag')
        high=_color(pixels[241],a,flags[241][identity])
        low=_color(pixels[3401],b,flags[3401][identity])
        score=compare_rgba_nearest(high,a['width'],a['height'],low,b['width'],b['height'])
        linear_high=_color(pixels[241],a,flags[241][identity],force_linear=True)
        linear_low=_color(pixels[3401],b,flags[3401][identity],force_linear=True)
        baseline=compare_rgba_nearest(linear_high,a['width'],a['height'],
                                      linear_low,b['width'],b['height'])
        pal_a=bytes(_palette(pixels[241],a));pal_b=bytes(_palette(pixels[3401],b))
        groups[str(a['codec'])].append({'rgb':score['mean_absolute_rgb_error'],
                                       'alpha':score['mean_absolute_alpha_error'],
                                       'linear':baseline['mean_absolute_rgb_error'],
                                       'same_palette':pal_a==pal_b})
        modes[(flags[241][identity],flags[3401][identity])]+=1
    return {'cross_section_shared_identities':len(large),
            'larger_section':241,'smaller_section':3401,
            'all_dimension_ratios':'2x width, 2x height',
            'pixel_base_padding':{str(s):pads[s] for s in SECTION_IDS},
            'by_indexed_depth':{key:_summarize(groups[key]) for key in ('4','8') if groups[key]},
            'all':_summarize([row for g in groups.values() for row in g]),
            'swizzle_flag_pair_counts':{f'{a}/{b}':count for (a,b),count in sorted(modes.items())},
            'verdict':'CROSS-VARIANT CONSISTENCY ONLY: no independent PC-format identity match, alpha blending, small-mip fidelity, shader/UV modes or runtime loading proven'}


def analyze_original_archive(path):
    import zipfile
    if not Path(path).is_file():raise ValueError('Missing original Undercover archive')
    with zipfile.ZipFile(path) as z:
        bun='TRACKS/L2RB.BUN';stream='TRACKS/STREAML2RB.BUN'
        if not 0<z.getinfo(bun).file_size<=MAX_SMALL_BUN or not 0<z.getinfo(stream).file_size<=MAX_STREAM:
            raise ValueError('Original archive member exceeds source bound')
        header=z.read(bun)
        data=z.read(stream)   # full ZIP-member CRC checked
    bounds=_bounds(header,len(data),SECTION_IDS)
    return compare_variant_sections({s:data[o:o+n] for s,(o,n) in bounds.items()})


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(analyze_original_archive(args.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
