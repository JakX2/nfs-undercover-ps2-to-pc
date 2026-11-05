#!/usr/bin/env python3
"""Read-only 0x33310004 texture metadata -> 0x33320002 pixel span validator.

Records/texture names/bytes are kept private in memory. No original source
assets are written, decoded or printed. Inferred field names are corroborated
by six original Carbon PC/PS2 and Undercover PS2 texture-pack controls, not by
an independent Carbon PC runtime ABI test.
"""
from collections import Counter
import math
import struct

ROOT=0xB3300000
DESC_ROOT=0xB3310000
PIX_ROOT=0xB3320000
INDEX=0x33310002
TEXTURE_META=0x33310004
PLATFORM_META=0x33310005
PIX_DATA=0x33320002
MAX_SECTION=32*1024*1024
MAX_TEXTURES=32768
CODEC_FOURCC={34:b'DXT1',36:b'DXT3',38:b'DXT5'}


def children(raw, begin=0, end=None):
    if end is None:end=len(raw)
    out=[]
    while begin<end:
        if begin+8>end:raise ValueError('Truncated texture chunk header')
        cid, length=struct.unpack_from('<II',raw,begin)
        stop=begin+8+length
        if stop>end:raise ValueError('Texture chunk extends beyond parent')
        out.append((cid,raw[begin+8:stop]))
        begin=stop
    return out


def mip_size(width,height,codec,levels):
    if codec in CODEC_FOURCC:
        bytes_block=8 if codec==34 else 16
        return sum(max(1,((width>>k)+3)//4)*max(1,((height>>k)+3)//4)*bytes_block for k in range(levels))
    if codec in (4,8):
        return sum((max(1,width>>k)*max(1,height>>k)*codec+7)//8 for k in range(levels))
    raise ValueError('Unknown image compression')


def parse_pack(section, platform):
    """Return private hash-keyed image metadata and safe aggregate statistics.

    platform is 'pc' or 'ps2'. Index, names, image/palette ranges and DXT/CLUT
    byte-size equations are checked before callers may locate raw image bytes.
    """
    if platform not in ('pc','ps2') or not 40<=len(section)<=MAX_SECTION:
        raise ValueError('Bad platform or unsafe texture section size')
    cid,size=struct.unpack_from('<II',section)
    if cid!=ROOT or size+8>len(section):raise ValueError('Not a complete texture-pack root')
    root=children(section,8,8+size)
    if [cid for cid,_ in root]!=[0,DESC_ROOT,0,PIX_ROOT]:
        raise ValueError('Unexpected texture-pack root layout')
    desc=children(root[1][1]);pix=children(root[3][1])
    if [cid for cid,_ in desc]!=[0x33310001,INDEX,TEXTURE_META,PLATFORM_META]:
        raise ValueError('Unexpected texture descriptor layout')
    if [cid for cid,_ in pix]!=[0x33320001,0,PIX_DATA]:
        raise ValueError('Unexpected texture pixel-resource layout')
    if len(pix[0][1])!=24 or not pix[2][1]:
        raise ValueError('Missing pixel-data header/payload')
    raw_index=desc[1][1]
    if not raw_index or len(raw_index)%8 or len(raw_index)//8>MAX_TEXTURES:
        raise ValueError('Invalid texture hash index stride/count')
    ids=[h for h,pointer in struct.iter_unpack('<II',raw_index) if pointer==0]
    count=len(raw_index)//8
    if len(ids)!=count or 0 in ids or ids!=sorted(set(ids)):
        raise ValueError('Duplicate or unsorted texture hash index or nonzero pointer')
    metadata=desc[2][1];platform_info=desc[3][1]
    stride=24 if platform=='pc' else 84
    if len(platform_info)!=count*stride:
        raise ValueError('Wrong PC/PS2 texture platform metadata stride')
    pixel=memoryview(pix[2][1])
    cursor=0
    records={};segments=[];codecs=Counter();zero_palette=0
    name_size=Counter()
    for index,h in enumerate(ids):
        if cursor+89>len(metadata):raise ValueError('Truncated variable-length texture metadata')
        if metadata[cursor:cursor+12]!=bytes(12):
            raise ValueError('Unexpected texture-info lead-in')
        n=metadata[cursor+88]
        if n<3 or n%4!=3 or cursor+89+n>len(metadata):
            raise ValueError('Invalid length-prefixed padded texture name')
        row=memoryview(metadata)[cursor:cursor+89+n]
        source_hash=struct.unpack_from('<I',row,12)[0]
        if source_hash!=h:raise ValueError('Texture metadata hash differs from sorted index')
        name=bytes(row[89:])
        name_end=name.find(b'\0')
        if name_end<=0 or any(name[name_end:]) or any(not 32<=c<=126 for c in name[:name_end]):
            raise ValueError('Malformed ASCII texture name/padding')
        placement,palette_offset,image_size,palette_size,base_size=struct.unpack_from('<5I',row,20)
        width,height=struct.unpack_from('<HH',row,40)
        shift_x,shift_y,codec,palcodec=row[44:48]
        palette_entries=struct.unpack_from('<H',row,48)[0]
        mip_count=row[50]
        tile_mode=row[51]
        if not (0<width<=8192 and 0<height<=8192 and
                width&(width-1)==0 and height&(height-1)==0 and
                shift_x==width.bit_length()-1 and shift_y==height.bit_length()-1 and
                1<=mip_count<=16):
            raise ValueError('Invalid texture dimensions, shifts or mip count')
        if platform=='pc':
            if codec not in CODEC_FOURCC or palette_size or palette_entries or palcodec:
                raise ValueError('Unsupported PC DXT/palette metadata')
            fourcc=platform_info[index*stride+12:index*stride+16]
            if fourcc!=CODEC_FOURCC[codec]:
                raise ValueError('PC platform FOURCC disagrees with texture compression')
        else:
            if codec not in (4,8) or palette_size!=(64 if codec==4 else 1024) or palcodec:
                raise ValueError('Unexpected PS2 indexed texture/palette size')
            if palette_entries!=(16 if codec==4 else 256):
                raise ValueError('Unexpected PS2 palette entry count')
        expected_base=mip_size(width,height,codec,1)
        expected_image=mip_size(width,height,codec,mip_count)
        if base_size!=expected_base or image_size!=expected_image:
            raise ValueError('Image bytes disagree with dimension/compression/mipmap metadata')
        if placement+image_size>len(pixel):
            raise ValueError('Texture image placement exceeds pixel array')
        segments.append((placement,placement+image_size))
        if palette_size:
            if palette_offset+palette_size>len(pixel):
                raise ValueError('Texture palette placement exceeds pixel array')
            segments.append((palette_offset,palette_offset+palette_size))
        else:zero_palette+=1
        records[h]={'width':width,'height':height,'codec':int(codec),
                    'mip_levels':int(mip_count),'tile_mode':int(tile_mode),
                    'name':name[:name_end], 'image_offset':placement,
                    'image_bytes':image_size, 'palette_offset':palette_offset,
                    'palette_bytes':palette_size, 'base_image_bytes':base_size}
        codecs[int(codec)]+=1;name_size[int(n)]+=1
        cursor+=89+n
    if cursor!=len(metadata):raise ValueError('Trailing bytes in variable-length texture metadata table')
    spans=sorted(segments)
    if any(nxt[0]<prev[1] for prev,nxt in zip(spans,spans[1:])):
        raise ValueError('Texture images or palettes overlap in the pixel resource')
    return {'records':records,'summary':{
        'indexed_texture_records':count,
        'texture_info_bytes':len(metadata),
        'platform_info_bytes_per_record':stride,
        'pixel_data_array_bytes':len(pixel),
        'valid_image_ranges':count,
        'valid_palette_ranges':count-zero_palette,
        'all_pixel_spans_disjoint':True,
        'image_compression_types':dict(sorted(codecs.items())),
        'name_storage_length_histogram':dict(sorted(name_size.items())),
    }}


def compare_carbon(left,right):
    """Compare *only shared hash records* across independent Carbon sources."""
    a,b=left['records'],right['records']
    common=a.keys()&b.keys()
    return {'common_texture_hashes':len(common),
            'matching_debug_names':sum(a[h]['name']==b[h]['name'] for h in common),
            'matching_tile_mode_flags':sum(a[h]['tile_mode']==b[h]['tile_mode'] for h in common),
            'same_dimensions':sum((a[h]['width'],a[h]['height'])==(b[h]['width'],b[h]['height']) for h in common),
            'left_at_least_as_large_in_both_dimensions':sum(a[h]['width']>=b[h]['width'] and a[h]['height']>=b[h]['height'] for h in common)}
