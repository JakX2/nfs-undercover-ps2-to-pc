#!/usr/bin/env python3
"""Find possible direct writes to the authenticated Wii SC retry-status SDA byte.

This is a *conservative lexical scan*, not a data-flow proof. It includes D-form
stores whose base register is r13 and whose displacement covers the one-byte
status field. Indexed stores, aliased pointers and compiler inline data cannot
be resolved by this scan. Original game bytes and translated code stay private.
"""
import argparse
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

STATUS_READ_PC = 0x8052F84C
STATUS_OFFSET = -3176
STATUS_BASE = 13
STATUS_REGISTER = 29
STATUS_LOAD_OP = 34  # original instruction is lbz r29, -3176(r13)
MAX_PUBLIC_SITES = 16
STORES = {
    36: ("stw", 4), 37: ("stwu", 4),
    38: ("stb", 1), 39: ("stbu", 1),
    44: ("sth", 2), 45: ("sthu", 2),
    52: ("stfs", 4), 53: ("stfsu", 4),
    54: ("stfd", 8), 55: ("stfdu", 8),
}

@dataclass(frozen=True, order=True)
class StoreSite:
    pc: int
    kind: str
    width: int
    offset: int


def signed16(n: int) -> int:
    n &= 0xFFFF
    return n - 0x10000 if n & 0x8000 else n


def code_sections(raw: bytes):
    """Return validated, nonoverlapping (guest address, bytes) DOL text ranges."""
    if len(raw) < 256:
        raise ValueError("truncated Wii DOL header")
    ranges = []
    file_ranges = []
    for i in range(7):
        off = struct.unpack_from(">I", raw, i * 4)[0]
        pc = struct.unpack_from(">I", raw, 0x48 + i * 4)[0]
        size = struct.unpack_from(">I", raw, 0x90 + i * 4)[0]
        if size == 0:
            continue
        if off < 256 or (off | pc | size) & 3 or off + size > len(raw) or pc + size > 0x100000000:
            raise ValueError("invalid Wii DOL text section geometry")
        if any(pc < e and b < pc + size for b, e in ranges):
            raise ValueError("overlapping Wii guest text ranges")
        if any(off < e and b < off + size for b, e in file_ranges):
            raise ValueError("overlapping Wii DOL file text ranges")
        ranges.append((pc, pc + size))
        file_ranges.append((off, off + size))
        yield (pc, raw[off:off + size])
    if not ranges:
        raise ValueError("no Wii DOL text sections")


def verify_status_load(word: int):
    if (word >> 26 != STATUS_LOAD_OP or
        (word >> 21) & 31 != STATUS_REGISTER or
        (word >> 16) & 31 != STATUS_BASE or
        signed16(word) != STATUS_OFFSET):
        raise ValueError("authenticated SC status read shape differs")


def direct_writer_sites(raw: bytes) -> list[StoreSite]:
    result = []
    for base, body in code_sections(raw):
        for index in range(0, len(body), 4):
            word = struct.unpack_from(">I", body, index)[0]
            op = word >> 26
            if (word >> 16) & 31 != STATUS_BASE:
                continue
            if op == 47:  # stmw: register-number-dependent length
                kind = "stmw"
                width = 4 * (32 - ((word >> 21) & 31))
            elif op in STORES:
                kind, width = STORES[op]
            else:
                continue
            off = signed16(word)
            if off <= STATUS_OFFSET < off + width:
                result.append(StoreSite(base + index, kind, width, off))
    return sorted(result)


def report(sites: list[StoreSite]) -> list[str]:
    lines = ["SC_SDA_WRITERS direct_candidates=%d shown=%d truncated=%d indexed_unresolved=1" %
             (len(sites), min(len(sites), MAX_PUBLIC_SITES), int(len(sites) > MAX_PUBLIC_SITES))]
    for site in sites[:MAX_PUBLIC_SITES]:
        lines.append("SC_SDA_WRITER pc=%08x kind=%s width=%d delta=%d" %
                     (site.pc, site.kind, site.width, site.offset - STATUS_OFFSET))
    return lines


def audit_owner(raw: bytes) -> list[StoreSite]:
    from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
    from diagnose_v131_osinit_retry import CALL, analyze
    from diagnose_v132_sc_status import ENTRY, SIZE, inspect as inspect_sc
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("original Wii owner SHA mismatch")
    loop = analyze(struct.unpack(">IIII", text_at(raw, CALL, 16)))
    if (loop["cmp_reg"], loop["compare_imm"], loop["retry_on_equal"], loop["retry_back"]) != (3, 1, 1, 1):
        raise ValueError("Wii OSInit retry contract differs")
    status = inspect_sc(text_at(raw, ENTRY, SIZE))
    if (status["disable"], status["restore"]) != (1, 1) or \
       (STATUS_READ_PC, STATUS_LOAD_OP, STATUS_BASE, STATUS_OFFSET) not in status["sda_sites"]:
        raise ValueError("Wii SC original status use differs")
    verify_status_load(struct.unpack(">I", text_at(raw, STATUS_READ_PC, 4))[0])
    return direct_writer_sites(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha_authenticated_wii_dol", type=Path)
    args = parser.parse_args()
    try:
        sites = audit_owner(args.sha_authenticated_wii_dol.read_bytes())
    except Exception:
        print("SC_SDA_WRITERS result=failed")
        return 1
    for line in report(sites):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
