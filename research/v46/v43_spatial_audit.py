#!/usr/bin/env python3
"""NFS UC Wii / Carbon PC V43: strict, source-backed, READ-ONLY scenery spatial audit.

VERIFIED ON the supplied original UC Wii RedBuilding 0x80034100 fixture.
VERIFIED ON Carbon PC: none in this package; V42 full PC scene was unavailable.

0x34105 interpretation supported for the fixture: 48-byte node, first and second
AABB corners at +0 and +16, u16 reference count at +12, signed i16 refs +28.
Positive refs = 0-based instance slots; negative -k = child node k.
This is a structural finding, NOT a proven runtime loader algorithm, and
NOT a verified writer for Carbon PC. 0x34107 remains OPAQUE.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import mmap
import os
import struct
from pathlib import Path

ROOT = 0x80034100
INFO = 0x34102
INST = 0x34103
AUX = 0x3410D
TREE = 0x34105
UNKNOWN = 0x34107
HEADER = 0x34101
INSTANCE_WIDTH = 96
NODE_WIDTH = 48
INSTANCE_ALIGN = 16
MAX_SIZE = 512 * 1024 * 1024  # only a single scene extracted, not a whole BUN
SOURCE_SHA = 'cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'


class AuditError(ValueError):
    pass


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def read_root_from_stream(path: Path, offset: int):
    """Return only root bytes from a supplied stream using mmap READ access."""
    with path.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        if offset < 0 or offset + 8 > len(m):
            raise AuditError('Root offset outside original stream')
        tag, length = struct.unpack_from('<II', m, offset)
        if tag != ROOT:
            raise AuditError(f'Expected root 0x{ROOT:08X} at 0x{offset:X}, got 0x{tag:08X}')
        if length > MAX_SIZE or offset + 8 + length > len(m):
            raise AuditError('Root length invalid or out of stream bounds')
        return bytes(m[offset:offset + 8 + length])


def parse_root(blob: bytes):
    if len(blob) < 8:
        raise AuditError('Truncated scenery root')
    tag, size = struct.unpack_from('<II', blob)
    if tag != ROOT or size != len(blob) - 8:
        raise AuditError('Scene root framing invalid or multiple chunks concatenated')
    found = {}
    p = 8
    while p < len(blob):
        if p + 8 > len(blob):
            raise AuditError('Truncated scene child header')
        child_tag, child_size = struct.unpack_from('<II', blob, p)
        start = p + 8
        end = start + child_size
        if end > len(blob):
            raise AuditError('Child extends beyond parent scene root')
        if child_tag in found:
            raise AuditError(f'Duplicate child tag 0x{child_tag:X}')
        found[child_tag] = {'chunk_offset': p, 'payload_offset': start,
                            'payload_size': child_size, 'data': blob[start:end]}
        p = end
    if p != len(blob):
        raise AuditError('Unconsumed scene bytes')
    return found


def _finite_aabb(mins, maxs):
    return all(math.isfinite(x) for x in (*mins, *maxs)) and all(a <= b for a, b in zip(mins, maxs))


def parse_instances(blob, children):
    if INST not in children:
        raise AuditError('No 0x34103 instance table')
    c = children[INST]
    base = c['payload_offset']
    start = (base + INSTANCE_ALIGN - 1) & -INSTANCE_ALIGN
    pad = blob[base:start]
    if start > base + c['payload_size']:
        raise AuditError('Instance alignment exceeds chunk')
    data_len = base + c['payload_size'] - start
    if data_len % INSTANCE_WIDTH:
        raise AuditError('0x34103 data not divisible by 96-byte instance stride')
    rows = []
    for idx, off in enumerate(range(start, base + c['payload_size'], INSTANCE_WIDTH)):
        row = blob[off:off+INSTANCE_WIDTH]
        mins = struct.unpack_from('<3f', row, 0)
        maxs = struct.unpack_from('<3f', row, 16)
        if not _finite_aabb(mins, maxs):
            raise AuditError(f'Invalid instance AABB in row {idx}')
        rows.append({'slot': idx, 'info_index': struct.unpack_from('<h', row, 0x54)[0],
                     'aabb_min': mins, 'aabb_max': maxs,
                     'sha256': checksum(row)})
    return rows, len(pad), checksum(pad)


def analyze_34105(payload: bytes, instances: list):
    """Validate a candidate 48-byte spatial tree; fail closed on anomalies."""
    if not payload or len(payload) % NODE_WIDTH:
        raise AuditError('0x34105 length not a nonzero multiple of 48')
    nodes = []
    n_inst = len(instances)
    for i in range(len(payload) // NODE_WIDTH):
        row = payload[i*NODE_WIDTH:(i+1)*NODE_WIDTH]
        count = struct.unpack_from('<H', row, 12)[0]
        reserved = struct.unpack_from('<H', row, 14)[0]
        if not 1 <= count <= 10:
            raise AuditError(f'Node {i} count {count} not within reference capacity 1..10')
        if reserved:
            raise AuditError(f'Node {i} +14 field nonzero; unknown layout')
        refs = list(struct.unpack_from('<'+'h'*count, row, 28))
        unused = row[28+2*count:]
        if any(unused):
            raise AuditError(f'Node {i} unexpected nonzero trailing bytes')
        mins = struct.unpack_from('<3f', row, 0)
        maxs = struct.unpack_from('<3f', row, 16)
        if not _finite_aabb(mins, maxs):
            raise AuditError(f'Node {i} invalid bounding box')
        for ref in refs:
            if ref >= n_inst:
                raise AuditError(f'Node {i} references nonexistent instance {ref}')
            if ref < 0 and -ref >= len(payload) // NODE_WIDTH:
                raise AuditError(f'Node {i} references nonexistent child node {-ref}')
        nodes.append({'node_id':i,'bounds_min':mins,'bounds_max':maxs,
                      'refs':refs,'reference_count':count,
                      'row_sha256':checksum(row)})

    visited_nodes = set()
    instance_hits = collections.Counter()
    child_hits = collections.Counter()
    def descend(node_id, active):
        if node_id in active:
            raise AuditError('Cycle in negative-reference child graph')
        if node_id in visited_nodes:
            raise AuditError('Node referenced by multiple ancestors')
        visited_nodes.add(node_id)
        n = nodes[node_id]
        members = []
        for ref in n['refs']:
            if ref < 0:
                child = -ref
                child_hits[child] += 1
                members.extend(descend(child, active | {node_id}))
            else:
                instance_hits[ref] += 1
                members.append(ref)
        if not members:
            raise AuditError(f'Node {node_id} has empty subtree')
        mins = tuple(min(instances[k]['aabb_min'][axis] for k in members) for axis in range(3))
        maxs = tuple(max(instances[k]['aabb_max'][axis] for k in members) for axis in range(3))
        if mins != n['bounds_min'] or maxs != n['bounds_max']:
            raise AuditError(f'Node {node_id} bounding box differs from exact instance union')
        n['all_instances_in_subtree'] = members
        n['subtree_instance_count'] = len(members)
        n['bounds_match_exact_instance_union'] = True
        return members
    root_members = descend(0, set())
    if visited_nodes != set(range(len(nodes))):
        raise AuditError('Unreferenced nodes remain in spatial tree')
    if instance_hits != collections.Counter({i:1 for i in range(n_inst)}):
        raise AuditError('Instance coverage not exactly once per source instance')
    if child_hits != collections.Counter({i:1 for i in range(1,len(nodes))}):
        raise AuditError('Child node references not exactly once')
    return {'record_width':NODE_WIDTH,'node_count':len(nodes),
            'root_id':0,'root_instance_count':len(root_members),
            'all_instances_referenced_exactly_once':True,
            'all_nonroot_nodes_referenced_exactly_once':True,
            'all_node_aabbs_equal_instance_unions':True,
            'nodes':nodes}


def analyze_34107(payload: bytes, n_inst: int):
    """Bytes and shape ONLY. Never assert a semantic meaning or writable schema."""
    zero_prefix = 0
    for byte in payload:
        if byte:break
        zero_prefix += 1
    lengths = {}
    for stride in (16,32,48,64,96,128,256):
        if len(payload) % stride == 0:
            rows = [payload[k:k+stride] for k in range(0,len(payload),stride)]
            lengths[str(stride)] = {
                'row_count':len(rows),'distinct_rows':len(set(rows)),
                'all_zero_rows':sum(not any(row) for row in rows),
                'nonzero_rows':sum(bool(any(row)) for row in rows),
            }
    return {'state':'opaque; no runtime meaning established',
            'payload_size':len(payload),'sha256':checksum(payload),
            'nonzero_bytes':sum(bool(byte) for byte in payload),
            'initial_zero_bytes':zero_prefix,
            'observed_strides_without_semantic_claim':lengths,
            'size_equal_to_instances_plus_one_times_96':len(payload)==(n_inst+1)*96,
            'size_equal_to_instances_times_96':len(payload)==n_inst*96,
            'must_preserve_bytes':True}


def analyze_scene(blob: bytes, *, expected_sha: str | None = None, strict_tree=False):
    if expected_sha and checksum(blob)!=expected_sha:
        raise AuditError('Source fingerprint mismatch, refusing to label as verified original fixture')
    parts = parse_root(blob)
    instances, pad_len, pad_digest = parse_instances(blob,parts)
    info_names = None
    if INFO in parts:
        info_bytes=parts[INFO]['data']
        if len(info_bytes)%72==0:
            info_names=[]
            for off in range(0,len(info_bytes),72):
                raw_name=info_bytes[off:off+24].split(b'\0',1)[0]
                info_names.append(raw_name.decode('ascii',errors='replace'))
    report = {
        'schema':'v43-readonly-structural-audit-v1',
        'file_sha256':checksum(blob),'root_total_bytes':len(blob),
        'child_chunks':[{'tag':f'0x{tag:08X}', 'offset':p['chunk_offset'],
                          'payload_bytes':p['payload_size'], 'payload_sha256':checksum(p['data'])}
                         for tag,p in parts.items()],
        'instance_count':len(instances),'scenery_info_names_72_byte_candidate':info_names,
        'instance_alignment_padding_bytes':pad_len,
        'instance_padding_sha256':pad_digest,
        '3410D_size_per_instance_32': AUX in parts and len(parts[AUX]['data'])==len(instances)*32,
        'spatial_34105':None, 'opaque_34107':None,
        'model_placement_patch_ready':False,'carbon_pc_runtime_schema_verified':False,
        'loader_scenery_behavior_verified':False,
        'collision_nav_stream_registration_verified':False,
    }
    if TREE in parts:
        try:
            report['spatial_34105']=analyze_34105(parts[TREE]['data'],instances)
            report['spatial_34105_verification']='exact reconstruction for this file'
        except AuditError as exc:
            if strict_tree:raise
            report['spatial_34105_verification']='not established for this file'
            report['spatial_34105_failure']=str(exc)
    elif strict_tree:
        raise AuditError('Missing 0x34105')
    if UNKNOWN in parts:
        report['opaque_34107']=analyze_34107(parts[UNKNOWN]['data'],len(instances))
    if info_names is not None:
        target_name='XBu_RedBuilding_1b_00'
        matches=[]
        for idx,inst in enumerate(instances):
            if 0<=inst['info_index']<len(info_names) and info_names[inst['info_index']].casefold()==target_name.casefold():
                base=parts[INST]['payload_offset']
                first=(base+INSTANCE_ALIGN-1)&-INSTANCE_ALIGN
                raw=blob[first+idx*INSTANCE_WIDTH:first+(idx+1)*INSTANCE_WIDTH]
                matches.append({'instance_index':idx,'info_index':inst['info_index'],
                                'position_float3_at_0x20':struct.unpack_from('<3f',raw,0x20),
                                'rotation_nine_floats_at_0x2c':struct.unpack_from('<9f',raw,0x2c),
                                'aabb_min':inst['aabb_min'],'aabb_max':inst['aabb_max'],
                                'original_record_sha256':inst['sha256']})
        report['redbuilding_1b_instances_by_name_and_info_index']=matches
    if report['spatial_34105']:
        matches = []
        for n in report['spatial_34105']['nodes']:
            if 26 in n['all_instances_in_subtree']:
                matches.append(n['node_id'])
        report['instance26_containing_nodes'] = matches
        report['instance26_direct_parent_nodes'] = [n['node_id'] for n in report['spatial_34105']['nodes'] if 26 in n['refs']]
    return report


def dot_tree(report):
    tree=report.get('spatial_34105')
    if not tree:
        return 'digraph Scenery { label="No verified tree for this input"; }\n'
    out=['digraph Scenery {','  rankdir=TB;','  node [fontname="Arial"];']
    for n in tree['nodes']:
        out.append(f'  n{n["node_id"]} [shape=box,label="Node {n["node_id"]}\\n{n["subtree_instance_count"]} instances"];')
        for r in n['refs']:
            if r<0:out.append(f'  n{n["node_id"]} -> n{-r};')
            else:
                out.append(f'  inst{r} [shape=ellipse,label="#{r}"];')
                out.append(f'  n{n["node_id"]} -> inst{r};')
    out.append('}')
    return '\n'.join(out)+'\n'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--scene',type=Path,help='One original full root, 0x80034100')
    g.add_argument('--stream',type=Path,help='READ-ONLY full original world BUN')
    ap.add_argument('--offset',type=lambda x:int(x,0),help='Root byte offset in stream, e.g. 0x27BAF0C0')
    ap.add_argument('--expected-sha256',help='Optional exact expected original source digest guard')
    ap.add_argument('--strict-tree',action='store_true',help='Reject any unverified 0x34105 structure')
    ap.add_argument('--json',required=True,type=Path,help='New JSON report path, not original game file')
    ap.add_argument('--dot',type=Path,help='Optional Graphviz source diagram path')
    args=ap.parse_args()
    if args.stream and args.offset is None:ap.error('--stream requires --offset')
    if args.scene and args.offset is not None:ap.error('--offset requires --stream')
    sources=[x for x in [args.scene,args.stream] if x]
    outputs=[x for x in [args.json,args.dot] if x]
    if len({p.resolve() for p in outputs})!=len(outputs):ap.error('Report paths must differ')
    if any(o.resolve()==i.resolve() for o in outputs for i in sources):ap.error('Refusing to overwrite an input')
    data=read_root_from_stream(args.stream,args.offset) if args.stream else args.scene.read_bytes()
    report=analyze_scene(data,expected_sha=args.expected_sha256,strict_tree=args.strict_tree)
    report['provenance']={'input_filename':sources[0].name,'offset':args.offset,
                          'exact_original_source_sha256_checked':bool(args.expected_sha256)}
    for output in outputs:
        if output.exists():ap.error(f'Refusing to overwrite existing report: {output}')
        output.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf8')
    if args.dot:args.dot.write_text(dot_tree(report),encoding='utf8')
    print('READ-ONLY V43 report',args.json)
    print('0x34105:',report['spatial_34105_verification'] if TREE in parse_root(data) else 'missing')
    print('0x34107:',report['opaque_34107']['state'] if report['opaque_34107'] else 'missing')
    print('No patches, writers, or game install artifacts created.')


if __name__=='__main__':main()
