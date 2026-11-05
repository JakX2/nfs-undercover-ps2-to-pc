#!/usr/bin/env python3
"""Read-only, privacy-preserving Carbon PC before/after PNG screenshot evidence gate.

Checks screenshot ROI changes against multiple user-selected *background* anchors;
optionally joins the existing verified private smoke-session/ProcMon gate.
Never edits or exports images, original archives, game files, private paths,
coordinates, hashes or PIDs. A positive result is a SCREEN DIFFERENCE CANDIDATE,
not proof of Undercover texture rendering, game loader ABI or time-of-capture.

Uses only Python's standard library. Supported input: 8-bit, noninterlaced,
truecolor PNG (RGB or RGBA). Other images fail closed instead of relying on
implicit color conversions, animated frames or third-party plugins.
"""
import argparse
import json
import math
import os
from pathlib import Path
import struct
import zlib

PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
MAX_PNG_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 14_000_000
MAX_ROW_BYTES = 32768
MAX_ROI_BYTES = 8192
MAX_CHUNKS = 4096
MAX_SAMPLES_PER_BOX = 100000
MIN_BOX_PIXELS = 16
MIN_ANCHORS = 2
MAX_ANCHORS = 8
ROI_FORMAT = 'nfsuc-carbon-visual-roi-v1'


def _owner_file(path, limit):
    p = Path(path).absolute()
    if any(q.is_symlink() for q in (p, *p.parents)):
        raise ValueError('Refusing symlinked private input or ancestor')
    if not p.is_file() or not 0 < p.stat().st_size <= limit:
        raise ValueError('Private input is missing, empty or oversized')
    return p


def decode_rgb_png(data):
    """Decode one bounded noninterlaced RGB/RGBA PNG; discard display alpha.

    Verify all chunk CRCs and zlib framing, including Adler-32. Reject unsafe,
    unknown critical, palette, grayscale, 16-bit and interlaced variants.
    Image pixels remain in caller-owned memory and never enter a report.
    """
    if not isinstance(data, bytes) or not len(PNG_MAGIC) < len(data) <= MAX_PNG_BYTES or not data.startswith(PNG_MAGIC):
        raise ValueError('Expected bounded 8-bit RGB/RGBA PNG bytes')
    p = len(PNG_MAGIC)
    width = height = channels = None
    packed = bytearray()
    chunk_count = 0
    seen_idat = False
    finished_idat = False
    finished = False
    while p < len(data):
        if p + 12 > len(data) or chunk_count >= MAX_CHUNKS:
            raise ValueError('Truncated PNG or excessive chunk count')
        n = struct.unpack_from('>I', data, p)[0]
        tag = data[p + 4:p + 8]
        stop = p + 12 + n
        if n > MAX_PNG_BYTES or stop > len(data) or len(tag) != 4 or not all(65 <= x <= 90 or 97 <= x <= 122 for x in tag):
            raise ValueError('Malformed PNG chunk')
        body = data[p + 8:p + 8 + n]
        crc = struct.unpack_from('>I', data, p + 8 + n)[0]
        if zlib.crc32(tag + body) & 0xffffffff != crc:
            raise ValueError('PNG chunk CRC mismatch')
        chunk_count += 1
        p = stop
        if chunk_count == 1 and tag != b'IHDR':
            raise ValueError('PNG must begin with IHDR')
        if tag == b'IHDR':
            if chunk_count != 1 or len(body) != 13:
                raise ValueError('Repeated or invalid PNG IHDR')
            width, height, depth, ctype, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if (not width or not height or width * height > MAX_PIXELS or
                    depth != 8 or ctype not in (2, 6) or compression or filtering or interlace):
                raise ValueError('Unsupported PNG dimensions or pixel format')
            channels = 3 if ctype == 2 else 4
            if width * channels > MAX_ROW_BYTES:
                raise ValueError('Unsafe PNG row size')
        elif tag == b'IDAT':
            if finished_idat or width is None:
                raise ValueError('Out-of-order PNG IDAT')
            seen_idat = True
            if len(packed) + n > MAX_PNG_BYTES:
                raise ValueError('Excessive PNG compressed pixel bytes')
            packed.extend(body)
        elif tag == b'IEND':
            if n or not seen_idat or p != len(data):
                raise ValueError('Invalid or premature PNG IEND')
            finished = True
            break
        elif tag in (b'PLTE', b'tRNS', b'acTL', b'fcTL', b'fdAT'):
            raise ValueError('Palette/transparency/animated PNG not supported')
        elif tag[0] & 32 == 0:
            raise ValueError('Unknown critical PNG chunk')
        if seen_idat and tag != b'IDAT':
            finished_idat = True
    if not finished or width is None:
        raise ValueError('PNG has no complete image')
    row_bytes = width * channels
    expected = height * (1 + row_bytes)
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(bytes(packed), expected + 1)
        raw += decoder.flush(expected + 1 - len(raw))
    except zlib.error as exc:
        raise ValueError('Invalid PNG zlib stream') from exc
    if len(raw) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PNG inflated pixel bytes or zlib framing mismatch')
    rgb = bytearray(width * height * 3)
    prev = bytearray(row_bytes)
    pos = 0
    for y in range(height):
        filter_id = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + row_bytes])
        pos += row_bytes
        if filter_id not in (0, 1, 2, 3, 4):
            raise ValueError('Unsupported PNG row filter')
        for x in range(row_bytes):
            left = row[x - channels] if x >= channels else 0
            up = prev[x]
            upper_left = prev[x - channels] if x >= channels else 0
            if filter_id == 1:
                predictor = left
            elif filter_id == 2:
                predictor = up
            elif filter_id == 3:
                predictor = (left + up) // 2
            elif filter_id == 4:
                p0 = left + up - upper_left
                a, b, c = abs(p0-left), abs(p0-up), abs(p0-upper_left)
                predictor = left if a <= b and a <= c else (up if b <= c else upper_left)
            else:
                predictor = 0
            row[x] = (row[x] + predictor) & 255
        dst = y * width * 3
        if channels == 3:
            rgb[dst:dst + width * 3] = row
        else:
            for x in range(width):
                rgb[dst + x*3:dst + x*3 + 3] = row[x*4:x*4 + 3]
        prev = row
    return width, height, bytes(rgb)


def _json_no_repeated_keys(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('Duplicate private ROI JSON field')
        out[k] = v
    return out


def parse_roi(data, width, height):
    """Validate private pixel-space target and >=2 disjoint reference regions."""
    if not isinstance(data, str) or len(data.encode('utf-8')) > MAX_ROI_BYTES:
        raise ValueError('Invalid private ROI JSON')
    try:
        roi = json.loads(data, object_pairs_hook=_json_no_repeated_keys)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError('Malformed private ROI JSON') from exc
    if not isinstance(roi, dict) or set(roi) != {'format', 'target', 'anchors'} or roi['format'] != ROI_FORMAT:
        raise ValueError('Unsupported or incomplete private ROI format')
    if not isinstance(roi['anchors'], list) or not MIN_ANCHORS <= len(roi['anchors']) <= MAX_ANCHORS:
        raise ValueError('Require two to eight background anchor boxes')
    def valid_box(obj):
        if (not isinstance(obj, list) or len(obj) != 4 or
                any(type(x) is not int or x < 0 for x in obj)):
            raise ValueError('ROI rectangles require four nonnegative integers')
        x, y, w, h = obj
        if w < 1 or h < 1 or w*h < MIN_BOX_PIXELS or x+w > width or y+h > height:
            raise ValueError('ROI outside PNG or too small')
        return tuple(obj)
    boxes = [valid_box(roi['target'])] + [valid_box(x) for x in roi['anchors']]
    for i, a in enumerate(boxes):
        for b in boxes[i+1:]:
            if a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]:
                raise ValueError('Target and background reference regions overlap')
    return boxes[0], boxes[1:]


def _box_score(before, after, width, rect):
    x0, y0, w, h = rect
    step = max(1, math.ceil(math.sqrt((w*h) / MAX_SAMPLES_PER_BOX)))
    total = changed = samples = 0
    for y in range(y0, y0+h, step):
        for x in range(x0, x0+w, step):
            off = (y*width+x)*3
            d = sum(abs(before[off+k]-after[off+k]) for k in range(3))
            total += d
            changed += d >= 3*24
            samples += 1
    return (total / (3*samples), changed/samples, samples)


def compare_png_evidence(before_path, after_path, roi_path, restored_path=None):
    """Compare clean/staged images and optionally test clean/staged/restored reversion.

    Even three snapshots cannot establish their creation order or prove texture
    rendering. Source images, pixel-space ROIs and paths are never published.
    """
    a = _owner_file(before_path, MAX_PNG_BYTES)
    b = _owner_file(after_path, MAX_PNG_BYTES)
    roifile = _owner_file(roi_path, MAX_ROI_BYTES)
    restored = _owner_file(restored_path, MAX_PNG_BYTES) if restored_path is not None else None
    sources = (a, b, roifile) + ((restored,) if restored is not None else ())
    if (len({p.resolve() for p in sources}) != len(sources) or
            any(os.path.samefile(x, y) for i, x in enumerate(sources) for y in sources[i+1:])):
        raise ValueError('Private screenshot and ROI inputs must be distinct')
    before_w, before_h, before = decode_rgb_png(a.read_bytes())
    after_w, after_h, after = decode_rgb_png(b.read_bytes())
    if (before_w, before_h) != (after_w, after_h):
        raise ValueError('Screenshot dimensions differ; compare matching views')
    target, anchors = parse_roi(roifile.read_text(encoding='utf-8-sig'), before_w, before_h)
    t_mae, t_fraction, t_samples = _box_score(before, after, before_w, target)
    ref = [_box_score(before, after, before_w, anchor) for anchor in anchors]
    ref_mean = sum(a[0]*a[2] for a in ref)/sum(a[2] for a in ref)
    ref_max = max(a[0] for a in ref)
    ref_changed = max(a[1] for a in ref)
    stable = ref_max <= 6.5 and ref_changed <= 0.08
    localized = t_mae >= 15 and t_fraction >= 0.12 and t_mae >= 3*ref_mean + 10
    if not stable:
        verdict = 'background_changed_framing_or_scene_not_controlled'
    elif localized:
        verdict = 'localized_screen_difference_candidate_not_rendering_proof'
    elif t_mae < 8 and t_fraction < 0.08:
        verdict = 'no_material_screen_difference_detected'
    else:
        verdict = 'ambiguous_screen_change_not_rendering_proof'
    restoration = {'restoration_control_performed':False}
    if restored is not None:
        restored_w, restored_h, restored_pixels = decode_rgb_png(restored.read_bytes())
        if (restored_w, restored_h) != (before_w, before_h):
            raise ValueError('Restored screenshot dimensions differ')
        r_mae, r_fraction, _ = _box_score(before, restored_pixels, before_w, target)
        r_refs = [_box_score(before, restored_pixels, before_w, anchor) for anchor in anchors]
        r_stable = max(x[0] for x in r_refs) <= 6.5 and max(x[1] for x in r_refs) <= 0.08
        r_clean = r_mae < 8 and r_fraction < 0.08
        restoration = {'restoration_control_performed':True,
                       'restoration_background_stable':r_stable,
                       'restored_target_rgb_delta_0_255':round(r_mae,4),
                       'restored_target_pixels_changed_fraction':round(r_fraction,6),
                       'restoration_visual_match_to_baseline':bool(r_stable and r_clean)}
        if not r_stable:
            verdict = 'restoration_frame_unstable_no_reversible_visual_inference'
        elif not r_clean:
            verdict = 'restored_target_differs_from_baseline_no_reversion_proof'
        elif verdict == 'localized_screen_difference_candidate_not_rendering_proof':
            verdict = 'reversible_localized_screen_difference_candidate_not_rendering_proof'
    return {'scope':'PRIVATE_SCREENSHOT_PIXEL_COMPARISON_NOT_RENDERING_PROOF',
            'same_dimensions':True,
            'background_anchor_count':len(ref),
            'background_anchor_stability_passed':stable,
            'background_mean_rgb_delta_0_255':round(ref_mean,4),
            'background_worst_anchor_rgb_delta_0_255':round(ref_max,4),
            'target_mean_rgb_delta_0_255':round(t_mae,4),
            'target_pixels_changed_fraction':round(t_fraction,6),
            'target_sample_count':t_samples,
            'verdict':verdict,
            **restoration,
            'private_paths_coordinates_images_and_hashes_omitted':True,
            'limitations':('Static pixel differences cannot prove the changed object is the target texture. '
                           'Camera motion, lighting, occlusion, HUD, animation, gamma and game state remain '
                           'possible confounders even when backgrounds look stable. Before/staged/restored '
                           'capture order and timestamps are not attested.')}


def attest_session_visual(session_dir, procmon_csv, before_png, after_png, roi_json):
    """Join the prior full-stream/ProcMon evidence gate with private PNG control.

    The existing session gate validates currently installed bytes; it cannot
    establish which bytes were installed at screenshot/ReadFile capture time.
    """
    from carbon_pc_private_smoke_session import evidence
    image = compare_png_evidence(before_png, after_png, roi_json)
    stream = evidence(session_dir, procmon_csv)
    trace = stream['procmon']
    access = trace['evidence_level'] in (
        'some_image_bytes_read_observed_not_rendering',
        'full_image_span_read_observed_not_rendering')
    candidate = image['verdict'] == 'localized_screen_difference_candidate_not_rendering_proof'
    if candidate and access:
        verdict = 'read_span_and_localized_visual_difference_candidate_not_rendering_proof'
    elif candidate:
        verdict = 'localized_visual_change_without_verified_image_read'
    elif access:
        verdict = 'image_span_read_without_controlled_visual_difference'
    else:
        verdict = 'no_joint_image_read_and_visual_evidence'
    return {'scope':'POST_CAPTURE_INTEGRITY_AND_VISUAL_EVIDENCE_NOT_RENDERING_PROOF',
            'visual':image,
            'stream':stream,
            'joint_verdict':verdict,
            'timestamp_and_runtime_rendering_unverified':True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    simple = sub.add_parser('compare', help='Private read-only PNG before/after/(optional restore) comparison')
    joined = sub.add_parser('session', help='Combine PNG comparison with existing private session/ProcMon proof')
    for parser in (simple, joined):
        parser.add_argument('--before-png', type=Path, required=True)
        parser.add_argument('--after-png', type=Path, required=True)
        parser.add_argument('--roi-json', type=Path, required=True)
    simple.add_argument('--restored-png', type=Path, help='Optional third screenshot AFTER byte-exact restoration')
    joined.add_argument('--session-dir', type=Path, required=True)
    joined.add_argument('--procmon-csv', type=Path, required=True)
    a = p.parse_args()
    result = (compare_png_evidence(a.before_png, a.after_png, a.roi_json, a.restored_png)
              if a.command == 'compare' else
              attest_session_visual(a.session_dir, a.procmon_csv,
                                    a.before_png, a.after_png, a.roi_json))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
