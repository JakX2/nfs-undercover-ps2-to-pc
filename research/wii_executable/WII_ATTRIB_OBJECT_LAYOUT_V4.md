# Wii Undercover V4: typed Attrib collection/attribute layout bridge

**2026-11-10.** The original Wii PowerPC ELF was examined read-only. The owner-original ELF is not distributed. This research introduces source-only portable C++17 that can interpret a bounded **32-bit, big-endian Wii memory snapshot** without treating any Wii pointer as a native 64-bit PC pointer.

## Assembly-backed field accesses

| Named Wii function | Wii address | Verified behavior |
|---|---|---|
| GetCollection (Attribute) | 0x8007B2BC | Read attribute +0x04 as collection pointer |
| IsValid (Attribute) | 0x8007B208 | Return descriptor pointer at attribute +0x08 nonzero |
| IsMutable (Attribute) | 0x8007B21C | Require collection +0x04 and descriptor +0x08 nonzero, then source at collection +0x1C must be zero |
| GetKey (Attribute) | 0x8007B24C | Descriptor pointer at +0x08, descriptor byte +0x0B flag bit 0x80, return descriptor u32 at +0x00 if set |
| GetCollectionKey (Attrib) | 0x8007A970 | Collection +0x10, zero if null |
| GetCollectionClassKey (Attrib) | 0x8007A988 | Collection +0x14 points to class whose +0x00 gives key; zero for absent collection/class |
| GetCollectionParent (Attrib) | 0x8007A9B4 | Collection +0x0C, zero if null |
| GetCollectionSource (Attrib) | 0x8007A9E8 | Collection +0x1C, **original has no null guard** |
| IsSourceVault (Attrib) | 0x8007A9D4 | Compare collection +0x1C source word with supplied vault pointer; original has no null guard |

The Attribute assignment operator at 0x8007B1E4 copies four 32-bit fields, consistent with a 16-byte Wii object copy. We do **not** invent names for unused fields and we do not claim identical PS2 layout.

## Reproducible new source

- attrib_memory.hpp/.cpp: WiiAddressSpace maps bounded memory regions and reads 8-bit or big-endian 32-bit values. It rejects absent/unmapped/overflowing/unaligned values, overlapping regions and excessive region sizes. Read-only.
- Reconstructed getters provide null handling based on original branch behavior on valid snapshots. The unguarded Wii operations produce host-side exceptions for unmapped objects rather than emulating memory faults.
- DecodeTweakFields connects decoded original Wii object fields with the V3 host EncodeTweakPacket function. Attribute name and index are supplied separately; no claim is made about their source in live Wii memory.

## Validation

- test_attrib_memory.cpp exercises a complete synthetic attribute → descriptor/collection/class → formatted tweak-message flow, all **256 possible flag bytes**, null/missing class or descriptor, parent and vault matching, mutability conditions, unaligned or out-of-region reads, overlapping ranges and oversized memory.
- The new C++ source/test passes locally with **both GCC and Clang** under AddressSanitizer and UndefinedBehaviorSanitizer. Existing **37** Wii ELF/DOL/call-graph synthetic Python tests still pass.
- The dedicated GitHub Actions workflow now compiles and runs this additional reader/integration test under Clang sanitizers. CI has no access to owner game binaries, only original-free test fixtures.

## Limits and next evidence gate

These are verified **field-offset and accessor semantics**, not a complete object model, full decompilation, emulator behavior match, original Wii ABI, Windows gameplay engine or playable port. This bridge is suitable for host-side controlled validation and future incremental PC code reconstruction.

Next: capture an owner-private read-only example of an actual Wii Attrib object from emulated RAM, compare its accessor/packet behavior against these controls, then reconstruct the selected vehicle speed and physics function family without assuming Wii struct pointer offsets are suitable for PC.
