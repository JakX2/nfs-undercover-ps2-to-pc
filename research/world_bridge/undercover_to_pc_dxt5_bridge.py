#!/usr/bin/env python3
"""Source-free, memory-only Undercover PS2 RGBA -> existing Carbon PC DXT5 slot.

This is an OFFLINE codec+envelope proof, not a Carbon game texture loader.
Actual source textures and hashes remain caller-owned and never leave process
memory or appear in returned aggregates. PS2 alpha doubling is a *candidate*
for color/alpha byte reconstruction, not proof of material blending semantics.
"""
from collections import Counter
from statistics import mean,median

from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from texture_visual_pair_gate import _base, _palette, _platform_flags
from ps2_texture_layout_candidates import decode_indices,palette_rgba,indices_to_rgba
from ps2_ct16_transfer_candidate import decode_ct16_psmt4
from pc_texture_header_overlay_gate import _source_image_span
from synthetic_dxt5_texture_writer import encode_dxt5_base,encode_dxt5_mips,downsample_rgba_2x2
from pc_dxt_reference_decode import decode_dxt_base,compare_rgba_nearest

MAX_TEXTURES = 512


def decode_undercover_source(section, ordinal):
    """One original or synthetic PS2 texture, by private sorted-index ordinal."""
    if type(ordinal) is not int or ordinal < 0:
        raise ValueError('Invalid private source ordinal')
    records = parse_pack(section,'ps2')['records']
    if len(records)>MAX_TEXTURES or ordinal >= len(records):
        raise ValueError('Source ordinal outside bounded texture index')
    pixels,_ = aligned_pixel_array(section,records)
    key = sorted(records)[ordinal]
    meta = records[key]
    flags = _platform_flags(section,records)
    flag,bits = flags[key],meta['codec']
    raw = _base(pixels,meta)
    if flag==0:
        indices=decode_indices(raw,meta['width'],meta['height'],bits,'linear')
    elif flag==1 and bits==4:
        indices=decode_ct16_psmt4(raw,meta['width'],meta['height'])
    elif flag==1 and bits==8:
        indices=decode_indices(raw,meta['width'],meta['height'],bits,'ct32_transfer')
    else:
        raise ValueError('Unsupported PS2 indexed transfer layout')
    clut='csm1' if bits==8 else 'linear'
    palette=palette_rgba(_palette(pixels,meta),bits,clut,'double','rgba')
    rgba=indices_to_rgba(indices,palette,bits)
    return rgba,meta['width'],meta['height'],bits,flag


def encode_roundtrip(rgba,width,height):
    """Compare one DXT5 base-level encode/decode to PS2 source RGBA."""
    encoded=encode_dxt5_base(rgba,width,height)
    decoded=decode_dxt_base(encoded,width,height,b'DXT5')
    error=compare_rgba_nearest(rgba,width,height,decoded,width,height)
    return encoded,error


def audit_undercover_section(section, max_samples=512):
    """Bounded, aggregate-only original PS2 -> PC BC3 codec viability audit."""
    if type(max_samples) is not int or not 1<=max_samples<=MAX_TEXTURES:
        raise ValueError('Unsafe sample limit')
    records=parse_pack(section,'ps2')['records']
    if len(records)>MAX_TEXTURES:
        raise ValueError('Too many donor textures')
    results=[]
    for ordinal in range(min(max_samples,len(records))):
        rgba,w,h,bits,flag=decode_undercover_source(section,ordinal)
        _,errors=encode_roundtrip(rgba,w,h)
        nonopaque=sum(a != 255 for a in rgba[3::4]);n=w*h
        results.append({'depth':bits,'flag':flag,'rgb':errors['mean_absolute_rgb_error'],
                        'alpha':errors['mean_absolute_alpha_error'],'nonopaque':nonopaque/n})
    if not results:
        raise ValueError('No textures to audit')
    by_depth={}
    for bits in (4,8):
        group=[r for r in results if r['depth']==bits]
        if not group: continue
        by_depth[str(bits)]={'textures':len(group),
            'mean_rgb_mae':round(mean(r['rgb'] for r in group),4),
            'mean_alpha_mae':round(mean(r['alpha'] for r in group),4),
            'max_rgb_mae':round(max(r['rgb'] for r in group),4),
            'max_alpha_mae':round(max(r['alpha'] for r in group),4)}
    return {'sampled_textures':len(results),
            'source_textures_with_nonopaque_alpha':sum(r['nonopaque']>0 for r in results),
            'source_textures_with_no_fully_opaque_pixels':sum(r['nonopaque']==1 for r in results),
            'mean_nonopaque_pixel_fraction':round(mean(r['nonopaque'] for r in results),6),
            'swizzle_flag_counts':dict(sorted(Counter(str(r['flag']) for r in results).items())),
            'mean_rgb_mae':round(mean(r['rgb'] for r in results),4),
            'mean_alpha_mae':round(mean(r['alpha'] for r in results),4),
            'median_rgb_mae':round(median(r['rgb'] for r in results),4),
            'median_alpha_mae':round(median(r['alpha'] for r in results),4),
            'max_rgb_mae':round(max(r['rgb'] for r in results),4),
            'max_alpha_mae':round(max(r['alpha'] for r in results),4),
            'by_indexed_depth':by_depth,
            'verdict':'OFFLINE DXT5 CODEC COMPARISON ONLY; runtime, material blending, sampler and texture identity registration UNVERIFIED'}


def overlay_undercover_on_existing_pc_dxt5(pc_section, uc_section, donor_ordinal=0, pc_dxt5_ordinal=0):
    """Replace one existing PC DXT5 image span in memory, no file writes.

    Only exact source dimensions are accepted; no automatic resize or texture
    identity reinterpretation. Existing PC hash/metadata/mips are preserved.
    """
    if type(pc_dxt5_ordinal) is not int or pc_dxt5_ordinal<0:
        raise ValueError('Invalid PC DXT5 ordinal')
    source,w,h,bits,flag=decode_undercover_source(uc_section,donor_ordinal)
    pc=parse_pack(pc_section,'pc')['records']
    aligned_pixel_array(pc_section,pc)
    targets=sorted(k for k,m in pc.items() if m['codec']==38)
    if pc_dxt5_ordinal>=len(targets):
        raise ValueError('Existing PC DXT5 ordinal outside available slots')
    key=targets[pc_dxt5_ordinal]; meta=pc[key]
    if (w,h) != (meta['width'],meta['height']):
        raise ValueError('Source and target dimensions differ; no resizing allowed')
    packed,spans=encode_dxt5_mips(source,w,h,meta['mip_levels'])
    if len(packed)!=meta['image_bytes'] or spans[0][3]!=meta['base_image_bytes']:
        raise ValueError('DXT5 output disagrees with existing PC source image size')
    left,right=_source_image_span(pc_section,meta)
    if right-left!=len(packed):
        raise ValueError('Original PC DXT5 image span is inconsistent')
    updated=bytearray(pc_section)
    updated[left:right]=packed
    rebuilt=bytes(updated)
    if rebuilt[:left]!=pc_section[:left] or rebuilt[right:]!=pc_section[right:]:
        raise ValueError('Modified nontexture resource bytes')
    if parse_pack(rebuilt,'pc')['records']!=pc:
        raise ValueError('Existing PC texture metadata changed')
    aligned_pixel_array(rebuilt,pc)
    decoded=decode_dxt_base(packed[:spans[0][3]],w,h,b'DXT5')
    score=compare_rgba_nearest(source,w,h,decoded,w,h)
    changed=sum(a!=b for a,b in zip(pc_section[left:right],packed))
    if not changed:
        raise ValueError('No DXT5 bytes changed in existing source')
    return rebuilt,{'original_pc_texture_count':len(pc),
                    'available_existing_pc_dxt5_slots':len(targets),
                    'source_indexed_bits':bits,'source_swizzle_flag':flag,
                    'width':w,'height':h,'mip_levels':meta['mip_levels'],
                    'replaced_image_bytes':len(packed),'changed_image_bytes':changed,
                    'rgb_mae_against_decoded_ps2':round(score['mean_absolute_rgb_error'],4),
                    'alpha_mae_against_decoded_ps2':round(score['mean_absolute_alpha_error'],4),
                    'only_one_existing_image_span_changed':True,
                    'runtime_compatibility':'UNVERIFIED'}
