// Bounded original PPC exec-params tests. Original instructions are never in source.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
constexpr uint32_t ENTRY=0x80523B1Cu,STOP=0x80004900u;
constexpr uint32_t FLAG=0x800030F0u,DEST=0x80037000u,SOURCE=0x80038000u;
constexpr uint32_t SP=0x80082000u,LR=STOP;
uint64_t checks=0;
void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);++checks;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0,fallthrough=0,exec_entries=0,copy_entries=0;
void trace_call(uint32_t pc,CPUContext&){
 if(pc==ENTRY){++exec_entries;return;}
 if(pc==0x80004338u){++copy_entries;return;}
 if(pc==STOP){return;}
 throw std::runtime_error("unexpected native dispatch target");
}
bool handle_syscall(CPUContext& ctx){
 if(ctx.pc!=STOP){++fallthrough;throw std::runtime_error("unexpected system call");}
 ++stops;ctx.is_running=false;return true;
}
void interpret_step(CPUContext&){++fallthrough;throw std::runtime_error("interpreter fallback");}
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
int main(int argc,char** argv)try{
 check(argc==2,"usage: test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"wrong DOL entry");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 const uint32_t cases[]={0u,0x7fffffffu,SOURCE,0x80000000u};
 for(unsigned run=0;run<sizeof(cases)/sizeof(*cases);++run){
  const uint32_t ptr=cases[run];
  const bool copy=ptr>=0x80000000u;
  ctx->mmu.write32(FLAG,ptr);
  for(uint32_t i=0;i<32;++i){
   const uint8_t value=uint8_t((run*43+i*17+9)&255);
   ctx->mmu.write8(DEST+i,0xA5u);
   if(copy)ctx->mmu.write8(ptr+i,value);
  }
  const uint8_t source_byte=copy?ctx->mmu.read8(ptr):0;
  ctx->mmu.write8(DEST-1,0xC7u);
  ctx->mmu.write8(DEST+28,0xD7u);
  ctx->mmu.write8(DEST+29,0xE7u);
  const uint32_t prev_stop=nwii::runtime::stops;
  const uint32_t prev_entry=nwii::runtime::exec_entries;
  const uint32_t prev_copy=nwii::runtime::copy_entries;
  ctx->pc=ENTRY;ctx->lr=LR;ctx->gpr[1]=SP;ctx->gpr[3]=DEST;
  ctx->gpr[29]=0x1BCDA5E0u+run;
  ctx->is_running=true;
  const uint64_t inst=ctx->inst_count;
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==STOP,"unexpected native exit location");
  check(ctx->lr==LR&&ctx->gpr[1]==SP,"guest LR or SP corrupted");
  check(ctx->gpr[29]==0x1BCDA5E0u+run,"callee-saved register corrupted");
  check(ctx->inst_count>inst,"original function did not run");
  check(nwii::runtime::stops==prev_stop+1,"explicit syscall stop missing");
  check(nwii::runtime::exec_entries==prev_entry+1,"original exec-params dispatch missing");
  check(nwii::runtime::copy_entries==prev_copy+(copy?1u:0u),
        "original memcpy must be dispatched exactly on valid pointer path");
  check(ctx->mmu.read8(DEST-1)==0xC7u,"destination underrun");
  check(ctx->mmu.read8(DEST+28)==0xD7u&&ctx->mmu.read8(DEST+29)==0xE7u,
        "destination overrun");
  for(uint32_t i=0;i<28;++i){
   const uint8_t expected=(copy?uint8_t((run*43+i*17+9)&255):
       (i<4?0u:0xA5u));
   check(ctx->mmu.read8(DEST+i)==expected,"guest copy/zero result mismatch");
  }
  if(copy)check(ctx->mmu.read8(ptr)==source_byte,"source byte was overwritten");
 }
 check(nwii::runtime::fallthrough==0,"unexpected syscall or interpreter fallback");
 std::cout<<"PASS: "<<checks<<" V27 original exec-params/memcpy native assertions, four paths\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V27 original test: "<<e.what()<<'\n';return 1;}
