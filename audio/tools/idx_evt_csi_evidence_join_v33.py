#!/usr/bin/env python3
"""V33: evidence-preserving IDX -> EVT -> CSI attribution for EA SCHl candidates.

This DOES NOT parse undocumented IDX/EVT/CSI binary layouts. It joins three
OPERATOR-SUPPLIED, explicitly exported CSV tables with V31 scanner JSON and
optional V32 real-decoder triage JSON. Offsets and lengths are cross-checked.

Labels like "police" are assertions in the supplied CSI CSV, NOT detected
dialogue or independently confirmed provenance. No police voice, game bank,
or Carbon PC playback is considered proven by a successful join.

No game media is read, converted or written; result is metadata-only JSON.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_ROWS = 200_000
MAX_SCAN_CANDIDATES = 20_000
MAX_LABEL = 200
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
INT_VALUE = re.compile(r"^(?:0[xX][0-9a-fA-F]+|[0-9]+)$")


class AttributionError(Exception):
    pass


def number(value, field: str, *, allow_zero: bool = True, maximum: int = 2**63 - 1) -> int:
    if isinstance(value, bool):
        raise AttributionError(f"Invalid boolean for {field}")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and INT_VALUE.fullmatch(value.strip()):
        word = value.strip()
        parsed = int(word, 16 if word.lower().startswith("0x") else 10)
    else:
        raise AttributionError(f"Invalid integer field: {field}")
    if parsed < (0 if allow_zero else 1) or parsed > maximum:
        raise AttributionError(f"Out-of-range field: {field}")
    return parsed


def safe_name(value: str, field: str) -> str:
    value = value.strip()
    if not value or len(value) > MAX_LABEL or any(ord(ch) < 32 for ch in value):
        raise AttributionError(f"Invalid {field}")
    return value


def load_json(path: Path, fmt: str) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise AttributionError(f"Missing/oversized JSON: {fmt}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise AttributionError(f"Invalid JSON: {fmt}") from exc
    if not isinstance(data, dict) or data.get("format") != fmt:
        raise AttributionError(f"Incorrect format tag: {fmt}")
    return data


def read_csv(path: Path, columns: set[str]) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise AttributionError("Missing or oversized source CSV")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not columns.issubset(set(reader.fieldnames)):
                raise AttributionError("CSV missing mandatory columns: " + ", ".join(sorted(columns)))
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise AttributionError("Duplicate CSV header name")
            rows = []
            for row in reader:
                if len(rows) >= MAX_ROWS:
                    raise AttributionError("CSV row count exceeds safety bound")
                if None in row or any(v is None for v in row.values()):
                    raise AttributionError("Malformed CSV row")
                rows.append(row)
            return rows
    except (UnicodeError, csv.Error) as exc:
        raise AttributionError("Invalid CSV encoding or quoting") from exc


def load_idx(path: Path) -> list[dict]:
    # stream_length is required as a COLUMN but may be blank: an IDX exported
    # with offsets only must never be presented as a full offset+length match.
    rows = read_csv(path, {"group_id", "substream", "big_offset", "stream_length"})
    records = []
    seen = set()
    for row in rows:
        group = number(row["group_id"], "IDX group_id", maximum=2**32 - 1)
        substream = number(row["substream"], "IDX substream", maximum=2**32 - 1)
        offset = number(row["big_offset"], "IDX big_offset")
        length_text = row["stream_length"].strip()
        length = number(length_text, "IDX stream_length", allow_zero=False) if length_text else None
        key = (group, substream)
        if key in seen:
            raise AttributionError("Duplicate IDX (group_id, substream) mapping")
        seen.add(key)
        records.append({
            "group_id": group, "substream": substream,
            "big_offset": offset, "stream_length": length,
        })
    return records


def load_evt(path: Path) -> list[dict]:
    rows = read_csv(path, {"event_id", "group_id"})
    records = []
    seen = set()
    for row in rows:
        event = safe_name(row["event_id"], "EVT event_id")
        group = number(row["group_id"], "EVT group_id", maximum=2**32 - 1)
        key = (event, group)
        if key in seen:
            raise AttributionError("Duplicate EVT event-to-group link")
        seen.add(key)
        records.append({"event_id": event, "group_id": group})
    return records


def load_csi(path: Path) -> list[dict]:
    # "police" is classification in operator-supplied export, not proof
    # that a recording has been heard or recognized in the actual game.
    rows = read_csv(path, {"event_id", "event_name", "classification"})
    records = []
    seen = set()
    for row in rows:
        event = safe_name(row["event_id"], "CSI event_id")
        name = safe_name(row["event_name"], "CSI event_name")
        label = row["classification"].strip().lower()
        if label not in {"police", "other", "unknown"}:
            raise AttributionError("CSI classification must be police, other or unknown")
        if event in seen:
            raise AttributionError("Duplicate CSI event ID")
        seen.add(event)
        records.append({
            "event_id": event, "event_name": name,
            "classification_supplied": label,
        })
    return records


def load_scan(path: Path) -> list[dict]:
    data = load_json(path, "NFS_AUDIO_V31_BIG_SCHL_SCANNER")
    raw = data.get("candidates")
    if not isinstance(raw, list) or len(raw) > MAX_SCAN_CANDIDATES:
        raise AttributionError("Invalid V31 candidate list")
    records = []
    seen = set()
    for value in raw:
        if not isinstance(value, dict):
            raise AttributionError("Malformed V31 scan entry")
        offset = number(value.get("offset"), "scan offset")
        size = number(value.get("length"), "scan stream length", allow_zero=False)
        samples = number(value.get("samples"), "scan sample count", allow_zero=False)
        blocks = number(value.get("blocks"), "scan block count", allow_zero=False)
        if offset in seen:
            raise AttributionError("Duplicate V31 candidate offset")
        seen.add(offset)
        records.append({
            "offset": offset, "length": size,
            "samples": samples, "blocks": blocks,
        })
    return records


def load_triage(path: Path | None) -> dict[int, dict]:
    if path is None:
        return {}
    data = load_json(path, "NFS_AUDIO_V32_PRIVATE_BIG_DECODE_TRIAGE")
    raw = data.get("outcomes")
    if not isinstance(raw, list) or len(raw) > MAX_SCAN_CANDIDATES:
        raise AttributionError("Invalid V32 outcomes")
    entries = {}
    for value in raw:
        if not isinstance(value, dict):
            raise AttributionError("Malformed V32 result")
        offset = number(value.get("offset"), "V32 offset")
        size = number(value.get("source_bytes"), "V32 size", allow_zero=False)
        status = value.get("status")
        if status not in {"independent_decoder_pcm_equal", "decode_or_validation_failed"}:
            raise AttributionError("Unknown V32 decoder status")
        if offset in entries:
            raise AttributionError("Duplicate V32 triage offset")
        item = {"offset": offset, "source_bytes": size, "status": status}
        if status == "independent_decoder_pcm_equal":
            a, b = value.get("original_pcm_sha256"), value.get("converted_pcm_sha256")
            if not isinstance(a, str) or not isinstance(b, str) or not HEX_SHA.fullmatch(a) or not HEX_SHA.fullmatch(b):
                raise AttributionError("Missing or invalid V32 PCM hashes")
            if a != b:
                raise AttributionError("Contradictory V32 equal-PCM status with unequal hashes")
            item["pcm_sha256"] = a
        entries[offset] = item
    return entries


def correlate(scan: list[dict], triage: dict[int, dict], idx: list[dict],
              evt: list[dict], csi: list[dict]) -> dict:
    scan_by_offset = {s["offset"]: s for s in scan}
    if len(scan_by_offset) != len(scan):
        raise AttributionError("Duplicate scan offsets")
    for ofs, candidate in triage.items():
        source = scan_by_offset.get(ofs)
        if source is None or candidate["source_bytes"] != source["length"]:
            raise AttributionError("V32 result not aligned with V31 scan offset/length")

    idx_by_offset = defaultdict(list)
    for entry in idx:
        idx_by_offset[entry["big_offset"]].append(entry)

    event_by_group = defaultdict(list)
    for edge in evt:
        event_by_group[edge["group_id"]].append(edge["event_id"])
    csi_by_id = {entry["event_id"]: entry for entry in csi}

    results = []
    counts = Counter()
    for item in sorted(scan, key=lambda x: x["offset"]):
        matches = []
        for index in sorted(idx_by_offset[item["offset"]],
                            key=lambda x: (x["group_id"], x["substream"])):
            length = index["stream_length"]
            strength = ("offset_only" if length is None
                        else "offset_and_length" if length == item["length"]
                        else "offset_but_length_mismatch")
            events = []
            if strength != "offset_but_length_mismatch":
                for eid in sorted(set(event_by_group[index["group_id"]])):
                    named = csi_by_id.get(eid)
                    events.append({
                        "event_id": eid,
                        "event_name": named["event_name"] if named else None,
                        "classification_supplied": (
                            named["classification_supplied"] if named else None
                        ),
                        "csi_name_present": named is not None,
                    })
            matches.append({
                "group_id": index["group_id"],
                "substream": index["substream"],
                "idx_stream_length": length,
                "idx_match": strength,
                "event_links": events,
            })
        decoded = triage.get(item["offset"])
        status = decoded["status"] if decoded else "not_decoder_tested"
        exact_named_police = [
            (m, e) for m in matches
            if m["idx_match"] == "offset_and_length"
            for e in m["event_links"]
            if e["csi_name_present"] and e["classification_supplied"] == "police"
        ]
        if exact_named_police:
            counts["exact_idx_evt_csi_police_labeled"] += 1
        if status == "independent_decoder_pcm_equal":
            counts["real_decoder_pcm_equal"] += 1
        if exact_named_police and status == "independent_decoder_pcm_equal":
            counts["pcm_equal_and_operator_police_labeled"] += 1
        if matches:
            counts["offset_has_idx_entry"] += 1
        if any(m["idx_match"] == "offset_and_length" for m in matches):
            counts["has_exact_idx_offset_and_length"] += 1
        if len(matches) > 1:
            counts["multiple_idx_entries_at_same_offset"] += 1
        if any(m["idx_match"] == "offset_but_length_mismatch" for m in matches):
            counts["idx_length_mismatch"] += 1

        results.append({
            **item,
            "index_matches": matches,
            "decoder_pcm_status": status,
            "decoder_pcm_sha256": decoded.get("pcm_sha256") if decoded else None,
            "operator_police_labeled_event_candidates": len(exact_named_police),
            # These remain false even when supplied exports line up.
            "original_game_provenance_independently_verified": False,
            "actual_police_voice_heard_or_confirmed": False,
            "carbon_pc_runtime_verified": False,
        })

    return {
        "format": "NFS_AUDIO_V33_IDX_EVT_CSI_EVIDENCE_JOIN",
        "research_only": True,
        "input_basis": "operator_exported_CSV_and_local_V31_V32_reports",
        "joined_candidates": len(results),
        "counts": dict(sorted(counts.items())),
        "candidates": results,
        "idx_evt_csi_binary_parsers_executed": False,
        "original_game_provenance_independently_verified": False,
        "actual_police_voice_heard_or_confirmed": False,
        "carbon_pc_runtime_verified": False,
    }


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def make_report(scan: Path, idx: Path, evt: Path, csi: Path,
                triage: Path | None = None) -> dict:
    parsed = correlate(
        load_scan(scan), load_triage(triage),
        load_idx(idx), load_evt(evt), load_csi(csi),
    )
    parsed["input_sha256"] = {
        "v31_scan_json": sha256_file(scan),
        "v32_triage_json": sha256_file(triage) if triage else None,
        "idx_export_csv": sha256_file(idx),
        "evt_export_csv": sha256_file(evt),
        "csi_export_csv": sha256_file(csi),
    }
    return parsed


def self_test() -> dict:
    """Tiny source-free fixture, proves join graph and ambiguity preservation."""
    scans = [{"offset": 24, "length": 96, "samples": 432, "blocks": 1},
             {"offset": 300, "length": 144, "samples": 864, "blocks": 2}]
    hashes = "a" * 64
    triage = {24: {"offset": 24, "source_bytes": 96,
                   "status": "independent_decoder_pcm_equal", "pcm_sha256": hashes}}
    idx = [{"group_id": 42, "substream": 2, "big_offset": 24, "stream_length": 96},
           {"group_id": 43, "substream": 0, "big_offset": 300, "stream_length": None}]
    evt = [{"event_id": "E_TEST_POLICE", "group_id": 42},
           {"event_id": "E_TEST_OTHER", "group_id": 43}]
    csi = [{"event_id": "E_TEST_POLICE", "event_name": "Original synthetic candidate",
            "classification_supplied": "police"},
           {"event_id": "E_TEST_OTHER", "event_name": "Other synthetic event",
            "classification_supplied": "other"}]
    report = correlate(scans, triage, idx, evt, csi)
    if report["counts"].get("pcm_equal_and_operator_police_labeled") != 1:
        raise AttributionError("Synthetic complete graph did not join")
    if report["candidates"][1]["index_matches"][0]["idx_match"] != "offset_only":
        raise AttributionError("Offset-only evidence was overstated")
    if report["actual_police_voice_heard_or_confirmed"]:
        raise AttributionError("Synthetic fixture cannot confirm police voice")
    return {
        "format": "NFS_AUDIO_V33_SYNTHETIC_JOIN_SELFTEST",
        "joined_candidates": 2,
        "exact_candidate_with_decoded_pcm": 1,
        "offset_only_idx_candidate": 1,
        "game_files_used": False,
        "actual_police_voice_confirmed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("join", help="Join CSV exports and V31/V32 metadata reports")
    for arg in ("scan", "idx", "evt", "csi"):
        run.add_argument("--" + arg, type=Path, required=True)
    run.add_argument("--triage", type=Path)
    run.add_argument("--report", type=Path, required=True, help="New JSON path only")
    sub.add_parser("self-test", help="Synthetic graph only, no game audio")
    args = parser.parse_args(argv)
    try:
        if args.action == "self-test":
            print(json.dumps(self_test(), indent=2, sort_keys=True))
            return 0
        if args.report.exists():
            raise AttributionError("Refusing to overwrite existing report")
        source_paths = [args.scan, args.idx, args.evt, args.csi]
        if args.triage is not None:
            source_paths.append(args.triage)
        if any(args.report.resolve() == x.resolve() for x in source_paths):
            raise AttributionError("Output path cannot equal an input")
        report = make_report(args.scan, args.idx, args.evt, args.csi, args.triage)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2, sort_keys=True)
            output.write("\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (AttributionError, OSError) as exc:
        print(f"V33 evidence join failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
