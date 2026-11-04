#!/usr/bin/env python3
"""Source-private, resumable DXT5 quality audit for Undercover PS2.

Each bounded batch decodes original owner-supplied textures only in memory.
It returns arithmetic aggregates without source texture identifiers, pixels,
images, names, palettes, or modified game files. Combining rejects gaps,
overlaps, malformed totals, and cross-section mixing. Not a game runtime test.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from texture_metadata_pixel_bridge import parse_pack
from undercover_to_pc_dxt5_bridge import decode_undercover_source, encode_roundtrip

SCHEMA = 'nfsuc-dxt5-batch-v1'
MAX_BATCH = 12
MAX_TEXTURES = 512
DEPTHS = ('4', '8')


def _whole(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid integer ' + name)
    return value


def _metric(value, name):
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError('Invalid metric ' + name)
    return float(value)


def _empty():
    return {'textures': 0, 'pixels': 0, 'rgb_absolute_sum': 0,
            'alpha_absolute_sum': 0, 'texture_rgb_mae_sum': 0.0,
            'texture_alpha_mae_sum': 0.0, 'max_texture_rgb_mae': 0.0,
            'max_texture_alpha_mae': 0.0}


def _add_sample(bucket, n_pixels, rgb_error, alpha_error):
    _whole(n_pixels, 'pixels', 1)
    for metric in (rgb_error, alpha_error):
        _metric(metric, 'codec error')
        if metric > 255:
            raise ValueError('Codec error outside RGBA byte range')
    rgb_sum = round(rgb_error * 3 * n_pixels)
    alpha_sum = round(alpha_error * n_pixels)
    bucket['textures'] += 1
    bucket['pixels'] += n_pixels
    bucket['rgb_absolute_sum'] += rgb_sum
    bucket['alpha_absolute_sum'] += alpha_sum
    bucket['texture_rgb_mae_sum'] += rgb_error
    bucket['texture_alpha_mae_sum'] += alpha_error
    bucket['max_texture_rgb_mae'] = max(bucket['max_texture_rgb_mae'], rgb_error)
    bucket['max_texture_alpha_mae'] = max(bucket['max_texture_alpha_mae'], alpha_error)


def audit_section_range(section, section_id, start, count):
    """Bound a single original-source pass to at most MAX_BATCH textures."""
    if section_id not in (241, 3401) or type(section_id) is not int:
        raise ValueError('Unsupported original Undercover texture section')
    _whole(start, 'start')
    _whole(count, 'count', 1)
    if count > MAX_BATCH:
        raise ValueError('Batch exceeds bounded texture count')
    records = parse_pack(section, 'ps2')['records']
    total = len(records)
    if not 0 < total <= MAX_TEXTURES or start + count > total:
        raise ValueError('Texture batch is outside verified source index')
    overall = _empty()
    depths = {bits: _empty() for bits in DEPTHS}
    nonopaque_pixels = 0
    textures_with_nonopaque = 0
    textures_without_opaque = 0
    flag_counts = {'0': 0, '1': 0}
    for ordinal in range(start, start + count):
        rgba, width, height, bits, flag = decode_undercover_source(section, ordinal)
        if bits not in (4,8) or flag not in (0,1):
            raise ValueError('Unsupported decoded source profile')
        if len(rgba) != 4 * width * height:
            raise ValueError('Decoder produced wrong RGBA byte count')
        _, error = encode_roundtrip(rgba, width, height)
        n = width * height
        alpha_nonopaque = sum(a != 255 for a in rgba[3::4])
        nonopaque_pixels += alpha_nonopaque
        textures_with_nonopaque += alpha_nonopaque > 0
        textures_without_opaque += alpha_nonopaque == n
        flag_counts[str(flag)] += 1
        for bucket in (overall, depths[str(bits)]):
            _add_sample(bucket, n, error['mean_absolute_rgb_error'],
                        error['mean_absolute_alpha_error'])
    return {'schema': SCHEMA, 'section_id': section_id,
            'private_source_sha256': hashlib.sha256(section).hexdigest(),
            'source_texture_count': total, 'range_start': start,
            'range_end': start + count, 'data': overall,
            'indexed_depths': depths, 'swizzle_flags': flag_counts,
            'nonopaque_pixels': nonopaque_pixels,
            'textures_with_nonopaque_alpha': textures_with_nonopaque,
            'textures_without_fully_opaque_pixels': textures_without_opaque,
            'scope': 'OFFLINE_BASE_RGBA_DXT5_NOT_GAME_LOADED'}


def _validate_bucket(bucket):
    if type(bucket) is not dict or set(bucket) != set(_empty()):
        raise ValueError('Malformed per-depth/total DXT5 aggregate')
    n = _whole(bucket['textures'], 'texture count')
    pixels = _whole(bucket['pixels'], 'pixel count')
    rgb_sum = _whole(bucket['rgb_absolute_sum'], 'rgb absolute sum')
    alpha_sum = _whole(bucket['alpha_absolute_sum'], 'alpha absolute sum')
    if (pixels < n or rgb_sum > 3 * pixels * 255 or alpha_sum > pixels * 255 or
            (n == 0 and (pixels or rgb_sum or alpha_sum))):
        raise ValueError('Impossible DXT5 aggregate totals')
    for name in ('texture_rgb_mae_sum', 'texture_alpha_mae_sum',
                 'max_texture_rgb_mae', 'max_texture_alpha_mae'):
        value = _metric(bucket[name], name)
        if value > (255 * n if name.endswith('_sum') else (255 if n else 0)):
            raise ValueError('Impossible DXT5 metric')
    return n


def combine_batches(reports):
    """Merge complete source-order batches, with no skipped/duplicated ordinals.

    Mean-by-texture and mean-by-pixel are reported separately; neither is
    falsely labeled a lossless conversion or validated in-game texture.
    """
    if not isinstance(reports, (tuple, list)) or not reports:
        raise ValueError('No batch reports to merge')
    result = _empty()
    depth_totals = {k: _empty() for k in DEPTHS}
    flags = {'0':0,'1':0}
    nonopaque = has_nonopaque = lacks_opaque = 0
    sorted_reports = sorted(reports, key=lambda x: x.get('range_start', -1))
    first = sorted_reports[0]
    section_id = first.get('section_id')
    total = first.get('source_texture_count')
    source_digest = first.get('private_source_sha256')
    if (type(source_digest) is not str or len(source_digest) != 64 or
            any(ch not in '0123456789abcdef' for ch in source_digest)):
        raise ValueError('Malformed private source fingerprint')
    if type(section_id) is not int or section_id not in (241, 3401):
        raise ValueError('Unsupported source section for DXT5 merge')
    _whole(total, 'source total', 1)
    if total > MAX_TEXTURES:
        raise ValueError('Excessive original texture index size')
    cursor = 0
    for batch in sorted_reports:
        if (batch.get('schema') != SCHEMA or batch.get('section_id') != section_id or
                batch.get('source_texture_count') != total or
                batch.get('private_source_sha256') != source_digest or
                batch.get('scope') != 'OFFLINE_BASE_RGBA_DXT5_NOT_GAME_LOADED'):
            raise ValueError('Mixed or unsupported DXT5 batch reports')
        start = _whole(batch.get('range_start'), 'batch start')
        end = _whole(batch.get('range_end'), 'batch end')
        if start != cursor or not start < end <= total or end-start > MAX_BATCH:
            raise ValueError('Missing, overlapping, or unsafe DXT5 batch ranges')
        _validate_bucket(batch.get('data'))
        if batch['data']['textures'] != end-start:
            raise ValueError('Batch texture count and range disagree')
        depths = batch.get('indexed_depths')
        if type(depths) is not dict or set(depths) != set(DEPTHS):
            raise ValueError('Malformed indexed-depth coverage')
        for key in DEPTHS:
            _validate_bucket(depths[key])
        if (sum(depths[k]['textures'] for k in DEPTHS) != end-start or
                any(sum(depths[k][field] for k in DEPTHS) != batch['data'][field]
                    for field in ('pixels','rgb_absolute_sum','alpha_absolute_sum')) or
                any(not math.isclose(sum(depths[k][field] for k in DEPTHS),
                                     batch['data'][field],abs_tol=1e-6,rel_tol=1e-12)
                    for field in ('texture_rgb_mae_sum','texture_alpha_mae_sum'))):
            raise ValueError('Per-depth totals do not reconcile')
        row_flags = batch.get('swizzle_flags')
        if type(row_flags) is not dict or set(row_flags) != {'0','1'}:
            raise ValueError('Malformed swizzle flag aggregate')
        for key in flags:
            flags[key] += _whole(row_flags[key], 'flag count')
        if sum(_whole(row_flags[k], 'swizzle flag count') for k in flags) != end-start:
            raise ValueError('Source swizzle flags do not reconcile')
        npx = _whole(batch.get('nonopaque_pixels'), 'nonopaque texels')
        with_nonopaque = _whole(batch.get('textures_with_nonopaque_alpha'), 'nonopaque textures')
        without_opaque = _whole(batch.get('textures_without_fully_opaque_pixels'), 'no-opaque textures')
        if (npx > batch['data']['pixels'] or without_opaque > with_nonopaque or
                with_nonopaque > end-start):
            raise ValueError('Impossible source alpha coverage')
        nonopaque += npx
        has_nonopaque += with_nonopaque
        lacks_opaque += without_opaque
        for bucket, row in [(result,batch['data'])] + [(depth_totals[k],depths[k]) for k in DEPTHS]:
            for field in ('textures','pixels','rgb_absolute_sum','alpha_absolute_sum',
                          'texture_rgb_mae_sum','texture_alpha_mae_sum'):
                bucket[field] += row[field]
            for field in ('max_texture_rgb_mae','max_texture_alpha_mae'):
                bucket[field] = max(bucket[field],row[field])
        cursor = end
    if cursor != total or result['textures'] != total:
        raise ValueError('Incomplete original texture coverage')
    def formatted(bucket):
        if not bucket['textures']:
            return {'textures':0, 'pixels':0}
        return {'textures':bucket['textures'], 'pixels':bucket['pixels'],
                'mean_texture_rgb_mae':round(bucket['texture_rgb_mae_sum']/bucket['textures'],4),
                'mean_texture_alpha_mae':round(bucket['texture_alpha_mae_sum']/bucket['textures'],4),
                'mean_pixel_rgb_mae':round(bucket['rgb_absolute_sum']/(3*bucket['pixels']),4),
                'mean_pixel_alpha_mae':round(bucket['alpha_absolute_sum']/bucket['pixels'],4),
                'max_texture_rgb_mae':round(bucket['max_texture_rgb_mae'],4),
                'max_texture_alpha_mae':round(bucket['max_texture_alpha_mae'],4)}
    return {'section_id':section_id, 'original_textures_covered':total,
            'complete_contiguous_coverage':True,
            'texture_errors':formatted(result),
            'indexed_depths':{k:formatted(v) for k,v in depth_totals.items()},
            'swizzle_flags':flags,
            'source_textures_with_nonopaque_alpha':has_nonopaque,
            'source_textures_with_no_fully_opaque_pixels':lacks_opaque,
            'mean_nonopaque_pixel_fraction':round(nonopaque/result['pixels'],6),
            'scope':'OFFLINE_DXT5_TRANSCODE_ONLY_RUNTIME_AND_BLENDING_UNVERIFIED'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    actions = p.add_subparsers(dest='action',required=True)
    audit = actions.add_parser('audit',help='Decode owner archive in bounded batches')
    audit.add_argument('--undercover-ps2-zip',type=Path,required=True)
    audit.add_argument('--section',type=int,choices=(241,3401),default=241)
    audit.add_argument('--start',type=int,required=True)
    audit.add_argument('--count',type=int,required=True)
    combine = actions.add_parser('combine',help='Merge aggregate JSON batch reports')
    combine.add_argument('batch_reports',type=Path,nargs='+')
    args = p.parse_args()
    if args.action=='audit':
        from private_undercover_dxt5_archive_audit import _private_uc_section
        source = _private_uc_section(args.undercover_ps2_zip,args.section)
        answer = audit_section_range(source,args.section,args.start,args.count)
    else:
        if len(args.batch_reports)>MAX_TEXTURES:
            p.error('Too many batch reports')
        report_rows=[]
        for path in args.batch_reports:
            if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:
                p.error('Invalid or oversized local batch JSON file')
            with path.open('r',encoding='utf-8') as fp:
                report_rows.append(json.load(fp))
        answer=combine_batches(report_rows)
    print(json.dumps(answer,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
