#!/usr/bin/env python3
"""Privately stage a real PS2 Undercover texture in one existing Carbon PC DXT5 slot.

Read-only dry-run by default. Explicit writing produces a NEW, private and
same-size *copy* of the original Carbon PC STREAML5RB.BUN; it never installs,
modifies source archives, touches an executable, or creates new texture hashes.
Original game bytes must never be committed, published, or attached to issues.
This is an offline resource-envelope test, NOT evidence of in-game rendering.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

from private_undercover_dxt5_archive_audit import _private_uc_section
from private_carbon_dxt1_stream_stage import (section_span, _verify_output,
                                               _digest_file, READ_SIZE)
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from pc_texture_header_overlay_gate import _source_image_span
from undercover_to_pc_dxt5_bridge import overlay_undercover_on_existing_pc_dxt5

MAX_UC_ZIP = 1024 * 1024 * 1024
MAX_BUN = 8 * 1024 * 1024
MAX_STREAM = 2 * 1024 * 1024 * 1024


def _owner_file(path, maximum):
    p = Path(path).absolute()
    if any(s.is_symlink() for s in (p, *p.parents)):
        raise ValueError('Symlinks in original source path are not permitted')
    if not p.is_file() or not 0 < p.stat().st_size <= maximum:
        raise ValueError('Missing, empty or oversized original source file')
    return p.resolve(strict=True)


def compatible_pairs(uc_section, pc_section):
    """Return only private ordinal/dimension matches, never texture hashes."""
    uc = parse_pack(uc_section, 'ps2')['records']
    pc = parse_pack(pc_section, 'pc')['records']
    aligned_pixel_array(uc_section, uc)
    aligned_pixel_array(pc_section, pc)
    donors = [m for _, m in sorted(uc.items())]
    targets = [m for _, m in sorted(pc.items()) if m['codec'] == 38]
    pairs = [(i, j, d['width'], d['height'])
             for i, d in enumerate(donors)
             for j, t in enumerate(targets)
             if (d['width'], d['height']) == (t['width'], t['height'])]
    return sorted(pairs, key=lambda v: (v[2] * v[3], v[0], v[1]))


def plan_undercover_dxt5(bundle, stream_length, pc_section, uc_section,
                          carbon_section=142, donor_ordinal=None, pc_dxt5_slot=None):
    """Make one in-memory image-span plan, preserving PC metadata and hashes.

    Omitted donor+slot selects the lowest-pixel-count matching pair for a fast
    initial smoke test; both ordinals must be specified to override it.
    """
    if (donor_ordinal is None) != (pc_dxt5_slot is None):
        raise ValueError('Supply both donor and PC DXT5 slot ordinals or neither')
    if donor_ordinal is not None and (type(donor_ordinal) is not int or donor_ordinal < 0):
        raise ValueError('Invalid donor ordinal')
    if pc_dxt5_slot is not None and (type(pc_dxt5_slot) is not int or pc_dxt5_slot < 0):
        raise ValueError('Invalid target DXT5 slot ordinal')
    off, length = section_span(bundle, stream_length, carbon_section)
    if not isinstance(pc_section, bytes) or len(pc_section) != length:
        raise ValueError('Original PC section differs from its table row')
    if not isinstance(uc_section, bytes):
        raise ValueError('Invalid owner-supplied Undercover section')
    pairs = compatible_pairs(uc_section, pc_section)
    if not pairs:
        raise ValueError('No exact-dimension existing PC DXT5 pair')
    auto = donor_ordinal is None
    if auto:
        donor_ordinal, pc_dxt5_slot = pairs[0][:2]
    pc_meta = parse_pack(pc_section, 'pc')['records']
    targets = [m for _, m in sorted(pc_meta.items()) if m['codec'] == 38]
    if donor_ordinal >= len(parse_pack(uc_section, 'ps2')['records']) or pc_dxt5_slot >= len(targets):
        raise ValueError('Selected donor or PC DXT5 slot ordinal is out of range')
    dmeta = list(m for _, m in sorted(parse_pack(uc_section, 'ps2')['records'].items()))[donor_ordinal]
    tmeta = targets[pc_dxt5_slot]
    if (dmeta['width'], dmeta['height']) != (tmeta['width'], tmeta['height']):
        raise ValueError('Selected source and target dimensions do not match')
    modified, stats = overlay_undercover_on_existing_pc_dxt5(
        pc_section, uc_section, donor_ordinal, pc_dxt5_slot)
    left, right = _source_image_span(pc_section, tmeta)
    if (len(modified) != length or modified[:left] != pc_section[:left] or
            modified[right:] != pc_section[right:] or
            len(modified[left:right]) != tmeta['image_bytes'] or
            modified[left:right] == pc_section[left:right]):
        raise ValueError('DXT5 overlay escaped the one existing image span')
    restored = bytearray(modified)
    restored[left:right] = pc_section[left:right]
    if bytes(restored) != pc_section:
        raise ValueError('In-memory exact restoration failed')
    return {
        'change_start': off + left,
        'original_image': pc_section[left:right],
        'replacement_image': modified[left:right],
        'compatible_pairs': len(pairs),
        'donor_ordinal': donor_ordinal,
        'pc_dxt5_slot': pc_dxt5_slot,
        'automatic_selection': auto,
        'stats': stats,
    }


def stage_undercover_dxt5_copy(uc_zip, carbon_bun, carbon_stream,
                                undercover_section=3401, carbon_section=142,
                                donor_ordinal=None, pc_dxt5_slot=None,
                                private_output=None, write_private_copy=False):
    """Build a private DXT5 donor replacement plan; opt-in new-file write.

    The original ZIP member CRCs are checked by zipfile. An output write
    verifies SHA-256 and byte identity of the full original before/after.
    """
    if undercover_section not in (241, 3401) or type(undercover_section) is not int:
        raise ValueError('Unsupported Undercover donor section')
    if carbon_section not in (141, 142) or type(carbon_section) is not int:
        raise ValueError('Unsupported Carbon PC target section')
    if type(write_private_copy) is not bool:
        raise ValueError('Invalid explicit-write flag')
    if write_private_copy and private_output is None:
        raise ValueError('Explicit new private output is required')
    if not write_private_copy and private_output is not None:
        raise ValueError('Private output path requires explicit write opt-in')
    uc_zip = _owner_file(uc_zip, MAX_UC_ZIP)
    carbon_bun = _owner_file(carbon_bun, MAX_BUN)
    carbon_stream = _owner_file(carbon_stream, MAX_STREAM)
    source_paths = (uc_zip, carbon_bun, carbon_stream)
    if (len(set(source_paths)) != 3 or
            any(os.path.samefile(a, b) for i, a in enumerate(source_paths)
                for b in source_paths[i + 1:])):
        raise ValueError('Input source files unexpectedly alias')
    # An existing source must never be opened writable.
    snapshot = {p: (p.stat().st_size, p.stat().st_mtime_ns, _digest_file(p))
                for p in (uc_zip, carbon_bun, carbon_stream)}
    bundle = carbon_bun.read_bytes()
    stream_size = carbon_stream.stat().st_size
    off, n = section_span(bundle, stream_size, carbon_section)
    with carbon_stream.open('rb') as fp:
        fp.seek(off)
        pc_section = fp.read(n)
    if len(pc_section) != n:
        raise ValueError('Short original Carbon section read')
    uc_section = _private_uc_section(uc_zip, undercover_section)
    plan = plan_undercover_dxt5(bundle, stream_size, pc_section, uc_section,
                               carbon_section, donor_ordinal, pc_dxt5_slot)
    for p, state in snapshot.items():
        if (p.stat().st_size, p.stat().st_mtime_ns, _digest_file(p)) != state:
            raise ValueError('Owner-supplied original file changed during audit')
    s = plan['stats']
    report = {
        'scope': 'PRIVATE_OFFLINE_DXT5_EXISTING_SLOT_NOT_RENDERED',
        'undercover_section': undercover_section, 'carbon_section': carbon_section,
        'donor_ordinal': plan['donor_ordinal'], 'pc_dxt5_slot': plan['pc_dxt5_slot'],
        'automatic_dimension_match': plan['automatic_selection'],
        'available_dimension_matches': plan['compatible_pairs'],
        'width': s['width'], 'height': s['height'], 'mip_levels': s['mip_levels'],
        'source_bits': s['source_indexed_bits'],
        'image_span_bytes': s['replaced_image_bytes'],
        'changed_image_bytes': s['changed_image_bytes'],
        'rgb_mae': s['rgb_mae_against_decoded_ps2'],
        'alpha_mae': s['alpha_mae_against_decoded_ps2'],
        'same_size_and_every_other_stream_byte_preserved': True,
        'originals_unchanged': True, 'private_copy_created': False,
    }
    if not write_private_copy:
        return report
    output = Path(private_output).absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError('Symlinked private output path is forbidden')
    if (not output.parent.is_dir() or output.exists() or
            output.parent.name.casefold() == 'tracks' or
            output.name.casefold() == 'streaml5rb.bun' or
            not output.name.upper().startswith('STAGED_')):
        raise ValueError('Output must be NEW STAGED_ private file in an existing directory')
    if output in (uc_zip, carbon_bun, carbon_stream):
        raise ValueError('Cannot overwrite original sources')
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix='.nfsuc-private-stage-',suffix='.tmp',dir=output.parent)
        with os.fdopen(fd,'w+b') as dst, carbon_stream.open('rb') as src:
            while block := src.read(READ_SIZE):
                dst.write(block)
            dst.seek(plan['change_start'])
            dst.write(plan['replacement_image'])
            dst.flush()
            os.fsync(dst.fileno())
        changed = _verify_output(carbon_stream, Path(tmp), plan['change_start'],
                                 plan['original_image'], plan['replacement_image'])
        if changed != s['changed_image_bytes']:
            raise ValueError('Staged stream differs from expected image replacement')
        for p, state in snapshot.items():
            if (p.stat().st_size, p.stat().st_mtime_ns, _digest_file(p)) != state:
                raise ValueError('Owner-supplied original file changed before publication')
        os.link(tmp, output)  # atomic, no-overwrite final pathname
        report['private_copy_created'] = True
        return report
    finally:
        if tmp is not None:
            try: os.unlink(tmp)
            except FileNotFoundError: pass


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--undercover-ps2-zip',type=Path,required=True)
    ap.add_argument('--carbon-bun',type=Path,required=True)
    ap.add_argument('--carbon-stream',type=Path,required=True)
    ap.add_argument('--undercover-section',type=int,choices=(241,3401),default=3401)
    ap.add_argument('--carbon-section',type=int,choices=(141,142),default=142)
    ap.add_argument('--donor-ordinal',type=int,default=None)
    ap.add_argument('--pc-dxt5-slot',type=int,default=None)
    ap.add_argument('--private-output',type=Path)
    ap.add_argument('--write-private-copy',action='store_true')
    a=ap.parse_args()
    print(json.dumps(stage_undercover_dxt5_copy(
        a.undercover_ps2_zip,a.carbon_bun,a.carbon_stream,
        a.undercover_section,a.carbon_section,
        a.donor_ordinal,a.pc_dxt5_slot,
        a.private_output,a.write_private_copy),indent=2))

if __name__=='__main__':
    main()
