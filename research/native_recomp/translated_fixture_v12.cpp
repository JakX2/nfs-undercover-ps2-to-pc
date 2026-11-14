// Original-free, synthetic function fixture with NWiiRecomp's real ABI.
#include "runtime/cpu_context.h"
extern "C" void run_game(nwii::runtime::CPUContext& ctx) {
    ctx.gpr[3] = ctx.gpr[3] + ctx.gpr[4]; // 32-bit PowerPC wraparound
    ctx.mmu.write32(0x80001000u,ctx.gpr[3]);
    ctx.pc = ctx.lr;
    ctx.is_running = false;
}
