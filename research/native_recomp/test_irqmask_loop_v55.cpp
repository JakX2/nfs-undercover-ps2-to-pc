// Source-only oracle for original Wii __OSInterruptInit -> SetInterruptMask loop.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
namespace {
constexpr uint32_t IRQ=0x8052661cu,STOP=0x805266acu,DISABLE=0x805265acu;
constexpr uint32_t SETMASK=0x805266e0u,MEMSET=0x8000443cu,FILL=0x80004388u;
constexpr uint32_t SP=0x80082000u,R13=0x8070e8e0u;
constexpr uint32_t HANDLERS=0x80003040u,HANDLERS_GLOBAL=R13-3408u;
constexpr uint32_t LOW_A=0x800000c4u,LOW_B=0x800000c8u;
struct Stop{};
struct IO{bool read; unsigned width;uint32_t addr,val;};
std::vector<IO> events;
uint64_t checked=0;
unsigned stop_count=0,forbidden=0,interpreter=0;
std::array<unsigned,5> count{};
void check(bool ok,const char*err){if(!ok)throw std::runtime_error(err);++checked;}
uint32_t value_for(uint32_t addr){
 switch(addr){
 case 0x0c00500au:return 0xf7f7u;
 case 0x0d006c00u:return 0x12345678u;
 case 0x0d006800u:return 0x98765432u;
 case 0x0d006814u:return 0xaabbccddu;
 case 0x0d006828u:return 0xdeadbeefu;
 default:throw std::runtime_error("unexpected original Wii MMIO register read");
 }
}
// Independent controller bank expectations for the seven-pass original loop.
constexpr std::array<IO,14> oracle{{
 {false,32,0x0c003004u,0xf0u},         // original initializer interrupt write
 {false,32,0x0d000034u,0x40000000u}, // original initializer device write
 {false,16,0x0c00401cu,0u},          // bank 0..4
 {true,16,0x0c00500au,0xf7f7u},
 {false,16,0x0c00500au,0xf607u},     // bank 5..7
 {true,32,0x0d006c00u,0x12345678u},
 {false,32,0x0d006c00u,0x12345650u},// bank 8
 {true,32,0x0d006800u,0x98765432u},
 {false,32,0x0d006800u,0x98765030u},// bank 9..11
 {true,32,0x0d006814u,0xaabbccddu},
 {false,32,0x0d006814u,0xaabbc0d0u},// bank 12..14
 {true,32,0x0d006828u,0xdeadbeefu},
 {false,32,0x0d006828u,0xdeadbee0u},// bank 15..16
 {false,32,0x0c003004u,0xf0u}       // bank 17..27
}};
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){
 constexpr std::array<uint32_t,5> addresses{IRQ,MEMSET,FILL,DISABLE,SETMASK};
 for(size_t i=0;i<addresses.size();++i)if(pc==addresses[i]){++count[i];return;}
 if(pc==STOP)return;
 ++forbidden;throw std::runtime_error("unexpected original Wii function entry");
}
bool handle_syscall(CPUContext&ctx){
 if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("unexpected guest syscall PC");}
 ++stop_count;ctx.is_running=false;throw Stop{};
}
void interpret_step(CPUContext&){++interpreter;throw std::runtime_error("guest PPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t addr){const uint32_t val=value_for(addr);events.push_back({true,16,addr,val&0xffffu});return uint16_t(val);}
uint32_t HW_Reg_Read32(uint32_t addr){const uint32_t val=value_for(addr);events.push_back({true,32,addr,val});return val;}
void HW_Reg_Write16(uint32_t addr,uint16_t value){events.push_back({false,16,addr,value});}
void HW_Reg_Write32(uint32_t addr,uint32_t value){events.push_back({false,32,addr,value});}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
 check(argc==2,"usage: native_irqmask_test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==IRQ,"invalid original owner-private Wii interrupt DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr std::array<uint32_t,8> msrs{0u,0x8000u,0xa000u,0x12345678u,
                                    0xffffffffu,0x00000020u,0x00008020u,0x01020304u};
 for(size_t run=0;run<msrs.size();++run){
   const uint32_t lr=0x8000e100u+uint32_t(run)*4u;
   for(uint32_t i=0;i<128;++i)ctx->mmu.write8(HANDLERS+i,uint8_t(i+3*run+7));
   ctx->mmu.write8(HANDLERS-1,uint8_t(0xb1u+run));
   ctx->mmu.write8(HANDLERS+128,uint8_t(0xc2u+run));
   ctx->mmu.write32(HANDLERS_GLOBAL,0x11556600u+uint32_t(run));
   ctx->mmu.write32(HANDLERS_GLOBAL-4,0xdeed0000u+uint32_t(run));
   ctx->mmu.write32(HANDLERS_GLOBAL+4,0xbabe0000u+uint32_t(run));
   ctx->mmu.write32(LOW_A-4u,0xa1a1a1a1u);
   ctx->mmu.write32(LOW_A,0xffffffffu);
   ctx->mmu.write32(LOW_B,0xffffffffu);
   ctx->mmu.write32(LOW_B+4u,0xb2b2b2b2u);
   ctx->gpr[1]=SP;ctx->gpr[13]=R13;
   for(unsigned r=29;r<=31;++r)ctx->gpr[r]=0x70000000u+uint32_t(run*32+r);
   const uint32_t old29=ctx->gpr[29],old30=ctx->gpr[30],old31=ctx->gpr[31];
   ctx->lr=lr;ctx->msr=msrs[run];ctx->pc=IRQ;ctx->is_running=true;
   const unsigned start=stop_count;
   const std::array<unsigned,5> before=count;
   const uint64_t before_inst=ctx->inst_count;
   events.clear();bool stopped=false;
   try{run_game(*ctx);}catch(const Stop&){stopped=true;}
   check(stopped&&!ctx->is_running&&ctx->pc==STOP&&stop_count==start+1,"native original interrupt loop stop mismatch");
   constexpr std::array<unsigned,5> calls{1,1,1,1,7};
   for(size_t j=0;j<calls.size();++j)check(count[j]==before[j]+calls[j],"original native helper call count or seven-pass loop mismatch");
   check(ctx->inst_count>before_inst+130,"original interrupt-mask loop executed too few PPC instructions");
   check(ctx->gpr[3]==0u,"genuine original interrupt loop failed to consume all seven mask banks");
   check(ctx->gpr[1]==SP-32u&&ctx->gpr[13]==R13,"guest interrupt stack or r13 corrupted");
   check(ctx->mmu.read32(SP+4u)==lr,"original interrupt prologue did not save LR");
   check(ctx->mmu.read32(SP-4u)==old31&&ctx->mmu.read32(SP-8u)==old30&&
         ctx->mmu.read32(SP-12u)==old29,"original interrupt prologue did not save nonvolatile GPRs");
   check(ctx->gpr[31]==0x80000000u&&ctx->gpr[30]==0xfffffff0u,"original interrupt mask state not preserved across helper loop");
   check(ctx->gpr[29]==unsigned((msrs[run]&0x8000u)!=0),"original interrupt disable helper previous EE state mismatch");
   check(ctx->msr==(msrs[run]&~0x8000u),"genuine original interrupt helper modified unrelated MSR bits");
   check(ctx->mmu.read32(HANDLERS_GLOBAL)==HANDLERS,"original memset interrupt handler global wrong");
   check(ctx->mmu.read32(HANDLERS_GLOBAL-4)==0xdeed0000u+run&&
         ctx->mmu.read32(HANDLERS_GLOBAL+4)==0xbabe0000u+run,"interrupt table adjacent global corruption");
   check(ctx->mmu.read8(HANDLERS-1)==uint8_t(0xb1u+run)&&
         ctx->mmu.read8(HANDLERS+128)==uint8_t(0xc2u+run),"original memset overran interrupt table");
   for(uint32_t i=0;i<128u;++i)check(ctx->mmu.read8(HANDLERS+i)==0u,"original memset/ __fill_mem table not zeroed");
   check(ctx->mmu.read32(LOW_A)==0xfffffff0u&&ctx->mmu.read32(LOW_B)==0u,"original interrupt low-memory mask globals wrong");
   check(ctx->mmu.read32(LOW_A-4u)==0xa1a1a1a1u&&ctx->mmu.read32(LOW_B+4u)==0xb2b2b2b2u,
         "original low-memory mask global canary overwritten");
   check(events.size()==oracle.size(),"original IRQ MMIO read/write count differs from seven-bank loop");
   for(size_t i=0;i<oracle.size();++i){const IO& observed=events[i],&expected=oracle[i];
     if(observed.read!=expected.read||observed.width!=expected.width||
         observed.addr!=expected.addr||observed.val!=expected.val){
       std::cerr<<std::hex<<"run "<<run<<" event "<<i<<" actual "<<observed.read<<":"<<observed.width<<":"<<observed.addr<<":"<<observed.val
         <<" expected "<<expected.read<<":"<<expected.width<<":"<<expected.addr<<":"<<expected.val<<std::dec<<'\n';
       throw std::runtime_error("original Wii IRQ MMIO event differs from independent oracle");
     }
     ++checked;
   }
 }
 check(!forbidden&&!interpreter,"unplanned original Wii function entry or interpreter fallback");
 std::cout<<"PASS: "<<checked<<" V55 original __OSInterruptInit+SetInterruptMask 7-pass native-loop assertions across "<<msrs.size()<<" MSR states; zero interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V55 original IRQ mask loop: "<<e.what()<<'\n';return 1;}
