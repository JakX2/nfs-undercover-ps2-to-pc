#!/usr/bin/env python3
"""Read-only alpha-channel provenance audit for original paired Carbon textures.

This is intentionally a *diagnostic*, never a native texture writer or an
alpha-conversion policy. Carbon PC DXT1/3/5 and PS2 GS indexed-palette alpha may
have different rendering duties. Compare explicit candidate interpretations
without auto-selecting any candidate or leaking original identifiers/pixels.

Original sources are caller-supplied and stay in memory. The report contains
only format-grouped aggregates. Run synthetic tests without any game files.
"""
from collections import defaultdict
from statistics import mean

from carbon_ps2_texture_color_control import (
    parse_pack, CODEC_FOURCC, aligned_pixel_array, _platform_flags, _base, _palette,
    decode_indices, decode_ct16_psmt4, palette_rgba, decode_dxt_base,
)

MAX_PIXELS = 4 * 1024 * 1024
CANDIDATES = ('raw', 'double', 'opaque', 'zero', 'binary_nonzero', 'binary_ge64')


def score_alpha_candidates(pc_rgba, pc_width, pc_height,
                           ps2_indices, ps2_width, ps2_height, rgba_palette, bits):
    """Compare matched pixel centres; candidate results are NOT decisions.

    Source palettes must already have the caller-selected 8-bit CSM1 or 4-bit
    linear entry reordering applied, but must contain untouched byte alpha.
    No assumptions about PS2 framebuffer blending or material alpha are made.
    """
    if (bits not in (4, 8) or not all(type(v) is int and v > 0 for v in
            (pc_width, pc_height, ps2_width, ps2_height)) or
            pc_width * pc_height > MAX_PIXELS or ps2_width * ps2_height > MAX_PIXELS):
        raise ValueError('Unsafe dimensions or indexed depth')
    if (len(pc_rgba) != pc_width * pc_height * 4 or
            len(ps2_indices) != ps2_width * ps2_height or
            len(rgba_palette) != (1 << bits) * 4):
        raise ValueError('Invalid alpha comparison buffer lengths')
    if any(v >= (1 << bits) for v in ps2_indices):
        raise ValueError('Palette index outside source range')
    totals = {name: 0 for name in CANDIDATES}
    pc_partial = pc_opaque = ps2_zero = ps2_half = ps2_full = 0
    for y in range(ps2_height):
        py = min(pc_height - 1, (2*y+1) * pc_height // (2*ps2_height))
        for x in range(ps2_width):
            px = min(pc_width - 1, (2*x+1) * pc_width // (2*ps2_width))
            pa = pc_rgba[(py * pc_width + px)*4 + 3]
            sa = rgba_palette[ps2_indices[y*ps2_width+x]*4+3]
            pc_partial += pa != 255
            pc_opaque += pa == 255
            ps2_zero += sa == 0
            ps2_half += sa == 128
            ps2_full += sa == 255
            vals = (sa, min(255, 2*sa), 255, 0,
                    255 if sa else 0, 255 if sa >= 64 else 0)
            for name, result in zip(CANDIDATES, vals):
                totals[name] += abs(pa - result)
    n = ps2_width * ps2_height
    return {'pixels': n, 'pc_nonopaque_pixels':pc_partial,
            'pc_opaque_pixels':pc_opaque, 'ps2_raw_alpha_zero_pixels':ps2_zero,
            'ps2_raw_alpha_128_pixels':ps2_half, 'ps2_raw_alpha_255_pixels':ps2_full,
            'mae':{name:totals[name]/n for name in CANDIDATES}}


def _summarize(rows):
    pixels = sum(r['pixels'] for r in rows)
    if not pixels:
        return None
    by_mode = {}
    for name in CANDIDATES:
        errs = [r['mae'][name] for r in rows]
        by_mode[name] = {
            'mean_per_texture_mae':round(mean(errs),4),
            'pixel_weighted_mae':round(sum(r['mae'][name]*r['pixels'] for r in rows)/pixels,4),
            'textures_below_10_mae':sum(v < 10 for v in errs),
        }
    return {'textures':len(rows), 'compared_pixels':pixels,
            'fully_opaque_pc_textures':sum(r['pc_nonopaque_pixels']==0 for r in rows),
            'pc_nonopaque_fraction':round(sum(r['pc_nonopaque_pixels'] for r in rows)/pixels,4),
            'ps2_raw_alpha_zero_fraction':round(sum(r['ps2_raw_alpha_zero_pixels'] for r in rows)/pixels,4),
            'ps2_raw_alpha_128_fraction':round(sum(r['ps2_raw_alpha_128_pixels'] for r in rows)/pixels,4),
            'ps2_raw_alpha_255_fraction':round(sum(r['ps2_raw_alpha_255_pixels'] for r in rows)/pixels,4),
            'candidate_scores':by_mode}


def compare_source_alpha_sections(pc_section, ps2_section):
    """Evaluate ALL same-hash original Carbon pairs without exposing identity."""
    pc = parse_pack(pc_section, 'pc')['records']
    ps = parse_pack(ps2_section, 'ps2')['records']
    pc_data, pc_pad = aligned_pixel_array(pc_section, pc)
    ps_data, ps_pad = aligned_pixel_array(ps2_section, ps)
    flags = _platform_flags(ps2_section, ps)
    common = sorted(pc.keys() & ps.keys())
    if len(common) < 2:
        raise ValueError('Need two matched Carbon textures')
    groups = defaultdict(list)
    for identity in common:
        p, s = pc[identity], ps[identity]
        if p['name'] != s['name'] or p['tile_mode'] != s['tile_mode']:
            raise ValueError('Matched source identity disagrees')
        bits, flag = s['codec'], flags[identity]
        source = _base(ps_data,s)
        if flag == 0:
            indices = decode_indices(source,s['width'],s['height'],bits,'linear')
        elif flag == 1 and bits == 4:
            indices = decode_ct16_psmt4(source,s['width'],s['height'])
        elif flag == 1 and bits == 8:
            indices = decode_indices(source,s['width'],s['height'],bits,'ct32_transfer')
        else:
            raise ValueError('Unsupported PS2 format/flag; no fallback')
        palette = palette_rgba(_palette(ps_data,s),bits,
                               'csm1' if bits==8 else 'linear','raw','rgba')
        codec = CODEC_FOURCC[p['codec']]
        pc_rgba = decode_dxt_base(_base(pc_data,p),p['width'],p['height'],codec)
        groups[codec.decode()].append(score_alpha_candidates(pc_rgba,p['width'],p['height'],
                           indices,s['width'],s['height'],palette,bits))
    return {'matched_texture_count':len(common),
            'pixel_data_base_padding':{'pc':pc_pad,'ps2':ps_pad},
            'by_pc_dxt_codec':{key:_summarize(groups[key]) for key in ('DXT1','DXT3','DXT5') if groups[key]},
            'verdict':'COMPARISON ONLY: no universal PS2 alpha semantics, PC alpha policy, blending, or runtime rendering proven'}


def main():
    import argparse, json
    from pathlib import Path
    from texture_original_archive_pair_audit import _read_split, _read_regular
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    args=p.parse_args()
    pc = _read_split(args.pc_volumes,(141,142))
    ps = _read_regular(args.carbon_ps2_zip,(141,142))
    print(json.dumps({str(sec):compare_source_alpha_sections(pc[sec],ps[sec]) for sec in (141,142)},indent=2))


if __name__=='__main__':main()
