# V744: later possible handler dependency census

V740 found the actual ordinal-3 call to __OSGetSystemTime. V744 privately walks the remaining handler with both branch paths and explicitly hypothetical call-return edges. Reports only bounded classes, known SDK names, repeated system-time identity, original extents and potential restore aliases. The output is not a dynamic trace; it does not authorize any additional call or indicate which path is taken. Used to prepare the next native boundary without exposing original instructions or raw symbols.

## V746

The original-free V744 test failed on the minimal two-instruction external-tail fixture because the generic walker called `shape`, whose full original handler contract requires at least four words and a store. Separate the direct/indirect call census from that unrelated restriction. Original inputs still go through SHA and full-handler DOL/ELF verification before the walker. Retest pending.
