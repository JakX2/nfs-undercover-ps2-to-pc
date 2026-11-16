#!/usr/bin/env python3
"""Owner-local Undercover Wii ELF/DOL recompilation preflight.

No game data is included. Generates local ELF-derived function map and a
WiiCompiled generic-DOL manifest; never publishes/distributes these outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


class PreflightError(ValueError):
    pass


def checked_slice(blob: bytes, off: int, size: int) -> bytes:
    if off < 0 or size < 0 or off > len(blob) or size > len(blob) - off:
        raise PreflightError(f"out-of-bounds ELF/DOL range: {off}, {size}")
    return blob[off:off + size]


def parse_elf(blob: bytes):
    if len(blob) < 52 or blob[:7] != b"\x7fELF\x01\x02\x01":
        raise PreflightError("expected big-endian ELF32")
    (etype, machine, version, entry, phoff, shoff, flags, ehsize, phentsize,
     phnum, shentsize, shnum, shstrndx) = struct.unpack_from(">HHIIIIIHHHHHH", blob, 16)
    if etype != 2 or machine != 20 or version != 1 or shentsize != 40:
        raise PreflightError("expected PPC ELF32 executable with 40-byte section headers")
    if shnum == 0 or shnum > 4096:
        raise PreflightError("invalid section count")
    hdrs = checked_slice(blob, shoff, shnum * 40)
    sections = [dict(zip(("name", "type", "flags", "addr", "off", "size", "link", "info", "align", "entsize"),
                        struct.unpack_from(">10I", hdrs, 40 * i))) for i in range(shnum)]
    if shstrndx >= shnum:
        raise PreflightError("invalid section-name table")
    shstr = checked_slice(blob, sections[shstrndx]["off"], sections[shstrndx]["size"])
    for sec in sections:
        start = sec["name"]
        sec["label"] = shstr[start:shstr.find(b"\0", start)].decode("ascii", errors="replace") if start < len(shstr) else "?"
        if sec["type"] != 8:  # SHT_NOBITS reserves virtual memory only
            checked_slice(blob, sec["off"], sec["size"])

    symbols = []
    for sec in sections:
        if sec["type"] != 2:  # SHT_SYMTAB
            continue
        if sec["link"] >= shnum or sec["entsize"] != 16 or sec["size"] % 16:
            raise PreflightError("invalid symbol table linkage or entry stride")
        strings = checked_slice(blob, sections[sec["link"]]["off"], sections[sec["link"]]["size"])
        data = checked_slice(blob, sec["off"], sec["size"])
        for off in range(0, len(data), 16):
            nameoff, addr, size, info, other, shndx = struct.unpack_from(">IIIBBH", data, off)
            if (info & 15) != 2 or not size or shndx >= shnum:
                continue
            target = sections[shndx]
            if target["flags"] & 0x4 == 0 or not (target["addr"] <= addr and addr + size <= target["addr"] + target["size"]):
                continue
            if nameoff >= len(strings):
                raise PreflightError("invalid symbol name offset")
            end = strings.find(b"\0", nameoff)
            if end < 0:
                raise PreflightError("unterminated symbol")
            name = strings[nameoff:end].decode("utf-8", errors="replace")
            symbols.append((addr, size, name, (info >> 4)))
    return {"entry": entry, "sections": sections, "functions": symbols, "blob": blob}


def parse_dol(blob: bytes):
    if len(blob) < 0x100:
        raise PreflightError("DOL too short")
    off = struct.unpack_from(">18I", blob, 0x00)
    va = struct.unpack_from(">18I", blob, 0x48)
    size = struct.unpack_from(">18I", blob, 0x90)
    entry = struct.unpack_from(">I", blob, 0xE0)[0]
    regions = []
    for i, (o, a, n) in enumerate(zip(off, va, size)):
        if n:
            checked_slice(blob, o, n)
            if a + n > 0x100000000:
                raise PreflightError("DOL region address overflow")
            regions.append({"index": i, "off": o, "addr": a, "size": n})
    return {"entry": entry, "regions": regions, "blob": blob}


def verify_elf_dol(elf, dol):
    if elf["entry"] != dol["entry"]:
        raise PreflightError("ELF/DOL entrypoint disagreement")
    original_bytes = 0
    for r in dol["regions"]:
        # DOL loader can group ELF sections and include only zero alignment padding.
        a, n = r["addr"], r["size"]
        relevant = sorted((s for s in elf["sections"] if s["type"] == 1 and s["flags"] & 2
                           and a <= s["addr"] and s["addr"] + s["size"] <= a + n and s["size"]),
                          key=lambda s: s["addr"])
        if not relevant:
            raise PreflightError(f"no matching ELF sections for DOL region {r['index']}")
        full = bytearray(n)
        filled = bytearray(n)
        for s in relevant:
            delta = s["addr"] - a
            if any(filled[delta:delta + s["size"]]):
                raise PreflightError("overlapping ELF sections")
            original = checked_slice(elf["blob"], s["off"], s["size"])
            full[delta:delta + s["size"]] = original
            filled[delta:delta + s["size"]] = b"\x01" * s["size"]
            original_bytes += s["size"]
        if bytes(full) != checked_slice(dol["blob"], r["off"], n):
            raise PreflightError(f"ELF/DOL bytes differ at DOL region {r['index']}")
    return original_bytes


def find_sda_bases(elf):
    regs = [f for f in elf["functions"] if f[2] == "__init_registers"]
    if len(regs) != 1:
        raise PreflightError("unique __init_registers symbol not found")
    start, length, _, _ = regs[0]
    matches = [s for s in elf["sections"] if s["type"] == 1 and s["flags"] & 4
               and s["addr"] <= start and start + length <= s["addr"] + s["size"]]
    if len(matches) != 1:
        raise PreflightError("__init_registers not within a unique executable section")
    sec = matches[0]
    code = checked_slice(elf["blob"], sec["off"] + start - sec["addr"], length)
    words = [int.from_bytes(code[i:i + 4], "big") for i in range(0, len(code) - 3, 4)]
    out = {}
    for i in range(len(words) - 1):
        hi, lo = words[i:i + 2]
        opcode, rt, ra = hi >> 26, (hi >> 21) & 31, (hi >> 16) & 31
        lo_opcode, lo_rt, lo_ra = lo >> 26, (lo >> 21) & 31, (lo >> 16) & 31
        # lis rN, hi16; ori rN, rN, lo16
        if opcode == 15 and ra == 0 and lo_opcode == 24 and lo_rt == rt and lo_ra == rt and rt in (2, 13):
            if rt in out:
                raise PreflightError("ambiguous SDA init pair")
            out[rt] = ((hi & 0xFFFF) << 16) | (lo & 0xFFFF)
    if 2 not in out or 13 not in out:
        raise PreflightError("unable to derive both r2 and r13 SDA bases")
    return out


def safe_symbol(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)[:100] or "anonymous"


def emit(elf_blob: bytes, dol_blob: bytes, output: Path) -> dict:
    elf, dol = parse_elf(elf_blob), parse_dol(dol_blob)
    verified_bytes = verify_elf_dol(elf, dol)
    sda = find_sda_bases(elf)
    symbols = elf["functions"]
    funcs = {}
    for addr, size, name, binding in symbols:
        candidate = (binding == 1, len(name) > 0, -len(name), name)
        if addr not in funcs or candidate > funcs[addr][0]:
            funcs[addr] = (candidate, name)
    output.mkdir(parents=True, exist_ok=True)
    fmap = output / "private_function_map.txt"
    fmap.write_text("".join(f"0x{addr:08X} fn_{addr:08X}_{safe_symbol(name)}\n"
                            for addr, (_, name) in sorted(funcs.items())), encoding="utf-8")
    sha = hashlib.sha256(dol_blob).hexdigest()
    manifest = output / "undercover-wii-generic.yml"
    manifest.write_text(f"""schema_version: 1
workspace_root: .
project:
  id: nfs-undercover-wii-preflight
  display_name: NFS Undercover Wii translation preflight
memory:
  base: 0x80000000
  size: 0x01800000
  sda_base: 0x{sda[13]:08X}
  sda2_base: 0x{sda[2]:08X}
inputs:
  dol:
    path: \"%RECOMP_UC_WII_DOL%\"
    sha256: \"{sha}\"
translation:
  allow_unsupported_instructions: false
  function_map:
    path: private_function_map.txt
runtime:
  native_abi_directories: []
output:
  root: build/undercover-wii
  functions: functions
  runtime_config: RuntimeConfig.h
  data_initializer: data_sections_init.cpp
  base_manifest: base/base_manifest.json
""", encoding="utf-8")
    info = {
        "elf_sha256": hashlib.sha256(elf_blob).hexdigest(),
        "dol_sha256": sha,
        "elf_entry": f"0x{elf['entry']:08X}",
        "dol_regions": len(dol["regions"]),
        "dol_nonpadding_bytes_verified": verified_bytes,
        "elf_function_symbols": len(symbols),
        "unique_function_addresses": len(funcs),
        "r13_sda_base": f"0x{sda[13]:08X}",
        "r2_sda2_base": f"0x{sda[2]:08X}",
        "toolchain_execution": "not attempted"
    }
    (output / "preflight_summary.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--dol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True,
                    help="Private local directory; do not commit generated artifacts")
    a = ap.parse_args()
    try:
        print(json.dumps(emit(a.elf.read_bytes(), a.dol.read_bytes(), a.output), indent=2))
    except PreflightError as exc:
        ap.exit(1, f"preflight failed: {exc}\n")

if __name__ == "__main__":
    main()
