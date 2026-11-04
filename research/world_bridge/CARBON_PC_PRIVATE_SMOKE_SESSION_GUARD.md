# Carbon PC private reversible texture smoke session

**2026-11-04 | Source-free tooling, synthetic tests, original-source private file-copy control.**

This gate bridges the previous **read-only whole-stream/span attestation** and a future user-controlled **Windows gameplay capture**. It does **not** claim that Carbon's loader reads the replacement, that any texture registers, or that Undercover assets are visible in-game.

## New tool and operating boundary

`carbon_pc_private_smoke_session.py` is a *private installation safety guard*, not an automatically applied patch or distribution package. It accepts only existing Carbon PC section **141** or **142**, an original PC **DXT1** or **DXT5** texture slot identified by ordinal, and an already-created staged `STREAML5RB.BUN` copy. The selected image span is derived from the previously committed source-backed `carbon_pc_runtime_span_attestation.existing_image_span()`, not from a user-supplied raw offset.

It has six explicit commands:

| Command | Effect | Preconditions |
| --- | --- | --- |
| `preflight` | Read-only byte-isolation and provenance inspection | Original Carbon PC `L5RB.BUN`, pristine stream, staged stream, installed stream, selected section/codec/slot |
| `prepare` | Create a **new** private session directory, a full-size pristine installed-stream backup and a local manifest | The installed stream must still be pristine; no existing session directory may be overwritten |
| `status` | Re-check every source and backup, then classify installed stream as original/staged/unknown | Private manifest and backup |
| `install` | **Explicit opt-in only**: atomically replace only `TRACKS/STREAML5RB.BUN` with staged copy | `--apply --game-closed`, Windows, positive game-closed check, intact backup, verified original installed, original-source image-span proof |
| `evidence` | Read-only analysis of private Windows Process Monitor CSV against verified staged installed file | Previously committed `carbon_pc_runtime_span_attestation.py`, user capture, stage currently installed |
| `restore` | **Explicit opt-in only**: atomically restore verified pristine backup | `--apply --game-closed`, Windows, positive game-closed check, current file exactly matches staged or original, original backup intact |

The tool never launches the game, contacts a network, installs on its own, writes into GitHub/Drive, creates new texture identities, or publishes proprietary data. The **only** installed-file write possible is during a user-invoked `install` or `restore` command. It never writes `L5RB.BUN` or other game data.

The session directory contains **an original proprietary stream backup**, private Windows installation paths and local file digests. Do **not** share this directory or its manifest, install it to GitHub, or upload it with a bug report. Console reports omit paths and SHA-256 values. Choose a private session directory **outside the game installation** and preserve it until the original has been restored and verified.

### Safety invariants

- Absolute existing regular files only; reject symlinks, hard-linked alias inputs, absent data, mismatched sizes, incorrect installed filename/directory, unsupported section or codec and excessive inputs. Staged and pristine streams must be byte-identical **outside exactly one source-derived original image span**, with at least one changed image byte.
- Before creating the session backup, the installed `TRACKS/STREAML5RB.BUN` must be **byte-identical to the provided pristine stream**. A new backup and manifest are created exclusively **outside the game directory**; existing backups are never overwritten.
- Before either write operation, verify the bundle, pristine, staged and backup contents against their private recorded SHA-256 digests; recompute the selected image span; recheck the entire original/staged difference. Installation is refused unless current installed bytes still match pristine. Restore refuses any unexpected installed bytes instead of overwriting them.
- Windows writes use a unique temporary file in the installed `TRACKS` directory, flush and hash its entire contents, then use `os.replace` and verify the whole installed file again. The original backup remains intact. A per-session exclusive lock prevents simultaneous writes; an existing lock is never deleted on conflict.
- `--apply` and `--game-closed` are both mandatory for writes. On Windows a second `tasklist` check refuses any detected running `NFSC.exe`, or an uninterpretable/failed process query. Unsupported operating systems cannot use the installer/restore commands.

**Limits:** Windows filesystem copy/rename behavior, ACLs, antivirus and game-specific running-file locks cannot be completely modeled on Linux. A game launched immediately after a preflight can invalidate the assumption that the game is closed; only run install/restore with the game fully exited. The manifest is an unencrypted private local record, not a signed security boundary. A time-of-check/time-of-use race remains theoretically possible. A positive ProcMon read still does **not** prove rendering.

## Private original Carbon PC file-size smoke test

A locally supplied original Carbon PC split `TRACKS` archive was read without changing the source volumes. Both `TRACKS/L5RB.BUN` and `TRACKS/STREAML5RB.BUN` were independently extracted into a **private temporary directory**, and each member passed its ZIP CRC32 and expanded-length check. The streamed file is exactly **82,837,504 bytes**.

An independent section-table/texture-metadata probe identified the first DXT1 image in section **141**, with exactly **43,680 image bytes**, **six mip levels**, and **30 existing DXT1 slots** in that section. The test staged a *separate* copy containing an opaque-black replacement within that range, with **41,850 actually changed bytes** and no other modifications. The guard then:

1. Passed full-file `preflight` against a private `TRACKS/STREAML5RB.BUN` stand-in.
2. Created a private session backup without changing the stand-in.
3. Installed the staged copy **only inside the private test directory** (mocking the Windows process-exited gate in the Linux test environment).
4. Reported stage-installed status and preserved original source+backup integrity.
5. Restored the original file and verified **exact SHA-256 byte identity** with the pristine original.
6. Removed the private extracted and staged game-data copies, session backup and stand-in. No original game bytes are in this repository or the download package.

This tests the 82.8 MB byte-copy/rollback and validation logic in a sandbox; it is **not** a Windows game installation test or an in-game observation.

## Synthetic regression suite

`test_carbon_pc_private_smoke_session.py` contains **44 synthetic-only tests**. They exercise preflight, source-anchored image-span confinement, missing/oversize data, wrong game path, hard/symlinks, exclusive backups, manifest privacy/validation, explicit install/restore confirmation, session locks, no-clobber on errors, stage/backup mutation, unexpected installed changes, atomic temp-checksum failure, idempotent restore, and read-only evidence handoff. The tests use small artificial files and mock the game-closed condition; they never modify real installations.

These 44 tests passed locally on Python 3.13. The previous **336/336** local baseline came from a *partial assembled research workspace*, so adding 44 yields **380 local-workspace tests**, **not** the count of every test in the complete repository. GitHub Actions **World bridge source-only tests**, run **#7**, subsequently completed successfully from a clean checkout, with the job log showing **816 tests run, OK**. No original game assets were needed in CI. These results test source logic, not Windows installation or game rendering.

## Windows workflow (deliberately explicit)

Only with your own legitimate Carbon PC installation, an **original pristine extracted** `L5RB.BUN` + `STREAML5RB.BUN`, and a *separate* prevalidated staged copy produced by the earlier tool. **First confirm that the game actually has a loose `TRACKS/STREAML5RB.BUN`; if it does not, stop. Do not guess an archive override path.** Replace these example paths with your own paths locally. From `research/world_bridge` in a checked-out repository:

```powershell
# 1. Read-only: identify an original Carbon PC section-141 DXT1 slot
python carbon_pc_private_smoke_session.py preflight `
  --carbon-bun 'D:\PrivateOriginal\L5RB.BUN' `
  --pristine-stream 'D:\PrivateOriginal\STREAML5RB.BUN' `
  --staged-stream 'D:\PrivateTest\STAGED_STREAML5RB.BUN' `
  --installed-stream 'C:\Games\Carbon\TRACKS\STREAML5RB.BUN' `
  --section 141 --codec DXT1 --slot 0

# 2. Make a separate, exclusive original backup+manifest; still no installation change
python carbon_pc_private_smoke_session.py prepare `
  --session-dir 'D:\PrivateTest\session-001' `
  --carbon-bun 'D:\PrivateOriginal\L5RB.BUN' `
  --pristine-stream 'D:\PrivateOriginal\STREAML5RB.BUN' `
  --staged-stream 'D:\PrivateTest\STAGED_STREAML5RB.BUN' `
  --installed-stream 'C:\Games\Carbon\TRACKS\STREAML5RB.BUN' `
  --section 141 --codec DXT1 --slot 0

# 3. Only after shutting down Carbon and confirming the private backup
python carbon_pc_private_smoke_session.py install `
  --session-dir 'D:\PrivateTest\session-001' --apply --game-closed

# 4. Capture game launch and track navigation with ProcMon on Windows.
#    Close Carbon, stop capture, export CSV preserving Process Name, PID,
#    Operation, Path, Result, Detail. Keep the raw capture private.
python carbon_pc_private_smoke_session.py evidence `
  --session-dir 'D:\PrivateTest\session-001' `
  --procmon-csv 'D:\PrivateTest\carbon-trace.csv'

# 5. Close Carbon, restore verified original, check final status
python carbon_pc_private_smoke_session.py restore `
  --session-dir 'D:\PrivateTest\session-001' --apply --game-closed
python carbon_pc_private_smoke_session.py status `
  --session-dir 'D:\PrivateTest\session-001'
```

Do not assume a successful filesystem read is visual proof. Take separate before/after screenshots of the same known material and lighting, and do not distribute private original game assets or raw process traces. If the guard refuses any step, **do not manually force a replacement**; inspect the private files and preserve the original backup.

## What comes next

A **real Windows test by the user** is needed to establish file lookup, read overlap and rendered appearance. Existing-slot patching does not automatically register new Undercover texture hashes, nor solve material blending, game streaming or geometry/traffic/collision. This PR remains draft and unmerged; `main` should remain unchanged until runtime proof is available.
