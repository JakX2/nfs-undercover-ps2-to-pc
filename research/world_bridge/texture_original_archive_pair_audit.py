#!/usr/bin/env python3
"""Read-only original Carbon PC split-ZIP / PS2 ZIP texture-pair audit.

Stream members are decompressed in small chunks, CRC-checked in full and only
selected 0x34110 sections are retained in RAM. The tool publishes no original
archive bytes, texture hash inventories, texture names, image files or offsets.
This module intentionally cannot modify or write any game file.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile
import zlib

from track_bundle_probe import SplitZip
from texture_visual_pair_gate import compare_sections
from texture_metadata_pixel_bridge import MAX_SECTION

SECTION_TABLE = 0x34110
ROW_SIZE = 92
MAX_SMALL_BUN = 8 * 1024 * 1024
MAX_STREAM = 2 * 1024 * 1024 * 1024
MAX_SECTIONS = 4
READ_CHUNK = 65536


def _bounds(bundle, stream_size, section_ids):
    """Locate only requested section table rows. Reject duplicate/unsafe ranges."""
    if not 0 < len(bundle) <= MAX_SMALL_BUN or not 0 < stream_size <= MAX_STREAM:
        raise ValueError('Unsafe source bundle or stream size')
    if not section_ids or len(section_ids) > MAX_SECTIONS or len(set(section_ids)) != len(section_ids):
        raise ValueError('Invalid requested section ids')
    tag = struct.pack('<I',SECTION_TABLE)
    pos = bundle.find(tag)
    if pos < 0 or pos+8 > len(bundle):
        raise ValueError('Missing section table')
    size = struct.unpack_from('<I',bundle,pos+4)[0]
    if size < ROW_SIZE or size % ROW_SIZE or pos+8+size > len(bundle):
        raise ValueError('Malformed section table')
    out = {}
    seen = set()
    for p in range(pos+8,pos+8+size,ROW_SIZE):
        number = struct.unpack_from('<h',bundle,p+8)[0]
        if number in seen: raise ValueError('Duplicate section number')
        seen.add(number)
        if number not in section_ids:
            continue
        start, length = struct.unpack_from('<II',bundle,p+0x14)
        if start % 2048 or length < 8 or length > MAX_SECTION or start+length > stream_size:
            raise ValueError('Requested section is misaligned or out of bounds')
        out[number] = (start,length)
    if set(out) != set(section_ids):
        raise ValueError('Missing requested section number')
    intervals=sorted((p,p+n) for p,n in out.values())
    if any(left[0] < right[1] for right,left in zip(intervals,intervals[1:])):
        raise ValueError('Requested source sections overlap')
    return out


def _capture(chunks, expected_size, intervals):
    """Collect only selected intervals while consuming entire CRC-checked ZIP."""
    if sum(n for _,n in intervals.values()) > MAX_SECTIONS*MAX_SECTION:
        raise ValueError('Too many retained bytes')
    result={k:bytearray(n) for k,(_,n) in intervals.items()}
    stream_at=0
    for data in chunks:
        if not data: continue
        stop=stream_at+len(data)
        if stop > expected_size: raise ValueError('Stream exceeds advertised uncompressed size')
        for identity,(start,length) in intervals.items():
            begin=max(start,stream_at)
            end=min(start+length,stop)
            if begin < end:
                result[identity][begin-start:end-start]=data[begin-stream_at:end-stream_at]
        stream_at=stop
    if stream_at != expected_size:
        raise ValueError('Truncated stream member')
    return {k:bytes(v) for k,v in result.items()}


def _split_chunks(split, member):
    """Verify a split PKZIP member without buffering its full expanded stream."""
    disk,local_offset,method,compressed,usize,expected_crc=split.entries[member]
    if not 0 < usize <= MAX_STREAM or not 0 <= compressed <= MAX_STREAM:
        raise ValueError('Split source stream violates safety bound')
    offset=split.starts[disk]+local_offset
    header=split._read(offset,30)
    sig,_need,flags,actual_method,_time,_date,_crc,_csize,_usize,nlen,xlen=struct.unpack('<4s5H3I2H',header)
    if sig != b'PK\x03\x04' or flags & 1 or method not in (0,8) or actual_method != method:
        raise ValueError('Invalid split ZIP local header')
    offset+=30+nlen+xlen
    crc=0
    total=0
    decoder=zlib.decompressobj(-15) if method==8 else None
    remaining=compressed
    while remaining:
        take=min(READ_CHUNK,remaining)
        packed=split._read(offset,take)
        if len(packed)!=take:
            raise ValueError('Incomplete split compressed stream')
        offset+=take
        remaining-=take
        if decoder:
            data=decoder.decompress(packed,READ_CHUNK)
            while True:
                if data:
                    total+=len(data)
                    if total>usize:raise ValueError('Decompressed stream exceeds metadata')
                    crc=zlib.crc32(data,crc)
                    yield data
                if not decoder.unconsumed_tail: break
                data=decoder.decompress(decoder.unconsumed_tail,READ_CHUNK)
        else:
            total+=len(packed)
            if total>usize: raise ValueError('Stored stream exceeds metadata')
            crc=zlib.crc32(packed,crc)
            yield packed
    if decoder:
        if not decoder.eof or decoder.unused_data:
            raise ValueError('Truncated or extended compressed split stream')
        flushed=decoder.flush()
        if flushed:
            total+=len(flushed)
            if total>usize:raise ValueError('Expanded flush exceeds metadata')
            crc=zlib.crc32(flushed,crc)
            yield flushed
    if total!=usize or crc != expected_crc:
        raise ValueError('Split ZIP stream length/CRC mismatch')


def _regular_chunks(z,member):
    info=z.getinfo(member)
    if not 0<info.file_size<=MAX_STREAM:
        raise ValueError('Regular ZIP stream size violates safety bound')
    with z.open(info) as fp:
        while True:
            data=fp.read(READ_CHUNK)
            if not data:break
            yield data


def _read_regular(zip_path, section_ids=(141,142)):
    with zipfile.ZipFile(zip_path) as z:
        bun='TRACKS/L5RB.BUN';stream='TRACKS/STREAML5RB.BUN'
        if z.getinfo(bun).file_size>MAX_SMALL_BUN:
            raise ValueError('Oversize PS2 small BUN')
        bundle=z.read(bun)  # zipfile verifies this member's CRC
        stream_size=z.getinfo(stream).file_size
        intervals=_bounds(bundle,stream_size,section_ids)
        return _capture(_regular_chunks(z,stream),stream_size,intervals)


def _read_split(pc_volumes,section_ids=(141,142)):
    split=SplitZip(pc_volumes)
    bun='TRACKS/L5RB.BUN';stream='TRACKS/STREAML5RB.BUN'
    bundle=split.read(bun,MAX_SMALL_BUN)
    intervals=_bounds(bundle,split.entries[stream][4],section_ids)
    return _capture(_split_chunks(split,stream),split.entries[stream][4],intervals)


def analyze_archives(pc_volumes,carbon_ps2_zip,section_ids=(141,142),max_pairs=8):
    """Only counts and candidate scoring leave this function."""
    if not pc_volumes or not Path(carbon_ps2_zip).is_file():
        raise ValueError('Missing locally owned original archives')
    pc=_read_split(pc_volumes,section_ids)
    ps2=_read_regular(carbon_ps2_zip,section_ids)
    results={str(i):compare_sections(pc[i],ps2[i],max_pairs) for i in section_ids}
    return {'sections':results,'provenance':'Original Carbon PC split TRACKS and Carbon PS2 TRACKS members, CRC checked',
            'verdict':'UNVERIFIED: original-source candidate metrics; external visual verification and game runtime validation absent'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pc-volumes',nargs='+',type=Path,required=True,
                        help='Original Carbon PC TRACKS.z01 ... TRACKS.zip in disk order')
    parser.add_argument('--carbon-ps2-zip',type=Path,required=True)
    parser.add_argument('--max-pairs',type=int,default=8)
    args=parser.parse_args()
    print(json.dumps(analyze_archives(args.pc_volumes,args.carbon_ps2_zip,max_pairs=args.max_pairs),indent=2))


if __name__=='__main__':
    main()
