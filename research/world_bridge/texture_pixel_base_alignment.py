#!/usr/bin/env python3
"""Strict, read-only 128-byte pixel-data origin for NFS streamed texture packs.

Unlike offset-only size checks, original 0x33310004 image/palette offsets are
relative to the 128-byte-aligned interior of 0x33320002, not its first byte.
The observed padding is 0x11. Do not silently guess another offset/filler.
Source bytes stay in caller-owned memory. No file writes or asset exports.
"""
import struct

ROOT = 0xB3300000
PIX_ROOT = 0xB3320000
PIX_DATA = 0x33320002
MAX_SECTION = 32 * 1024 * 1024


def _chunks(section, begin, end):
    out = []
    while begin < end:
        if begin + 8 > end:
            raise ValueError('Truncated texture chunk header')
        cid, size = struct.unpack_from('<II', section, begin)
        stop = begin + 8 + size
        if stop > end:
            raise ValueError('Texture chunk exceeds parent bounds')
        out.append((cid, begin + 8, stop))
        begin = stop
    return out


def aligned_pixel_array(section, records=None):
    """Return (memoryview of true pixel base, padding length).

    The 0x33320002 payload's physical beginning need not be 128-byte aligned.
    Any gap before the aligned base must consist of the observed 0x11 filler.
    If records are supplied, verify *every* image/palette span from that base.
    """
    if not isinstance(section, (bytes, bytearray)) or not 40 <= len(section) <= MAX_SECTION:
        raise ValueError('Unsafe texture section')
    cid, size = struct.unpack_from('<II', section)
    if cid != ROOT or 8 + size > len(section):
        raise ValueError('Not a complete streamed texture root')
    root = _chunks(section, 8, 8 + size)
    if [row[0] for row in root] != [0, 0xB3310000, 0, PIX_ROOT]:
        raise ValueError('Unexpected root layout')
    pixels = _chunks(section, root[3][1], root[3][2])
    if [row[0] for row in pixels] != [0x33320001, 0, PIX_DATA]:
        raise ValueError('Unexpected pixel-resource chunk layout')
    start, end = pixels[2][1], pixels[2][2]
    padding = -start % 128
    if start + padding >= end or section[start:start + padding] != bytes([0x11]) * padding:
        raise ValueError('Missing 128-byte aligned 0x11 texture pixel padding')
    view = memoryview(section)[start + padding:end]
    if records is not None:
        for meta in records.values():
            for offset_key, size_key in [('image_offset','image_bytes'), ('palette_offset','palette_bytes')]:
                off = meta[offset_key]
                n = meta[size_key]
                if (type(off) is not int or type(n) is not int or off < 0 or n < 0 or
                        (n > 0 and off + n > len(view))):
                    raise ValueError('Texture range exceeds aligned pixel data')
    return view, padding
