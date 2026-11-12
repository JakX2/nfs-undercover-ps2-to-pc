#!/usr/bin/env python3
"""Experimental PSMCT16-upload -> PSMT4-reading PS2 texture candidate.

Some PS2 engines upload 4bpp packed source bytes as PSMCT16 texels over
(width/2,height/2), then read the same GS VRAM as PSMT4. This is an explicit
candidate, not a verified Undercover PS2 conversion method. Source-free,
bounded, RAM-only. Address geometry cross-checked with MIT-licensed PS2 GS
memory research in the owner's Most Wanted reference archive.
"""
from ps2_texture_layout_candidates import _gs_address, _ct32_word, MAX_GS_BYTES, MAX_PIXELS

_BLOCK16 = (
    0,2,8,10,1,3,9,11,4,6,12,14,5,7,13,15,
    16,18,24,26,17,19,25,27,20,22,28,30,21,23,29,31,
)


def _addr16(x, y, width):
    """Return byte offset of a 16-bit color texel in GS memory, TBP=0.

    PSMCT16 page 64x64, block 16x8, column two rows. Each page is 8192
    bytes, with column word+nibble interleaving fully explicit.
    """
    page = (y // 64) * ((width + 63) // 64) + x // 64
    px, py = x % 64, y % 64
    block = _BLOCK16[(py // 8) * 4 + (px // 16)]
    cx, cy = px % 16, py % 8
    col = cy // 2
    cw = _ct32_word(cx % 8, cy % 2)
    return page * 8192 + block * 256 + col * 64 + cw * 4 + (cx // 8) * 2


def decode_ct16_psmt4(source, width, height):
    """Return one unpacked 4bit index per pixel; reject unaddressed bytes."""
    if type(width) is not int or type(height) is not int or width < 2 or height < 2 or width * height > MAX_PIXELS:
        raise ValueError('Invalid PSMT4 dimensions for CT16 transfer')
    if width % 2 or height % 2:
        raise ValueError('CT16 transfer requires even texture dimensions')
    if not isinstance(source, (bytes, bytearray, memoryview)) or len(source) != width * height // 2:
        raise ValueError('Wrong source CT16/PSMT4 byte count')
    w2, h2 = width // 2, height // 2
    pages = ((w2 + 63) // 64) * ((h2 + 63) // 64)
    size = pages * 8192
    if size > MAX_GS_BYTES:
        raise ValueError('CT16 transfer exceeds GS safety bound')
    mem = bytearray(size)
    written = bytearray(size)
    for y in range(h2):
        for x in range(w2):
            src = (y * w2 + x) * 2
            dst = _addr16(x, y, w2)
            if dst + 2 > size:
                raise ValueError('CT16 write exceeds GS allocation')
            mem[dst:dst+2] = source[src:src+2]
            written[dst:dst+2] = b'\1\1'
    out = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            addr,shift = _gs_address(x,y,width,4)
            if addr >= size or not written[addr]:
                raise ValueError('PSMT4 address was not initialized by CT16 upload')
            out[y*width+x] = (mem[addr] >> shift) & 15
    return bytes(out)
