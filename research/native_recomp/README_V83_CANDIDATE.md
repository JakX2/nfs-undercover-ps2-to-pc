# V83 candidate: first synchronous IOS_Open return to second STM open

Requires verified V82. The original synchronous submit restores interrupts,
then releases its request using the original allocator-free function.
The second original IOS_Open call (0x8052B0B4 -> 0x80519944) must arrive with
a distinct authenticated STM device pathname, an intact ABI stack, restored
interrupt state and no remaining external IRQ. The first device descriptor
must exist in the native IOS service. No request, return value or register is
fabricated by the host; the path check reads authenticated initialized data.

This candidate stops before the second IOS_Open body, not after a completed
second transaction. V82 verified in run 44236726199; focused V83 workflow is now enabled.
Assumptions about allocator ABI are intentionally fail-closed and must be
validated against original runtime evidence before marking the stage verified.
