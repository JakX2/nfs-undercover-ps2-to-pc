# IPC ring dispatch contract

Verified prior original native profiling return: run 45849960908, eight trials, 41 instruction visits and four profile stores per trial, with the original ring and request preserved. Source witness run 45849598881 passed 42 cases.

The older SDK reconstruction in zeldaret/tp, libs/revolution/src/ipc/ipcclt.c, suggests a send operation writes the request physical address to PPCMSG, advances the read pointer and count, decrements mailbox credit, then writes PPCCTRL. The independent single-request observer tests those three exact memory updates, permits no unrelated ring/request changes, and requires externally authenticated device-write observations. It does not write memory, implement IOS service, or fabricate an available credit. Ring and credit object identity, actual store sites, exact branch paths, and actual device integration are not yet established for this next lane. Source-only run 45850503907 passed 100 synthetic cases under ASan/UBSan. Private geometry preflight is introduced at 4e4a622; the original mailbox-credit object and corridor were subsequently authenticated in owner run 45850694194.


## Verified private geometry

Run 45850694194 passed four source-only test groups and private original authentication. The route from the profile return to the second mailbox write call contains 53 labels capable of reaching that call, five outgoing static edges, one pre-message store site, and three post-message direct word-store sites. The first message write and control read dominate the final control write in the bounded static graph. The credit and ring are distinct validated writable objects.

The pre-message store site's actual behavior and all three post-message destinations/values remain runtime requirements. Do not infer the pre-message branch is taken, mutate credit, authorize MMIO, or service the deferred IOS request based solely on this geometry. The next implementation should join the read-only instruction/memory witness to the existing StmDeferredEventGate at the real PPCMSG/PPCCTRL helpers, then establish a native masked service boundary.


## Original native mailbox submission verified

- Source run 45856274973 passed 15 instruction/MMIO provenance cases and the generated hook installer regressions. Run 45856274811 passed 28 cases joining the witness to the real native IOS transport (both descriptor orders, empty/nonempty input, explicit deferred acceptance).
- The first two owner builds (45855862408 and 45856274873) authenticated the original helper roots, 70 labels, three direct edges and three return hooks, but failed compilation at an existing global witness name. The new private namespace was renamed; a synthetic generated-header compile regression now checks coexistence with that existing symbol.
- The pinned NWiiRecomp MMU forwards physical addresses rather than raw guest aliases to HW_Reg_Read32/Write32. The observer now computes the actual guest effective address, validates its alias and compares the physical callback address. It does not broaden the allowed device registers.
- Owner run 45856550747 passed eight original trials. Each visited 60 original instructions, executed three authenticated ring/credit stores, called the three real helpers, performed two native mailbox writes and one native control read, then returned to the original caller continuation with EE masked. The native IOS transport held the queued request. The pre-message alternative store path was not taken. The original request, stack, profiling objects and scheduler context were preserved. No interpreter fallback or fifth IOS service occurred in that run.
- A separate optional deferred-acceptance owner mode has been added. It services the request at this exact authenticated return boundary and verifies the unchanged CPU state, request, ring, and pending ACK/no-reply condition. Its owner result is pending; do not describe the actual async event as accepted until that run passes.
