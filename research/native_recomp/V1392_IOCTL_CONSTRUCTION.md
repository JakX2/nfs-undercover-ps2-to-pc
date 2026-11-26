# V1392 original ioctl request construction to first cache flush

V1389 passed 8/8 owner allocation returns with 18 stores, 11 heap stores and one metadata store per trial. Continue from that same outer-dispatch poll, without a guest restart or request rewrite. Capture original STM ioctl arguments at the verified entry, fence native writes to the allocated request and caller stack, retain full outside-request heap and metadata shadows, and compare all seven known wire fields with the original input arguments. The callback value must occur at a unique aligned extension word; its precise field and userdata provenance remain a separate private dataflow question. Stop before executing the first actual DCFlushRange body. No new cache syscall or IOS submission is claimed. Owner verification pending.

## V1394 bounded frame retry

V1392 owner run 45837165950 failed in trial 0 at wrapper store ordinal 24 (range category 7, no accepted stores). The original allocator return and native translation audit succeeded before this refusal. The construction fence originally allowed only eight bytes above the current SP, despite a verified larger wrapper frame. Restrict its stack write region to the actual wrapper frame [current SP, incoming SP), not the preceding allocator scratch area. No global, caller-frame or additional heap writes are admitted. Add a synthetic local store at SP+16 and report the base-register category for any further owner refusal. This is a candidate correction, not proof of the original rejected store's provenance. Owner rerun required.

## V1395/V1396 verification hardening

V1394's original-free job 139973209310 passed 40 construction cases under ASan/UBSan. V1395 adds direct caller-frame escape, corrupted local store, and both first-flush branch tests (74 synthetic cases); the owner log filter now preserves only the bounded base-register class. V1396 adds direct focused workflow triggers for construction changes and a private static classification of the previously refused instruction (category only, no original instruction word, register value, or address). No claim of successful original construction until the owner run completes.
