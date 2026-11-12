#!/usr/bin/env python3
"""Deterministic, source-free BC3/DXT5 encoder for *offline* texture research.

The encoded bytes are ordinary DXT5 blocks, NOT an independently verified
Carbon PC runtime resource. No source asset I/O or proprietary bytes included.
Alpha is compressed explicitly; never silently discarded as DXT1 would do.
"""
from synthetic_dxt1_texture_writer import encode_dxt1_block, _dims, MAX_LEVELS


def _alpha_palette(a0, a1):
    if a0 > a1:
        return (a0, a1) + tuple(((7-i)*a0 + i*a1)//7 for i in range(1, 7))
    return (a0, a1) + tuple(((5-i)*a0 + i*a1)//5 for i in range(1, 5)) + (0, 255)


def encode_dxt5_alpha_block(alpha):
    """16 alpha texels to 8-byte BC3 block, with bounded deterministic search.

    Compare full 8-step and endpoint-inclusive 6-step modes. Also consider
    dropping just the extreme one unique shade to reduce outlier distortion.
    This is a compact research encoder, not a production quality optimizer.
    """
    if not isinstance(alpha, (bytes, bytearray, memoryview)) or len(alpha) != 16:
        raise ValueError('DXT5 alpha block requires exactly sixteen samples')
    values = tuple(alpha)
    unique = sorted(set(values))
    if len(unique) == 1:
        return bytes((unique[0], unique[0])) + bytes(6)
    low, high = unique[0], unique[-1]
    pairs = [(high, low), (low, high), (0, 255)]
    if len(unique) > 2:
        # Ignore one extreme only as a candidate; retain best full error.
        pairs.extend([(unique[-2], low), (high, unique[1]),
                      (unique[1], high), (low, unique[-2])])
    best = None
    for a0, a1 in pairs:
        palette = _alpha_palette(a0, a1)
        selectors = []
        error = 0
        for value in values:
            chosen = min(range(8), key=lambda j: ((value-palette[j])**2, j))
            error += (value - palette[chosen])**2
            selectors.append(chosen)
        word = sum(sel << (3 * i) for i, sel in enumerate(selectors))
        encoded = bytes((a0, a1)) + word.to_bytes(6, 'little')
        score = (error, encoded)
        if best is None or score < best:
            best = score
    return best[1]


def encode_dxt5_block(pixels):
    """Compress 16 RGBA texels, using a separate opaque DXT1 color block."""
    if not isinstance(pixels, (bytes, bytearray, memoryview)) or len(pixels) != 64:
        raise ValueError('DXT5 block requires exactly 16 RGBA texels')
    colors = bytearray(pixels)
    colors[3::4] = bytes([255])*16
    return encode_dxt5_alpha_block(pixels[3::4]) + encode_dxt1_block(colors)


def encode_dxt5_base(rgba, width, height):
    _dims(width, height)
    if not isinstance(rgba, (bytes, bytearray, memoryview)) or len(rgba) != 4*width*height:
        raise ValueError('Invalid DXT5 RGBA byte count')
    out = bytearray()
    for by in range((height+3)//4):
        for bx in range((width+3)//4):
            block = bytearray()
            for py in range(4):
                y = min(height-1, 4*by+py)
                for px in range(4):
                    x = min(width-1, 4*bx+px)
                    off = 4*(y*width+x)
                    block.extend(rgba[off:off+4])
            out.extend(encode_dxt5_block(block))
    return bytes(out)


def downsample_rgba_2x2(rgba, width, height):
    """Box-filter alpha and alpha-weighted color to avoid transparent fringes."""
    _dims(width,height)
    if not isinstance(rgba, (bytes, bytearray, memoryview)) or len(rgba) != width*height*4:
        raise ValueError('Invalid RGBA mip input')
    nw, nh = max(1,width//2), max(1,height//2)
    out = bytearray()
    for y in range(nh):
        ys = (min(height-1,2*y), min(height-1,2*y+1)) if height>1 else (0,)
        for x in range(nw):
            xs = (min(width-1,2*x), min(width-1,2*x+1)) if width>1 else (0,)
            offsets=[4*(yy*width+xx) for yy in ys for xx in xs]
            a_sum=sum(rgba[o+3] for o in offsets)
            for c in range(3):
                if a_sum:
                    out.append((sum(rgba[o+c]*rgba[o+3] for o in offsets) + a_sum//2)//a_sum)
                else:
                    out.append((sum(rgba[o+c] for o in offsets) + len(offsets)//2)//len(offsets))
            out.append((a_sum + len(offsets)//2)//len(offsets))
    return bytes(out),nw,nh


def encode_dxt5_mips(rgba, width, height, mip_levels=1):
    _dims(width,height)
    if type(mip_levels) is not int or not 1<=mip_levels<=min(MAX_LEVELS,max(width,height).bit_length()):
        raise ValueError('Invalid DXT5 mip count')
    out=bytearray(); spans=[]
    for n in range(mip_levels):
        level=encode_dxt5_base(rgba,width,height)
        spans.append((width,height,len(out),len(level)))
        out.extend(level)
        if n+1<mip_levels:
            rgba,width,height=downsample_rgba_2x2(rgba,width,height)
    return bytes(out),tuple(spans)
