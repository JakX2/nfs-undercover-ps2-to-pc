#!/usr/bin/env python3
"""Read-only Carbon PC/PS2 and Undercover PS2 scenery hash-to-solid controls.

Every candidate model hash must resolve through a bounded geometry-pack index
and an actual eSolid resource header. Emits aggregate statistics only; never
exports game bytes or patches an archive. Structural interpretations are not
proof of Carbon PC runtime model/material binding or in-game rendering.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip
from visibility_stream_join import read_small
from rb_scenery_graph_census import read_rb

GEOM = 0x80134000
GEOM_HEADER = 0x80134001
SOLID_ROOT = 0x80134010
SOLID_HEADER = 0x00134011
SOLID_TEX = 0x00134012
SOLID_PLATFORM = 0x80134100
MODEL_INDEX = 0x00134003
PLATFORM_PC = 0x00134900
PLATFORM_PS2 = 0x00134a00
MAX_REGION = 128 * 1024 * 1024
MAX_SECTION = 32 * 1024 * 1024
MAX_SOLIDS = 8192


def read_chunks(source, start, end, count_limit=MAX_SOLIDS+8):
    """Yield complete immediate children; never search inside opaque child data."""
    cursor = start
    count = 0
    while cursor < end:
        if cursor+8 > end:
            raise ValueError('Truncated nested chunk header')
        tag, size = struct.unpack_from('<II', source, cursor)
        stop = cursor+8+size
        if stop > end:
            raise ValueError('Nested chunk exceeds parent')
        if count >= count_limit:
            raise ValueError('Too many nested chunks')
        yield tag, source[cursor+8:stop]
        cursor = stop
        count += 1
    if cursor != end:
        raise ValueError('Partial trailing child bytes')


def parse_solid(data):
    children = list(read_chunks(data, 0, len(data), count_limit=5))
    ids = [k for k, _ in children]
    if ids not in ([SOLID_HEADER, SOLID_TEX, SOLID_PLATFORM],
                   [SOLID_HEADER, SOLID_TEX, 0x13401a, SOLID_PLATFORM]):
        raise ValueError('Unexpected nested eSolid chunk sequence')
    header = children[0][1]
    padding = 0
    while padding+4 <= len(header) and header[padding:padding+4] == b'\x11'*4:
        padding += 4
    if padding not in (0, 4, 8, 12) or padding+20 > len(header):
        raise ValueError('Invalid eSolid header alignment padding')
    version = struct.unpack_from('<I', header, padding+12)[0]
    if version not in (0x16, 0x800016):
        raise ValueError('Unknown eSolid version or offset')
    namehash = struct.unpack_from('<I', header, padding+16)[0]
    if namehash == 0:
        raise ValueError('Zero eSolid model hash')
    plat = children[-1][1]
    if len(plat) < 8:
        raise ValueError('Empty platform chunk')
    platform, size = struct.unpack_from('<II', plat)
    if platform not in (PLATFORM_PC, PLATFORM_PS2) or 8+size > len(plat):
        raise ValueError('Unsupported platform model data')
    return namehash, platform, padding


def parse_geometry_root(blob):
    """Validate one 0x80134000 geometry root and resolve indexed solid hashes."""
    if len(blob) < 24 or struct.unpack_from('<II', blob) != (GEOM, len(blob)-8):
        raise ValueError('Not a complete geometry-pack root')
    if blob[8:16] != b'\x00'*8:
        raise ValueError('Unsupported geometry-pack framing')
    children = list(read_chunks(blob, 16, len(blob)))
    if not children or children[0][0] != GEOM_HEADER or any(c != SOLID_ROOT for c,_ in children[1:]):
        raise ValueError('Unexpected geometry-pack child sequence')
    header_children = list(read_chunks(children[0][1], 0, len(children[0][1]), 4))
    if [x for x,_ in header_children] != [0x134002, MODEL_INDEX, 0x80134008]:
        raise ValueError('Missing model index in geometry header')
    if len(header_children[0][1]) != 144 or header_children[2][1]:
        raise ValueError('Unexpected geometry header size')
    index_payload = header_children[1][1]
    if not index_payload or len(index_payload) % 8:
        raise ValueError('Geometry index must contain 8-byte records')
    index_entries = list(struct.iter_unpack('<II', index_payload))
    hashes = [h for h, pointer in index_entries]
    if any(pointer for _,pointer in index_entries):
        raise ValueError('Index contains nonzero serialized pointers')
    if len(hashes) > MAX_SOLIDS or 0 in hashes or hashes != sorted(set(hashes)):
        raise ValueError('Unsorted, repeated, or invalid index hashes')
    solids = [parse_solid(payload) for _,payload in children[1:]]
    solid_hashes = [h for h,_,_ in solids]
    if len(hashes) != len(solids) or set(hashes) != set(solid_hashes):
        raise ValueError('Index does not exactly enumerate the embedded solid headers')
    if len(set(solid_hashes)) != len(solid_hashes):
        raise ValueError('Duplicate embedded solid hash')
    platforms = {platform for _, platform, _ in solids}
    if len(platforms) != 1:
        raise ValueError('Mixed platform types within geometry pack')
    return {'hashes': frozenset(hashes), 'solid_count':len(solids),
            'platform': next(iter(platforms)),
            'alignment_counts':{str(n):sum(pad==n for _,_,pad in solids) for n in (0,4,8,12)}}


def locate_geometry(section_data):
    """Scan for complete anchored geometry roots; multiple packs are legitimate."""
    if len(section_data) > MAX_SECTION:
        raise ValueError('Streaming section exceeds 32 MiB inspection bound')
    signature = struct.pack('<I', GEOM)
    cursor, matches = 0, []
    while True:
        at = section_data.find(signature, cursor)
        if at < 0:
            break
        cursor = at + 4
        if at % 4 or at+8 > len(section_data):
            continue
        length = struct.unpack_from('<I', section_data, at+4)[0]
        if length > len(section_data)-at-8:
            continue
        try:
            info = parse_geometry_root(section_data[at:at+8+length])
        except ValueError:
            continue
        if any(at < prev_end and prev_start < at+8+length for prev_start,prev_end,_ in matches):
            raise ValueError('Overlapping validated geometry packs')
        matches.append((at, at+8+length, info))
        if len(matches) > 16:
            raise ValueError('Too many geometry packs in one section')
        cursor = at+8+length
    if not matches:
        raise ValueError('No validated geometry pack in section')
    return tuple(info for _,_,info in matches)


def info_hashes(info_blob, pc=False):
    if not info_blob or len(info_blob)%72:
        raise ValueError('Unexpected 72-byte scenery info stride')
    off = 24 if pc else 28
    hashes = [struct.unpack_from('<I', info_blob, i+off)[0]
              for i in range(0, len(info_blob), 72)]
    if not all(hashes):
        raise ValueError('Zero scenery model hash')
    return frozenset(hashes), len(hashes)


def validate_scene_geometry(scene, packs, pc=False):
    """Resolve source info hashes against the union of all local geometry packs."""
    info_set, info_count = info_hashes(scene['children'][0x34102], pc)
    index_set = frozenset().union(*(g['hashes'] for g in packs))
    for geom in packs:
        if (pc and geom['platform'] != PLATFORM_PC) or (not pc and geom['platform'] != PLATFORM_PS2):
            raise ValueError('Geometry payload platform differs from expected platform')
    return {'scenery_info_records': info_count,
            'unique_info_hashes': len(info_set),
            'geometry_packs':len(packs),
            'indexed_solid_resource_occurrences':sum(g['solid_count'] for g in packs),
            'distinct_indexed_solid_hashes':len(index_set),
            'indexed_hashes_repeated_across_packs':sum(g['solid_count'] for g in packs)-len(index_set),
            'info_hashes_backed_by_local_solids':len(info_set & index_set),
            'info_hashes_unresolved_in_this_section':len(info_set-index_set),
            'indexed_solid_hashes_not_in_local_info':len(index_set-info_set),
            'index_and_embedded_solid_hashes_exact_per_pack':True,
            'platform_chunks':sorted({f'0x{g["platform"]:08x}' for g in packs}),
            'alignment_prefix_distribution':{
                str(n):sum(g['alignment_counts'][str(n)] for g in packs)
                for n in (0,4,8,12)},
           }


def analyze(pc_volumes, carbon_ps2_zip, undercover_ps2_zip):
    sources = {
        'carbon_pc':(SplitZip(pc_volumes),'L5',True,(141,142)),
        'carbon_ps2':(Path(carbon_ps2_zip),'L5',False,(141,142)),
        'undercover_ps2':(Path(undercover_ps2_zip),'L2',False,(241,3401)),
    }
    reports, sets, all_infos = {}, {}, {}
    for label,(archive,stem,is_pc,sections) in sources.items():
        scenes,_ = read_rb(archive,stem)
        rows,_,_ = read_small(archive,stem,'RB')
        member=f'TRACKS/STREAM{stem}RB.BUN'
        if isinstance(archive,SplitZip):
            raw=archive.read(member,limit=MAX_REGION)
        else:
            with zipfile.ZipFile(archive) as z:
                if z.getinfo(member).file_size > MAX_REGION:
                    raise ValueError('Secondary-area stream exceeds 128 MiB bound')
                raw=z.read(member)
        for sec in sections:
            if sec not in scenes or sec not in rows:
                raise ValueError('Missing authenticated scenery/stream section')
            off,size=struct.unpack_from('<II',rows[sec],0x14)
            packs=locate_geometry(raw[off:off+size])
            reports[f'{label}_{sec}']=validate_scene_geometry(scenes[sec],packs,is_pc)
            sets[(label,sec)] = frozenset().union(*(g['hashes'] for g in packs))
            all_infos[(label,sec)] = info_hashes(scenes[sec]['children'][0x34102],is_pc)[0]
    same = {str(sec):sets['carbon_pc',sec] == sets['carbon_ps2',sec] for sec in (141,142)}
    if not all(same.values()):
        raise ValueError('Carbon PC and PS2 controls have divergent indexed solid identities')
    donor_ids = (241,3401)
    donor_info = frozenset().union(*(all_infos['undercover_ps2',sec] for sec in donor_ids))
    donor_solids = frozenset().union(*(sets['undercover_ps2',sec] for sec in donor_ids))
    return {'scenes':reports,
            'carbon_pc_ps2_index_hash_sets_identical':same,
            'undercover_combined_rb': {
                'distinct_info_hashes':len(donor_info),
                'distinct_indexed_solid_hashes':len(donor_solids),
                'info_hashes_resolved_by_either_pack_group':len(donor_info & donor_solids),
                'info_hashes_unresolved_by_both_pack_groups':len(donor_info - donor_solids),
            },
            'limits':('Geometry-index and eSolid-header hashes are validated in the selected '
                      'original RB scene packs only. Other stream packs or global resources '
                      'may resolve additional donor hashes. No vertex/index decoding, '
                      'texture binding, PC loading, collision, or gameplay conversion.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.undercover_ps2_zip),indent=2))


if __name__=='__main__':
    main()
