# V456: compose native cache operation implementations with full startup

The full-image compiler still treats dcbz, dcbst, eieio and other cache
instructions as no-ops. Older isolated tests provide V39/V43/V44 cache
event and ordering support and V67 flat-RAM dcbz. V456 adds separate
dcbst and eieio operations: guest effective addresses obey RA=0 and
32-byte alignment, dcbst has a distinct counter and last line, eieio
has an independent ordering count, and both issue host fences. This is
flat shared-RAM ordering, not hardware cache residency, writeback,
MMIO completion, locked cache or dynamic-code coherency.

The pinned original-free test composes the current complete-image
compiler patch stack with V39/V44/V67 and V456, generates independent
synthetic PPC in split and non-split modes, then compiles and executes
under ASan/UBSan. It tests five valid RAM cases including cached,
uncached and physical aliases and both effective-address modes, three
invalid/MMIO cache-line zero cases, unchanged adjacent bytes, distinct
store/flush/invalidate events, sync/eieio/isync, exact native ticks and
zero interpreter fallback. No owner startup scope is changed before
this independent composition passes.

The complete original game still has not booted. No proprietary
original instructions or resources are included.
