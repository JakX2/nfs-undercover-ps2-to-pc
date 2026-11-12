#!/usr/bin/env python3
"""Validate candidate 92-byte 0x34110 track-stream table records.

Read-only: accepts three owner-supplied TRACKS ZIPs (the PC archive is split
PKZIP), prints only aggregate counts, never exports original row data.
Field offsets are corroborated by a Most Wanted reconstruction but do NOT
establish Carbon's loader ABI or runtime semantics.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip

MAX_BUNDLE = 8 * 1024 * 1024
ROW_SIZE = 0x5c
STREAM_CHUNK = 0x00034110


def find_chunk(data, cid=STREAM_CHUNK):
    pos, found = 0, []
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("Truncated BUN chunk header")
        identifier, size = struct.unpack_from('<II',data,pos)
        end=pos+8+size
        if end>len(data):
            raise ValueError("BUN chunk exceeds file")
        if identifier == cid:
            found.append(data[pos+8:end])
        pos=end
    if len(found) != 1:
        raise ValueError("Expected exactly one streaming table chunk")
    return found[0]


def parse_sections(payload, stream_bytes):
    if not payload or len(payload)%ROW_SIZE:
        raise ValueError("Streaming table is not a nonempty series of 92-byte rows")
    if not isinstance(stream_bytes,int) or stream_bytes<=0:
        raise ValueError("Invalid stream size")
    records={}
    summary={'rows':len(payload)//ROW_SIZE,'filetype_one':0,'status_zero':0,
             'sizes_equal_compressed':0,'all_offsets_2048_aligned':0,
             'offset_ranges_in_stream':0,'nonoverlapping_ordered_ranges':0}
    prior_end = 0
    for i in range(summary['rows']):
        row=payload[i*ROW_SIZE:(i+1)*ROW_SIZE]
        name_bytes=row[:8].split(b'\x00',1)[0]
        if not name_bytes or not all(32<=b<=126 for b in name_bytes):
            raise ValueError("Unprintable or empty section name")
        name=name_bytes.decode('ascii')
        section=struct.unpack_from('<h',row,8)[0]
        status=struct.unpack_from('<I',row,0x0c)[0]
        filetype=struct.unpack_from('<I',row,0x10)[0]
        offset, size, compressed=struct.unpack_from('<III',row,0x14)
        if section in records:
            raise ValueError("Duplicate section number")
        if size<=0 or compressed<=0 or offset+compressed>stream_bytes or offset+size>stream_bytes:
            raise ValueError("Section range outside stream or empty")
        if offset<prior_end:
            raise ValueError("Overlapping or unordered section ranges")
        records[section]=name
        summary['filetype_one'] += filetype==1
        summary['status_zero'] += status==0
        summary['sizes_equal_compressed'] += size==compressed
        summary['all_offsets_2048_aligned'] += offset%2048==0
        summary['offset_ranges_in_stream']+=1
        summary['nonoverlapping_ordered_ranges']+=1
        prior_end=offset+max(size,compressed)
    summary['max_section_end']=prior_end
    return records,summary


def compare_section_ids(left,right):
    common=left.keys() & right.keys()
    same_names=sum(left[num]==right[num] for num in common)
    return {'shared_section_numbers':len(common),
            'matching_names_at_shared_numbers':same_names,
            'conflicting_names_at_shared_numbers':len(common)-same_names}


def analyze(pc_volumes,carbon_ps2_zip,uc_ps2_zip):
    pc=SplitZip(pc_volumes)
    rows={}
    summaries={}
    for label,archive,stem in (
        ('carbon_pc',pc,'L5'),('carbon_ps2',carbon_ps2_zip,'L5'),
        ('undercover_ps2',uc_ps2_zip,'L2')):
        for sector in ('RA','RB'):
            small=f'TRACKS/{stem}{sector}.BUN'
            stream=f'TRACKS/STREAM{stem}{sector}.BUN'
            if label=='carbon_pc':
                data=archive.read(small)
                stream_size=archive.entries[stream][4]
            else:
                with zipfile.ZipFile(archive) as z:
                    if z.getinfo(small).file_size>MAX_BUNDLE:
                        raise ValueError("Small BUN exceeds safety limit")
                    data=z.read(small)
                    stream_size=z.getinfo(stream).file_size
            resource=label+'_'+sector
            rows[resource],summaries[resource]=parse_sections(
                find_chunk(data),stream_size)
            summaries[resource]['stream_bytes']=stream_size
    comparisons={}
    for a,b,sector in (
        ('carbon_pc','carbon_ps2','RA'),('carbon_pc','carbon_ps2','RB'),
        ('carbon_ps2','undercover_ps2','RA'),('carbon_ps2','undercover_ps2','RB')):
        comparisons[f'{a}_vs_{b}_{sector}']=compare_section_ids(
            rows[f'{a}_{sector}'],rows[f'{b}_{sector}'])
    return {'sources':summaries,'comparisons':comparisons,
            'limits':('All fields are candidate TrackStreamingSection interpretations. '
                      'All reported offsets are within the corresponding uncompressed STREAM* file size. '
                      'This is not proof the offsets locate scenery roots, '
                      'or that Carbon PC can load Undercover geometry, collision or AI.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.undercover_ps2_zip),indent=2))


if __name__=='__main__':
    main()
