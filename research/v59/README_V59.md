# V59: verify archive/root handoff through the same opened file

**Scope:** Research-only, read-only source integrity fix for V55/V58. This
change does **not** authenticate a new original Wii scenery scene, prove an
on-disk Carbon PC schema, or provide an installable world patch.

## Problem

V58 scans an archive using a read-only mapped descriptor and emits a
*private* candidate ROOT manifest containing both the full-archive SHA-256
and the extracted ROOT SHA-256. The V55 manifest reader formerly:

1. Opened the archive to hash all bytes.
2. Closed that file.
3. Opened the path **again** to extract the indicated ROOT and checked only
   that ROOT's digest.

If bytes outside the ROOT changed between steps 1 and 3, the source could
be inconsistent while the ROOT still matched its fingerprint. Filesystem
replacement or concurrent writes were also not explicitly checked.

## Fix

`research/v55/v55_cross_scene_hypothesis_gate.py::read_verified_root` now:

- Opens the source **once** and keeps the same descriptor through all work.
- Hashes the complete file in bounded chunks, verifies its expected SHA-256,
  extracts a bounded ROOT at the explicit offset (or standalone root),
  verifies the expected ROOT SHA-256, and hashes the whole file a second time.
- Checks `fstat` identity/size/mtime/ctime and detects when the named path
  was replaced while the handle was open.
- Rejects an inconsistent source without returning a report.
- Adds metadata flags
  `same_open_handle_hash_and_extract`,
  `best_effort_file_change_check_passed` and
  `atomic_filesystem_snapshot: false` to the returned internal metadata.

The checks provide **best-effort consistency, not a transactional filesystem
snapshot**. As before, game files should be kept unchanged while processing.
The reader never writes or patches an original archive.

## Tests

Run the new source-only tests and selected previous suites:

```sh
python -m unittest discover -s research/v59 -p 'test_v59.py' -v
python -m unittest discover -s research/v55 -p 'test_v55.py' -v
python -m unittest discover -s research/v56 -p 'test_v56.py' -v
python -m unittest discover -s research/v58 -p 'test_v58.py' -v
```

Twelve new synthetic tests cover isolated ROOTs, embedded ROOTs, expected file
and ROOT hashes, mid-read unrelated trailer mutation, file path replacement,
metadata changes, old two-open path avoidance, exact V58 private-manifest
interoperability, unchanged source files and offset failures.

Original proprietary game assets and private source manifests are not
committed. Existing private fixture tests remain conditional, and GitHub CI
tests only synthesized data.

## Remaining research blockers

An independently sourced second Undercover Wii scenery sector and authenticated
Carbon PC stream are still unavailable to this public fixture-free workflow.
Graph/culling semantics, native Carbon PC world registration, streaming,
shaders, collision/navigation and in-game testing remain unverified.
