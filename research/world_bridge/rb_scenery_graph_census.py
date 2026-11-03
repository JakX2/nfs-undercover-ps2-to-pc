#!/usr/bin/env python3
"""Bounded read-only five-platform RB scenery-root and nested graph census.

For each member of the owner-supplied original TRACKS archives, read the full
secondary-area stream (max 128 MiB), locate structurally sound scenery roots,
validate graph references, and bind them to 92-byte streaming table entries.
Only aggregate counts are printed; no game bytes or lists are exported.
"""
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip
from scenery_visibility_anchor import find_unique_chunk
from section_identity_anchor import parse_rows
from z0_tree_graph_probe import scene_children, inspect_scene, MAX_Z0_FRAME

STREAM_LIMIT = 128 * 1024 * 1024
SIGNATURE = struct.pack('<I', 0x80034100)
CHUNK_IDS = (0x34101,0x34103,0x34102,0x3410d,0x34105,0x34107)


def scan_stream(data, table_rows):
    """Reject structurally-valid roots that are not contained by one table row."""
    if len(data) > STREAM_LIMIT:
        raise ValueError('Secondary area stream exceeds inspection bound')
    starts=[]
    for sec, row in table_rows.items():
        offset, length = struct.unpack_from('<II', row, 0x14)
        starts.append((offset, length, sec))
    starts.sort()
    offsets=[item[0] for item in starts]
    results={}
    rejected_markers=0
    position=0
    while True:
        position=data.find(SIGNATURE, position)
        if position < 0:
            break
        try:
            children, extent = scene_children(data[position:position + MAX_Z0_FRAME + 8])
        except ValueError:
            rejected_markers += 1
            position += 4
            continue
        # A structurally credible root must also pass the full graph check.
        # Do not hide invalid parsed structures as random marker collisions.
        graph = inspect_scene(data[position:position+extent])
        idx=bisect_right(offsets,position)-1
        if idx<0:
            raise ValueError('Validated scenery root is outside any stream section')
        offset,length,sec=starts[idx]
        if position+extent > offset+length:
            raise ValueError('Validated scenery root crosses its stream section')
        if sec in results:
            raise ValueError('Multiple scenery roots inside one stream section')
        results[sec]={'at_section_start':position==offset,
                      'children':children, 'graph':graph}
        position += extent
    return results, rejected_markers


def summarize(scene_map, stream_rows, rejected):
    graphs=[s['graph'] for s in scene_map.values()]
    def total(field):return sum(g[field] for g in graphs)
    return {'stream_sections':len(stream_rows),
            'valid_scenery_roots':len(graphs),
            'distinct_root_section_ids':len(scene_map),
            'roots_at_section_starts':sum(s['at_section_start'] for s in scene_map.values()),
            'roots_embedded_in_sections':sum(not s['at_section_start'] for s in scene_map.values()),
            'rejected_unframed_header_candidates':rejected,
            'tree_nodes':total('nodes'),'scenery_instances':total('scenery_instances'),
            'scenery_infos':total('scenery_infos'),
            'nested_node_references':total('nested_node_references'),
            'scene_instance_references':total('instance_references'),
            'prefixed_0x34105_chunks':sum(g['prefix_filler_bytes'] == 8 for g in graphs),
            'all_unknown_0x34107_zero':all(g['unknown_0x34107_all_zero'] for g in graphs)}


def compare(left,right):
    shared=left.keys() & right.keys()
    result={'shared_root_section_ids':len(shared),
            'only_left':len(left)-len(shared), 'only_right':len(right)-len(shared)}
    for cid,caption in [('0x34103','instance_bytes'),('0x34105','tree_bytes'),('0x34107','unknown_34107_bytes')]:
        tag=int(cid,16)
        result['matching_'+caption]=sum(left[s]['children'][tag]==right[s]['children'][tag] for s in shared)
    result['same_graph_counts']=sum(
        all(left[s]['graph'][field] == right[s]['graph'][field] for field in (
            'nodes','scenery_instances','scenery_infos','nested_node_references','instance_references'))
        for s in shared)
    return result


def read_rb(source,stem):
    bun=f'TRACKS/{stem}RB.BUN';stream=f'TRACKS/STREAM{stem}RB.BUN'
    if isinstance(source,SplitZip):
        packed=source.read(bun)
        length=source.entries[stream][4]
        if length>STREAM_LIMIT:raise ValueError('RB member exceeds 128 MiB')
        raw=source.read(stream,limit=STREAM_LIMIT)
    else:
        with zipfile.ZipFile(source) as z:
            packed=z.read(bun)
            length=z.getinfo(stream).file_size
            if length>STREAM_LIMIT:raise ValueError('RB member exceeds 128 MiB')
            raw=z.read(stream)
    if len(raw)!=length:raise ValueError('Incomplete RB uncompressed member')
    rows=parse_rows(find_unique_chunk(packed,0x34110)[8:],len(raw))
    scenes,errors=scan_stream(raw,rows)
    return scenes,summarize(scenes,rows,errors)


def analyze(pc_volumes,carbon_ps2_zip,carbon_wii_volumes,uc_ps2_zip,uc_wii_zip):
    sources={
        'carbon_pc':(SplitZip(pc_volumes),'L5'),
        'carbon_ps2':(Path(carbon_ps2_zip),'L5'),
        'carbon_wii':(SplitZip(carbon_wii_volumes),'L5'),
        'undercover_ps2':(Path(uc_ps2_zip),'L2'),
        'undercover_wii':(Path(uc_wii_zip),'L2'),
    }
    scenes={};summaries={}
    for name,(archive,stem) in sources.items():
        scenes[name],summaries[name]=read_rb(archive,stem)
    pairs=(('carbon_pc','carbon_ps2'),('carbon_pc','carbon_wii'),
           ('carbon_ps2','carbon_wii'),('undercover_ps2','undercover_wii'),
           ('carbon_ps2','undercover_ps2'))
    return {'sources':summaries,
            'comparisons':{f'{a}_vs_{b}':compare(scenes[a],scenes[b]) for a,b in pairs},
            'limits':('The census is restricted to the five secondary-area RB streams. '
                      'The common scenery graph layout is a supported candidate, not a '
                      'proven runtime ABI, and the unknown 0x34107 chunk is all zero '
                      'in the validated scenes. No main-area RA streaming conversion, '
                      'collision, rendering, or PC in-game behavior verified.')}


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
