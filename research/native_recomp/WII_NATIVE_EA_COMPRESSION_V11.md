# V11 Undercover Wii EA/HUFF resource decoder analysis (2026-11-13)

## Original asset validation

* `GLOBAL/GLOBALA.LZC`: original wrapper `48 55 46 46 01 10 00 00`; little-endian output length `265564`; packed payload length `90437`; 16-byte wrapper + packed payload = `90453` bytes.
* Internal codec begins at offset 16 with big-endian `30 FB`, followed by 24-bit decompressed length `04 0D 5C` and escape byte `86`.
* The canonical Huffman lengths in this sample close at **width 12**, with **256 symbols**, then a symbol permutation table and encoded literals/repeats.
* Original resource `GLOBALA.BUN` is **265564 bytes**, exact byte-by-byte match against independently decoded source; SHA-256 for both is `04d3f350a47dd6623e31a31aee8ff7e3e91ec7f9f1e3c64a9cd565dfef2859a7`.
* Five previously validated JDLZ pairs also pass the new combined C++ dispatcher, bringing the checked resource set to **six pairs** and **26,080,852 decoded bytes**.

## Source-level evidence from the owner's Wii ELF

The original release ELF contains named PowerPC functions:

* `HUFFDecompress__FPUcPUc` at `0x802DF030`. Its wrapper validates the `HUFF` signature/version, passes the payload at input + `0x10` to `HUFF_decode`, and returns the wrapped output size.
* `HUFF_decode__FPvPCv` at `0x802DD7A4` swaps its arguments and branches to `HUFF_decompress`.
* `HUFF_decompress__FPUcPUc` at `0x802DCA48` is the full guest codec routine.
* `JLZDecompress__FPUcPUc` at `0x802DC8C4` handles the separate JDLZ family.

Those functions establish what can be targeted for a future HLE parity test, **not** that the game has booted natively.

## Implementation and validation

`huff_decoder_v11.h` implements: bounded HUFF v1 container recognition; 30FB/32FB/34FB method recognition; MSB-first EA bit parsing; variable-width unsigned codes; canonical length table; circular assignment of at-most-256 symbols; decode and repeat/escape/EOS handling; optional single/double prefix-sum unfilters; and strict output/read bounds.

* **47/47** original-free synthetic Huffman assertions passed, including extended headers, all three method variants and malformed length/copy boundaries.
* **25,000** deterministic mutated compressed-input cases passed under GCC AddressSanitizer and UndefinedBehaviorSanitizer. The test includes a valid original-free seed (2,451 variants decoded successfully) and verifies strict output/input limits.
* **11/11** synthetic combined resource dispatcher assertions passed.
* Six owner-original pairs were compared byte-for-byte by `ea_resource_cli_v11`; all passed.

No original Wii archive contents or generated proprietary game translation have been committed. The GPL-3.0 EA C&C Generals code was consulted as external background only; the V11 decoder is independently written from the public format description and validated against owner-provided binaries. Reference: https://psx-spx.consoledev.net/dev/ps1/cdr/cdromfileformats/compression/.

## Next native-port gate

Capture the original guest-side caller and output-buffer semantics for `HUFFDecompress`/`JLZDecompress`. Once the source-backed call trace is available, optional high-level substitutions can call the native C++ decoder without changing what the guest reads off disc. The native Wii runtime and system dependencies still need complete linking and boot verification.
