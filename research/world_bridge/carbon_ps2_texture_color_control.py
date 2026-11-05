#!/usr/bin/env python3
"""Read-only Carbon PC/PS2 same-hash native texture *RGB* validation.

Sources: caller-owned 0xB3300000 original section bytes. This does NOT write
images or select game texture conversion outputs. Only aggregate, non-identifying
scores leave this function; all image bytes and hash keys remain private.

Empirically tested conventions for Carbon original section 141/142:
  - Base begins at 128-byte aligned origin inside pixel-data chunk;
  - PS2 platform byte +0x17 = 0: source indices are linear;
  - +0x17 = 1: PSMT4 uploaded as CT16 at W/2,H/2;
                PSMT8 uploaded as CT32 at W/2,H/2;
  - 8bpp palettes use CSM1 index exchange, 4bpp palettes remain linear.
These are source-backed *candidate* rules, not an Undercover runtime ABI proof.
Alpha/sampler behavior, mips, PC serialization and in-game rendering remain open.
"""
from collections import Counter, defaultdict
from statistics import mean, median

from texture_metadata_pixel_bridge import parse_pack, CODEC_FOURCC
from texture_pixel_base_alignment import aligned_pixel_array
from texture_visual_pair_gate import _base, _palette, _platform_flags
from ps2_texture_layout_candidates import decode_indices, palette_rgba, indices_to_rgba
from ps2_ct16_transfer_candidate import decode_ct16_psmt4
from pc_dxt_reference_decode import decode_dxt_base, compare_rgba_nearest


def _summarize(scored):
    if not scored:
        return None
    values = [r['rgb'] for r in scored]
    return {'textures':len(scored),
            'mean_rgb_mae':round(mean(values),4),
            'median_rgb_mae':round(median(values),4),
            'maximum_rgb_mae':round(max(values),4),
            'textures_below_10_rgb_mae':sum(v < 10 for v in values),
            'textures_below_20_rgb_mae':sum(v < 20 for v in values),
            'mean_linear_baseline_rgb_mae':round(mean(r['baseline'] for r in scored),4),
            'mean_alpha_mae_double_candidate':round(mean(r['alpha'] for r in scored),4)}


def compare_source_color_sections(pc_section, ps2_section):
    """Decode all matching Carbon PC/PS2 textures; fail closed on any issue.

    A low mean RGB error demonstrates spatial/color agreement for the tested
    source textures; alpha remains explicitly unverified. Caller should verify
    this across multiple independent section controls before generalization.
    """
    pc = parse_pack(pc_section, 'pc')['records']
    ps2 = parse_pack(ps2_section, 'ps2')['records']
    pc_pixels, pc_pad = aligned_pixel_array(pc_section, pc)
    ps2_pixels, ps2_pad = aligned_pixel_array(ps2_section, ps2)
    flags = _platform_flags(ps2_section, ps2)
    common = sorted(pc.keys() & ps2.keys())
    if len(common) < 2:
        raise ValueError('Need at least two matched original texture identities')
    results = []
    flag_counts = Counter()
    for identity in common:
        a, b = pc[identity], ps2[identity]
        if a['name'] != b['name'] or a['tile_mode'] != b['tile_mode']:
            raise ValueError('Same-hash Carbon texture metadata disagrees')
        bit_depth, flag = b['codec'], flags[identity]
        if flag not in (0, 1):
            raise ValueError('Unsupported PS2 swizzle flag; refusing to guess')
        source = _base(ps2_pixels, b)
        if flag == 0:
            indices = decode_indices(source, b['width'], b['height'], bit_depth, 'linear')
        elif bit_depth == 4:
            indices = decode_ct16_psmt4(source, b['width'], b['height'])
        elif bit_depth == 8:
            indices = decode_indices(source, b['width'], b['height'], 8, 'ct32_transfer')
        else:
            raise ValueError('Unsupported source pixel codec')
        clut = 'csm1' if bit_depth == 8 else 'linear'
        palette = _palette(ps2_pixels, b)
        ps2_rgba = indices_to_rgba(indices, palette_rgba(palette, bit_depth, clut, 'double', 'rgba'), bit_depth)
        pc_rgba = decode_dxt_base(_base(pc_pixels, a), a['width'], a['height'], CODEC_FOURCC[a['codec']])
        score = compare_rgba_nearest(pc_rgba, a['width'], a['height'], ps2_rgba, b['width'], b['height'])
        baseline_indices = decode_indices(source, b['width'], b['height'], bit_depth, 'linear')
        baseline_palette = palette_rgba(palette, bit_depth, 'linear', 'double', 'rgba')
        baseline_rgba = indices_to_rgba(baseline_indices, baseline_palette, bit_depth)
        baseline = compare_rgba_nearest(pc_rgba, a['width'], a['height'], baseline_rgba, b['width'], b['height'])
        results.append({'depth':bit_depth,'flag':flag,'rgb':score['mean_absolute_rgb_error'],
                        'alpha':score['mean_absolute_alpha_error'],
                        'baseline':baseline['mean_absolute_rgb_error']})
        flag_counts[flag] += 1
    by_depth = {str(bits):_summarize([row for row in results if row['depth'] == bits])
                for bits in (4,8) if any(row['depth'] == bits for row in results)}
    return {'shared_source_identities':len(common),'decoded_base_images':len(results),
            'texture_pixel_base_padding_bytes':{'pc':pc_pad, 'ps2':ps2_pad},
            'ps2_swizzle_flag_counts':{str(k):v for k,v in sorted(flag_counts.items())},
            'by_indexed_depth':by_depth,'all':_summarize(results),
            'verdict':'RGB source control only: PS2 alpha, mips, full texture writer and game rendering UNVERIFIED'}


def main():
    """CLI: private original Carbon archives, aggregates only, never images."""
    import argparse
    import json
    from pathlib import Path
    from texture_original_archive_pair_audit import _read_split, _read_regular
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', required=True, type=Path, nargs='+')
    p.add_argument('--carbon-ps2-zip', required=True, type=Path)
    args = p.parse_args()
    pc = _read_split(args.pc_volumes, (141, 142))
    ps2 = _read_regular(args.carbon_ps2_zip, (141, 142))
    report = {str(s): compare_source_color_sections(pc[s], ps2[s]) for s in (141, 142)}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
