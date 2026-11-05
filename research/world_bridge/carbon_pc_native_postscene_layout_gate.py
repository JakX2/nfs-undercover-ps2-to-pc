#!/usr/bin/env python3
"""Read-only source-backed Carbon PC RB section/post-scene control-frame census.

Owner originals stay local. This module does not emit game bytes, filenames,
model/texture hashes, or coordinates; it never writes a game file. The observed
0x372xx sequence is an empirical Carbon PC source profile, NOT a proven runtime
registration format. Numeric placement is not an installable world-sector patch.
"""
import argparse
import json
import struct
from pathlib import Path
import zipfile

TEXTURE = 0xB3300000
GEOMETRY = 0x80134000
SCENE = 0x80034100
TABLE = 0x34110
TAIL_HEAD = 0x37220
TAIL_PRE = 0x37260
TAIL_DATA = 0x37250
TAIL_END = 0x37270
SCENE_CHILDREN = (0x34101, 0x34103, 0x34102, 0x3410d, 0x34105, 0x34107)
ROW_BYTES = 92
MAX_SMALL = 8 * 1024 * 1024
MAX_STREAM = 512 * 1024 * 1024
MAX_ROOT = 32 * 1024 * 1024
MAX_SCENE = 64 * 1024
# Source-private candidate size measurements from the earlier 268-eSolid audit.
# These constants are *prior measurements*, not an assertion that this module
# re-encoded 268 original solids. Revalidate if the builder or mip policy changes.
MEASURED_PC_PACK_TOTAL_BYTES = {241: 2272112, 3401: 2266292}
MEASURED_DXT5_CANDIDATE_BYTES = 1176688


def _u32(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError('Truncated 32-bit frame field')
    return struct.unpack_from('<I', data, offset)[0]


def _frame(data, pos, expected=None, limit=MAX_ROOT):
    if type(pos) is not int or pos < 0 or pos + 8 > len(data):
        raise ValueError('Truncated or invalid resource root')
    tag, n = struct.unpack_from('<II', data, pos)
    if expected is not None and tag != expected:
        raise ValueError('Unexpected resource root kind')
    if n > limit or pos + 8 + n > len(data):
        raise ValueError('Resource root length out of bounds')
    return tag, pos + 8 + n


def _children(data, start, end):
    rows = []
    pos = start
    while pos < end:
        if pos + 8 > end:
            raise ValueError('Truncated nested chunk')
        tag = _u32(data, pos)
        n = _u32(data, pos + 4)
        stop = pos + 8 + n
        if stop > end:
            raise ValueError('Nested child overruns parent')
        rows.append((tag, pos + 8, stop))
        if len(rows) > 8192:
            raise ValueError('Too many nested children')
        pos = stop
    return rows


def scene_profile(root, platform):
    """Validate candidate primary-detail info/instance associations, read-only.

    The first-versus-second LOD hash rule is source-empirical and does not
    establish native retail loader semantics or visibility.
    """
    if platform not in ('pc', 'ps2') or not isinstance(root, bytes):
        raise ValueError('Invalid private scenery root/platform')
    _, end = _frame(root, 0, SCENE, MAX_SCENE)
    if end != len(root):
        raise ValueError('Scenery root has trailing bytes')
    rows = _children(root, 8, end)
    if tuple(k for k, _, _ in rows) != SCENE_CHILDREN:
        raise ValueError('Scenery child order disagrees with source controls')
    by_tag = {k: (a, b) for k, a, b in rows}
    ia, ib = by_tag[0x34102]
    if ib - ia < 72 or (ib - ia) % 72:
        raise ValueError('Invalid 72-byte scene info table')
    n = (ib - ia) // 72
    first_zero = first_equal = 0
    for i in range(n):
        first, second = struct.unpack_from('<II', root, ia + i*72 + 0x18)
        if not second or (platform == 'pc' and first != second) or (platform == 'ps2' and first):
            raise ValueError('Unexpected source scenery primary-detail slot profile')
        first_zero += first == 0
        first_equal += first == second
    a, b = by_tag[0x34103]
    if b - a < 4 or root[a:a+4] != b'\x11' * 4 or (b - a - 4) % 96:
        raise ValueError('Invalid source scenery instance table')
    inst = (b - a - 4)//96
    if inst < 1:
        raise ValueError('Empty scenery instance table')
    for i in range(inst):
        ref = struct.unpack_from('<h', root, a + 4 + i*96 + 0x54)[0]
        if not 0 <= ref < n:
            raise ValueError('Scenery instance references nonexistent source info')
    xa, xb = by_tag[0x3410d]
    if xb - xa != 32*inst:
        raise ValueError('Auxiliary scene-instance record count mismatch')
    return {'scenery_info_records': n, 'scenery_instance_records': inst,
            'zero_first_detail_hash_records': first_zero,
            'first_equal_second_detail_hash_records': first_equal,
            'source_candidate_lod_slots_valid': True}


def stream_rows(bundle, length):
    """Bounds-check original 92-byte section rows, including disjointness."""
    if not isinstance(bundle, bytes) or not 8 <= len(bundle) <= MAX_SMALL or type(length) is not int or not 0 < length <= MAX_STREAM:
        raise ValueError('Invalid original bundle/stream dimensions')
    signature = struct.pack('<I', TABLE)
    hits = []
    cursor = 0
    while True:
        p = bundle.find(signature, cursor)
        if p < 0: break
        hits.append(p)
        cursor = p + 4
    if len(hits) != 1:
        raise ValueError('Missing or ambiguous section table')
    p = hits[0]
    size = _u32(bundle, p + 4)
    if not size or size % ROW_BYTES or p + 8 + size > len(bundle):
        raise ValueError('Invalid streaming table length')
    rows = {}
    ranges = []
    for at in range(p + 8, p + 8 + size, ROW_BYTES):
        sec = struct.unpack_from('<h', bundle, at+8)[0]
        offset, n = struct.unpack_from('<II', bundle, at+0x14)
        if sec in rows or offset + n > length or (n and offset % 2048):
            raise ValueError('Duplicate, unaligned or out-of-range streaming section')
        rows[sec] = (offset, n)
        if n: ranges.append((offset, offset+n))
    ranges.sort()
    if any(b > c for (_, b), (c, _) in zip(ranges, ranges[1:])):
        raise ValueError('Original section table has overlapping ranges')
    return rows


def _scan_roots(section, geom_count):
    if not isinstance(section, bytes) or not 16 <= len(section) <= MAX_ROOT:
        raise ValueError('Unsafe private source section bytes')
    at = 0
    _, at = _frame(section, at, TEXTURE)
    texture = at
    geometry_lengths = []
    for _ in range(geom_count):
        if at % 16:
            raise ValueError('Source geometry root is not 16-byte aligned')
        _, end = _frame(section, at, GEOMETRY)
        geometry_lengths.append(end-at)
        at = end
    middle = 0
    if at + 8 <= len(section) and _u32(section, at) == 0:
        # A zero-tag/zero-payload chunk is observed in Carbon PC section 142.
        _, end = _frame(section, at, 0, 128)
        if any(section[at+8:end]):
            raise ValueError('Source inter-root zero chunk has nonzero payload')
        middle = end-at
        at = end
    if at % 16:
        raise ValueError('Source scenery root is not 16-byte aligned')
    _, end = _frame(section, at, SCENE, MAX_SCENE)
    scene = section[at:end]
    return {'texture_root_bytes': texture, 'geometry_root_bytes': tuple(geometry_lengths),
            'interroot_zero_chunk_bytes': middle, 'scene_root_bytes': len(scene),
            'scene_end': end, 'scene': scene,
            'postscene': section[end:]}


def native_pc_postscene_profile(tail):
    """Exact empirical Carbon PC 0x372xx framing, with all opaque payloads intact."""
    if not isinstance(tail, bytes) or not 68 <= len(tail) <= 4096 or tail[:8] != bytes(8):
        raise ValueError('Carbon PC post-scene framing prefix missing')
    pos = 8
    _, end = _frame(tail, pos, TAIL_HEAD, 24)
    if end-pos != 32:
        raise ValueError('Unexpected native post-scene header size')
    words = struct.unpack_from('<6I', tail, pos+8)
    groups = words[2]
    if words[0:2] != (0x11111111,)*2 or not 1 <= groups <= 64 or words[3] != groups or words[5] != groups:
        raise ValueError('Native post-scene group-count cross-check failed')
    pos = end
    for i in range(groups):
        _, end = _frame(tail, pos, TAIL_PRE, 12 if i == 0 else 8)
        if end-pos != (20 if i == 0 else 16):
            raise ValueError('Unexpected native prelude frame size')
        pos = end
        _, end = _frame(tail, pos, TAIL_DATA, 120)
        if end-pos != 128:
            raise ValueError('Unexpected native control-data frame size')
        pos = end
        _, end = _frame(tail, pos, TAIL_END, 8)
        if end-pos != 16:
            raise ValueError('Unexpected native end-frame size')
        pos = end
    if pos != len(tail):
        raise ValueError('Unrecognized bytes after Carbon native control records')
    return {'native_postscene_control_groups':groups,
            'native_postscene_bytes':len(tail),
            'native_postscene_header_count_consistent':True,
            'native_postscene_frames_bounded':True}


def profile_carbon_section(data):
    a = _scan_roots(data, 1)
    result = native_pc_postscene_profile(a['postscene'])
    return {'section_bytes':len(data),
            'native_texture_root_bytes':a['texture_root_bytes'],
            'native_geometry_root_bytes':sum(a['geometry_root_bytes']),
            'native_scene_root_bytes':a['scene_root_bytes'],
            'native_interroot_zero_chunk_bytes':a['interroot_zero_chunk_bytes'],
            **scene_profile(a['scene'],'pc'), **result}


def profile_undercover_section(data):
    a = _scan_roots(data, 4)
    if len(a['postscene']) < 16 or a['postscene'][:8] != bytes(8):
        raise ValueError('Unframed original Undercover post-scene data')
    # An original PS2 tail is *not* a PC native 0x372xx resource sequence.
    if _u32(a['postscene'],8) == TAIL_HEAD:
        raise ValueError('Source unexpectedly uses PC post-scene control header')
    return {'section_bytes':len(data), 'source_texture_root_bytes':a['texture_root_bytes'],
            'source_geometry_pack_count':len(a['geometry_root_bytes']),
            'source_geometry_root_bytes':sum(a['geometry_root_bytes']),
            'source_scene_root_bytes':a['scene_root_bytes'],
            'source_postscene_bytes':len(a['postscene']),
            'source_postscene_is_native_pc_372xx':False,
            **scene_profile(a['scene'],'ps2')}


def conservative_candidate_budget(carbon, donor_geometry_bytes, donor_texture_bytes, donor_scene_bytes):
    """Size feasibility only. Five separate 16-byte alignment pads are budgeted.

    This is deliberately *not* a resource-writer or relocation rule; it cannot
    prove that the Carbon postlude's opaque references survive regeneration.
    """
    if not isinstance(carbon,dict) or any(type(x) is not int or x <= 0 for x in
        (donor_geometry_bytes, donor_texture_bytes, donor_scene_bytes)):
        raise ValueError('Invalid private candidate size evidence')
    needed = (donor_texture_bytes + donor_geometry_bytes + donor_scene_bytes +
              carbon['native_postscene_bytes'] + 5*15)
    limit = carbon['section_bytes']
    return {'existing_pc_section_bytes':limit,
            'candidate_size_worst_case_bytes':needed,
            'max_16byte_padding_bytes':75,
            'nominal_section_headroom_bytes':limit-needed,
            'would_fit_section_byte_budget':needed <= limit,
            'candidate_geometry_pack_count':4,
            'native_pc_postscene_transplant_validated':False,
            'source_scene_loader_abi_validated':False,
            'same_section_id_install_safe':False}


def inspect_private_sources(carbon_bun, carbon_stream, undercover_zip):
    """Owner-only read-only files; output is aggregate structure counts."""
    paths = [Path(x) for x in (carbon_bun, carbon_stream, undercover_zip)]
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise ValueError('Source paths must be regular files, not symlinks')
    if not (0 < paths[0].stat().st_size <= MAX_SMALL and
            0 < paths[1].stat().st_size <= MAX_STREAM and
            0 < paths[2].stat().st_size <= MAX_STREAM):
        raise ValueError('Source file violates bounded size limit')
    if len({p.resolve() for p in paths}) != 3:
        raise ValueError('Original files must not alias')
    with paths[0].open('rb') as fp:
        pc_bun = fp.read()
    pc_rows = stream_rows(pc_bun, paths[1].stat().st_size)
    result_pc = {}
    with paths[1].open('rb') as fp:
        for sec in (141,142):
            if sec not in pc_rows:
                raise ValueError('Carbon RB target section missing')
            off, length = pc_rows[sec]
            if not 0 < length <= MAX_ROOT:
                raise ValueError('Carbon RB section oversized')
            fp.seek(off)
            raw = fp.read(length)
            if len(raw) != length:
                raise ValueError('Short original Carbon section')
            result_pc[sec] = profile_carbon_section(raw)
    with zipfile.ZipFile(paths[2]) as z:
        for name in ('TRACKS/L2RB.BUN','TRACKS/STREAML2RB.BUN'):
            if z.getinfo(name).file_size > MAX_STREAM:
                raise ValueError('Oversized owner archive member')
        uc_bun = z.read('TRACKS/L2RB.BUN')
        uc_stream = z.read('TRACKS/STREAML2RB.BUN') # ZIP CRC validated
    uc_rows = stream_rows(uc_bun, len(uc_stream))
    result_uc={}
    for sec in (241,3401):
        if sec not in uc_rows:
            raise ValueError('Undercover RB source section missing')
        off, length = uc_rows[sec]
        if not 0 < length <= MAX_ROOT:
            raise ValueError('Oversized Undercover source section')
        result_uc[sec] = profile_undercover_section(uc_stream[off:off+length])
    plans={}
    for pc_sec,uc_sec in ((141,241),(142,3401)):
        plans[str(pc_sec)] = conservative_candidate_budget(
            result_pc[pc_sec],MEASURED_PC_PACK_TOTAL_BYTES[uc_sec],
            MEASURED_DXT5_CANDIDATE_BYTES, result_uc[uc_sec]['source_scene_root_bytes'])
    return {'scope':'OFFLINE_NATIVE_POSTSCENE_AND_SIZE_ONLY_NOT_PC_RUNTIME',
            'original_carbon_pc':{str(k):v for k,v in result_pc.items()},
            'original_undercover_ps2':{str(k):v for k,v in result_uc.items()},
            'measured_prior_pc_candidate_root_bytes_by_donor_section':{
                str(k):v for k,v in MEASURED_PC_PACK_TOTAL_BYTES.items()},
            'measured_prior_low_resolution_dxt5_root_bytes':MEASURED_DXT5_CANDIDATE_BYTES,
            'conservative_four_pack_candidate_budget':plans,
            'postscene_control_semantics_and_relocation':'UNVERIFIED',
            'runtime_registration_or_rendering':'UNVERIFIED',
            'no_original_game_files_written':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--carbon-bun',type=Path,required=True)
    p.add_argument('--carbon-stream',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(inspect_private_sources(a.carbon_bun,a.carbon_stream,
                                              a.undercover_ps2_zip),indent=2))


if __name__=='__main__':
    main()
