# GAMEPLAY VPAK six-chunk boundary audit

**Status: verified offline on supplied archives; read-only.** This is not a decoder for race payload semantics, a proof of platform loader ABI compatibility, or an in-game test.

## Reproduce

Run from the repository root with Python 3.10+ and your own local copies of the three archives:

```sh
python research/global_vpak/chunk_layout.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

The analyzer reads `GAMEPLAY.BIN` and, for Carbon PC, `GAMEPLAY.BAK` from the ZIPs. It validates record boundaries and compares whole serialized chunks in memory. Output contains aggregate counts and zero-based difference indices only, not extracted game content. Eleven new synthetic-only regression tests passed locally.

## Verified structure

All **767 indexed records** inspected across four source variants have exactly this six-chunk sequence in their declared auxiliary regions:

```text
sreV -> NpeD -> NrtS -> NtaD -> NpxE -> NrtP
```

The per-chunk size field is a little-endian 32-bit value at chunk offset +4 and includes the eight-byte chunk header. Every chunk has a size divisible by 16, and the six chunks exactly cover the declared auxiliary length. Each record also begins its text region with an `ErtS` string block.

The `NpxE` block has a little-endian count at offset +8. **For all 767 records, its length equals `16 + 16 * count`.** This validates a useful structural relationship but does not yet establish what each 16-byte element means. Other internal fields and the full semantics of the chunk names remain unverified.

| Source | Indexed records | Six-chunk records passing checks |
| --- | ---: | ---: |
| Carbon PC active `GAMEPLAY.BIN` | 190 | 190 |
| Carbon PC backup `GAMEPLAY.BAK` | 190 | 190 |
| Carbon PS2 `GAMEPLAY.BIN` | 190 | 190 |
| Undercover PS2 `GAMEPLAY.BIN` | 197 | 197 |

## Carbon PC backup vs Carbon PS2

Same-index, **exact byte-for-byte chunk** equality (190 pairs):

| Chunk | Identical pairs | Zero-based exception indices |
| --- | ---: | --- |
| `sreV` | 0 | All (platform-specific version/signature bytes differ) |
| `NpeD` | 190 | None |
| `NrtS` | 190 | None |
| `NtaD` | 187 | 74, 118, 169 |
| `NpxE` | 188 | 74, 118 |
| `NrtP` | 182 | 74, 118, 173, 174, 178, 179, 180, 182 |

**181/190 records** have all five non-`sreV` chunks identical. **181/190** also have identical entire pre-auxiliary string regions, including non-string bytes. This is stronger evidence than name-set overlap, but does not establish engine/runtime compatibility.

## Other comparisons

- **Carbon PC active vs backup:** `sreV`, `NpeD`, and `NrtS` match for all 190 records. `NtaD` and `NpxE` match for only 3/190; `NrtP` matches for 0/190. The active PC archive carries an editor signature, so do not treat active and backup as interchangeable baselines.
- **Undercover PS2 vs Carbon PS2:** same six-chunk grammar, but no same-index `NtaD`, `NpxE`, or `NrtP` chunk matches in the 190 pairs examined. Undercover has seven additional indexed records. Matching grammar alone does not make these payloads interchangeable.
- **Version chunks:** the eight-byte `sreV` payload is constant within each inspected platform source, differs between Carbon PC backup, Carbon PS2, and Undercover PS2, and is not interpreted here.

## Next technical targets

1. Reverse-engineer the `NpxE` 16-byte entry fields and validate counts and references against `NtaD` using independent evidence.
2. Characterize the eight Carbon PC/PS2 `NrtP` exceptions. Some are isolated to `NrtP` despite identical `NtaD` and `NpxE` blocks. Treat any relocation/offset interpretation as a hypothesis until tested.
3. Build a **reversible, single-record laboratory fixture** before attempting PC game runtime integration.
4. Keep all original archives, extracted binary payloads, and executable patches outside this public source-only repository.

The data source is the owner's privately supplied archives. No original game assets are included.
