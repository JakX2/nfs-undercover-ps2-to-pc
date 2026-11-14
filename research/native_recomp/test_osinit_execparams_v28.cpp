// Source-only assertions for genuine original Wii OSInit prefix under AOT native dispatch.
// Private extracted code and original DOL stay off GitHub and out of test source.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
constexpr uint32_t OSINIT=0x80520670u,STOP=0x805206C0u,ALT=0x80520BDCu;
constexpr uint32_t TIME=0x8052A844u,GETTIME=0x8052A824u,DISABLE=0x805265ACu;
constexpr uint32_t RESTORE=0x805265D4u,EXEC=0x80523B1Cu,SAVE=0x805450E8u,COPY=0x80004338u;
constexpr uint32_t SP=0x80082000u, R13=0x8070E8E0u, INITFLAG=0x8070DAFCu;
constexpr uint32_t DEST=0x806F4F00u,SOURCE=0x80038000u,TIMEHI=0x8070DB30u;
uint64_t assertions=0;
void check(bool b,const char* text){if(!b)throw std::runtime_error(text);++assertions;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0,forbidden=0;
static uint64_t target_time=0;
static uint32_t call_counts[9]{};
void trace_call(uint32_t pc,CPUContext& ctx){
 constexpr uint32_t symbols[9]={OSINIT,TIME,GETTIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT};
 for(size_t i=0;i<9;++i)if(pc==symbols[i]){
   ++call_counts[i];
   // Deterministic test-only virtual-clock start; not a production runtime override.
   if(pc==GETTIME)ctx.inst_count=target_time;
   return;
 }
 throw std::runtime_error("unplanned original Wii function entered");
}
bool handle_syscall(CPUContext& ctx){
 if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("unexpected guest syscall stop");}
 ++stops;ctx.is_running=false;return true;
}
void interpret_step(CPUContext&){++forbidden;throw std::runtime_error("PPC interpreter fallback");}
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
 check(argc==2,"usage: original-native-test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"wrong bounded OSInit DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr std::array<uint32_t,4> source{0u,0x7fffffffu,SOURCE,0x80000000u};
 constexpr std::array<uint64_t,4> clocks{0x0000000000100000ull,0x00000001fffffffcull,
       0x00000000fffffff0ull,0x0000000200000004ull};
 constexpr std::array<uint64_t,4> offsets{0x0000000000000000ull,0x0000000200000050ull,
       0x00000003ffffffe0ull,0x00000001fffffffdull};
 for(size_t run=0;run<source.size();++run){
  const uint32_t ptr=source[run];const bool copied=ptr>=0x80000000u;
  const uint32_t msr=(run&1)?0x2000u:0xA000u;
  constexpr uint32_t SAVED_LR=0x8000BEEFu;
  ctx->mmu.write32(INITFLAG,0);
  ctx->mmu.write32(0x800030F0u,ptr);
  ctx->mmu.write32(0x800030D8u,uint32_t(offsets[run]>>32));
  ctx->mmu.write32(0x800030DCu,uint32_t(offsets[run]));
  ctx->mmu.write32(TIMEHI,0xA0A0A0A0u);
  ctx->mmu.write32(TIMEHI+4,0xBBBBBBBBu);
  ctx->mmu.write8(DEST-1,0xAC);
  for(uint32_t i=0;i<32;++i){
    ctx->mmu.write8(DEST+i,0xAA);
    if(copied)ctx->mmu.write8(ptr+i,uint8_t((run*43+i*17+9)&255));
  }
  ctx->mmu.write8(DEST+28,0xC9);
  ctx->mmu.write8(DEST+29,0xD9);
  for(unsigned i=20;i<=31;++i){
   ctx->gpr[i]=0x1CA00000u+(uint32_t(run)<<16)+i;
   ctx->mmu.write32(SP-48u+4u*(i-20u),0xFAFAFAFAu);
  }
  ctx->gpr[13]=R13;
  ctx->gpr[1]=SP;ctx->lr=SAVED_LR;ctx->pc=OSINIT;ctx->msr=msr;
  ctx->is_running=true;
  nwii::runtime::target_time=clocks[run];
  const uint32_t stops=nwii::runtime::stops;
  const std::array<uint32_t,9> before{
   nwii::runtime::call_counts[0],nwii::runtime::call_counts[1],
   nwii::runtime::call_counts[2],nwii::runtime::call_counts[3],
   nwii::runtime::call_counts[4],nwii::runtime::call_counts[5],
   nwii::runtime::call_counts[6],nwii::runtime::call_counts[7],
   nwii::runtime::call_counts[8]};
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==STOP,"wrong exact guest syscall boundary");
  check(nwii::runtime::stops==stops+1,"missing original OSInit continuation stop");
  check(ctx->gpr[1]==SP-80,"original OSInit stack frame incorrect");
  check(ctx->mmu.read32(SP+4)==SAVED_LR,"original caller LR was not saved");
  check(ctx->mmu.read32(INITFLAG)==1,"OSInit one-time global not set");
  check((ctx->msr&0x8000u)==0,"original second interrupt disable not executed");
  check((ctx->msr&~0x8000u)==(msr&~0x8000u),"original OSInit corrupted other MSR bits");
  check(ctx->gpr[13]==R13,"OSInit guest small-data pointer changed");
  const uint64_t stamp=(uint64_t(ctx->mmu.read32(TIMEHI))<<32)|ctx->mmu.read32(TIMEHI+4);
  const uint64_t low=clocks[run]+offsets[run];
  check(stamp>=low+1 && stamp<=low+48,"OSInit timestamp outside original timebase window");
  const uint32_t expected_entries[9]={1,1,1,2,1,1,1,(copied?1u:0u),0};
  for(size_t i=0;i<9;++i)
    check(nwii::runtime::call_counts[i]-before[i]==expected_entries[i],
      "wrong number of original guest function dispatches");
  for(unsigned i=20;i<=31;++i)
    check(ctx->mmu.read32(SP-48u+4u*(i-20u))==0x1CA00000u+(uint32_t(run)<<16)+i,
      "original _savegpr_20 guest stack slot wrong");
  check(ctx->mmu.read8(DEST-1)==0xAC && ctx->mmu.read8(DEST+28)==0xC9 &&
        ctx->mmu.read8(DEST+29)==0xD9,"execparams destination guard changed");
  for(uint32_t i=0;i<28;++i){
    const uint8_t expected=copied?uint8_t((run*43+i*17+9)&255):(i<4?0u:0xAA);
    check(ctx->mmu.read8(DEST+i)==expected,"OSInit original exec-params copy/zero wrong");
  }
 }
 check(nwii::runtime::forbidden==0,"interpreter or unexpected syscall reached");
 std::cout << std::dec << "PASS: " << assertions << " V28 original OSInit→exec-params native assertions, 4 paths, no interpreter fallback\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V28 original test failed: "<<e.what()<<'\n';return 1;}
