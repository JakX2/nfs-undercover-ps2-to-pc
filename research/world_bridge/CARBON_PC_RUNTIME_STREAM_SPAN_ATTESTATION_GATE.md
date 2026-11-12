# Carbon PC: staged texture-stream read attestation

**2026-11-04 | Source-free tool, synthetic tests, private original-source controls.**

## What this adds

`carbon_pc_runtime_span_attestation.py` is a **read-only evidence gate**, designed for a user-controlled Windows Process Monitor capture. It combines independent checks:

1. Parse the owner's original `L5RB.BUN` section table, identify section 141 or 142 inside the **pristine** `STREAML5RB.BUN`, validate the original Carbon PC texture index/pixel alignment and locate **one existing DXT1 or DXT5 image by ordinal**. The user cannot simply assert an image offset.
2. Check the **entire** pristine, staged, and current installed stream files. All must be distinct, non-symlinked files of equal bounded size. Stage differences must be **nonzero and entirely within the one selected image span**; the installed file must match the staged file by privately calculated SHA-256. No game stream is written, installed or restored by this command.
3. Read a user-supplied ProcMon CSV containing `Process Name`, `PID`, `Operation`, `Path`, `Result`, and `Detail`. Accept only `NFSC.exe`, `SUCCESS`, the **exact normalized installed Windows file path**, and a **successful CreateFile followed by ReadFile from the same PID**. Where `Detail` contains `Offset` and `Length`, intersect those ranges with the verified image span and count **unique** covered bytes, without combining unrelated PIDs.

Reported evidence grades distinguish **no open**, **open only**, **same-process open/read without image overlap**, **partial image-span read**, and **full image-span read**. The final grade still ends in `not_rendering`: a disk read is **not** proof of a texture being registered, sampled, correctly blended, or visible in the game.

**Privacy:** Reports omit full file paths, user names, PID values, resource names, game texture hashes, image data, source digests and source bytes. The program does not invoke the game, hook processes, use the network, or modify the Carbon installation.

## Private original Carbon PC confirmation

Original Carbon PC split-archive members `TRACKS/L5RB.BUN` and `TRACKS/STREAML5RB.BUN` were extracted into a **private temporary workspace** with both ZIP members' uncompressed lengths and CRC32 values validated. The stream is **82,837,504 bytes**. On those originals, the tool located these first available existing-slot image spans:

| Original PC texture section | Existing slot format | Span bytes | Verified within stream |
| --- | --- | ---: | :---: |
| 141 | DXT1 | 43,680 | yes |
| 141 | DXT5 | 349,504 | yes |
| 142 | DXT1 | 21,824 | yes |
| 142 | DXT5 | 87,360 | yes |

A separate **existing-slot DXT1 solid magenta** test stream was created using the previously validated, opt-in private-copy staging tool. A second copy standing in for an installed stream was made **only inside the private test directory**, and the new attestor verified all full-file, byte-span and digest controls. The existing staging control independently reported **41,893** changed bytes confined to the **43,680-byte** six-mip image in section 141. No game installation was touched; private test copies are **not** distributed.

## Regression tests

`test_carbon_pc_runtime_span_attestation.py` adds **33 synthetic-only tests**, covering offset parsing (decimal, comma-grouped, hex), disjoint/overlapping reads, exact path and process identity, strict same-PID ordered operations, PID/path mismatch, absence of offset details, failed requests, missing/over-limit data, original PC DXT1/DXT5 slot extraction, full-copy isolation, stage mismatch, hardlinks and symlinks, and an end-to-end **synthetic** successful trace. The full assembled local research workspace ran **336/336 tests** successfully, including the preexisting **303** tests. This is a local result, **not** a claim that GitHub CI or Carbon game runtime passed.

## How to use on Windows (only with a legitimate private installation)

First use the existing tool to generate a private **staged** stream copy from a pristine Carbon PC extracted bundle/stream. Back up your installed `TRACKS/STREAML5RB.BUN` externally before making **any manual replacement**. The attestor itself never replaces anything. Capture the actual `NFSC.exe` launch and navigation with Microsoft's Process Monitor, retaining successful `CreateFile` and `ReadFile` events and `Detail` values, and export the capture to CSV.

From the checked-out repository's `research/world_bridge` directory, for an existing DXT1 slot 0 in section 141:

```bash
python carbon_pc_runtime_span_attestation.py \
  --carbon-bun "C:\\PrivateBackup\\L5RB.BUN" \
  --pristine-stream "C:\\PrivateBackup\\STREAML5RB.BUN" \
  --staged-stream "C:\\PrivateTest\\STAGED_STREAML5RB.BUN" \
  --installed-stream "C:\\Games\\Carbon\\TRACKS\\STREAML5RB.BUN" \
  --procmon-csv "C:\\PrivateTest\\nfsc-procmon.csv" \
  --section 141 --codec DXT1 --slot 0
```

All supplied paths are examples. A DXT5 staged overlay can be tested by selecting `--codec DXT5` and its existing-slot ordinal once such a file has been privately prepared. Do **not** upload original game files, private stream copies or raw ProcMon logs to GitHub. The tool returns **only aggregate evidence**; restoring the original installed stream is a separate manual, user-controlled step.

## Known limits / next gate

- No **actual Windows ProcMon capture from a gameplay session** was provided or processed in this milestone. Therefore **no game file read, texture registration or in-game rendering is claimed**. The positive trace in unit tests is synthetic.
- ProcMon filtering, memory-mapped IO, cache behavior, path namespace aliases and PID reuse can cause absent or ambiguous evidence; the checker intentionally favors false negatives over unwarranted proof.
- SHA-256 equality of the installed file is verified **at analysis time**, not necessarily at capture time. An external trace with timestamps does not cryptographically bind file contents to the moment of a read.
- An observed read of a texture byte range does not prove its DXT blocks are decoded or sampled, or that the texture-hash/UV/material binding is correct. A private game screenshot or equivalent runtime observation is still needed for that claim.
- The tool neither creates a usable Undercover world patch nor inserts new Carbon texture identities. PR remains **draft**; `main` unchanged; no original copyrighted content in the committed sources.
