#!/usr/bin/env python3
"""Bounded, read-only DXT1/3/5 base-level decoder for *comparison* controls.

This intentionally produces memory-only RGBA, not a Carbon PC texture writer.
DXT color interpolation uses integer truncation and common RGB565 bit replication.
"""

MAX_PIXELS = 4 * 1024 * 1024
DXT = {b'DXT1': 8, b'DXT3': 16, b'DXT5': 16}


def _rgb565(v):
    r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def _colors(c0, c1, opaque):
    a, b = _rgb565(c0), _rgb565(c1)
    colors = [(*a, 255), (*b, 255)]
    if c0 > c1 or opaque:
        colors += [tuple((2 * a[k] + b[k]) // 3 for k in range(3)) + (255,),
                   tuple((a[k] + 2 * b[k]) // 3 for k in range(3)) + (255,)]
    else:
        colors += [tuple((a[k] + b[k]) // 2 for k in range(3)) + (255,),
                   (0, 0, 0, 0)]
    return colors


def _alpha_dxt5(block):
    a0, a1 = block[0], block[1]
    if a0 > a1:
        values = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
    else:
        values = [a0, a1] + [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]
    indices = int.from_bytes(block[2:8], 'little')
    return [values[(indices >> (3 * i)) & 7] for i in range(16)]


def decode_dxt_base(packed, width, height, fourcc):
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0 or width * height > MAX_PIXELS:
        raise ValueError('Invalid DXT image dimensions')
    if fourcc not in DXT:
        raise ValueError('Unsupported DXT FOURCC')
    if not isinstance(packed, (bytes, bytearray, memoryview)):
        raise ValueError('DXT bytes must be a bytes-like object')
    block_bytes = DXT[fourcc]
    width_blocks, height_blocks = (width + 3) // 4, (height + 3) // 4
    if len(packed) != width_blocks * height_blocks * block_bytes:
        raise ValueError('Invalid DXT base-level byte count')
    rgba = bytearray(width * height * 4)
    for by in range(height_blocks):
        for bx in range(width_blocks):
            start = (by * width_blocks + bx) * block_bytes
            block = packed[start:start + block_bytes]
            c_offset = 0 if fourcc == b'DXT1' else 8
            c0 = int.from_bytes(block[c_offset:c_offset+2], 'little')
            c1 = int.from_bytes(block[c_offset+2:c_offset+4], 'little')
            palette = _colors(c0, c1, fourcc != b'DXT1')
            selectors = int.from_bytes(block[c_offset+4:c_offset+8], 'little')
            alphas = None
            if fourcc == b'DXT3':
                alpha_word = int.from_bytes(block[:8], 'little')
                alphas = [((alpha_word >> (4 * i)) & 15) * 17 for i in range(16)]
            elif fourcc == b'DXT5':
                alphas = _alpha_dxt5(block)
            for py in range(4):
                for px in range(4):
                    x, y = bx * 4 + px, by * 4 + py
                    if x >= width or y >= height:
                        continue
                    i = py * 4 + px
                    pixel = palette[(selectors >> (2 * i)) & 3]
                    at = (y * width + x) * 4
                    rgba[at:at+4] = bytes((*pixel[:3], alphas[i] if alphas is not None else pixel[3]))
    return bytes(rgba)


def compare_rgba_nearest(pc, pc_width, pc_height, ps2, ps2_width, ps2_height):
    """Resolution-aware comparison metrics, not a verdict or auto-selection.

    Compare on the lower-resolution PS2 pixel grid, mapping normalized pixel
    centers to nearest PC texels. Ordinary DXT artifacts and resampling can
    produce nonzero error for correct texture identities.
    """
    for w, h in ((pc_width, pc_height), (ps2_width, ps2_height)):
        if type(w) is not int or type(h) is not int or w <= 0 or h <= 0 or w*h > MAX_PIXELS:
            raise ValueError('Invalid comparison dimensions')
    if len(pc) != pc_width * pc_height * 4 or len(ps2) != ps2_width * ps2_height * 4:
        raise ValueError('Comparison buffer length mismatch')
    rgb_diff = 0
    alpha_diff = 0
    for y in range(ps2_height):
        pc_y = min(pc_height-1, (2*y+1) * pc_height // (2*ps2_height))
        for x in range(ps2_width):
            pc_x = min(pc_width-1, (2*x+1) * pc_width // (2*ps2_width))
            a = (pc_y*pc_width+pc_x)*4
            b = (y*ps2_width+x)*4
            rgb_diff += sum(abs(pc[a+k]-ps2[b+k]) for k in range(3))
            alpha_diff += abs(pc[a+3]-ps2[b+3])
    n = ps2_width * ps2_height
    return {'compared_pixels': n,
            'mean_absolute_rgb_error': rgb_diff/(3*n),
            'mean_absolute_alpha_error': alpha_diff/n}
