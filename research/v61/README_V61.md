# V61: format-neutral Carbon PC scenery / streaming chunk probe

**Offline and read-only. No installation, writer, original game binary, or
verified Carbon world-index ABI.**

## Why V61 exists

V58–V60 focus on source-observed Wii scenery ROOTs and independently verifiable
Wii candidate graphs. V59 on the *other* research branch applies a
caller-declared master-index layout, but that **does not establish Carbon PC's
actual row format**. A published Most Wanted 2005 `0x34110` 92-byte row is
not source-verified Carbon PC serialization.

To investigate original Carbon PC archives safely, V61 searches for **chunk
framing evidence without requiring any Wii instance, preculler or tree layout**.

## What is scanned

- Only two selected 32-bit EA chunk tags:
  - `0x80034100`: candidate scenery ROOT
  - `0x00034110`: candidate streaming master chunk
- Both explicit endian orders (little/big) and both **payload-length** and
  **total-length** header interpretations. If several fit, V61 records every
  bounded candidate instead of pretending one is correct.
- For candidate scenery ROOTs, a separate best-effort attempt to parse
  contiguous direct `0x341xx` child headers **under that same framing
  hypothesis**. Failure is labeled `unparsed`, not proof that the source
  is invalid or not Carbon PC.
- For master chunks, optional *caller-supplied* row stride, row start and
  32-bit field offset. With optional reference offsets, the probe counts
  simple raw integer matches. It does not default to MW or Wii layouts.
  These raw matches are **not proven pointers, relocations, ownerships or
  engine-loader reads**.
- All outputs are metadata: full-file and chunk-payload SHA-256, offsets,
  interpreted lengths, candidate child tags and limited numerical matches.
  No binary game payloads, private input file paths or source strings.

## Commands

Python 3.10+, standard library only. Provide your **locally owned** game
archive and keep any game files outside your public GitHub clone.

First, make an exploratory format inventory:

```powershell
py -3 research/v61/v61_carbon_chunk_probe.py `
  --archive "D:\Games\Carbon\TRACKS\STREAML5RA.BUN" `
  --report "D:\PrivateResearch\carbon_stream_v61.json"
```

This path is **illustrative**; it does not assert that your installation uses
this precise file. For stronger file identity checks, pass an independently
established SHA-256:

```powershell
py -3 research/v61/v61_carbon_chunk_probe.py `
  --archive "D:\Games\Carbon\TRACKS\STREAML5RA.BUN" `
  --expected-sha256 "YOUR_64_HEX_SHA256" `
  --report "D:\PrivateResearch\carbon_verified_v61.json"
```

On a separately inspected master table, a **declared experimental** 92-byte
row layout and 32-bit field at offset 20 can be probed by supplying all
parameters explicitly:

```powershell
py -3 research/v61/v61_carbon_chunk_probe.py `
  --archive "D:\Games\Carbon\TRACKS\L5RA.BUN" `
  --endian little --length-mode payload `
  --row-stride 92 --field-offset 20 `
  --reference-offset 0x27BAF0C0 `
  --report "D:\PrivateResearch\carbon_master_hypothesis_v61.json"
```

**The 92 / +20 example originates from published MW2005 research, NOT an
authenticated Carbon PC schema.** The reference offset is historical
research context, not proven correct for your exact archive. Use reliable
independently observed offsets and validate them against original Carbon
loader behavior before drawing any conclusions.

## Safety limits

- Mapped archives are read-only; the scanner checks the same memory map's
  SHA-256 before and after scanning plus file identity/size/times. These
  checks are **best effort, not an atomic snapshot**. Keep game archives
  unchanged while running.
- Default maximum framed chunk size: 64 MiB. Default 100,000 signature
  hits and 10,000 candidate interpretations; limits fail closed.
- Report creation is exclusive; an existing report and the input archive
  cannot be overwritten.
- Chunk-signature hits in unrelated data can be false positives. A
  compressed or differently framed genuine source may not show a match.
- Original game assets are never uploaded to CI or the public repository.
- Every report permanently marks Carbon serialization, loader and in-game
  compatibility as unverified. `safe_to_install=false`.

## Tests

```sh
python -m unittest discover -s research/v61 -p test_v61.py -v
```

30 synthetic tests cover both byte orders and size conventions, ROOT/index
headers, ambiguity, unknown child framing, integer-only index hypotheses,
out-of-range framing, hash guards, mutation/path replacement checks, CLI
non-overwrite behavior and path isolation.

## Next source-backed decision

Run V61 privately on an **independently authenticated original Carbon PC
archive**. Compare the bounded candidate headers and child inventories against
the published V42 PC donor assumptions and original engine loader reads.
Only actual original source files plus verified loader consumption can decide
the native PC index, relocation and scene ownership format.

This tool is not an installable NFS Undercover PC mod.
