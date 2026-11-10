# Wii Undercover V2: symbol-bounded PowerPC direct-call graph

**2026-11-10.** Read-only, owner-original analysis of Wii NfsMWRelease.elf, previously shown byte-identical with the corresponding Wii DOL loaded sections. This is a static branch-with-link census, not a complete CFG, runtime trace or PC port.

## Original Wii ELF call census

| Metric | Result |
|---|---:|
| Named, sized ELF function ranges scanned | **27,941** |
| PPC unconditional direct branch-with-link (bl) sites | **90,861** |
| Conditional direct branch-with-link (bcl) sites | **0** |
| Direct call sites resolving inside named function ranges | **90,854** |
| Direct call sites without a named containing function | **7** |
| Resolved destinations at function entry | **87,626** |
| Resolved destinations inside function spans | **3,228** |
| Distinct named caller–callee ordered pairs | **59,129** |
| Indirect branch-with-link calls (bctrl/blrl) | **13,323** |
| Nonlink unconditional branch sites, NOT calls | **45,780** |
| Nonlink conditional branch sites, NOT calls | **101,495** |
| Indirect nonlink branch or return sites, NOT calls | **28,798** |
| Calls back into own containing function | **182** |

The seven unmatched sites come from file/console-support routines and target nearby code addresses without sized function symbols; this does not prove that the destination code is absent. A branch into a named function's interior is not necessarily a normal C++ function call. These counts classify the encoded words within symbol bounds, not dynamically executed edges.

## Branch decoding rules

- PPC opcode 18 with link bit set means a direct unconditional branch-with-link. Opcode 16 with the link bit set is a direct conditional branch-with-link. Both decode and sign-extend the appropriate displacement and handle absolute-address vs PC-relative modes.
- Opcode 19, XO 16 or 528 and link bit set classifies register-based branch-with-link. The indirect target is deliberately unresolved.
- Ordinary nonlink branches and returns are counted separately, never silently treated as direct calls.
- Calls are mapped to nonoverlapping, 4-byte-aligned ELF STT_FUNC ranges with bounded binary search. Invalid symbol overlap fails closed.

## Important symbol-to-source-file qualification

ELF STT_FILE labels identify source filenames, but symbol-table sh_info separates local symbols from the later global/weak symbols. It is **incorrect** to assign every global function to the last preceding source file marker. In this original:

- **1,564** local functions have supported nearby STT_FILE compilation-unit association, spanning **195** units with local functions.
- **26,377** global/weak functions have no justified compilation-unit mapping from symbol-table ordering alone.
- **506** direct call sites are local-to-local within one confirmed unit, **300** are local-to-local between different confirmed units, and **90,048** have at least one function whose compilation unit is not established. There are **72** distinct verified ordered unit-to-unit direct relationships.

The original 774 unique STT_FILE labels remain correct as names present in the ELF; they are not 774 verified groupings of the entire function table. The remaining groupings need further compiler metadata or independent source evidence.

## Example: first reconstructed Attrib routines

The exact-name, owner-local focused graph identifies two callers of 28-byte NibbleChar__6AttribFUc, at Wii address 0x8007ADAC:

- ValueToText__6AttribFPCvUiPc has 2 encoded direct call sites.
- TweakAttribute__6AttribFRQ26Attrib9AttributeUiPCcPCvUi has 2 encoded direct call sites.

Thus TweakAttribute is a practical next reconstruction target, and the call topology independently connects the earlier hex conversion implementation with its original caller. This is not proof of runtime execution or an equivalent PS2 calling convention.

## Reproducible source-only tools

The new wii_ppc_call_graph.py scans the owner-local ELF read-only, emits aggregate JSON, and optionally supplies at most 20 incoming and outgoing function names for one exact focus symbol. It never writes raw instructions, model bytes, complete function listings or modified game images.

~~~sh
python research/wii_executable/wii_ppc_call_graph.py --wii-elf NfsMWRelease.elf

python research/wii_executable/wii_ppc_call_graph.py \
  --wii-elf NfsMWRelease.elf \
  --focus-symbol NibbleChar__6AttribFUc
~~~

The new test_wii_ppc_call_graph.py adds **24 original-free synthetic regression cases**. Together with the earlier ELF/DOL tests, **37/37 Python tests passed locally**, and the C++ Attrib regression binary compiled and passed locally. CI is configured on this branch and must be checked after pushing.

## Remaining engineering gates

1. Reconstruct the Attrib TweakAttribute caller as a small semantic unit, with validated parameter contracts and host C++ tests.
2. Recover register-indirect dispatch and compiler-specific global symbol/source ownership without false assignments.
3. Select Wii AI, vehicle-physics and world-streaming entry functions from the real named graph. Use the PS2 MIPS executable for independently checked behavior, not address equivalence.
4. Preserve separate original-free source and test branches; do not publish owner game binaries, extracted compiled code or proprietary resource payloads.

**Nothing in this milestone proves a playable Windows build or Undercover gameplay rendering.**
