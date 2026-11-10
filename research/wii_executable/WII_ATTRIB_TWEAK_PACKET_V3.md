# Wii Undercover V3: Attrib tweak-message serialization reconstruction

**2026-11-10.** Assembly-informed read-only reconstruction using the owner's original Wii ELF. No retail executable, original binary data or extracted proprietary game assets are committed. The new portable C++ source is independently written.

## PowerPC function evidence

| Named Wii symbol | Wii address | Size | Role |
|---|---|---:|---|
| NibbleChar__6AttribFUc | 0x8007ADAC | 28 | Convert a hexadecimal nibble to a character |
| ValueToText__6AttribFPCvUiPc | 0x8007ADC8 | 112 | Convert binary bytes to lowercase hexadecimal text |
| CopyString__6AttribFPcPCc | 0x8007AE38 | 44 | Copy through NUL, return pointer at final NUL |
| IntToString__6AttribFPcUi | 0x8007AE64 | 120 | Convert unsigned 32-bit integer to decimal |
| EncodeTweakPacketPrefix__6AttribFRQ26Attrib9AttributeUiPCcPc | 0x8007AEDC | 284 | Build attribute packet path prefix |
| TweakAttribute__6AttribFRQ26Attrib9AttributeUiPCcPCvUi | 0x8007AFF8 | 148 | Append payload as hex, optionally dispatch |

The call sites were inspected directly in the owner-original PowerPC assembly. The original TweakAttribute accesses gMessageSender__6Attrib at 0x8070AEA4 via the r13-relative small-data base, checks for null, and dispatches using an indirect bctrl only if set.

## Inferred complete packet syntax

The helper emits a fixed literal prefix, three eight-digit hexadecimal keys, decimal element index, field name, literal delimiter and a hexadecimal payload. A synthetic representative is:

~~~text
AttribSys.rev\11223344\a1b2c3d4\01020304\42\Speed\[]:00107f80ff
~~~

- The literal initial fragment is AttribSys.rev followed by a backslash (verified in the original Wii .data).
- The literal pre-payload fragment is a backslash followed by [, ], and : (verified in the original Wii .sdata).
- The three 32-bit fields are rendered as their four **big-endian Wii memory bytes**, with lowercase hex, preserving leading zeroes.
- The element index uses unsigned decimal notation. The name is copied without escaping in original code, stopping at NUL.
- Each original payload byte produces high and low hexadecimal digits. The original final output receives a NUL byte before the callback.
- The three key values are sourced through GetCollectionClassKey, GetCollectionKey and GetKey. The first two have a zero fallback for missing collection or class data; GetKey checks a descriptor validity flag. Raw Wii structures are not reused by host code.

## Portable C++17 implementation

Added attrib_tweak.hpp, attrib_tweak.cpp and test_attrib_tweak.cpp. The host interfaces use a plain TweakFields snapshot with three uint32 keys, a uint32 index, a string_view name, and a byte-buffer payload. EncodeTweakPacketPrefix reconstructs the original prefix, EncodeTweakPacket appends hex bytes, and TweakAttribute calls an optional host callback once and returns the packet.

**Intentional safety changes:** The original function builds into a fixed stack buffer without an apparent payload-size guard. The PC version uses std::string, rejects a nonempty null payload and an embedded NUL name, places a 1 MiB cap on the complete packet, and substitutes std::function for the Wii callback pointer. It is a behavioral adaptation, **not** Wii ABI-equivalent source or object layout.

## Verification

Original-free C++ tests validate a full synthetic packet, empty payload, big-endian 32-bit key formatting, zero/max integer boundaries, high-bit data bytes, optional callback and error-handling/size bounds. Locally, the C++17 test passed under AddressSanitizer and UndefinedBehaviorSanitizer, with no reported errors. The existing 37 synthetic Python tests passed as well.

The dedicated Wii GitHub Actions workflow now compiles and executes this sanitizer-enabled test alongside the earlier Attrib text regression executable. The original executable was used strictly for local analysis and is not available to CI.

## Limits and next step

This is not a live Wii-emulator differential test, recovered packet receiver, reconstructed attribute mutation engine or runnable Windows game. The receiver path, remaining global callback semantics, object ownership and cross-platform PS2 correspondence are still open. The next decomp pass should reconstruct typed attribute/collection accessors and trace the receiver graph, while also beginning a narrow vehicle/world runtime interface from named Wii symbols.
