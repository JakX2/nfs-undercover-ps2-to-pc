#!/usr/bin/env python3
"""Read-only, version-gated checker for the inferred Carbon PC steering routine."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SHA256 = "baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3"
CALLS = {
    0x006EF5E9: 0x006DFDE0,
    0x006EF63E: 0x006DFDE0,
    0x006EF74E: 0x006A1900,
    0x006EF75A: 0x006E0090,
    0x006EF7EC: 0x0075CF60,
    0x006EF802: 0x006A2250,
    0x006EF841: 0x006EF540,
}
BYTES = {
    0x006EF540: "83ec0c568bf1",
    0x006EF816: "c20400",
    0x006EF819: "cccccccccccccc",
    0x006EF820: "83ec24568bf1",
    0x006DFDE0: "51568b74240c",
    0x006E0090: "56578b7c240c",
    0x006A2250: "0fb65107",
    0x0075CF60: "d905d8cfb400c3",
    0x006EF7B9: "898604010000",
    0x006EF7C0: "899618010000",
}

def sections(data):
    if data[:2] != b"MZ":
        raise ValueError("Not an MZ executable")
    pos = struct.unpack_from("<I", data, 0x3c)[0]
    if data[pos:pos + 4] != b"PE\0\0":
        raise ValueError("Not a PE executable")
    n = struct.unpack_from("<H", data, pos + 6)[0]
    opt_size = struct.unpack_from("<H", data, pos + 20)[0]
    if struct.unpack_from("<H", data, pos + 24)[0] != 0x10b:
        raise ValueError("Not PE32")
    base = struct.unpack_from("<I", data, pos + 52)[0]
    if base != 0x400000:
        raise ValueError("Unexpected image base")
    out = []
    for idx in range(n):
        p = pos + 24 + opt_size + idx * 40
        virtual_size, rva, raw_size, raw_off = struct.unpack_from("<IIII", data, p + 8)
        out.append((base + rva, raw_size, raw_off))
    return out

def at(data, sec, address, n):
    for va, raw_size, raw_offset in sec:
        offset = address - va
        if 0 <= offset and offset + n <= raw_size:
            start = raw_offset + offset
            if start + n <= len(data):
                return data[start:start + n]
    raise ValueError(f"Unmapped address {address:#x}")

def verify(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise ValueError(f"Unsupported NFSC.exe SHA256: {digest}")
    sec = sections(data)
    for address, hx in BYTES.items():
        if at(data, sec, address, len(bytes.fromhex(hx))) != bytes.fromhex(hx):
            raise ValueError(f"Unexpected instruction bytes at {address:#x}")
    for address, target in CALLS.items():
        ins = at(data, sec, address, 5)
        if ins[0] != 0xe8 or address + 5 + struct.unpack("<i", ins[1:])[0] != target:
            raise ValueError(f"Unexpected call at {address:#x}")
    return {"sha256": digest, "function": "0x006EF540", "passed_checks": len(CALLS) + len(BYTES)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="Local, user-owned NFSC.exe")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.exe.read_bytes())
    except (ValueError, OSError, struct.error) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print("PASS:", result)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
