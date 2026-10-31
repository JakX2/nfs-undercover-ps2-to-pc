#!/usr/bin/env python3
"""V50: read-only, format-gated Wii scenery index/aux correlation audit.

The exact known original UC Wii RedBuilding scene authenticates the reported
Wii findings. Other roots are classified as unknown provenance, regardless of
whether their candidate byte layout passes. This is NOT a Carbon PC loader
schema, semantic culling decoder, writer, or in-game validation.

Works with Python 3.10+. No third-party dependencies.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

ROOT = 0x80034100
SCENE = 0x34101
INSTANCE = 0x34103
AUX = 0x3410D
PRECULLER = 0x34107
KNOWN_WII_SHA256 = 'cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'
MAX_ROOT = 64 * 1024 * 1024

class EvidenceError(ValueError):
    pass

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_root(path: Path, *, offset: int | None = None) -> bytes:
    size = path.stat().st_size
    if offset is None:
        if size > MAX_ROOT:
            raise EvidenceError('Standalone scenery root exceeds maximum; specify --offset')
        raw = path.read_bytes()
    else:
        if offset < 0 or size < offset + 8:
            raise EvidenceError('Root offset is outside source file')
        with path.open('rb') as f:
            f.seek(offset)
            header = f.read(8)
            tag, length = struct.unpack('<II', header)
            if tag != ROOT or length > MAX_ROOT-8 or offset + 8 + length > size:
                raise EvidenceError('Root framing at offset invalid or out of range')
            raw = header + f.read(length)
    if len(raw) < 8 or struct.unpack_from('<II', raw, 0) != (ROOT, len(raw)-8):
        raise EvidenceError('Incorrect root ID or declared length')
    return raw

def children_of(blob: bytes) -> dict[int, tuple[int, bytes]]:
    if len(blob) < 8 or len(blob) > MAX_ROOT:
        raise EvidenceError('Root length invalid')
    if struct.unpack_from('<II',blob,0) != (ROOT,len(blob)-8):
        raise EvidenceError('Root header invalid')
    children = {}
    p = 8
    while p < len(blob):
        if p + 8 > len(blob):
            raise EvidenceError('Truncated child header')
        tag, length = struct.unpack_from('<II',blob,p)
        start = p+8
        if tag in children or tag & 0x80000000 or length > len(blob)-start:
            raise EvidenceError('Duplicate, nested or out-of-bounds child')
        children[tag] = (start,blob[start:start+length])
        p = start+length
    if any(i not in children for i in (SCENE,INSTANCE,AUX,PRECULLER)):
        raise EvidenceError('Required child missing; no conclusion about indices')
    return children

def rows_and_indices(blob: bytes, children: dict[int, tuple[int, bytes]]) -> list[int]:
    # The source Wii fixture contains alignment padding between the 34103
    # payload header and the first 96-byte instance. Do not count that as a row.
    start, payload = children[INSTANCE]
    pad = (-start) & 15
    if len(payload) < pad or (len(payload)-pad) % 96:
        raise EvidenceError('Candidate aligned 96-byte instance rows invalid')
    return [struct.unpack_from('<h',payload,pad+i*96+28)[0]
            for i in range((len(payload)-pad)//96)]

def audit(blob: bytes, *, expected_sha256: str | None = None) -> dict:
    digest = sha256(blob)
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise EvidenceError('Root SHA-256 mismatch')
    children = children_of(blob)
    indices = rows_and_indices(blob, children)
    aux = children[AUX][1]
    raw = children[PRECULLER][1]
    if len(aux)%32:
        raise EvidenceError('0x3410D payload not divisible by 32')
    if len(raw)%128:
        raise EvidenceError('0x34107 candidate payload not divisible by 128')
    slots = [aux[i:i+32] for i in range(0,len(aux),32)]
    groups = [raw[i:i+128] for i in range(0,len(raw),128)]
    count = Counter(x for x in indices if x >= 0)
    negative = Counter(x for x in indices if x < 0)
    hi_zero = 0
    triad_consecutive = 0
    for s in slots:
        words = struct.unpack('<8I',s)
        if words[1::2]==(0,0,0,0): hi_zero+=1
        lo = words[::2]
        if lo[1] == (lo[0]+1)&0xffffffff and lo[2] == (lo[1]+1)&0xffffffff:
            triad_consecutive+=1
    invalid = sorted(x for x in count if x>=len(groups))
    referenced = sorted(x for x in count if x<len(groups))
    exact_wii = digest == KNOWN_WII_SHA256
    return {
        'source_root_sha256':digest,
        'source_provenance':'known_exact_Wii_RedBuilding_scene' if exact_wii else 'unknown_root',
        'expected_sha256_guarded':expected_sha256 is not None,
        'instance_candidate_count':len(indices),
        'preculler_candidate':{
            'block_width_bytes':128,'block_count':len(groups),
            'negative_indices_histogram':{str(k):v for k,v in sorted(negative.items())},
            'nonnegative_index_histogram':{str(k):v for k,v in sorted(count.items())},
            'invalid_nonnegative_indices':invalid,
            'all_nonnegative_indices_in_range':not invalid,
            'referenced_block_indices':referenced,
            'unreferenced_block_indices':sorted(set(range(len(groups)))-set(referenced)),
            'zero_block_indices':[i for i,g in enumerate(groups) if not any(g)],
            'indices_referencing_zero_blocks':sum(v for k,v in count.items()
                  if k<len(groups) and not any(groups[k])),
            'candidate_block_0_referenced_by_instance_slots':[i for i,v in enumerate(indices) if v==0],
        },
        'auxiliary_candidate':{
            'row_width_bytes':32,'row_count':len(slots),
            'rows_equal_instance_count':len(slots)==len(indices),
            'high_32bits_zero_in_each_64bit_slot_count':hi_zero,
            'rows_with_four_zero_upper_32bits':hi_zero,
            'rows_with_first_three_low_32bit_words_consecutive_mod2_32':triad_consecutive,
            'distinct_32byte_rows':len(set(slots)),
            'repeated_row_multiplicities':sorted((v for v in Counter(slots).values() if v>1),reverse=True),
        },
        'wii_observed_invariants_verified': (
            exact_wii and len(indices)==31 and len(groups)==24 and len(slots)==31
            and not invalid and len(count)==24 and len(referenced)==24
            and hi_zero==31 and triad_consecutive==31
            and len(set(slots))==29),
        'carbon_pc_serialized_layout_verified':False,
        '34107_semantic_bit_mapping_proven':False,
        '3410d_field_semantics_proven':False,
        'safe_to_install':False,
        'read_only':True,
    }

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scene',type=Path,required=True,help='Read-only original standalone ROOT or BUN')
    ap.add_argument('--offset',type=lambda s:int(s,0),help='Root offset in an original stream')
    ap.add_argument('--expected-root-sha256',help='Optional independently established root digest')
    ap.add_argument('--json',type=Path,required=True,help='New JSON report path (must not exist)')
    args = ap.parse_args()
    if args.json.resolve()==args.scene.resolve():
        ap.error('Report cannot overwrite source')
    if args.json.exists():
        ap.error('Report already exists')
    root = read_root(args.scene,offset=args.offset)
    result=audit(root,expected_sha256=args.expected_root_sha256)
    result['source_stream_offset']=args.offset
    result['source_file_basename']=args.scene.name
    args.json.parent.mkdir(parents=True,exist_ok=True)
    with args.json.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V50 evidence saved:',args.json)
    print('No game files modified. Not installable.')

if __name__=='__main__':main()