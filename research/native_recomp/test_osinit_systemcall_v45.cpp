// Independent native regression for genuine Wii __OSInitSystemCall PPC.
// No original game instruction bytes or generated game code are embedded here.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x805290C8u,SOURCE=0x805290A8u,COPY=0x80004338u;
constexpr uint32_t DC=0x80522320u,IC=0x80522378u,STOP=0x80004900u;
constexpr uint32_t DEST=0x80000C00u,SP=0x80082000u;
struct NativeStop{};
uint64_t checks=0;
void require(bool b,const char*why){if(!b)throw std::runtime_error(why);++checks;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0,unexpected=0,interpreter=0;
static std::array<uint32_t,5> calls{};
void trace_call(uint32_t pc,CPUContext&){
 constexpr std::array<uint32_t,5> roots{ENTRY,COPY,DC,IC,STOP};
 for(size_t i=0;i<roots.size();++i)if(pc==roots[i]){++calls[i];return;}
 ++unexpected;throw std::runtime_error("unexpected native dispatch root");
}
bool handle_syscall(CPUContext&ctx){
 if(ctx.pc!=STOP){++unexpected;throw std::runtime_error("unexpected test syscall PC");}
 ++stops;ctx.is_running=false;throw NativeStop{};
}
void interpret_step(CPUContext&){++interpreter;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){}
void HW_Reg_Write32(uint32_t,uint32_t){}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
 require(argc==2,"usage: original native executable PRIVATE_DOL");
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"private Wii test DOL rejected");
 std::array<uint8_t,28> original{};
 bool found=false;
 for(const auto&section:exe.sections)if(section.address==SOURCE&&!section.is_bss&&section.data.size()==0x80){
  for(size_t i=0;i<original.size();++i)original[i]=section.data[i];
  found=true;
 }
 require(found,"original syscall stub unavailable in private DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr unsigned trials=6;
 for(unsigned run=0;run<trials;++run){
  for(unsigned i=0;i<28;++i)ctx->mmu.write8(SOURCE+i,original[i]);
  const uint8_t fill=static_cast<uint8_t>(0xA0u+run*13u);
  for(unsigned i=0;i<256;++i)ctx->mmu.write8(DEST+i,fill);
  ctx->mmu.write8(DEST-1u,0xC7);
  ctx->mmu.write8(DEST+256u,0xE9);
  ctx->mmu.write8(SOURCE-1u,0xAB);
  ctx->mmu.write8(SOURCE+28u,0xBC);
  ctx->gpr[31]=0x5C000000u+run;
  ctx->gpr[1]=SP;
  ctx->lr=STOP;
  ctx->pc=ENTRY;
  ctx->is_running=true;
  ctx->guest_flush_count=0;
  ctx->guest_invalidate_count=0;
  ctx->guest_sync_count=0;
  ctx->guest_isync_count=0;
  const uint32_t before_stops=nwii::runtime::stops;
  const auto before_calls=nwii::runtime::calls;
  const uint64_t before_instructions=ctx->inst_count;
  bool stopped=false;
  try{run_game(*ctx);}catch(const NativeStop&){stopped=true;}
  require(stopped,"expected explicit synthetic termination");
  require(ctx->pc==STOP&&!ctx->is_running,"incorrect synthetic stop PC/state");
  require(nwii::runtime::stops==before_stops+1,"expected one controlled syscall");
  require(ctx->gpr[1]==SP&&ctx->gpr[31]==0x5C000000u+run&&ctx->lr==STOP,
          "original PowerPC ABI register or stack restoration failed");
  require(ctx->inst_count>before_instructions+100,"too few authentic instructions executed");
  for(size_t i=0;i<before_calls.size();++i)
    require(nwii::runtime::calls[i]==before_calls[i]+1,
            "missing original PPC helper dispatch");
  for(unsigned i=0;i<28;++i){
    require(ctx->mmu.read8(DEST+i)==original[i],"system-call vector copy mismatch");
    require(ctx->mmu.read8(SOURCE+i)==original[i],"system-call vector original changed");
  }
  for(unsigned i=28;i<256;++i)
    require(ctx->mmu.read8(DEST+i)==fill,"system-call vector copy exceeded 28 bytes");
  require(ctx->mmu.read8(DEST-1u)==0xC7&&ctx->mmu.read8(DEST+256u)==0xE9,
          "vector region canaries overwritten");
  require(ctx->mmu.read8(SOURCE-1u)==0xAB&&ctx->mmu.read8(SOURCE+28u)==0xBC,
          "source vector canaries overwritten");
  require(ctx->guest_flush_count==8&&ctx->guest_invalidate_count==8,
          "original cache routines did not process 8 cache lines");
  for(unsigned i=0;i<8;++i){
    require(ctx->guest_flush_lines[i]==DEST+32u*i,
            "guest flush-line trace mismatch");
    require(ctx->guest_invalidate_lines[i]==DEST+32u*i,
            "guest instruction invalidate trace mismatch");
  }
  require(ctx->guest_last_flush==DEST+224u&&ctx->guest_last_invalidate==DEST+224u,
          "unexpected last guest cache-line address");
  require(ctx->guest_sync_count==2&&ctx->guest_isync_count==1,
          "original system-call/cache memory-barrier sequence changed");
 }
 require(nwii::runtime::unexpected==0&&nwii::runtime::interpreter==0,
         "unexpected syscall/function or interpreter fallback");
 std::cout<<"PASS: V45 "<<checks<<" original native system-call initializer assertions across "
          <<trials<<" guest configurations, no interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V45 native regression failed: "<<e.what()<<'\n';return 1;}
