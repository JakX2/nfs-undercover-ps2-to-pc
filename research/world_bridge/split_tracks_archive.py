#!/usr/bin/env python3
"""Split a user-owned ZIP into individually downloadable parts, and rejoin it.

Source-only helper for NFS Undercover -> Carbon PC world-streaming research.
No game files or derived game content are bundled with this script.
The manifest records sizes and SHA-256 checksums only. A joined archive must
match the original byte-for-byte before any inspection or research can proceed.

Example:
  python split_tracks_archive.py split TRACKS.zip --output-dir split_tracks --chunk-mib 128
  python split_tracks_archive.py join split_tracks/TRACKS.zip.parts.json --output TRACKS.zip
"""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

MIB = 1024 * 1024
BUF = MIB
FORMAT = "nfs-world-zip-parts-v1"
MAX_CHUNK_MIB = 200


def _is_hex_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _part_name(original, number):
    return f"{original}.part{number:03d}"


def split(source, output_dir, chunk_mib=128):
    """Create raw byte chunks and a manifest; never alter the source ZIP."""
    source, output_dir = Path(source), Path(output_dir)
    if not source.is_file() or not zipfile.is_zipfile(source):
        raise ValueError("Source must be an existing valid ZIP archive")
    if source.name != source.name.strip() or not source.name.endswith(".zip"):
        raise ValueError("Source filename must end with .zip")
    if not isinstance(chunk_mib, int) or not 1 <= chunk_mib <= MAX_CHUNK_MIB:
        raise ValueError("Chunk size must be an integer from 1 to 200 MiB")
    if output_dir.resolve() == source.parent.resolve():
        raise ValueError("Use a separate output directory to avoid collisions")

    limit = chunk_mib * MIB
    total = source.stat().st_size
    if not total:
        raise ValueError("Empty input")
    part_count = (total + limit - 1) // limit
    if part_count >= 1000:
        raise ValueError("Too many parts for the three-digit naming scheme")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{source.name}.parts.json"
    names = [_part_name(source.name, i) for i in range(part_count)]
    for path in [manifest_path, *(output_dir / name for name in names)]:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite: {path.name}")

    parts = []
    original_digest = hashlib.sha256()
    try:
        with source.open("rb") as reader:
            for number, name in enumerate(names):
                path = output_dir / name
                part_digest = hashlib.sha256()
                part_size = 0
                remaining = limit
                with path.open("xb") as writer:
                    while remaining:
                        buf = reader.read(min(BUF, remaining))
                        if not buf:
                            break
                        writer.write(buf)
                        original_digest.update(buf)
                        part_digest.update(buf)
                        part_size += len(buf)
                        remaining -= len(buf)
                if not part_size or (number + 1 < len(names) and part_size != limit):
                    raise ValueError("Unexpected short part")
                parts.append({"name": name, "size": part_size, "sha256": part_digest.hexdigest()})
            if reader.read(1):
                raise ValueError("Source changed while splitting")
        manifest = {"format": FORMAT, "original_name": source.name,
                    "original_bytes": total, "original_sha256": original_digest.hexdigest(),
                    "chunk_mib": chunk_mib, "parts": parts}
        if sum(part["size"] for part in parts) != total:
            raise ValueError("Size mismatch while splitting")
        with manifest_path.open("x", encoding="utf-8") as writer:
            json.dump(manifest, writer, indent=2)
            writer.write("\n")
        return manifest_path
    except Exception:
        for name in names:
            (output_dir / name).unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise


def join(manifest_path, output):
    """Reconstruct only if every part and the whole ZIP match SHA-256."""
    manifest_path, output = Path(manifest_path), Path(output)
    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    original = meta.get("original_name")
    parts = meta.get("parts")
    if meta.get("format") != FORMAT or not isinstance(original, str) or not original.endswith(".zip"):
        raise ValueError("Unrecognized manifest")
    if Path(original).name != original or original in (".zip", "..zip"):
        raise ValueError("Unsafe original filename")
    if not isinstance(parts, list) or not 1 <= len(parts) < 1000:
        raise ValueError("Missing or invalid parts")
    expected_bytes = meta.get("original_bytes")
    if not isinstance(expected_bytes, int) or expected_bytes <= 0 or not _is_hex_sha(meta.get("original_sha256")):
        raise ValueError("Invalid original file fingerprint")
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing output ZIP")
    if not output.parent.is_dir():
        raise ValueError("Output directory does not exist")
    temp_path = output.with_name(output.name + ".rejoining")
    if temp_path.exists():
        raise FileExistsError("Temporary output already exists")

    whole = hashlib.sha256()
    total = 0
    try:
        with temp_path.open("xb") as writer:
            for number, p in enumerate(parts):
                expected_name = _part_name(original, number)
                if not isinstance(p, dict) or p.get("name") != expected_name:
                    raise ValueError("Invalid part sequence or unsafe part filename")
                size = p.get("size")
                if not isinstance(size, int) or not 0 < size <= MAX_CHUNK_MIB * MIB or not _is_hex_sha(p.get("sha256")):
                    raise ValueError("Invalid part size/checksum")
                part_path = manifest_path.parent / expected_name
                digest = hashlib.sha256()
                read_size = 0
                with part_path.open("rb") as reader:
                    while True:
                        block = reader.read(BUF)
                        if not block:
                            break
                        writer.write(block)
                        digest.update(block)
                        whole.update(block)
                        read_size += len(block)
                        total += len(block)
                if read_size != size or digest.hexdigest() != p["sha256"]:
                    raise ValueError(f"Part {number} failed size/SHA-256 validation")
        if total != expected_bytes or whole.hexdigest() != meta["original_sha256"]:
            raise ValueError("Reassembled ZIP differs from original")
        if not zipfile.is_zipfile(temp_path):
            raise ValueError("Reassembled bytes are not a ZIP")
        temp_path.rename(output)
        return output
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ps = commands.add_parser("split", help="Create separate parts each under the Drive size limit")
    ps.add_argument("source", type=Path)
    ps.add_argument("--output-dir", required=True, type=Path)
    ps.add_argument("--chunk-mib", type=int, default=128)
    pj = commands.add_parser("join", help="Rebuild and SHA-256-verify all parts")
    pj.add_argument("manifest", type=Path)
    pj.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "split":
        result = split(args.source, args.output_dir, args.chunk_mib)
        print(f"Parts and checksums created: {result}")
    else:
        result = join(args.manifest, args.output)
        print(f"Byte-identical original ZIP reconstructed: {result}")


if __name__ == "__main__":
    main()
