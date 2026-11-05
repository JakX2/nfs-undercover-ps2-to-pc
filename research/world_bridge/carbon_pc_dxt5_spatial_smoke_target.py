#!/usr/bin/env python3
"""Read-only Carbon PC eSolid texture -> scenery bounding-box spatial audit.

This supports a *candidate* local smoke-test target. It does not identify a
road position, camera, game world unit, runtime resource load, or render.
Original model/texture hashes and XYZ coordinates stay in caller memory; the
returned report contains only aggregate extents, counts and slot ordinals.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import struct

INSTANCE_SIZE = 96
TREE_SIZE = 48
MAX_INSTANCES = 32768
MAX_NODES = 2048
MAX_PROFILES = 8192
MAX_TARGET_INSTANCES = 1024


def _bounds(lower, upper):
    if (len(lower) != 3 or len(upper) != 3 or
            not all(math.isfinite(x) and abs(x) <= 10000000 for x in lower + upper) or
            any(a > b for a, b in zip(lower, upper))):
        raise ValueError('Invalid finite scenery AABB candidate')
    return (tuple(lower), tuple(upper))


def _inside(parent, child, tolerance=0.001):
    (lo, hi), (a, b) = parent, child
    return all(lo[i] - tolerance <= a[i] <= b[i] <= hi[i] + tolerance
               for i in range(3))


def instance_bounds(blob):
    """Read candidate world AABB min at +0x00, max at +0x10 per 96-byte row."""
    if (not isinstance(blob, bytes) or len(blob) < 4 + INSTANCE_SIZE or
            len(blob) > 4 + MAX_INSTANCES * INSTANCE_SIZE or
            blob[:4] != b'\x11' * 4 or (len(blob) - 4) % INSTANCE_SIZE):
        raise ValueError('Invalid padded Carbon scenery-instance table')
    result = []
    for pos in range(4, len(blob), INSTANCE_SIZE):
        lo = struct.unpack_from('<3f', blob, pos)
        hi = struct.unpack_from('<3f', blob, pos + 0x10)
        result.append(_bounds(lo, hi))
    return tuple(result)


def validate_tree_bounds(blob, bounds):
    """Independently verify each leaf AABB fits its scene-tree parent.

    Negative tree child codes refer to another node; nonnegative codes refer
    to an instance. The 0x34105 hierarchy is a candidate structure validated
    against the exact source tree and all referenced instance bounds.
    """
    if (not isinstance(blob, bytes) or not isinstance(bounds, (tuple, list)) or
            not 1 <= len(bounds) <= MAX_INSTANCES):
        raise ValueError('Invalid spatial hierarchy inputs')
    for bound in bounds:
        if not isinstance(bound, (tuple, list)) or len(bound) != 2:
            raise ValueError('Invalid instance bound entry')
        _bounds(bound[0], bound[1])
    prefix = len(blob) % TREE_SIZE
    if (prefix not in (0, 8) or (prefix and blob[:8] != b'\x11'*8) or
            not 1 <= (len(blob)-prefix)//TREE_SIZE <= MAX_NODES):
        raise ValueError('Invalid scene-tree byte stride/padding/count')
    nodes = []
    for at in range(prefix, len(blob), TREE_SIZE):
        lo = struct.unpack_from('<3f', blob, at)
        hi = struct.unpack_from('<3f', blob, at+16)
        box = _bounds(lo, hi)
        count = struct.unpack_from('<I', blob, at+12)[0]
        codes = struct.unpack_from('<10h', blob, at+28)
        if not 0 < count <= 10 or any(codes[count:]):
            raise ValueError('Invalid node fanout or unused child slots')
        nodes.append((box, codes[:count]))
    child_nodes, leaves = [], []
    for parent, (box, codes) in enumerate(nodes):
        for code in codes:
            if code < 0:
                idx = -code
                if not 1 <= idx < len(nodes) or idx == parent:
                    raise ValueError('Invalid nested tree index')
                if not _inside(box, nodes[idx][0]):
                    raise ValueError('Nested tree node exceeds parent AABB')
                child_nodes.append(idx)
            else:
                if not 0 <= code < len(bounds):
                    raise ValueError('Tree leaf index out of bounds')
                if not _inside(box, bounds[code]):
                    raise ValueError('Scenery instance exceeds parent AABB')
                leaves.append(code)
    if (len(child_nodes) != len(nodes)-1 or
            set(child_nodes) != set(range(1, len(nodes))) or
            len(leaves) != len(bounds) or set(leaves) != set(range(len(bounds)))):
        raise ValueError('Tree does not reference every node and leaf exactly once')
    visited = {0}
    stack = [0]
    while stack:
        parent = stack.pop()
        for code in nodes[parent][1]:
            if code < 0:
                idx = -code
                if idx in visited:
                    raise ValueError('Cycle/repeated scene-tree node')
                visited.add(idx)
                stack.append(idx)
    if len(visited) != len(nodes):
        raise ValueError('Disconnected scene-tree nodes')
    return {'scenery_instances': len(bounds), 'tree_nodes': len(nodes),
            'validated_instance_leaf_AABBs': len(leaves),
            'validated_nested_node_AABBs': len(child_nodes),
            'all_spatial_tree_bounds_contain_children': True}


def _clusters(centers, threshold):
    if (type(threshold) not in (float, int) or isinstance(threshold, bool) or
            not math.isfinite(threshold) or not 0 < threshold <= 1000000):
        raise ValueError('Invalid experimental clustering distance threshold')
    if not 1 <= len(centers) <= MAX_TARGET_INSTANCES:
        raise ValueError('No target instances or excessive target cluster size')
    limit_squared = threshold * threshold
    unseen = set(range(len(centers)))
    components = []
    while unseen:
        seed = min(unseen); unseen.remove(seed)
        stack = [seed]; group = []
        while stack:
            i = stack.pop();group.append(i)
            neighbors = [j for j in sorted(unseen)
                         if sum((centers[i][k]-centers[j][k])**2 for k in range(3)) <= limit_squared]
            unseen.difference_update(neighbors)
            stack.extend(neighbors)
        components.append(tuple(sorted(group)))
    return sorted(components, key=lambda group: (-len(group), group[0]))


def spatial_slot_profile(texture_records, material_profiles, primary_model_hashes,
                         instances, tree, *, section=142, slot=16, cluster_distance=12.0):
    """Join one existing DXT5 ordinal to model materials and instance bounds.

    Inputs are original/private, already validated PC resource records. Output
    is aggregate-only. Clustering is a deliberate proximity *heuristic*.
    """
    if type(section) is not int or section not in (141, 142) or type(slot) is not int or slot < 0:
        raise ValueError('Invalid original Carbon RB section or DXT5 slot')
    if not isinstance(texture_records, dict) or not texture_records:
        raise ValueError('Missing source texture records')
    targets = sorted(h for h, meta in texture_records.items()
                     if isinstance(meta, dict) and meta.get('codec') == 38)
    if slot >= len(targets) or any(type(h) is not int or h <= 0 or h > 0xffffffff for h in texture_records):
        raise ValueError('Source target DXT5 ordinal unavailable')
    image = texture_records[targets[slot]]
    if (type(image.get('width')) is not int or type(image.get('height')) is not int or
            image['width'] <= 0 or image['height'] <= 0):
        raise ValueError('Invalid native DXT5 dimensions')
    boxes = instance_bounds(instances)
    tree_stat = validate_tree_bounds(tree, boxes)
    if (not isinstance(primary_model_hashes, (tuple, list)) or
            len(primary_model_hashes) != len(boxes) or
            any(type(h) is not int or not 0 < h <= 0xffffffff for h in primary_model_hashes)):
        raise ValueError('Scenery model links do not match source instance table')
    if (not isinstance(material_profiles, (tuple, list)) or
            not 0 < len(material_profiles) <= MAX_PROFILES):
        raise ValueError('Invalid source model/material occurrence count')
    models = set(); triangles = 0; occurrences = 0
    for model, info in material_profiles:
        if type(model) is not int or not 0 < model <= 0xffffffff or not isinstance(info, dict):
            raise ValueError('Malformed validated source eSolid profile')
        table, counts = info.get('texture_table'), info.get('per_texture')
        if (not isinstance(table, (tuple, list)) or not 0 < len(table) <= 127 or
                any(type(h) is not int or not 0 < h <= 0xffffffff for h in table) or
                not hasattr(counts, 'items') or not counts):
            raise ValueError('Malformed native model texture/triangle table')
        for idx, count in counts.items():
            if type(idx) is not int or not 0 <= idx < len(table) or type(count) is not int or not 0 < count <= 10000000:
                raise ValueError('Invalid material triangle budget')
            if table[idx] == targets[slot]:
                models.add(model);triangles += count;occurrences += 1
    chosen = [box for model, box in zip(primary_model_hashes, boxes) if model in models]
    if not chosen:
        raise ValueError('No scene instance references this DXT5 target in the primary LOD')
    if len(chosen) > MAX_TARGET_INSTANCES:
        raise ValueError('Too many scene instances for bounded clustering')
    centers = [tuple((lo[k] + hi[k])/2 for k in range(3)) for lo, hi in chosen]
    clusters = _clusters(centers, cluster_distance)
    min_bound = [min(box[0][axis] for box in chosen) for axis in range(3)]
    max_bound = [max(box[1][axis] for box in chosen) for axis in range(3)]
    def extents(boxset):
        return [round(max(box[1][k] for box in boxset) - min(box[0][k] for box in boxset), 3)
                for k in range(3)]
    centroid_distance = None
    if len(clusters) == 2:
        cen = [tuple(sum(centers[i][k] for i in group)/len(group) for k in range(3))
               for group in clusters]
        centroid_distance = round(math.dist(cen[0], cen[1]), 3)
    return {'carbon_section': section, 'pc_dxt5_slot': slot,
            'width': image['width'], 'height': image['height'],
            'source_material_models': len(models),
            'source_material_occurrences': occurrences,
            'source_material_triangles': triangles,
            'source_primary_scenery_instances': len(chosen),
            'candidate_world_AABB_extent_xyz': extents(chosen),
            'experimental_cluster_distance': float(cluster_distance),
            'proximity_cluster_sizes': [len(group) for group in clusters],
            'largest_cluster_AABB_extent_xyz': extents([chosen[i] for i in clusters[0]]),
            'two_cluster_center_separation': centroid_distance,
            **tree_stat,
            'verdict': 'OFFLINE_SPATIAL_SOURCE_JOIN_NOT_DRIVE_LOCATION_OR_RUNTIME_VISIBILITY'}


def analyze_pc_source_section(pc_section, *, section=142, slot=16, cluster_distance=12.0):
    """Use previous source-backed validators to extract a private spatial join."""
    from texture_metadata_pixel_bridge import parse_pack
    from texture_pixel_base_alignment import aligned_pixel_array
    from carbon_pc_dxt5_material_target_rank import source_material_profiles
    from z0_tree_graph_probe import scene_children, inspect_scene, MAX_Z0_FRAME
    from scenery_model_hash_bridge import parse_info_records, validate_instance_links
    if not isinstance(pc_section, bytes) or not 40 <= len(pc_section) <= 32*1024*1024:
        raise ValueError('Unsafe original Carbon PC section')
    records = parse_pack(pc_section,'pc')['records']
    aligned_pixel_array(pc_section,records)
    profiles = source_material_profiles(pc_section)
    signature = struct.pack('<I',0x80034100)
    found = []
    cursor=0
    while True:
        at=pc_section.find(signature,cursor)
        if at < 0:break
        cursor=at+4
        if at % 4:continue
        try:
            blob=pc_section[at:at+MAX_Z0_FRAME+8]
            child, n=scene_children(blob)
            inspect_scene(blob[:n])
        except ValueError:continue
        found.append(child)
        if len(found)>1:raise ValueError('Ambiguous original scenery roots')
        cursor=at+n
    if len(found)!=1:raise ValueError('Missing complete original scenery root')
    child=found[0]
    rows=parse_info_records(child[0x34102])
    indices=validate_instance_links(child[0x34103],child[0x34102])
    primary=[struct.unpack_from('<I',rows[idx],0x18)[0] for idx in indices]
    return spatial_slot_profile(records,profiles,primary,child[0x34103],child[0x34105],
                                section=section,slot=slot,cluster_distance=cluster_distance)


def analyze_original_files(carbon_bun, carbon_stream, *, section=142, slot=16, cluster_distance=12.0):
    """Read original extracted loose Carbon files; never touch their bytes."""
    from private_carbon_dxt1_stream_stage import section_span
    paths=[Path(carbon_bun).absolute(),Path(carbon_stream).absolute()]
    for p in paths:
        if any(q.is_symlink() for q in (p,*p.parents)) or not p.is_file():
            raise ValueError('Original source is missing or symlinked')
    if paths[0]==paths[1] or not 0 < paths[0].stat().st_size <= 8*1024*1024 or not 0 < paths[1].stat().st_size <= 2*1024*1024*1024:
        raise ValueError('Unsafe Carbon original source file sizes')
    bundle=paths[0].read_bytes()
    off,n=section_span(bundle,paths[1].stat().st_size,section)
    with paths[1].open('rb') as stream:
        stream.seek(off);part=stream.read(n)
    if len(part)!=n:raise ValueError('Truncated Carbon section')
    return analyze_pc_source_section(part,section=section,slot=slot,cluster_distance=cluster_distance)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--carbon-bun',type=Path,required=True)
    ap.add_argument('--carbon-stream',type=Path,required=True)
    ap.add_argument('--section',type=int,choices=(141,142),default=142)
    ap.add_argument('--slot',type=int,default=16)
    ap.add_argument('--cluster-distance',type=float,default=12.0)
    a=ap.parse_args()
    print(json.dumps(analyze_original_files(a.carbon_bun,a.carbon_stream,section=a.section,slot=a.slot,cluster_distance=a.cluster_distance),indent=2))


if __name__=='__main__':main()
