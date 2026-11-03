#!/usr/bin/env python3
"""Read-only bounds-checked Z0 scenery hierarchy probe in 5 platform variants.

The field/edge interpretation is a candidate, not a verified Carbon runtime ABI.
Original game data stays in RAM and does not appear in the JSON report.
"""
import argparse
import json
import math
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip
from scenery_visibility_anchor import (find_unique_chunk, locate_z0_row,
                                       SCENE_ROOT, SCENE_CHILDREN)

INSTANCE_CHUNK = 0x00034103
INFO_CHUNK = 0x00034102
EXTRA_CHUNK = 0x0003410d
TREE_CHUNK = 0x00034105
UNKNOWN_CHUNK = 0x00034107
TREE_STRIDE = 48
INSTANCE_STRIDE = 96
INFO_STRIDE = 72
EXTRA_STRIDE = 32
MAX_Z0_FRAME = 64 * 1024
FILLER_WORD = b'\x11\x11\x11\x11'


def scene_children(root):
    if len(root) < 8 or struct.unpack_from('<I', root)[0] != SCENE_ROOT:
        raise ValueError('Missing scenery root')
    size = struct.unpack_from('<I', root, 4)[0]
    if size < 6 * 8 or size + 8 > len(root) or size > MAX_Z0_FRAME:
        raise ValueError('Truncated or oversized scenery root')
    cursor, end, children, order = 8, 8 + size, {}, []
    while cursor < end:
        if cursor + 8 > end:
            raise ValueError('Truncated scene child')
        tag, length = struct.unpack_from('<II', root, cursor)
        stop = cursor + 8 + length
        if stop > end or tag in children:
            raise ValueError('Overlapping or duplicated scene child')
        children[tag] = root[cursor+8:stop]
        order.append(tag)
        cursor = stop
    if tuple(order) != SCENE_CHILDREN:
        raise ValueError('Unexpected scene child order')
    return children, end


def parse_fixed_chunks(children):
    instance_data = children[INSTANCE_CHUNK]
    if (len(instance_data) < 4 or instance_data[:4] != FILLER_WORD
            or (len(instance_data)-4) % INSTANCE_STRIDE):
        raise ValueError('Unexpected scenery instance stride/prefix')
    instance_count = (len(instance_data)-4) // INSTANCE_STRIDE
    infos = children[INFO_CHUNK]
    extra = children[EXTRA_CHUNK]
    if not infos or len(infos) % INFO_STRIDE:
        raise ValueError('Unexpected scenery information stride')
    if len(extra) != instance_count * EXTRA_STRIDE:
        raise ValueError('Auxiliary instance record count differs')
    return instance_count, len(infos)//INFO_STRIDE


def parse_tree_nodes(data, instance_count):
    if not data:
        raise ValueError('No tree nodes')
    padding_bytes = len(data) % TREE_STRIDE
    if padding_bytes not in (0, 8):
        raise ValueError('Not a series of 48-byte tree nodes')
    if padding_bytes and data[:8] != 2*FILLER_WORD:
        raise ValueError('Unexpected eight-byte tree prefix')
    num_nodes = (len(data)-padding_bytes) // TREE_STRIDE
    if not 1 <= num_nodes <= 1024:
        raise ValueError('Implausible number of tree nodes')
    nodes = []
    node_edges = 0
    instance_edges = 0
    leaf_codes = []
    internal_codes = []
    for index in range(num_nodes):
        pos = padding_bytes + index*TREE_STRIDE
        bb_min = struct.unpack_from('<3f', data, pos)
        count = struct.unpack_from('<I', data, pos+12)[0]
        bb_max = struct.unpack_from('<3f', data, pos+16)
        codes = struct.unpack_from('<10h', data, pos+28)
        if not all(math.isfinite(value) for value in bb_min+bb_max):
            raise ValueError('Nonfinite tree bounds')
        if not all(lo <= hi for lo,hi in zip(bb_min,bb_max)):
            raise ValueError('Inverted tree bounds')
        if count > 10:
            raise ValueError('Too many tree children')
        if any(codes[count:]):
            raise ValueError('Nonzero unused tree child slots')
        for code in codes[:count]:
            if code < 0:
                if not 1 <= -code < num_nodes or -code == index:
                    raise ValueError('Invalid nested tree child index')
                node_edges += 1
                internal_codes.append(-code)
            else:
                if not 0 <= code < instance_count:
                    raise ValueError('Invalid scene instance child index')
                instance_edges += 1
                leaf_codes.append(code)
        nodes.append(tuple(codes[:count]))
    if len(leaf_codes) != instance_count or len(set(leaf_codes)) != instance_count:
        raise ValueError('Tree leaves do not reference each scenery instance exactly once')

    color = [0] * num_nodes
    def visit(index):
        if color[index] == 1:
            raise ValueError('Cycle in scenery hierarchy')
        if color[index] == 2:
            return
        color[index] = 1
        for code in nodes[index]:
            if code < 0:
                visit(-code)
        color[index] = 2
    visit(0)
    if any(value != 2 for value in color):
        raise ValueError('Tree nodes unreachable from root')
    if (len(internal_codes) != num_nodes - 1 or
            set(internal_codes) != set(range(1, num_nodes))):
        raise ValueError('Nested node references do not form a strict tree')
    return {'nodes': num_nodes, 'prefix_filler_bytes': padding_bytes,
            'nested_node_references': node_edges, 'instance_references': instance_edges,
            'all_node_links_bounded': True, 'acyclic_rooted_tree': True}


def inspect_scene(root):
    children, _end = scene_children(root)
    instances, infos = parse_fixed_chunks(children)
    tree = parse_tree_nodes(children[TREE_CHUNK], instances)
    return {'scenery_instances': instances, 'scenery_infos': infos,
            'auxiliary_32byte_instance_records': len(children[EXTRA_CHUNK])//EXTRA_STRIDE,
            **tree,
            'unknown_0x34107_bytes': len(children[UNKNOWN_CHUNK]),
            'unknown_0x34107_all_zero': not any(children[UNKNOWN_CHUNK])}


def z0_scene(source, stem, sector):
    member = f'TRACKS/{stem}{sector}.BUN'
    stream = f'TRACKS/STREAM{stem}{sector}.BUN'
    if isinstance(source, SplitZip):
        bundle = source.read(member)
        total = source.entries[stream][4]
        offset, section_size = locate_z0_row(find_unique_chunk(bundle, 0x34110), total)
        if offset + MAX_Z0_FRAME > total:
            raise ValueError('Z0 root not fully reachable')
        prefix = source.read(stream, limit=offset + MAX_Z0_FRAME, prefix=True)
    else:
        with zipfile.ZipFile(source) as z:
            bundle = z.read(member)
            total = z.getinfo(stream).file_size
            offset, section_size = locate_z0_row(find_unique_chunk(bundle, 0x34110), total)
            if offset + MAX_Z0_FRAME > total:
                raise ValueError('Z0 root not fully reachable')
            with z.open(stream) as handle:
                prefix = handle.read(offset + MAX_Z0_FRAME)
    root = prefix[offset:]
    children, end = scene_children(root)
    if end > section_size:
        raise ValueError('Z0 scene root outside declared section')
    return children, inspect_scene(root)


def analyze(pc_volumes, carbon_ps2_zip, carbon_wii_volumes,
            undercover_ps2_zip, undercover_wii_zip):
    sources = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2_zip), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(undercover_ps2_zip), 'L2'),
        'undercover_wii': (Path(undercover_wii_zip), 'L2'),
    }
    children, summary = {}, {}
    for label, (source, stem) in sources.items():
        for sector in ('RA', 'RB'):
            name = f'{label}_{sector}'
            children[name], summary[name] = z0_scene(source, stem, sector)
    comparisons = {}
    for a,b in [('carbon_ps2','carbon_wii'),('undercover_ps2','undercover_wii'),
                ('carbon_pc','carbon_ps2'),('carbon_pc','carbon_wii')]:
        for sector in ('RA','RB'):
            left=children[a+'_'+sector];right=children[b+'_'+sector]
            comparisons[f'{a}_vs_{b}_{sector}'] = {
                'identical_instance_bytes':left[INSTANCE_CHUNK]==right[INSTANCE_CHUNK],
                'identical_tree_bytes':left[TREE_CHUNK]==right[TREE_CHUNK],
                'identical_unknown_34107_bytes':left[UNKNOWN_CHUNK]==right[UNKNOWN_CHUNK],
            }
    return {'roots':summary, 'comparisons':comparisons,
            'limits':('These validators apply only to the designated Z0 roots. '
                      'The 48/96/72/32 byte layout and reference-edge semantics are '
                      'observed candidate formats. No runtime loader ABI, nonzero '
                      '0x34107 payload, or live collision/visibility proof.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--carbon-wii-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-wii-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.carbon_wii_volumes,
                              a.undercover_ps2_zip,a.undercover_wii_zip),indent=2))

if __name__=='__main__':main()
