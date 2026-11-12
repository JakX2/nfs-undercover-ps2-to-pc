#!/usr/bin/env python3
"""Source-free, deterministic opaque DXT1 encoder for experimental PC output.

Produces *only* in-memory DXT1 blocks or mip chains. No texture assets, game
files or Carbon runtime structures are written. The lossy encoding is not a
bit-identical replacement for original PC DXT1, nor a validated game writer.
Alpha is deliberately rejected rather than silently erased.
"""

MAX_PIXELS = 1024 * 1024
MAX_LEVELS = 16


def _dims(width, height):
    if (type(width) is not int or type(height) is not int or width <= 0 or
            height <= 0 or width * height > MAX_PIXELS):
        raise ValueError('Invalid/unsafe DXT1 dimensions')


def _rgb565(rgb):
    r, g, b = rgb
    return (((r * 31 + 127) // 255) << 11 |
            ((g * 63 + 127) // 255) << 5 |
            ((b * 31 + 127) // 255))


def _expand565(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def _palette(c0, c1):
    a, b = _expand565(c0), _expand565(c1)
    if c0 <= c1:
        # Equal endpoints must only use 0 and 1; never emit transparent index 3.
        return (a, b)
    return (a, b,
            tuple((2*a[i] + b[i]) // 3 for i in range(3)),
            tuple((a[i] + 2*b[i]) // 3 for i in range(3)))


def _candidate_endpoints(colors):
    unique = sorted({_rgb565(c) for c in colors})
    if len(unique) == 1:
        return unique[0], unique[0]
    # Quantized farthest-pair initialization avoids same-endpoint collapse on
    # near-constant blocks and keeps the result independent of pixel order.
    distance, pair = -1, (unique[-1], unique[0])
    unpacked = {c: _expand565(c) for c in unique}
    for i, a in enumerate(unique):
        for b in unique[i+1:]:
            x, y = unpacked[a], unpacked[b]
            d = sum((x[k]-y[k])**2 for k in range(3))
            if d > distance:
                distance, pair = d, (b, a)
    return pair


def encode_dxt1_block(pixels):
    """Encode 16 opaque row-major RGBA texels as one standard DXT1 block."""
    if (not isinstance(pixels, (bytes, bytearray, memoryview)) or
            len(pixels) != 64):
        raise ValueError('DXT1 block must contain exactly 16 RGBA texels')
    if any(pixels[i] != 255 for i in range(3, 64, 4)):
        raise ValueError('DXT1 opaque-only path rejects non-opaque alpha')
    colors = [tuple(pixels[i:i+3]) for i in range(0, 64, 4)]
    c0, c1 = _candidate_endpoints(colors)
    palette = _palette(c0, c1)
    packed = 0
    for i, rgb in enumerate(colors):
        distances = [sum((rgb[k] - p[k])**2 for k in range(3)) for p in palette]
        selected = min(range(len(distances)), key=lambda j: (distances[j], j))
        packed |= selected << (2*i)
    return c0.to_bytes(2, 'little') + c1.to_bytes(2, 'little') + packed.to_bytes(4, 'little')


def encode_dxt1_base(rgba, width, height):
    """DXT1 block stream; edge pixels clamp to last valid source texel."""
    _dims(width, height)
    if (not isinstance(rgba, (bytes, bytearray, memoryview)) or
            len(rgba) != width*height*4):
        raise ValueError('Invalid RGBA input byte count')
    if any(rgba[i] != 255 for i in range(3, len(rgba), 4)):
        raise ValueError('DXT1 opaque-only path rejects non-opaque alpha')
    out = bytearray()
    for by in range((height+3)//4):
        for bx in range((width+3)//4):
            block = bytearray()
            for yy in range(4):
                y = min(height-1, by*4+yy)
                for xx in range(4):
                    x = min(width-1, bx*4+xx)
                    at = (y*width+x)*4
                    block.extend(rgba[at:at+4])
            out.extend(encode_dxt1_block(block))
    return bytes(out)


def downsample_opaque_2x2(rgba, width, height):
    """Deterministic RGB box filter (rounded), clamping odd-sized edges."""
    _dims(width, height)
    if (not isinstance(rgba, (bytes, bytearray, memoryview)) or
            len(rgba) != width*height*4 or
            any(rgba[i] != 255 for i in range(3, len(rgba), 4))):
        raise ValueError('Expected opaque RGBA for mip filtering')
    next_w, next_h = max(1, width//2), max(1, height//2)
    dst = bytearray()
    for y in range(next_h):
        for x in range(next_w):
            # When an axis is already 1, do not accidentally weight it twice.
            xs = (min(width-1, 2*x), min(width-1, 2*x+1)) if width > 1 else (0,)
            ys = (min(height-1, 2*y), min(height-1, 2*y+1)) if height > 1 else (0,)
            for c in range(3):
                total = sum(rgba[(sy*width+sx)*4+c] for sy in ys for sx in xs)
                count = len(xs)*len(ys)
                dst.append((total + count//2)//count)
            dst.append(255)
    return bytes(dst), next_w, next_h


def encode_dxt1_mips(rgba, width, height, mip_levels=1):
    """Return (encoded concatenated mip chain, tuple of (width,height,offset,size)).

    Consecutive repeated 1x1 mip levels are forbidden. Mips are sourced from
    the *uncompressed* previous level; each level is encoded independently.
    """
    _dims(width, height)
    max_levels = max(width,height).bit_length()
    if (type(mip_levels) is not int or not 1 <= mip_levels <= min(MAX_LEVELS, max_levels)):
        raise ValueError('Invalid mip count for DXT1 dimensions')
    encoded, spans = bytearray(), []
    for _ in range(mip_levels):
        data = encode_dxt1_base(rgba, width, height)
        spans.append((width, height, len(encoded), len(data)))
        encoded.extend(data)
        if len(spans) < mip_levels:
            rgba, width, height = downsample_opaque_2x2(rgba, width, height)
    return bytes(encoded), tuple(spans)
