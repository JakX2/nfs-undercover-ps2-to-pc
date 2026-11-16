// Wii EXIInit original PowerPC polls: test-supplied device readings, no built-in hardware claims.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x804EF9BCu, STOP=0x804EFA14u, SP=0x80082000u, R13=0x8070E8E0u;
constexpr std::array<uint32_t,3> REG{0x0D00680Cu,0x0D006820u,0x0D006834u};
struct Terminal{};
uint64_t checks=0,calls=0,stops=0,forbidden=0;
std::array<unsigned,3> busy_remaining{0,0,0};
std::vector<std::pair<uint32_t,uint32_t>> reads;
unsigned max_reads=32;
void check(bool b,const char*msg){if(!b)throw std::runtime_error(msg);++checks;}
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){if(pc==ENTRY){++calls;return;}if(pc==STOP)return;++forbidden;throw std::runtime_error("unexpected EXI helper/fallback");}
bool handle_syscall(CPUContext&ctx){if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("unrecognized PowerPC syscall");}ctx.is_running=false;++stops;throw Terminal{};}
void interpret_step(CPUContext&){++forbidden;throw std::runtime_error("PowerPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){++forbidden;throw std::runtime_error("EXI 16-bit device access not verified");}
uint32_t HW_Reg_Read32(uint32_t a){
 if(reads.size()>=max_reads)throw std::runtime_error("V65 bounded EXI MMIO polling budget exceeded");
 for(size_t i=0;i<REG.size();++i)if(a==REG[i]){
  const uint32_t busy=(busy_remaining[i] ? 1u:0u);
  if(busy)--busy_remaining[i];
  // Test device data is explicit, not hardware implementation.
  const uint32_t v=0x2000u|uint32_t(i<<4)|busy;
  reads.emplace_back(a,v);return v;
 }
 ++forbidden;throw std::runtime_error("unexpected Wii EXI register read");
}
void HW_Reg_Write16(uint32_t,uint16_t){++forbidden;throw std::runtime_error("unexpected EXI MMIO write16");}
void HW_Reg_Write32(uint32_t,uint32_t){++forbidden;throw std::runtime_error("unexpected EXI MMIO write32");}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try {
 check(argc==2,"usage: exi-native-test PRIVATE_DOL");
 nwii::loader::Executable exe;check(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"wrong original EXI private fixture");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 const std::array<std::array<unsigned,3>,10> cases{{
   {{0,0,0}},{{1,0,0}},{{0,1,0}},{{0,0,1}},{{1,1,1}},
   {{2,0,0}},{{0,3,0}},{{0,0,4}},{{1,2,3}},{{2,2,2}}
 }};
 for(size_t run=0;run<cases.size();++run){
  busy_remaining=cases[run];reads.clear();max_reads=80;
  ctx->pc=ENTRY;ctx->is_running=true;ctx->gpr[1]=SP;ctx->gpr[13]=R13;
  ctx->gpr[28]=0x11111111u;ctx->gpr[29]=0x22222222u;
  ctx->gpr[30]=0x33333333u;ctx->gpr[31]=0x44444444u;
  ctx->lr=0x804EFA80u;ctx->msr=0x8130u;
  ctx->mmu.write32(SP-40u,0xCAFEBABEu);
  ctx->mmu.write32(SP-36u,0xDEADBEEFu);
  auto old_calls=calls,old_stops=stops;
  bool ended=false;try{run_game(*ctx);}catch(const Terminal&){ended=true;}
  check(ended&&ctx->pc==STOP&&!ctx->is_running,"original EXI MMIO polling failed to reach bounded stop");
  check(calls==old_calls+1&&stops==old_stops+1,"original EXI native function dispatch or stop changed");
  check(ctx->gpr[1]==SP-32u&&ctx->gpr[13]==R13&&ctx->lr==0x804EFA80u,"EXI original prologue/caller LR state differs");
  check(ctx->gpr[3]==0x007f8000u,"EXI original argument before OS interrupt masking differs");
  check(ctx->gpr[28]==0x11111111u&&ctx->gpr[29]==0x22222222u&&ctx->gpr[30]==0x33333333u&&ctx->gpr[31]==0x44444444u,"EXI entry unexpectedly modified callee-saved registers");
  check(ctx->msr==0x8130u&&ctx->mmu.read32(SP-40u)==0xCAFEBABEu&&ctx->mmu.read32(SP-36u)==0xDEADBEEFu,"EXI guest state/canary damaged");
  std::vector<uint32_t> oracle;
  std::array<unsigned,3> pending=cases[run];
  for(unsigned spins=0;spins<100;++spins){
   const bool b0=pending[0]>0; if(b0)--pending[0];
   oracle.push_back(REG[0]);if(b0)continue;
   const bool b1=pending[1]>0; if(b1)--pending[1];
   oracle.push_back(REG[1]);if(b1)continue;
   const bool b2=pending[2]>0; if(b2)--pending[2];
   oracle.push_back(REG[2]);if(b2)continue;
   break;
  }
  check(reads.size()==oracle.size(),"original EXI MMIO loop read-count mismatch");
  for(size_t i=0;i<oracle.size();++i){
   check(reads[i].first==oracle[i],"original EXI MMIO polling read order differs");
   check((reads[i].second&~1u)==(0x2000u+((reads[i].first-REG[0])/0x14u)*0x10u),"EXI synthetic status read fixture corrupted");
  }
  check(busy_remaining==std::array<unsigned,3>{{0,0,0}},"native EXI polling left pending injected busy responses");
 }
 // Fail-closed behavior: a device that never signals ready cannot escape the original loop.
 reads.clear();max_reads=8;busy_remaining={100,0,0};
 ctx->pc=ENTRY;ctx->is_running=true;ctx->gpr[1]=SP;ctx->lr=0x804EFA80u;
 bool bounded=false;try{run_game(*ctx);}catch(const std::runtime_error&e){bounded=std::string(e.what()).find("budget")!=std::string::npos;}
 check(bounded&&reads.size()==max_reads,"permanently busy EXI device incorrectly completed or exceeded budget");
 check(!forbidden,"unsupported original code or fallback executed");
 std::cout<<"PASS: "<<checks<<" V65 original Wii EXI three-channel polling native assertions over "<<cases.size()<<" ready/busy cases and bounded never-ready path, no interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V65 EXI native test failed: "<<e.what()<<'\n';return 1;}
