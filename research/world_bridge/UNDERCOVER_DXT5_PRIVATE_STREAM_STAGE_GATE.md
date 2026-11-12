# Undercover PS2 donor → reversible private Carbon PC DXT5 stream-copy gate

**2026-11-04. Owner-source-only research. No original game assets are distributed.**

This adds `private_undercover_dxt5_stream_stage.py` and 38 source-free regression tests, extending the previously validated Undercover indexed decoder, alpha-preserving DXT5 encoder, Carbon texture envelope overlay, section-table parser, and Windows smoke-session guard. This is **not** proof of game loading or rendering.

## What this actually implements

`stage_undercover_dxt5_copy()` requires locally owned original Undercover PS2 `TRACKS.zip` and extracted pristine Carbon PC `L5RB.BUN` + `STREAML5RB.BUN`. It validates Undercover ZIP member CRCs and the Carbon PC `0x34110` section-table placement; parses the actual section-241/3401 PS2 texture record and a section-141/142 Carbon PC texture pack; and finds existing DXT5 slots that **exactly match** donor width/height. It does **not** create a new Carbon resource identity, change names or metadata, resize the donor, or guess unseen runtime fields.

By default the tool only reports **aggregate, non-proprietary facts**: section IDs, private zero-based donor/target ordinals, resolution, mip count, compressed image span, number of changed bytes, DXT5 round-trip RGB/alpha errors, and whether a copy was created. No palette entries, source texture names/hashes, private paths, image pixels or source file digests appear in the report. With no explicit ordinals, it deterministically selects the lowest-pixel-count exact dimension match to reduce first-test CPU cost. That choice **does not imply the target is visible in gameplay**. To test a particular scene material, the chosen existing slot must be investigated separately.

**An explicit** `--write-private-copy --private-output <new STAGED_* file>` **can** create a private, uncompressed Carbon PC full-stream copy. The output path must be new and must not target a game `TRACKS` directory or use the installed stream's exact filename. Full-image encode is performed in memory first. The staging step copies the pristine stream into a temporary file, changes only the already-present target DXT5 image span, verifies the **entire** staged file byte for byte outside that span, rechecks all original source SHA-256 digests/size/mtime, and publishes by exclusive no-overwrite hard link. The ZIP and original Carbon source are read-only. No code in this tool installs, launches, modifies or patches the game.

The existing `carbon_pc_private_smoke_session.py` guard then handles *separate*, user-controlled `preflight` → `prepare` → explicit Windows `install` → `evidence` → verified `restore`. A new staged output cannot be considered safe for an installation without that extra check. No game installation was touched here.

## Source-backed private experiment

Both game archives were inspected privately. The original Carbon PC split TRACKS archive was flattened through ZIP's split-volume processing, and `L5RB.BUN` and `STREAML5RB.BUN` were read through `zipfile` with CRC checks. The extracted Carbon PC stream is **82,837,504 bytes**. The original Undercover PS2 ZIP's `L2RB.BUN` and `STREAML2RB.BUN` were likewise CRC checked in memory.

Dimension-compatible donor/existing-PC-DXT5 slot pairs (not unique materials):

| Undercover section → Carbon PC section | Exact dimension matches |
| --- | ---: |
| 241 → 141 | 32 |
| 241 → 142 | 116 |
| 3401 → 141 | 7 |
| 3401 → 142 | 139 |
| **Total** | **294** |

The first automatic, **dry-run only** original pair used section **3401 donor ordinal 12** into section **142 DXT5 slot 19**, 64×32, three PC mip levels: **2,688** image-span bytes, **2,612** changed, DXT5 base RGB/alpha MAE **2.3652/0.3940**.

A second **high-resolution donor experiment** used Undercover section **241 donor ordinal 1** into Carbon PC section **142 DXT5 slot 0**, **256×256**, **six PC mip levels**, **87,360-byte** image span, **80,561** changed bytes. The base-level DXT5 round-trip errors are **2.1577 RGB / 0.5086 alpha MAE** on a 0–255 channel scale. The replacement stream remained exactly **82,837,504 bytes**, with **all other original stream bytes unchanged**. The native Carbon PC texture index, hash identity, name, descriptor header, platform records and neighboring streams remain intact.

The genuine 256×256 donor stage was fed to the already committed `carbon_pc_private_smoke_session.py` in a **private sandbox stand-in game directory**, not a Windows game installation. Full-stream `preflight`, exclusive pristine backup creation, post-install status, and exact SHA-256 restoration to the original stream all passed. The Windows game-closed check was **mocked** to exercise the copy logic on Linux, so this is not an actual Windows security/ACL or running-game test. All private game-data copies and backups should be deleted after the experiment; no such data belongs in GitHub, Drive public shares, or download ZIPs.

## Regression evidence

The new module has **38 source-free tests** covering dimension-match enumeration, deterministic ordering, explicit and partial ordinals, unsupported sections/targets, exact changed-span isolation, in-memory reversal, default no-write, CLI argument handling, exclusive private output, symlink/path safety, absent inputs, invalid ZIPs, source aliasing, deliberately corrupted source data, injected full-file verification errors, and changing an original source during staging. **38/38** passed locally. The assembled local research workspace passed **374/374** tests; the complete repository CI count may differ because this working directory contains only a subset of the full GitHub tree. GitHub CI should be checked at the new branch head and quoted only after it completes.

**Critical limits:** PS2 `double` alpha is still an explicit decoding hypothesis, not proven Carbon shader blending. Automatic dimension compatibility does not imply a visually relevant target. New texture hash registration, gameplay material assignment, loader acceptance, actual Windows file-open behavior and rendering are all unproven. This is a reversible **existing-slot experiment**, not the full Undercover Tri-City Bay port. Do not merge this research into `main` until runtime verification.

## Safe Windows preparation (no install by these commands)

Run this from `research/world_bridge` of the same PR branch after privately extracting the original Carbon PC files. Use your own private filesystem paths. This first command is **read-only**:

```powershell
python private_undercover_dxt5_stream_stage.py `
  --undercover-ps2-zip 'D:\PrivateOriginal\UndercoverPS2_TRACKS.zip' `
  --carbon-bun 'D:\PrivateOriginal\L5RB.BUN' `
  --carbon-stream 'D:\PrivateOriginal\STREAML5RB.BUN' `
  --undercover-section 241 --carbon-section 142 `
  --donor-ordinal 1 --pc-dxt5-slot 0
```

After inspecting the report, create a **new private copy**, separate from the installation:

```powershell
python private_undercover_dxt5_stream_stage.py `
  --undercover-ps2-zip 'D:\PrivateOriginal\UndercoverPS2_TRACKS.zip' `
  --carbon-bun 'D:\PrivateOriginal\L5RB.BUN' `
  --carbon-stream 'D:\PrivateOriginal\STREAML5RB.BUN' `
  --undercover-section 241 --carbon-section 142 `
  --donor-ordinal 1 --pc-dxt5-slot 0 `
  --private-output 'D:\PrivateTest\STAGED_UNDERCOVER_STREAML5RB.BUN' `
  --write-private-copy
```

If there is **no existing loose** `TRACKS\STREAML5RB.BUN` at the intended Carbon PC installation path, stop. Do **not** infer an override location. For the existing loose file, continue with `carbon_pc_private_smoke_session.py preflight` using `--section 142 --codec DXT5 --slot 0`, then follow its documented exclusive backup and explicitly confirmed restore workflow. Capture a genuine Windows Process Monitor trace and before/after screenshots; a successful stream read would establish byte access, **not** itself prove material rendering. Never upload the staged stream or private session directory.
