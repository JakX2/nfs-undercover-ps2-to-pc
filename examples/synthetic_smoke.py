#!/usr/bin/env python3
"""Asset-free quickstart: run both Carbon research probes on SYNTHETIC data.

No NFS game files are accessed, installed, patched or distributed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import carbon_chunk_probe
import carbon_pe_preflight


def chunk(tag: int, payload: bytes) -> bytes:
    return struct.pack("<II",tag,len(payload))+payload


def make_fake_carbon_stream() -> bytes:
    # Deliberately synthetic EA-shaped headers, NOT an actual game sector.
    scene_header=chunk(0x34101,b"SYNTHETIC_SCENE")
    root=chunk(carbon_chunk_probe.ROOT,scene_header)
    master=chunk(carbon_chunk_probe.MASTER,bytes(48))
    return b"not a game archive:"+root+b"unrelated filler"+master


def make_fake_pe32() -> bytes:
    # Synthetic 32-bit PE whose .text covers the old plugin's four addresses.
    data=bytearray(0x200+0x9000)
    data[0:2]=b"MZ"
    struct.pack_into("<I",data,0x3C,0x80)
    data[0x80:0x84]=b"PE\x00\x00"
    struct.pack_into("<HHIIIHH",data,0x84,0x14C,1,0,0,0,0xE0,0x0102)
    struct.pack_into("<H",data,0x98,0x10B)
    struct.pack_into("<I",data,0x98+28,0x400000)
    struct.pack_into("<I",data,0x98+56,0x2C0000)
    sec=0x98+0xE0
    data[sec:sec+8]=b".text\x00\x00\x00"
    struct.pack_into("<IIII",data,sec+8,0x9000,0x2B0000,0x9000,0x200)
    struct.pack_into("<I",data,sec+36,0x60000020)
    data[0x200:]=b"\xCC"*0x9000
    return bytes(data)


def run_demo() -> dict:
    with tempfile.TemporaryDirectory(prefix="synthetic_nfs_research_") as temp:
        base=Path(temp)
        stream=make_fake_carbon_stream()
        exe=make_fake_pe32()
        stream_file=base/"FAKE_GAME_ARCHIVE.bin"
        exe_file=base/"FAKE_NFSC_NOT_RUN.exe"
        stream_file.write_bytes(stream)
        exe_file.write_bytes(exe)
        inventory=carbon_chunk_probe.scan_archive(
            stream_file,
            expected_sha256=hashlib.sha256(stream).hexdigest(),
            orders=("little",),
            modes=("payload",),
        )
        mapping=carbon_pe_preflight.inspect_executable(
            exe_file,
            expected_sha256=hashlib.sha256(exe).hexdigest(),
        )
        assert inventory["candidate_variants"] == 2
        assert len(mapping["historical_address_checks"]) == 4
        # Reports only derived synthetic counts, never source binary data.
        return {
            "fixture_data":"SYNTHETIC_ONLY",
            "archive_candidates_found":inventory["candidate_variants"],
            "candidate_tag_ids":[r["tag"] for r in inventory["candidates"]],
            "archive_digest_checked":inventory["trusted_expected_archive_digest_checked"],
            "old_public_hook_addresses_in_executable_sections":sum(
                x["file_backed"] and x["in_executable_section"]
                for x in mapping["historical_address_checks"].values()),
            "pe_digest_checked":mapping["expected_executable_sha256_guard_applied"],
            "real_original_game_input_used":False,
            "carbon_game_runtime_verified":False,
            "safe_to_install":False,
        }


if __name__=="__main__":
    print(json.dumps(run_demo(),indent=2,sort_keys=True))
