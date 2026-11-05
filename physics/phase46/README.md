# Phase 46: Carbon PC steering evidence review

**Status:** read-only post-processing for Phase 45's report. No game patch, executable modification, dynamic observation, PS2/PC field equivalence, or new source-binary scan was performed in this session.

## What it adds

Phase 45 generates a detailed JSON bundle from a locally owned, SHA-verified Carbon PC NFSC.exe. Phase 46 checks that the bundle's internal numbers and assertions are coherent, then renders a concise Markdown investigation review focused on the two previously anchored PC steering-function stores:

| Verified instruction PC | Syntactic write | Traced register |
| --- | --- | --- |
| 0x006EF7B9 | mov DWORD PTR [esi+0x104],eax | eax |
| 0x006EF7C0 | mov DWORD PTR [esi+0x118],edx | edx |

The report validator checks that instruction PCs, displacements, source register labels, candidate counts, read/write direction counts, CFG path states, known anchor marks, and unresolved memory-operand counts agree with one another. It fails on self-contradictory source-evidence claims, such as asserting that Carbon PC fields have already been matched to Undercover PS2 offsets.

**There are two distinct trust levels:**

- **Consistency-only** (existing JSON, no original executable): the Markdown header explicitly says **NOT AUTHENTICATED**. A SHA string inside JSON is only self-declared. Internal consistency cannot prove that a game executable produced the report.
- **Authenticated recheck** (`--exe`): Phase 46 calls the Phase 45 analyzer against the *local exact original Carbon PC executable* again, including its full Phase 31/40 version and byte checks and GNU objdump decoding, and requires the **whole recomputed report** to equal the supplied JSON. It refuses a mismatch or unsupported executable.

The supported executable's SHA-256 is `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`. Recomputed results are still static code observations, **not** verification of field semantics or in-game handling.

## How to run

Requires Python 3.11+ and standard library for consistency-only review. For authenticated recheck, GNU binutils `objdump` must also be installed and available on PATH.

From the repository root, with a JSON report generated privately by Phase 45:

```sh
# First generate evidence from your privately held supported original executable.
python physics/phase45/carbon_pc_steering_evidence_bundle.py /local/NFSC.exe --output phase45_evidence.json

# Fast review. Reports explicitly that source authentication was NOT repeated.
python physics/phase46/review_evidence_bundle.py phase45_evidence.json --output phase46_review.md

# Strict recheck. Independently reruns Phase 45 from the original executable.
python physics/phase46/review_evidence_bundle.py phase45_evidence.json --exe /local/NFSC.exe --output phase46_authenticated_review.md

# Tests need no game executable or assets.
python -m unittest discover -s physics/phase46 -p 'test_*.py' -v
```

The review can be printed to stdout without `--output`. By default, files are created exclusively; `--overwrite` must be explicit to replace an existing report. To prevent accidentally overwriting game files, the output file extension must be `.md` or `.markdown`, and it cannot resolve to the input JSON or to the executable path if supplied. The JSON input is capped at 8 MiB and access lists are bounded. No source executable, extracted function bytes, or runtime dumps are included in the Markdown review.

## Tests and limitations

- **41 synthetic tests passed locally** before commit. They cover valid/mismatched metadata, self-declared SHA labels, PC offsets, candidate access totals, read/write directions, contradictory CFG states, unknown-address forms, missing anchors, unverified object claims, safe output paths, recheck mismatch and failure without output.
- GitHub Actions runs synthetic Phase 36–46 suites. They validate the code's behavior but do **not** constitute a source-verified original Carbon PC scan.
- The original supported NFSC.exe was not present in this session; no authenticated Phase 45/46 game report was generated.
- A report labeled authenticated still does not prove that ESI always points to the same object, that a candidate field is a particular steering-state value, or that either PC offset equals Undercover PS2 +0x188/+0x19C.
- The **Phase 30 tire-force modification remains disabled**, because it made the upgraded CCX feel heavier.

## Next evidence

Run Phase 45 and Phase 46 on the exact supported original Carbon PC executable locally; review the EAX/EDX origin traces and ESI control-flow uncertainty. Only with independently supported field identities, types, units and live behavior should an opt-in reversible steering-only prototype be attempted.
