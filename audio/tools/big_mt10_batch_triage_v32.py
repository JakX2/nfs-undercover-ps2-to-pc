#!/usr/bin/env python3
"""V32: batch TRIAGE for locally extracted PS2 EA-MT10 mono SCHl streams.

Scans a local unmodified BIG with V31, selects a small deterministic subset,
and REQUIRES a real vgmstream-cli to decode original and V28 PC-header copies.
Reports per-candidate PCM match/mismatch/errors separately, without exporting
source clips, WAVs, or PC-style ASF. Candidate labels are NOT police identities.

The self-test creates only original copyright-free synthetic EA-MT10 frames.
No Carbon PC runtime, CSI/EVT matching, IDX parsing or game-file edits.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import AudioCheckError, resolve_decoder
from schl_wrapper_audit_v25 import SCHlAuditError
from undercover_big_voice_scan_v31 import (
    BIGProbeError, scan_big, verify_at,
)
from undercover_mt10_private_bridge_v28 import BridgeError

MAX_PER_RUN = 32


class TriageError(Exception):
    """Invalid settings or unsafe output."""


def choose_candidates(candidates: list[dict], *, limit: int,
                      minimum_samples: int, start: int = 0) -> list[dict]:
    if not 1 <= limit <= MAX_PER_RUN:
        raise TriageError(f"--limit must be 1..{MAX_PER_RUN}")
    if minimum_samples < 1:
        raise TriageError("--minimum-samples must be positive")
    if start < 0:
        raise TriageError("--start must be nonnegative")
    # Longer sources are useful probes of decoder/codec boundary handling.
    # Duration does NOT establish that a clip contains speech or police audio.
    ranked = sorted(
        (x for x in candidates if x["samples"] >= minimum_samples),
        key=lambda x: (-x["samples"], x["offset"]),
    )
    return ranked[start:start + limit]


def triage(big: Path, decoder: str, *, max_results: int = 1000,
           limit: int = 8, minimum_samples: int = 1, start: int = 0) -> dict:
    if not decoder:
        raise TriageError("A real decoder is mandatory")
    if not 1 <= max_results <= 20_000:
        raise TriageError("--max-results must be 1..20000")
    # Validate the decoder up front: never treat a structural scan as decode.
    resolve_decoder(decoder)
    candidates = scan_big(big, max_results=max_results)
    selected = choose_candidates(
        candidates, limit=limit, minimum_samples=minimum_samples, start=start
    )
    outcomes = []
    for candidate in selected:
        offset = candidate["offset"]
        try:
            verified = verify_at(big, offset, decoder)
            equal = verified.get("pcm_equivalent") is True
            if not equal:
                raise TriageError("Decoder executed but PCM comparison did not match")
            # Don't include WAVs, proprietary data, or inferred police identity.
            pcm = verified["decoded_pcm"]
            outcomes.append({
                "offset": offset,
                "source_bytes": candidate["length"],
                "samples": candidate["samples"],
                "blocks": candidate["blocks"],
                "status": "independent_decoder_pcm_equal",
                "original_pcm_sha256": pcm["original"]["pcm_sha256"],
                "converted_pcm_sha256": pcm["experimental"]["pcm_sha256"],
                "actual_undercover_provenance_verified": False,
                "police_event_identity_verified": False,
                "carbon_pc_runtime_tested": False,
            })
        except (BIGProbeError, BridgeError, SCHlAuditError,
                AudioCheckError, TriageError, OSError, ValueError) as exc:
            outcomes.append({
                "offset": offset,
                "source_bytes": candidate["length"],
                "samples": candidate["samples"],
                "blocks": candidate["blocks"],
                "status": "decode_or_validation_failed",
                # No raw exception string (may contain private filesystem paths).
                "error_type": type(exc).__name__,
                "actual_undercover_provenance_verified": False,
                "police_event_identity_verified": False,
                "carbon_pc_runtime_tested": False,
            })
    success = sum(x["status"] == "independent_decoder_pcm_equal" for x in outcomes)
    return {
        "format": "NFS_AUDIO_V32_PRIVATE_BIG_DECODE_TRIAGE",
        "mode": "read_only_originals",
        "decoder_is_required": True,
        "eligible_schl_candidates_found": len(candidates),
        "scan_result_limit": max_results,
        "scan_may_be_truncated": len(candidates) >= max_results,
        "selected_count": len(selected),
        "selection_order": "descending_samples_then_ascending_big_offset",
        "successful_pcm_pairs": success,
        "failed_pcm_pairs": len(outcomes) - success,
        "outcomes": outcomes,
        "extracted_audio_files_retained": False,
        "identified_police_events": 0,
        "carbon_pc_runtime_tested": False,
    }


def self_test(decoder: str) -> dict:
    from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
    from ea_mt10_multiblock_continuity_v29 import make_ps2_stream
    with tempfile.TemporaryDirectory(prefix="nfs_v32_synthetic_triage_") as tmp:
        big = Path(tmp) / "generated.BIG"
        a = make_single_block_stream()
        b = make_ps2_stream()
        big.write_bytes(b"decoySCHl\x00" + a + b"_padding_" + b)
        report = triage(big, decoder, limit=2, max_results=50)
    if report["successful_pcm_pairs"] != 2 or report["failed_pcm_pairs"] != 0:
        raise TriageError("Synthetic real-decoder triage failed")
    hashes = {x["original_pcm_sha256"] for x in report["outcomes"]}
    if len(hashes) != 1:
        raise TriageError("Same original generated audio decoded differently")
    return {
        "format": "NFS_AUDIO_V32_SYNTHETIC_REAL_DECODER_SELFTEST",
        "selected_count": report["selected_count"],
        "successful_pcm_pairs": report["successful_pcm_pairs"],
        "decoded_pcm_sha256": next(iter(hashes)),
        "game_audio_used": False,
        "gameplay_tested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("triage", help="Read-only source BIG, real decoder gate")
    run.add_argument("--big", type=Path, required=True)
    run.add_argument("--decoder", required=True)
    run.add_argument("--max-results", type=int, default=1000)
    run.add_argument("--limit", type=int, default=8)
    run.add_argument("--minimum-samples", type=int, default=1)
    run.add_argument("--start", type=int, default=0)
    run.add_argument("--out-dir", type=Path, required=True,
                     help="New private directory for metadata-only report.json")
    test = sub.add_parser("self-test", help="Generated MicroTalk; actual decoder")
    test.add_argument("--decoder", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "self-test":
            print(json.dumps(self_test(args.decoder), indent=2, sort_keys=True))
            return 0
        if args.out_dir.exists():
            raise TriageError("Refusing to overwrite existing output directory")
        report = triage(
            args.big, args.decoder,
            max_results=args.max_results, limit=args.limit,
            minimum_samples=args.minimum_samples, start=args.start,
        )
        # Do not create a results folder until source/decoder validation succeeds.
        args.out_dir.mkdir(parents=True, exist_ok=False)
        with (args.out_dir / "report.json").open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2, sort_keys=True)
            out.write("\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["selected_count"] == 0:
            return 3
        return 0 if report["successful_pcm_pairs"] == report["selected_count"] else 1
    except (TriageError, BIGProbeError, BridgeError, SCHlAuditError,
            AudioCheckError, OSError, ValueError) as exc:
        print(f"V32 offline triage failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
