# Native mtmsr continuation dispatch

NWiiRecomp emits asynchronous callback checks after writes that enable MSR.EE, but its outer dispatch switch does not directly recognize the resume instruction after `mtmsr`. The original-free patch adds explicit guest continuation cases in both split and non-split code generators, only when the successor is an analyzed instruction of the same function. A wholly synthetic PowerPC program exercises generated native mtmsr, interrupt entry, native handler rfi, continuation, and deterministic termination for 64 trials per output mode. CI pending; does not claim original IRQ handler execution.

The independent synthetic runner also applies the existing exact syscall-PC fix and adds a direct register-bank patch for all four SPRGs. Each generated IRQ writes r8-r11 into SPRG0-3 and reads them back into r12-r15; non-interrupted trials preserve the original SPRGs. This proves shared scratch-register state for the original vector lane once CI passes.
