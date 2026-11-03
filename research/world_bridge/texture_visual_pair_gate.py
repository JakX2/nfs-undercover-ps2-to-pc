#!/usr/bin/env python3
"""Read-only hypothesis audit of two *already extracted* original Carbon texture sections.

Never auto-picks a PS2 decode method. Original pixels, hashes and names remain
private to this process. The returned report contains aggregate counts only.

This is a bounded offline comparison harness, not a texture writer or evidence
that one hypothesis is the original Undercover GPU transfer convention.
"""
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import struct

from texture_metadata_pixel_bridge import parse_pack, children, CODEC_FOURCC, MAX_SECTION
from ps2_texture_layout_candidates import LAYOUTS, decode_indices, palette_rgba, indices_to_rgba
from pc_dxt_reference_decode import decode_dxt_base, compare_rgba_nearest

MAX_PAIRS = 12
MAX_PIXELS = 4 * 1024 * 1024


def _pixels(section):
    """Extract the already-validated, bounded 0x33320002 data in memory only."""
    root_length = struct.unpack_from('<I', section, 4)[0]
    root = children(section, 8, 8 + root_length)
    pix = children(root[3][1])
    return memoryview(pix[2][1])


def _base(section_pixel, meta):
    start, size = meta['image_offset'], meta['base_image_bytes']
    if size < 1 or start < 0 or start + size > len(section_pixel):
        raise ValueError('Texture base image exceeds validated pixel span')
    return section_pixel[start:start + size]


def _palette(section_pixel, meta):
    start, size = meta['palette_offset'], meta['palette_bytes']
    if size not in (64, 1024) or start < 0 or start + size > len(section_pixel):
        raise ValueError('Palette exceeds validated pixel span')
    return section_pixel[start:start + size]


def _platform_flags(section, records):
    """Return per-identity provisional +0x17 flag bytes, without exporting IDs."""
    root_length = struct.unpack_from('<I', section, 4)[0]
    root = children(section, 8, 8 + root_length)
    desc = children(root[1][1])
    raw = desc[3][1]
    return {identity: raw[i*84 + 0x17] for i, identity in enumerate(records)}


def _options(bits):
    # PSMT4 uses one 16-entry palette. CSM1's 8bpp bank exchange has no effect
    # there, so avoid creating duplicate candidates that tie spuriously.
    cluts = ('linear', 'csm1') if bits == 8 else ('linear',)
    for layout, clut, alpha, channels in itertools.product(
            LAYOUTS, cluts, ('raw', 'double'), ('rgba', 'bgra')):
        yield (layout, clut, alpha, channels)


def _score_key(option):
    return '/'.join(option)


def _sample_pairs(pc, ps2, max_pairs):
    """Deterministic fair-ish sampling across bit depths and size categories.

    Selection uses *only* metadata categories and ascending private identities.
    Hashes never appear in the returned report.
    """
    shared = sorted(pc.keys() & ps2.keys())
    groups = defaultdict(list)
    for identity in shared:
        a, b = pc[identity], ps2[identity]
        if (a['width'] * a['height'] > MAX_PIXELS or
                b['width'] * b['height'] > MAX_PIXELS):
            continue
        same = (a['width'], a['height']) == (b['width'], b['height'])
        groups[(b['codec'], same)].append(identity)
    ordered_groups = [groups[k] for k in sorted(groups)]
    selected = []
    pos = 0
    while len(selected) < max_pairs:
        advanced = False
        for group in ordered_groups:
            if pos < len(group) and len(selected) < max_pairs:
                selected.append(group[pos])
                advanced = True
        if not advanced:
            break
        pos += 1
    return len(shared), selected


def compare_sections(pc_section, ps2_section, max_pairs=8):
    """Compare same-hash Carbon PC/PS2 base levels; return no identifying data.

    Raw pixel bytes are never returned or written. Candidate failures are
    recorded, not silently replaced by another layout. Scores are not a
    fidelity proof: GPU alpha, UV mirroring, distinct art and resampling can
    still explain large disagreement between original game images.
    """
    if type(max_pairs) is not int or not 2 <= max_pairs <= MAX_PAIRS:
        raise ValueError('max_pairs must be between 2 and 12')
    if not isinstance(pc_section, (bytes, bytearray)) or not isinstance(ps2_section, (bytes, bytearray)):
        raise ValueError('Expected in-memory original section bytes')
    pc = parse_pack(pc_section, 'pc')['records']
    ps2 = parse_pack(ps2_section, 'ps2')['records']
    pc_pixel = _pixels(pc_section)
    ps2_pixel = _pixels(ps2_section)
    ps2_flags = _platform_flags(ps2_section, ps2)
    shared_count, chosen = _sample_pairs(pc, ps2, max_pairs)
    if shared_count < 2 or len(chosen) < 2:
        raise ValueError('At least two safe matching Carbon textures are required')
    stats = defaultdict(lambda: {'successful_pairs':0, 'failed_pairs':0,
                                 'rgb_mae_sum':0.0,'alpha_mae_sum':0.0})
    ignored_uniform = 0
    flag_histogram = defaultdict(int)
    for identity in chosen:
        p, s = pc[identity], ps2[identity]
        if p['name'] != s['name'] or p['tile_mode'] != s['tile_mode']:
            raise ValueError('Same-hash Carbon identity metadata mismatch')
        flag_histogram[str(ps2_flags[identity])] += 1
        pc_rgba = decode_dxt_base(_base(pc_pixel, p), p['width'],p['height'], CODEC_FOURCC[p['codec']])
        ps2_source = _base(ps2_pixel, s)
        ps2_clut = _palette(ps2_pixel, s)
        # Uniform PC images cannot establish spatial layout. They are measured
        # but explicitly counted as weak spatial evidence.
        pixel_colors = {pc_rgba[i:i+4] for i in range(0, len(pc_rgba), 4)}
        if len(pixel_colors) == 1:
            ignored_uniform += 1
        for layout in LAYOUTS:
            try:
                indices = decode_indices(ps2_source, s['width'],s['height'],s['codec'],layout)
            except ValueError:
                for opt in _options(s['codec']):
                    if opt[0] == layout: stats[_score_key(opt)]['failed_pairs'] += 1
                continue
            for opt in _options(s['codec']):
                if opt[0] != layout: continue
                _, clut, alpha, channels = opt
                key = _score_key(opt)
                try:
                    pal = palette_rgba(ps2_clut, s['codec'], clut, alpha, channels)
                    rgba = indices_to_rgba(indices, pal, s['codec'])
                    result = compare_rgba_nearest(pc_rgba,p['width'],p['height'],rgba,s['width'],s['height'])
                    stats[key]['successful_pairs'] += 1
                    stats[key]['rgb_mae_sum'] += result['mean_absolute_rgb_error']
                    stats[key]['alpha_mae_sum'] += result['mean_absolute_alpha_error']
                except ValueError:
                    stats[key]['failed_pairs'] += 1
    candidates = []
    for key, s in sorted(stats.items()):
        n = s['successful_pairs']
        candidates.append({'hypothesis':key,'supported_pairs':n,
                           'failed_pairs':s['failed_pairs'],
                           'mean_rgb_mae':round(s['rgb_mae_sum']/n,4) if n else None,
                           'mean_alpha_mae':round(s['alpha_mae_sum']/n,4) if n else None,
                           'complete_coverage':n==len(chosen)})
    return {'shared_identity_count':shared_count,'sampled_pairs':len(chosen),
            'sampled_uniform_pc_images':ignored_uniform,
            'spatially_informative_pairs':len(chosen)-ignored_uniform,
            'sampled_provisional_ps2_plus_0x17_flag_counts':dict(sorted(flag_histogram.items())),
            'candidates':candidates,
            'verdict':'UNVERIFIED: hypothesis scores only; no automatic layout selection',
            'scope':'Base mip only; not proof of pixel layout, visual identity, or PC runtime loading'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-section', type=Path, required=True, help='Private Carbon PC section slice (e.g. 141)')
    p.add_argument('--ps2-section', type=Path, required=True, help='Private Carbon PS2 same-ID section slice')
    p.add_argument('--max-pairs', type=int, default=8)
    args = p.parse_args()
    for path in (args.pc_section, args.ps2_section):
        if not path.is_file() or path.stat().st_size > MAX_SECTION:
            raise ValueError('Missing source section or exceeds 32 MiB safety bound')
    report = compare_sections(args.pc_section.read_bytes(), args.ps2_section.read_bytes(), args.max_pairs)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()