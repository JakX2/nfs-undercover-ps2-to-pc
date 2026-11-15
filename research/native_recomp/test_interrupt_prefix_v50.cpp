// Original-free semantic tests of genuine Wii interrupt init memory prefix.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x8052661Cu,STOP=0x8052664Cu;
constexpr uint32_t FILL=0x80004388u,MEMSET=0x8000443Cu;
constexpr uint32_t SP=0x80082000u,R13=0x8070E8E0u;
constexpr uint32_t BUFFER=0x80003040u,GLOBAL=R13-3408u;
struct Stop{};
uint64_t checked=0;
void check(bool ok,const char*msg){if(!ok)throw std::runtime_error(msg);++checked;}
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static unsigned call_entries[3]{};
static unsigned stops=0,forbidden=0,interpreter=0;
void trace_call(uint32_t pc,CPUContext&){
 if(pc==ENTRY){++call_entries[0];return;}
 if(pc==MEMSET){++call_entries[1];return;}
 if(pc==FILL){++call_entries[2];return;}
 if(pc==STOP)return;
 ++forbidden;throw std::runtime_error("unplanned original Wii guest entry");
}
bool handle_syscall(CPUContext&ctx){
 if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("syscall reached unexpected guest PC");}
 ++stops;ctx.is_running=false;throw Stop{};
}
void interpret_step(CPUContext&){++interpreter;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){} void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){} uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){} void HW_Reg_Write32(uint32_t,uint32_t){}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
 check(argc==2,"usage: native_test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"wrong private native interrupt fixture");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 for(unsigned trial=0;trial<8;++trial){
   const uint32_t pattern=0x7u+trial*0x13u;
   for(unsigned i=0;i<128;++i)ctx->mmu.write8(BUFFER+i,uint8_t(pattern+i));
   ctx->mmu.write8(BUFFER-1u,0xA3u+trial);
   ctx->mmu.write8(BUFFER+128u,0xC5u+trial);
   ctx->mmu.write32(GLOBAL,0xDEAD0000u+trial);
   ctx->mmu.write32(GLOBAL-4u,0xABCD0000u+trial);
   ctx->mmu.write32(GLOBAL+4u,0xFACE0000u+trial);
   constexpr uint32_t LR=0x8000BEEFu;
   ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=LR;
   for(unsigned i=29;i<32;++i)ctx->gpr[i]=0x77770000u+trial*256u+i;
   ctx->gpr[4]=0x12340000u+trial;
   ctx->pc=ENTRY;ctx->is_running=true;
   uint64_t before=ctx->inst_count;
   std::array<unsigned,3> count{nwii::runtime::call_entries[0],nwii::runtime::call_entries[1],nwii::runtime::call_entries[2]};
   unsigned before_stop=nwii::runtime::stops;
   bool exact=false;
   try{run_game(*ctx);}catch(const Stop&){exact=true;}
   check(exact&&!ctx->is_running&&ctx->pc==STOP,"interrupt prefix failed to reach synthetic boundary");
   check(nwii::runtime::stops==before_stop+1u,"terminal syscall not called exactly once");
   for(size_t i=0;i<count.size();++i)
     check(nwii::runtime::call_entries[i]==count[i]+1u,"original helper dispatch count changed");
   check(ctx->inst_count>before+25u,"too few native original PPC instructions executed");
   check(ctx->gpr[1]==SP-32u&&ctx->gpr[13]==R13,"original interrupt entry stack or r13 corrupted");
   check(ctx->mmu.read32(SP+4u)==LR,"original interrupt stack did not save LR");
   for(unsigned reg=29;reg<=31;++reg)
     check(ctx->mmu.read32(SP-4u*(32u-reg))==0x77770000u+trial*256u+reg,
           "genuine interrupt prefix callee-save store differs");
   check(ctx->gpr[31]==0x80000000u,"original interrupt code did not load MEM1 base");
   check(ctx->gpr[3]==BUFFER,"genuine original memset did not return destination address");
   check(ctx->mmu.read32(GLOBAL)==BUFFER,"genuine interrupt table pointer global not installed");
   check(ctx->mmu.read32(GLOBAL-4u)==0xABCD0000u+trial&&
         ctx->mmu.read32(GLOBAL+4u)==0xFACE0000u+trial,
         "interrupt initialization overwrote adjacent globals");
   check(ctx->mmu.read8(BUFFER-1u)==uint8_t(0xA3u+trial)&&
         ctx->mmu.read8(BUFFER+128u)==uint8_t(0xC5u+trial),
         "genuine original memset overran 128-byte interrupt table");
   for(unsigned i=0;i<128;++i)
     check(ctx->mmu.read8(BUFFER+i)==0u,"original __fill_mem interrupt-table zeroing failed");
 }
 check(nwii::runtime::forbidden==0u&&nwii::runtime::interpreter==0u,
       "interpreter fallback or unexpected Wii function executed");
 std::cout<<"PASS: "<<checked<<" V50 original Wii interrupt/memset native assertions across 8 trials; zero interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V50 native test error: "<<e.what()<<'\n';return 1;}
