// Original-free semantic regression of the authentic Wii alarm initialization.
// The private Wii code is supplied exclusively by the SHA-pinned owner DOL.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
namespace {
constexpr uint32_t ALARM=0x805210CCu,GET=0x80520EB0u,SET=0x80520E9Cu,
                   SHUTDOWN=0x80527B4Cu,STOP=0x80004900u;
constexpr uint32_t SP=0x80082000u,R13=0x8070E8E0u;
constexpr uint32_t TABLE=0x80034000u, HANDLER=0x805217BCu;
constexpr uint32_t ALARM_HEAD=R13-3496u,SHUTDOWN_HEAD=R13-3376u,SHUTDOWN_TAIL=R13-3372u;
constexpr uint32_t NODE=0x8060BCB8u,EXISTING=0x80035000u;
uint64_t checks=0;
struct Stop{};
void ck(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);++checks;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static std::array<uint32_t,5> calls{};
static uint32_t stops=0,interpreter=0,unexpected=0;
void trace_call(uint32_t pc,CPUContext&){
 constexpr std::array<uint32_t,5> roots{ALARM,GET,SET,SHUTDOWN,STOP};
 for(size_t i=0;i<roots.size();++i)if(pc==roots[i]){++calls[i];return;}
 ++unexpected;throw std::runtime_error("unexpected native Wii function");
}
bool handle_syscall(CPUContext&ctx){
 if(ctx.pc!=STOP){++unexpected;throw std::runtime_error("unexpected syscall pc");}
 ++stops;ctx.is_running=false;throw Stop{};
}
void interpret_step(CPUContext&){++interpreter;throw std::runtime_error("PowerPC interpreter fallback");}
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
 ck(argc==2,"usage: native PRIVATE_OWNER_DOL");
 nwii::loader::Executable exe;
 ck(exe.load_dol(argv[1])&&exe.entry_point==ALARM,"bad private owner Wii DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr unsigned runs=6;
 for(unsigned run=0;run<runs;++run){
  const bool already=(run==0||run==4);
  const bool existing=(run>=2);
  const uint32_t prev=already?HANDLER:0x80522900u+4u*run;
  const uint32_t oldhead=existing?EXISTING:0;
  const uint32_t priority=run==2?200u:run==3?20u:100u;
  ctx->mmu.write32(R13-3552u,TABLE);
  for(unsigned index=0;index<32;++index)ctx->mmu.write32(TABLE+4u*index,0xBEE00000u+index);
  ctx->mmu.write32(TABLE+8u*4u,prev);
  ctx->mmu.write32(TABLE-4u,0xAABBCCDDu);
  ctx->mmu.write32(TABLE+32u*4u,0xDDCCBBAAu);
  ctx->mmu.write32(ALARM_HEAD,0xB0A00000u+run);
  ctx->mmu.write32(ALARM_HEAD+4u,0xB0B00000u+run);
  ctx->mmu.write32(SHUTDOWN_HEAD,oldhead);
  ctx->mmu.write32(SHUTDOWN_TAIL,oldhead);
  ctx->mmu.write32(EXISTING+4u,100u); // comparator priority
  ctx->mmu.write32(EXISTING+8u,0u);
  ctx->mmu.write32(EXISTING+12u,0u);
  ctx->mmu.write32(NODE,0x11223344u+run);
  ctx->mmu.write32(NODE+4u,priority);
  ctx->mmu.write32(NODE+8u,0xAAAA0000u+run);
  ctx->mmu.write32(NODE+12u,0xBBBB0000u+run);
  ctx->mmu.write32(NODE+16u,0xC0FFEE00u+run);
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=STOP;ctx->pc=ALARM;
  ctx->gpr[20]=0xCAFEBABEu+run;
  ctx->is_running=true;
  const auto before=nwii::runtime::calls;
  const auto oldstops=nwii::runtime::stops;
  const auto oldinst=ctx->inst_count;
  bool didstop=false;
  try{run_game(*ctx);}catch(const Stop&){didstop=true;}
  ck(didstop&&!ctx->is_running&&ctx->pc==STOP,"original alarm did not return to controlled stop");
  ck(nwii::runtime::stops==oldstops+1,"missing controlled stop syscall");
  ck(ctx->inst_count>oldinst+10,"original alarm instructions not executed");
  ck(ctx->mmu.read32(SP+4u)==STOP,"original PPC alarm did not save return LR correctly");
  ck(ctx->gpr[3]==(already?HANDLER:NODE),"original alarm return value unexpected");
  ck(ctx->gpr[1]==SP&&ctx->lr==STOP&&ctx->gpr[20]==0xCAFEBABEu+run,
     "original alarm violated PPC ABI");
  constexpr std::array<unsigned,5> basic{1,1,0,0,1};
  for(size_t j=0;j<basic.size();++j)
   ck(nwii::runtime::calls[j]==before[j]+(j==2||j==3?unsigned(!already):basic[j]),
      "wrong original Wii alarm dispatch count");
  for(unsigned index=0;index<32;++index)
   ck(ctx->mmu.read32(TABLE+4u*index)==(index==8?(already?HANDLER:HANDLER):0xBEE00000u+index),
     "exception handler table corruption");
  ck(ctx->mmu.read32(TABLE-4u)==0xAABBCCDDu&&ctx->mmu.read32(TABLE+128u)==0xDDCCBBAAu,
     "exception handler canary overwritten");
  ck(ctx->mmu.read32(ALARM_HEAD)==(already?0xB0A00000u+run:0u),"alarm head incorrectly initialized");
  ck(ctx->mmu.read32(ALARM_HEAD+4u)==(already?0xB0B00000u+run:0u),"alarm tail incorrectly initialized");
  if(already){
   ck(ctx->mmu.read32(SHUTDOWN_HEAD)==oldhead&&ctx->mmu.read32(SHUTDOWN_TAIL)==oldhead,
      "already-installed alarm incorrectly registered");
   ck(ctx->mmu.read32(NODE+8u)==0xAAAA0000u+run&&ctx->mmu.read32(NODE+12u)==0xBBBB0000u+run,
      "already-installed alarm modified shutdown node");
  }else{
   ck(ctx->mmu.read32(SHUTDOWN_HEAD)!=0&&ctx->mmu.read32(SHUTDOWN_TAIL)!=0,
      "original shutdown registration omitted");
   ck(ctx->mmu.read32(NODE+16u)==0xC0FFEE00u+run,
      "shutdown registration overran node fields");
  }
  if(!already){
   if(!existing){
    ck(ctx->mmu.read32(SHUTDOWN_HEAD)==NODE&&ctx->mmu.read32(SHUTDOWN_TAIL)==NODE,
       "empty shutdown list not initialized correctly");
    ck(ctx->mmu.read32(NODE+8u)==0&&ctx->mmu.read32(NODE+12u)==0,
       "first shutdown node links not null");
   }else if(priority<100u){
    ck(ctx->mmu.read32(SHUTDOWN_HEAD)==NODE&&ctx->mmu.read32(SHUTDOWN_TAIL)==EXISTING,
       "priority-sorted prepend gave wrong list endpoints");
    ck(ctx->mmu.read32(NODE+8u)==EXISTING&&ctx->mmu.read32(NODE+12u)==0,
       "prepended shutdown node links incorrect");
    ck(ctx->mmu.read32(EXISTING+8u)==0&&ctx->mmu.read32(EXISTING+12u)==NODE,
       "preexisting shutdown node not linked back to prepended node");
   }else{
    ck(ctx->mmu.read32(SHUTDOWN_HEAD)==EXISTING&&ctx->mmu.read32(SHUTDOWN_TAIL)==NODE,
       "priority-sorted append gave wrong list endpoints");
    ck(ctx->mmu.read32(NODE+8u)==0&&ctx->mmu.read32(NODE+12u)==EXISTING,
       "appended shutdown node links incorrect");
    ck(ctx->mmu.read32(EXISTING+8u)==NODE&&ctx->mmu.read32(EXISTING+12u)==0,
       "preexisting shutdown node not linked to appended node");
   }
  }else{
   ck(ctx->mmu.read32(EXISTING+8u)==0&&ctx->mmu.read32(EXISTING+12u)==0,
      "already-installed handler mutated existing shutdown links");
  }
  ck(ctx->mmu.read32(NODE+4u)==priority,"shutdown registration overwrote priority");
 }
 // Independently execute the original exception-handler accessors with
 // non-default indices, verifying lwzx/stwx and return-value semantics.
 constexpr uint32_t DIRECT_INDEX=13u;
 for(unsigned trial=0;trial<4;++trial){
  const uint32_t old=0xF1200000u+trial;
  const uint32_t replacement=0xF3400000u+trial;
  ctx->mmu.write32(R13-3552u,TABLE);
  ctx->mmu.write32(TABLE+4u*DIRECT_INDEX,old);
  ctx->mmu.write32(TABLE+4u*(DIRECT_INDEX-1),0xCACA1616u);
  ctx->mmu.write32(TABLE+4u*(DIRECT_INDEX+1),0xDADA2727u);
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=STOP;ctx->pc=GET;
  ctx->gpr[3]=DIRECT_INDEX;ctx->is_running=true;
  const auto prior=nwii::runtime::calls;
  bool stopped=false;
  try{run_game(*ctx);}catch(const Stop&){stopped=true;}
  ck(stopped&&ctx->pc==STOP,"direct original exception getter failed return");
  ck(ctx->gpr[3]==old&&ctx->mmu.read32(TABLE+4u*DIRECT_INDEX)==old,
      "original getter returned unexpected handler");
  ck(nwii::runtime::calls[1]==prior[1]+1&&nwii::runtime::calls[4]==prior[4]+1,
      "original getter did not dispatch");
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=STOP;ctx->pc=SET;
  ctx->gpr[3]=DIRECT_INDEX;ctx->gpr[4]=replacement;ctx->is_running=true;
  const auto before_set=nwii::runtime::calls;
  stopped=false;
  try{run_game(*ctx);}catch(const Stop&){stopped=true;}
  ck(stopped&&ctx->pc==STOP,"direct original exception setter failed return");
  ck(ctx->gpr[3]==old&&ctx->mmu.read32(TABLE+4u*DIRECT_INDEX)==replacement,
      "original setter did not return old value and store new handler");
  ck(nwii::runtime::calls[2]==before_set[2]+1&&nwii::runtime::calls[4]==before_set[4]+1,
      "original exception setter did not dispatch");
  ck(ctx->mmu.read32(TABLE+4u*(DIRECT_INDEX-1))==0xCACA1616u&&
     ctx->mmu.read32(TABLE+4u*(DIRECT_INDEX+1))==0xDADA2727u,
     "accessors wrote adjacent exception handlers");
 }
 ck(nwii::runtime::interpreter==0&&nwii::runtime::unexpected==0,"unexpected PPC fallback/callback");
 std::cout<<"PASS: V47 original Wii alarm native initialization "<<checks<<"/"<<checks
          <<" assertions, runs="<<runs<<", interpreter_fallback=0\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL V47 alarm: "<<e.what()<<'\n';return 1;}
