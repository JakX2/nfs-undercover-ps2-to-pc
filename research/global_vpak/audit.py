#!/usr/bin/env python3
"""Read-only three-way VPAK container audit; standard library only.

Usage:
  python research/global_vpak/audit.py CARBON_PC_GLOBAL.zip CARBON_PS2_GLOBAL.zip UNDERCOVER_PS2_GLOBAL.zip

This prints only aggregate statistics and ZIP hashes. It does not export names,
archive members, original game bytes, or patched game data.
"""

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

EDITOR_MARKER = "NFS-VltEd 4.6.0.0 by nfsu360"
MEMBERS = ("GAMEPLAY.BIN", "GAMEPLAY.BAK", "ATTRIBUTES.BIN", "ATTRIBUTES.BAK", "FE_ATTRIB.BIN", "FE_ATTRIB.BAK")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_selected_members(path):
    """Read only relevant ZIP members; reject ambiguous duplicate basenames."""
    with zipfile.ZipFile(path) as archive:
        seen = {}
        entries = [info for info in archive.infolist() if not info.is_dir()]
        for info in entries:
            name = info.filename.rsplit("/", 1)[-1].upper()
            if name in MEMBERS:
                if name in seen:
                    raise ValueError(f"Duplicate ZIP member basename: {name}")
                seen[name] = info
        selected = {name: archive.read(info) for name, info in seen.items()}
        return selected, len(entries)


def string_region(data, offset):
    """Parse a bounded ErtS pool of NUL-separated ASCII strings."""
    if offset < 0 or offset + 8 > len(data) or data[offset:offset + 4] != b"ErtS":
        raise ValueError(f"Missing ErtS block at {offset:#x}")
    (block_size,) = struct.unpack_from("<I", data, offset + 4)
    if block_size < 8 or block_size > len(data) - offset:
        raise ValueError("ErtS block size exceeds input")
    names = []
    for part in data[offset + 8:offset + block_size].split(b"\x00"):
        if not part:
            continue
        if any(byte < 32 or byte > 126 for byte in part):
            raise ValueError("Non-ASCII name in ErtS block")
        names.append(part.decode("ascii"))
    return block_size, names


def require_vpak(data):
    if data[:4] != b"VPAK":
        raise ValueError("Missing VPAK signature")


def parse_gameplay(data):
    """Inspect the index and names. Payload semantics remain unverified."""
    require_vpak(data)
    if len(data) < 16:
        raise ValueError("Truncated VPAK header")
    count, table_end, unknown_word = struct.unpack_from("<III", data, 4)
    if not (0 < count <= 20000 and 16 + count * 20 <= table_end <= len(data)):
        raise ValueError("Invalid gameplay index bounds")
    all_names = []
    previous_aux = table_end
    for index in range(count):
        _cumulative, first_size, _aux_size, text_offset, aux_offset = struct.unpack_from(
            "<IIIII", data, 16 + 20 * index
        )
        if not (previous_aux <= text_offset <= aux_offset <= len(data)):
            raise ValueError(f"Invalid offsets in index entry {index}")
        if first_size > aux_offset - text_offset:
            raise ValueError(f"String payload exceeds index range at entry {index}")
        block_size, names = string_region(data, text_offset)
        if block_size > first_size:
            raise ValueError(f"ErtS block exceeds string payload at entry {index}")
        all_names.extend(names)
        previous_aux = aux_offset
    return {
        "indexed_entries": count,
        "index_end": table_end,
        "unknown_header_word": unknown_word,
        "name_occurrences": len(all_names),
        "distinct_names": len(set(all_names)),
        "editor_marker_occurrences": all_names.count(EDITOR_MARKER),
    }, set(all_names)


def parse_attributes(data):
    """Inspect the leading name pool only, not full attribute records."""
    require_vpak(data)
    _size, names = string_region(data, 0x80)
    return {
        "name_occurrences": len(names),
        "distinct_names": len(set(names)),
        "editor_marker_present": EDITOR_MARKER in names,
    }, set(names)


def overlap(left, right):
    return {
        "shared": len(left & right),
        "left_only": len(left - right),
        "right_only": len(right - left),
    }


def audit(pc, carbon_ps2, undercover_ps2):
    paths = {"carbon_pc": Path(pc), "carbon_ps2": Path(carbon_ps2), "undercover_ps2": Path(undercover_ps2)}
    report = {"sources": {}, "gameplay": {}, "attributes": {}, "comparisons": {}}
    gameplay_names = {}
    attribute_names = {}
    for platform, path in paths.items():
        blobs, total = read_selected_members(path)
        report["sources"][platform] = {"zip_sha256": sha256_file(path), "members": total}
        for member in ("GAMEPLAY.BIN", "GAMEPLAY.BAK"):
            if member not in blobs:
                continue
            key = f"{platform}/{member}"
            report["gameplay"][key], gameplay_names[key] = parse_gameplay(blobs[member])
        for member in ("ATTRIBUTES.BIN", "ATTRIBUTES.BAK", "FE_ATTRIB.BIN", "FE_ATTRIB.BAK"):
            if member not in blobs:
                continue
            key = f"{platform}/{member}"
            report["attributes"][key], attribute_names[key] = parse_attributes(blobs[member])
    for label, left, right in (
        ("pc_active_vs_backup", "carbon_pc/GAMEPLAY.BIN", "carbon_pc/GAMEPLAY.BAK"),
        ("pc_backup_vs_carbon_ps2", "carbon_pc/GAMEPLAY.BAK", "carbon_ps2/GAMEPLAY.BIN"),
        ("undercover_vs_carbon_ps2", "undercover_ps2/GAMEPLAY.BIN", "carbon_ps2/GAMEPLAY.BIN"),
    ):
        report["comparisons"][label] = overlap(gameplay_names[left], gameplay_names[right])
    for field in ("ATTRIBUTES", "FE_ATTRIB"):
        report["comparisons"][f"pc_backup_vs_carbon_ps2_{field}"] = overlap(
            attribute_names[f"carbon_pc/{field}.BAK"],
            attribute_names[f"carbon_ps2/{field}.BIN"],
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carbon_pc_zip")
    parser.add_argument("carbon_ps2_zip")
    parser.add_argument("undercover_ps2_zip")
    args = parser.parse_args()
    print(json.dumps(audit(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == "__main__":
    main()
