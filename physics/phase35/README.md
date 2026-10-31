# Phase 35: Undercover PS2 and Carbon PS2 share the angle lookup

**Status: offline verification, not a gameplay patch.** The original user-owned PS2 executables were used locally. Their game code, original LUT bytes and assets are not redistributed.

## Verified cross-game match

| Property | Undercover PS2 | Carbon PS2 |
|---|---|---|
| Original ELF SHA256 | 6c53252622348ee5981685420a27e6914e02757e739945f583940b8c35814646 | 1bcc9ff09b2dce748ab78453338c2733375a55ee4dd9a8ee534db9803a5e5d9b |
| Fixed-point angle helper | 0x00172CB8 | 0x00173780 |
| Helper size | 376 bytes (94 words) | 376 bytes |
| 257-entry LUT VA | 0x0063E138 | 0x00606A98 |
| 514-byte LUT SHA256 | 8f1184671782f4df2c006d4ef6674700aff401127a23d09c40f4475ecffe2929 | **same** |

**91/94 helper instructions are identical.** The only three differing words (relative offsets +0x3C, +0x4C, +0xA8) materialize the relocation-specific pointer to the table; the rest of the algorithmic instruction stream is identical. The two 257-entry tables are **byte-for-byte identical**.

This rules out a different **PS2 angle table** as the cause of lighter Undercover PS2 handling. It does **not** establish that Carbon **PC** uses the same table, nor that steering behavior across games is identical.

## Reconstructed angle-helper behavior

The helper approximates atan2(y,x) as a **16-bit whole-turn angle**. It selects quadrants, normalizes to a first-octant ratio, looks up adjacent unsigned 16-bit table elements and interpolates with the 8-bit fractional index. The later Undercover steering routine sign-extends the returned angle and scales it by 360/65536. Default MIPS FCSR round-to-nearest is assumed for the reference implementation. Rare near-table-endpoint and nonfinite cases remain unmodeled.

Sample predictions derived from the *actual* locally extracted original LUT:

| Input (x, y) | Raw angle | Decoded degrees | Exact atan2 degrees |
| --- | --- | --- | --- |
| (0.8,3.8) | 0x378D | 78.118286 | 78.111342 |
| (0.8,11.0) | 0x3D0B | 85.841675 | 85.840358 |
| (1,0.1) | 0x040F | 5.707397 | 5.710593 |
| (-1,-1) | 0xA000 | -135.000 | -135.000 |

These are derived **helper outputs**, not observed wheel angles. The helper table does not by itself explain handling feel.

## Later steering-code dependencies

Within Undercover PS2 DoHumanSteering (0x004082B0), distinct chassis state fields affect the branch:
- chassis +0x8C: input shaped by input * abs(input), with a ~0.12 branch threshold;
- chassis +0x48: selects the (state48,3.8), (-state48,11.0) or center 55-degree angle path;
- racer +0x160: dynamically scales the intermediate angle with 1+0.5*racer160, then upper-caps at 55;
- chassis +0x9C: multiplied by 360 and used as another state-dependent steering boundary;
- chassis +0x64, +0xD8, +0xC0: combined into (state64-stateD8)/(60*stateC0), subsequently used in a correction branch;
- output writes racer +0x188 (steering) and +0x19C (shaped input).

The meanings of many of these fields, the rest of the state machine, and the Carbon PC equivalents **remain unresolved**. Console object offsets must not be copied into PC.

## Verification / artifacts

The complete local source-only audit is in the Phase35 downloadable research ZIP (kept outside this repository); it extracts the source LUT from each **user-owned SHA-matching** ELF on demand and produces sample CSV and JSON reports without redistributing the original LUT. **21/21** model/binary tests passed locally, including deliberate SHA corruption rejection. The accompanying GitHub reference code reproduces the *mathematical algorithm* with the table supplied at runtime, but this smaller GitHub version is not the full ELF verifier.

Next step: map those original motion-state fields to the Carbon PC DoHumanSteering routine at 0x006EF540 using **read-only observation**. Keep the Phase30 tire-force alpha disabled because the user's CCX felt heavier with it.
