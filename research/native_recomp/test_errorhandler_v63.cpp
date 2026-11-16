// Original-free semantic checks for the genuine Wii OSSetErrorHandler ordinary-index path.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace {
constexpr uint32_t ENTRY=0x805230B8u,STOP=0x80523340u;
constexpr uint32_t R13=0x8070E8E0u,SP=0x80082000u,ERROR_TABLE=0x806F4F70u;
uint64_t assertions=0;unsigned errors=0,disabled=0,restored=0,stops=0,forbidden=0;
struct Terminal{};
void check(bool b,const char*s){if(!b)throw std::runtime_error(s);++assertions;}
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){
 if(pc==ENTRY){++errors;return;}
 if(pc==0x805265ACu){++disabled;return;}
 if(pc==0x805265D4u){++restored;return;}
 if(pc==STOP)return;
 ++forbidden;throw std::runtime_error("unverified exception FPU branch or unsupported guest function dispatched");
}
bool handle_syscall(CPUContext&ctx){if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("unexpected system call");}ctx.is_running=false;++stops;throw Terminal{};}
void interpret_step(CPUContext&){++forbidden;throw std::runtime_error("PowerPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){++forbidden;throw std::runtime_error("unexpected MMIO16 read");}
uint32_t HW_Reg_Read32(uint32_t){++forbidden;throw std::runtime_error("unexpected MMIO32 read");}
void HW_Reg_Write16(uint32_t,uint16_t){++forbidden;throw std::runtime_error("unexpected MMIO16 write");}
void HW_Reg_Write32(uint32_t,uint32_t){++forbidden;throw std::runtime_error("unexpected MMIO32 write");}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char **argv)try{
 check(argc==2,"usage: errorhandler_test PRIVATE_DOL");
 nwii::loader::Executable exe;check(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"original Wii error handler test image invalid");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr std::array<uint32_t,7> indices{0u,1u,2u,7u,15u,17u,31u};
 constexpr std::array<uint32_t,6> states{0u,0x8000u,0x2000u,0xA000u,0x12345678u,0xffffffffu};
 for(size_t t=0;t<indices.size()*states.size();++t){
  const auto index=indices[t%indices.size()];
  const auto msr=states[t/indices.size()];
  const auto previous=0xABC10000u+uint32_t(t);
  const auto next=0x805223F8u+4u*uint32_t(t);
  const auto addr=ERROR_TABLE+4u*index;
  ctx->mmu.write32(addr-4,0x11118888u+uint32_t(t));
  ctx->mmu.write32(addr,previous);
  ctx->mmu.write32(addr+4,0x22229999u+uint32_t(t));
  ctx->mmu.write32(SP-40u,0xA5000000u+uint32_t(t));
  const uint32_t r28=0x11223344u,r29=0x22334455u,r30=0x33445566u,r31=0x44556677u;
  ctx->pc=ENTRY;ctx->is_running=true;ctx->lr=STOP;ctx->msr=msr;
  ctx->gpr[1]=SP;ctx->gpr[3]=index;ctx->gpr[4]=next;ctx->gpr[13]=R13;
  ctx->gpr[28]=r28;ctx->gpr[29]=r29;ctx->gpr[30]=r30;ctx->gpr[31]=r31;
  auto before_error=errors,before_disable=disabled,before_restore=restored,before_stop=stops;
  bool stopped=false;try{run_game(*ctx);}catch(const Terminal&){stopped=true;}
  check(stopped&&!ctx->is_running&&ctx->pc==STOP,"original Wii OSSetErrorHandler did not return to test stop");
  check(ctx->mmu.read32(addr)==next,"original handler table store differs");
  check(ctx->mmu.read32(addr-4)==0x11118888u+uint32_t(t)&&ctx->mmu.read32(addr+4)==0x22229999u+uint32_t(t),"handler table write exceeded 32-bit slot");
  check(ctx->gpr[3]==previous,"original handler registration did not return old handler");
  check(ctx->msr==msr,"original interrupt enable save/restore altered guest MSR");
  check(ctx->gpr[1]==SP&&ctx->lr==STOP,"original stack or return address not restored");
  check(ctx->gpr[28]==r28&&ctx->gpr[29]==r29&&ctx->gpr[30]==r30&&ctx->gpr[31]==r31,"original handler callee-saved registers changed");
  check(ctx->gpr[13]==R13&&ctx->mmu.read32(SP-40u)==0xA5000000u+uint32_t(t),"original guest small-data pointer/stack canary changed");
  check(errors==before_error+1&&disabled==before_disable+1&&restored==before_restore+1&&stops==before_stop+1,"wrong native original function call counts");
  check(ctx->mmu.read32(SP+4u)==STOP&&ctx->mmu.read32(SP-4u)==r31&&ctx->mmu.read32(SP-8u)==r30,"original saved LR/r31/r30 frame slots mismatch");
 }
 check(!forbidden,"unverified original guest path or interpreter fallback reached");
 std::cout<<"PASS: "<<assertions<<" V63 original Wii OSSetErrorHandler ordinary-index native assertions across "<<indices.size()*states.size()<<" cases, no interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V63 native semantics failed: "<<e.what()<<'\n';return 1;}
