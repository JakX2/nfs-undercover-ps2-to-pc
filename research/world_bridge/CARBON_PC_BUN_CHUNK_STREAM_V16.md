# V16: Carbon PC bounded BUN top-level resource stream parsing

**2026-11-12. Source-only, read-only, original-free CI.**

## Motivation

The V14/V15 original external Carbon PC control was structurally limited
to a SINGLE decoded native PC geometry (0x80134000) or texture
(0xB3300000) root. Actual Carbon PC stream-section research shows
multiple adjacent top-level resource frames, including scenery,
geometry and textures. Therefore requiring a standalone root could
wrongly reject a structurally valid chunk stream and checking only
its first root could fail to examine the entire file accessed by NFSC.exe.

This milestone accepts the complete bounded file as a SEQUENCE of
little-endian top-level (chunk ID, payload length) frames. It NEVER
searches arbitrary embedded bytes for a resource signature.

## New source-only implementation

- carbon_pc_bun_chunk_stream_gate.py provides
  inspect_carbon_pc_chunk_stream(blob, expected_kind).
- It walks the full file with 8-byte chunk headers, checked payload
  boundaries, bounded total file size (32 MiB) and frame count (4096).
- Each top-level PC geometry root is validated by the previous strict
  parse_geometry_root; each PC texture root by parse_pack.
- Model and texture identities are tracked internally only, to refuse
  duplicates across separate roots. The public report contains only
  aggregate resource counts and explicit false loader/runtime flags.
- Unknown top-level chunks are counted, not guessed as known or scanned
  recursively. A file containing ONLY unknown chunks cannot pass.
- The expected control kind can be geometry, texture or either;
  mismatch is rejected. Missing/truncated tails or malformed nested
  recognized roots are rejected.

This is a complete CHUNK-BOUNDARY and selected native RESOURCE-PARSER
preflight, not a validation of Carbon's external resource-manager ABI,
a proprietary .BUN wrapper/version, required stream-index chunks,
loader-specific resource type or on-screen rendering.

## V15 integration

The in-memory audit_carbon_original_external_control in
carbon_pc_original_loader_control_chain.py now uses the complete
top-level chunk parser instead of assuming one standalone extracted
root. It still independently verifies the exact configured
XNFSModFiles.txt resource path and ordered same-PID NFSC.exe read
evidence from an owner-captured ProcMon CSV.

Additional output includes top-level chunk count, recognized
geometry/texture root count, unrecognized top-level chunk count,
and the record count for the requested kind. All file lengths
and I/O range checks refer to the ENTIRE input source file.

New explicit false field: external_loader_container_format_verified.

## Original-free tests

- test_carbon_pc_bun_chunk_stream_gate.py tests synthetic PC geometry,
  DXT textures, concatenated mixed resource frames, unknown top-level
  chunks, request-kind constraints, duplicate PC identities, truncated
  framing, invalid recognized roots, and refusal to signature-scan
  inside unrecognized data.
- Expanded test_carbon_pc_original_loader_control_chain.py verifies
  that the actual multi-frame input and full-file read evidence bind
  together, including unknown chunks and duplicate/missing roots.

At code commit fd2ef975, the [GitHub Actions run 43145220570]
completed successfully with 1,725 original-free synthetic tests.
The earlier failed workflow runs were caused by a negative test
accidentally writing zero to the ALREADY-ZERO low byte of the
little-endian GEOM tag. The corrected test mutates the high byte
and verifies failure as intended.

## Limits and next experiment

Even if the full source chunk stream parses and ProcMon reports
all bytes read, the same file may still fail external Carbon loader
registration because chunk sequence, loader file type, initialization
stage, stream metadata, resource dependencies and runtime visibility
are independent. We have not observed the user's own NFSC.exe load
or render this file.

The next decisive test remains a controlled **owner-local Windows
Carbon PC known-good original external BUN** using the real supported
XNFSModFiles loader. Verify manifest selection, exact filename reads,
and separately recorded in-game asset registration/visual change.
Only then use the proven path for one converted Undercover PS2/Wii
scenery model and its DXT texture.

No game binaries/assets, original resource IDs or private ProcMon
paths are included in this commit. PR #33 remains draft; native Wii
C++ decompilation in PR #35 remains separate and untouched.
