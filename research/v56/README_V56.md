# V56: same-open stream snapshot integrity guard

This is an incremental reliability fix to V55's read-only game-stream candidate scanner.

## Why this matters

V55 previously computed its whole-stream SHA-256 using one file open and later
opened a new memory map to scan ROOT records. A user-owned archive changing in
between could produce a report whose source hash and candidate records referred
to **different versions of the file**. An expected source hash guarded only the
first read.

## Change

- Hash the exact file descriptor being memory-mapped, *before and after* the
  candidate scan. Keep the descriptor open until the scan and checks finish.
- Compare file identity, size, modification time and change time before and
  after. Check whether the supplied path was replaced with a different file.
- Reject concurrent changes rather than write a report whose provenance is
  internally inconsistent.
- Handle empty files without attempting a zero-length memory map.
- Report `same_open_handle_hash_and_scan: true`,
  `best_effort_file_change_check_passed: true`, and
  `atomic_filesystem_snapshot: false`.

These are **best-effort checks, not an atomic immutable snapshot**. An archive
must remain unchanged while being scanned. The scanner never makes an
authenticated original-game claim merely from hash equality or matching
candidate record layouts. It does not prove Carbon PC serialized ABI.

## Regression coverage

Five additional asset-free test cases specifically validate:
1. Same-file reported SHA and source-snapshot flags.
2. No use of the old separate `digest_stream` call during a scan.
3. Mid-scan file-byte mutation rejection.
4. Mid-scan file-path replacement rejection.
5. Empty stream under a matching expected SHA.

The existing 20 synthetic V55 tests remain in the same suite.

Run from repository root:

```sh
python -m unittest discover -s research/v55 -p 'test_v55.py' -v
```

No game input is committed or modified by the tool. The synthetic mutation
tests only touch temporary test files. CI covers asset-free tests only.

## Still unresolved

A second independently authenticated Wii scenery ROOT, an independently
authenticated original Carbon PC world ROOT, loader semantics, visibility,
collision/navigation, and in-game placement remain unverified. No writer or
installable patch is introduced.
