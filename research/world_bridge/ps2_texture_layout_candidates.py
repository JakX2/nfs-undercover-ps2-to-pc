#!/usr/bin/env python3
"""Experimental, synthetic-first PS2 PSMT4/PSMT8 texture-layout candidates.

Source texture bytes may be (a) linear CPU indices, (b) GS VRAM memory order,
or (c) linear PSMCT32 transfer words intended for GS indexed reinterpretation.
Those are distinct hypotheses, not claims about any Undercover archive.

No archive I/O, image files, or automatic layout selection. Functions accept
bounded caller-owned byte strings and return only in-memory indices or RGBA.
GS addressing follows PSMT4/8 page/block/column geometry, cross-checked
against the MIT-licensed PDTools GS memory code and independent PS2 research.
"""

MAX_PIXELS = 4 * 1024 * 1024
MAX_GS_BYTES = 32 * 1024 * 1024
LAYOUTS = ('linear', 'gs_vram', 'ct32_transfer')


def _validate_dims(width, height, bits):
    if type(width) is not int or type(height) is not int or bits not in (4, 8):
        raise ValueError('Invalid dimensions or indexed depth')
    if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
        raise ValueError('Texture dimensions exceed decoder safety bound')
    if width * height * bits % 8:
        raise ValueError('Pixel bits are not byte-aligned')


def _ct32_word(x, y):
    return (x & 1) | ((y & 1) << 1) | (((x >> 1) & 1) << 2) | (((x >> 2) & 1) << 3)


def _gs_address(x, y, width, bits):
    """Return (byte offset, nibble shift) for PSMT4/8 or PSMCT32 (32)."""
    if bits == 32:
        pw, ph, bw, bh, blocks_per_row = 64, 32, 8, 8, 8
    elif bits == 8:
        pw, ph, bw, bh, blocks_per_row = 128, 64, 16, 16, 8
    elif bits == 4:
        pw, ph, bw, bh, blocks_per_row = 128, 128, 32, 16, 4
    else:
        raise ValueError('Unsupported GS pixel depth')
    pages_across = (width + pw - 1) // pw
    page = (y // ph) * pages_across + x // pw
    bx, by = (x % pw) // bw, (y % ph) // bh
    if bits == 4:
        block = (by & 1) | ((bx & 1) << 1) | (((by >> 1) & 1) << 2) | (((bx >> 1) & 1) << 3) | (((by >> 2) & 1) << 4)
    else:
        block = (bx & 1) | ((by & 1) << 1) | (((bx >> 1) & 1) << 2) | (((by >> 1) & 1) << 3) | (((bx >> 2) & 1) << 4)
    localx, localy = x % bw, y % bh
    col = localy // (2 if bits == 32 else 4)
    cy = localy % (2 if bits == 32 else 4)
    cw = _ct32_word(localx & 7, cy & 1)
    if bits != 32:
        cw ^= ((cy >> 1) ^ (col & 1)) << 3
    base = page * 8192 + block * 256 + col * 64 + cw * 4
    if bits == 32:
        return base, 0
    if bits == 8:
        return base + ((localx >> 3) & 1) * 2 + ((cy >> 1) & 1), 0
    nibble = ((localx >> 3) & 3) * 2 + ((cy >> 1) & 1)
    return base + (nibble >> 1), (nibble & 1) * 4


def _read_vram(raw, width, height, bits, written=None):
    out = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            at, shift = _gs_address(x, y, width, bits)
            if at >= len(raw) or (written is not None and not written[at]):
                raise ValueError('GS layout addresses bytes absent from supplied source')
            out[y * width + x] = (raw[at] >> shift) & ((1 << bits) - 1)
    return bytes(out)


def decode_indices(source, width, height, bits, layout='linear'):
    """Decode one *base level* to one byte per index; never choose a layout.

    - linear: row-major 8-bit bytes or low-nibble-first packed 4-bit indices.
    - gs_vram: provided bytes are already in GS indexed page/block order.
    - ct32_transfer: provided bytes are linear 32-bit transfer words whose
      CT32 VRAM writes are read back using the indexed GS pixel addressing.

    For small/padded textures the GS hypotheses may fail instead of inventing
    missing VRAM bytes. Mipmap levels must be provided separately by callers.
    """
    _validate_dims(width, height, bits)
    if layout not in LAYOUTS:
        raise ValueError('Unknown explicit PS2 layout hypothesis')
    if not isinstance(source, (bytes, bytearray, memoryview)):
        raise ValueError('Source must be bytes-like')
    packed = bytes(source)
    if len(packed) != width * height * bits // 8:
        raise ValueError('Wrong source base-level image byte count')
    if layout == 'linear':
        if bits == 8:
            return packed
        return bytes((v >> (4 * (i & 1))) & 15 for i in range(width * height)
                    for v in (packed[i // 2],))
    if layout == 'gs_vram':
        return _read_vram(packed, width, height, bits)
    # A CPU-side PSMCT32 image transfer can put words in locations whose
    # indexed PSMT8/4 interpretation is *not* row-major. Reconstruct VRAM.
    ct_width = width // 2
    ct_height = height // (2 if bits == 8 else 4)
    if ct_width <= 0 or ct_height <= 0 or ct_width * ct_height * 4 != len(packed):
        raise ValueError('Indexed dimensions cannot form CT32 transfer words')
    pages = ((ct_width + 63) // 64) * ((ct_height + 31) // 32)
    size = pages * 8192
    if size > MAX_GS_BYTES:
        raise ValueError('CT32 transfer exceeds safety bound')
    gs = bytearray(size)
    written = bytearray(size)
    at_source = 0
    for y in range(ct_height):
        for x in range(ct_width):
            dest, _ = _gs_address(x, y, ct_width, 32)
            gs[dest:dest + 4] = packed[at_source:at_source + 4]
            written[dest:dest + 4] = b'\1\1\1\1'
            at_source += 4
    return _read_vram(gs, width, height, bits, written)


def palette_rgba(palette, bits, clut='linear', alpha='raw', channels='rgba'):
    """Read 32-bit palette candidates without assuming CLUT mode or alpha.

    'csm1' swaps the 8/16 entry groups within each 32-entry bank for 8bpp.
    PS2's common half-range alpha (0..128) is an explicit opt-in candidate.
    """
    if bits not in (4, 8) or clut not in ('linear', 'csm1') or alpha not in ('raw', 'double') or channels not in ('rgba', 'bgra'):
        raise ValueError('Unsupported explicit palette candidate')
    if not isinstance(palette, (bytes, bytearray, memoryview)) or len(palette) != (1 << bits) * 4:
        raise ValueError('Wrong 32-bit palette byte count')
    out = bytearray(len(palette))
    for i in range(1 << bits):
        physical = i
        if clut == 'csm1' and bits == 8:
            physical = (i & ~0x18) | ((i & 8) << 1) | ((i & 16) >> 1)
        px = palette[physical * 4: physical * 4 + 4]
        r, g, b, a = (px[0], px[1], px[2], px[3]) if channels == 'rgba' else (px[2], px[1], px[0], px[3])
        out[i * 4:i * 4 + 4] = bytes((r, g, b, min(255, a * 2) if alpha == 'double' else a))
    return bytes(out)


def indices_to_rgba(indices, palette, bits):
    if bits not in (4, 8) or len(palette) != (1 << bits) * 4:
        raise ValueError('Invalid indexed RGBA palette')
    if len(indices) > MAX_PIXELS:
        raise ValueError('Excessive index count')
    if any(v >= (1 << bits) for v in indices):
        raise ValueError('Palette index exceeds codec range')
    return b''.join(palette[v * 4:v * 4 + 4] for v in indices)


def decode_rgba(source, palette, width, height, bits, layout='linear', clut='linear', alpha='raw', channels='rgba'):
    indices = decode_indices(source, width, height, bits, layout)
    return indices_to_rgba(indices, palette_rgba(palette, bits, clut, alpha, channels), bits)
