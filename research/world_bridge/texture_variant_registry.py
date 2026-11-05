#!/usr/bin/env python3
"""Read-only, section-explicit donor texture variant selection and coverage.

A name hash is an identity, not a unique image version. Never silently choose
among multiple section-specific original assets. This module exports counts only,
and its archived-input CLI does not write textures or print original names/hashes.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct
import zipfile

from texture_metadata_pixel_bridge import parse_pack

MAX_TRACKS_STREAM = 128 * 1024 * 1024
MAX_SMALL_BUN = 8 * 1024 * 1024
ROW_SIZE = 92
SECTION_TABLE_ID = 0x34110


class TextureVariantRegistry:
    def __init__(self, section_records):
        """section_records: {signed section_id: parsed records {hash: metadata}}.

        Original names/texture identities remain in private process memory.
        """
        if not section_records:
            raise ValueError('No section records supplied')
        self._by_section = {}
        self._by_hash = defaultdict(dict)
        for section, records in section_records.items():
            if type(section) is not int or not 0 < section < 32768:
                raise ValueError('Invalid section number')
            if not records:
                raise ValueError('No texture records for section')
            if section in self._by_section:
                raise ValueError('Repeated source section')
            current = {}
            for h, meta in records.items():
                if type(h) is not int or not 0 < h <= 0xffffffff:
                    raise ValueError('Invalid texture identity')
                if not isinstance(meta, dict):
                    raise ValueError('Invalid texture metadata')
                for field in ('width','height','codec','mip_levels','tile_mode','name',
                              'image_offset','image_bytes','palette_offset','palette_bytes'):
                    if field not in meta:
                        raise ValueError('Incomplete texture metadata')
                w, height = meta['width'], meta['height']
                if type(w) is not int or type(height) is not int or w < 1 or height < 1 or w > 8192 or height > 8192:
                    raise ValueError('Invalid source image dimensions')
                if not isinstance(meta['name'], bytes) or not meta['name']:
                    raise ValueError('Missing source texture name')
                if meta['image_bytes'] <= 0 or meta['image_offset'] < 0 or meta['palette_offset'] < 0:
                    raise ValueError('Invalid pixel-range provenance')
                current[h] = dict(meta)
                self._by_hash[h][section] = current[h]
            self._by_section[section] = current
        # Same name-hash is not proof that names/codecs/modes are interchangeable.
        # Reject ambiguous identity conflicts, but preserve legitimate differences
        # in dimensions, offsets, encoded byte sizes and mip counts.
        for versions in self._by_hash.values():
            if len(versions) < 2:
                continue
            common = {(m['name'],m['codec'],m['tile_mode']) for m in versions.values()}
            if len(common) != 1:
                raise ValueError('Same texture hash has incompatible identity metadata')

    def resolve(self, identity, section=None):
        """Require an explicit source section whenever versions are ambiguous."""
        candidates = self._by_hash.get(identity)
        if not candidates:
            raise KeyError('Texture hash is not present in source registry')
        if section is None:
            if len(candidates) != 1:
                raise ValueError('Ambiguous texture variants: source section required')
            return next(iter(candidates.values())).copy()
        if type(section) is not int or section not in candidates:
            raise KeyError('Texture is not supplied by requested source section')
        return candidates[section].copy()

    def coverage(self, model_texture_tables, source_section=None):
        """Report coverage without resolving or exposing source hashes.

        The return does not imply the texture is resident in the game runtime.
        """
        if not model_texture_tables:
            raise ValueError('Missing source model texture tables')
        occurrences = []
        for table in model_texture_tables:
            if not table or any(type(h) is not int or h <= 0 for h in table):
                raise ValueError('Invalid model texture references')
            occurrences.extend(table)
        distinct = set(occurrences)
        available = sum(h in self._by_hash for h in distinct)
        local = (None if source_section is None else
                 sum(h in self._by_section.get(source_section, {}) for h in distinct))
        ambiguous = sum(len(self._by_hash[h]) > 1 for h in distinct if h in self._by_hash)
        return {'reference_occurrences':len(occurrences),
                'distinct_referenced_hashes':len(distinct),
                'hashes_present_anywhere_in_examined_sections':available,
                'hashes_not_present_in_examined_sections':len(distinct)-available,
                'hashes_with_multiple_variants':ambiguous,
                'hashes_present_in_requested_section':local}

    def summary(self):
        variants = [x for x in self._by_hash.values() if len(x) > 1]
        strict_sizes = sum(len({(m['width'],m['height']) for m in v.values()}) == 1 for v in variants)
        mip_variants = sum(len({m['mip_levels'] for m in v.values()}) > 1 for v in variants)
        return {'source_sections':len(self._by_section),
                'texture_record_occurrences':sum(len(v) for v in self._by_section.values()),
                'distinct_texture_hashes':len(self._by_hash),
                'hashes_with_multiple_section_variants':len(variants),
                'multi_section_hashes_with_identical_dimensions':strict_sizes,
                'multi_section_hashes_with_different_mip_counts':mip_variants,
                'section_record_counts':{str(k):len(v) for k,v in sorted(self._by_section.items())},
                'all_reused_identity_names_codecs_and_modes_agree':True,
                'selection_requires_section_for_ambiguous_identity':True}


def _section_rows(bundle, stream_size):
    marker = struct.pack('<I', SECTION_TABLE_ID)
    at = bundle.find(marker)
    if at < 0 or at + 8 > len(bundle):
        raise ValueError('Missing stream section table')
    length = struct.unpack_from('<I', bundle, at + 4)[0]
    if length < ROW_SIZE or length % ROW_SIZE or at + 8 + length > len(bundle):
        raise ValueError('Malformed stream section table')
    payload = bundle[at+8:at+8+length]
    out = {}
    for i in range(0, len(payload), ROW_SIZE):
        sec = struct.unpack_from('<h', payload, i + 8)[0]
        off, size = struct.unpack_from('<II', payload, i + 0x14)
        if sec in out or sec <= 0 or size <= 0 or off + size > stream_size:
            raise ValueError('Duplicate, invalid or out-of-range streaming section')
        out[sec] = (off,size)
    return out


def analyze_undercover_archive(path):
    """Read source sections 241 and 3401 only; never serialize texture records."""
    with zipfile.ZipFile(path) as z:
        bun_name='TRACKS/L2RB.BUN'
        stream_name='TRACKS/STREAML2RB.BUN'
        if z.getinfo(bun_name).file_size > MAX_SMALL_BUN or z.getinfo(stream_name).file_size > MAX_TRACKS_STREAM:
            raise ValueError('Source archive member exceeds configured safety limit')
        bun=z.read(bun_name)
        stream=z.read(stream_name)
    rows=_section_rows(bun,len(stream))
    textures={}
    for section in (241,3401):
        if section not in rows:
            raise ValueError('Missing required donor texture section')
        offset,length=rows[section]
        record=parse_pack(stream[offset:offset+length],'ps2')
        textures[section]=record['records']
    registry=TextureVariantRegistry(textures)
    summary=registry.summary()
    shared=set(textures[241]) & set(textures[3401])
    summary['shared_hashes_with_section_241_at_least_as_large_in_each_axis']=sum(
        textures[241][h]['width'] >= textures[3401][h]['width'] and
        textures[241][h]['height'] >= textures[3401][h]['height'] for h in shared)
    summary['shared_hashes_with_strictly_larger_241_dimensions']=sum(
        textures[241][h]['width'] > textures[3401][h]['width'] or
        textures[241][h]['height'] > textures[3401][h]['height'] for h in shared)
    return {'undercover_ps2':summary,
            'limits':('Section-aware source texture identity and offset metadata only. '
                      'No PS2 pixel deswizzle, palette/render equivalence, GPU texture '
                      'writer or Carbon PC runtime registration claimed.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(analyze_undercover_archive(args.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
