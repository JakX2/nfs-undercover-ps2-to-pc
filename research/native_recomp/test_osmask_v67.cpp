// Original-free verification of Wii __OSMaskInterrupts/SetInterruptMask native execution.
// MMIO values are explicitly synthetic test inputs, not Wii device emulation.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x8052693cu,SET=0x805266e0u,DIS=0x805265acu,REST=0x805265d4u,STOP=0x90050000u;
constexpr uint32_t SP=0x80082000u,R13=0x8070e8e0u;
struct Stop {};
struct Transaction {bool read;uint32_t bits,address,value;};
std::vector<Transaction> actual;
uint64_t assertions=0;
uint32_t count_mask=0,count_set=0,count_disable=0,count_restore=0,count_stop=0,count_forbidden=0;
void check(bool ok,const char*what){if(!ok)throw std::runtime_error(what);++assertions;}
uint32_t ppc_bit(unsigned i){return uint32_t(0x80000000u)>>i;}
uint32_t read_value(uint32_t addr){
 switch(addr){
 case 0x0c00500au:return 0x0000f7f7u;
 case 0x0d006c00u:return 0x12345678u;
 case 0x0d006800u:return 0x98765432u;
 case 0x0d006814u:return 0xaabbccddu;
 case 0x0d006828u:return 0xdeadbeefu;
 default:throw std::runtime_error("unplanned synthetic MMIO read address");
 }
}
uint32_t expected_bank(uint32_t group_selector,uint32_t total_mask,std::vector<Transaction>&expected){
 // Independent bank oracle. The original routine determines a bank by the
 // top set PowerPC interrupt bit and clears that bank from the work mask.
 const unsigned group=unsigned(__builtin_clz(group_selector));
 uint32_t next=group_selector,register_addr=0,width=32,write=0,initial=0;
 bool need_read=false,need_write=true;
 if(group<5){register_addr=0x0c00401cu;width=16;next&=0x07ffffffu;
   for(unsigned i=0;i<5;++i)if(!(total_mask&ppc_bit(i)))write|=1u<<i;
 }else if(group<8){register_addr=0x0c00500au;width=16;next&=~0x07000000u;need_read=true;
   initial=read_value(register_addr);write=initial&~0x1f8u;
   if(!(total_mask&ppc_bit(5)))write|=0x10u;
   if(!(total_mask&ppc_bit(6)))write|=0x40u;
   if(!(total_mask&ppc_bit(7)))write|=0x100u;
 }else if(group==8){register_addr=0x0d006c00u;next&=~ppc_bit(8);need_read=true;
   initial=read_value(register_addr);write=(initial&0xffffffd3u)|(!(total_mask&ppc_bit(8))?4u:0u);
 }else if(group<12){register_addr=0x0d006800u;next&=~(ppc_bit(9)|ppc_bit(10)|ppc_bit(11));need_read=true;
   initial=read_value(register_addr);write=(initial&0xffffd3f0u)|(!(total_mask&ppc_bit(9))?1u:0u)|(!(total_mask&ppc_bit(10))?4u:0u)|(!(total_mask&ppc_bit(11))?0x400u:0u);
 }else if(group<15){register_addr=0x0d006814u;next&=~(ppc_bit(12)|ppc_bit(13)|ppc_bit(14));need_read=true;
   initial=read_value(register_addr);write=(initial&0xfffff3f0u)|(!(total_mask&ppc_bit(12))?1u:0u)|(!(total_mask&ppc_bit(13))?4u:0u)|(!(total_mask&ppc_bit(14))?0x400u:0u);
 }else if(group<17){register_addr=0x0d006828u;next&=~(ppc_bit(15)|ppc_bit(16));need_read=true;
   initial=read_value(register_addr);write=(initial&0xfffffff0u)|(!(total_mask&ppc_bit(15))?1u:0u)|(!(total_mask&ppc_bit(16))?4u:0u);
 }else if(group<28){register_addr=0x0c003004u;next&=~0x00007ff0u;write=0xf0u;
   constexpr std::array<unsigned,11> indices{17,20,21,22,23,24,25,18,19,26,27};
   constexpr std::array<uint32_t,11> values{0x800u,8u,4u,2u,1u,0x100u,0x1000u,0x200u,0x400u,0x2000u,0x4000u};
   for(size_t i=0;i<indices.size();++i)if(!(total_mask&ppc_bit(indices[i])))write|=values[i];
 }else throw std::runtime_error("test case selected an unhandled low interrupt group");
 if(need_read)expected.push_back({true,width,register_addr,initial});
 if(need_write)expected.push_back({false,width,register_addr,write&(width==16?0xffffu:0xffffffffu)});
 return next;
}
struct Case{uint32_t argument,old_mask,other_mask,msr;};
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){
 if(pc==ENTRY){++count_mask;return;}
 if(pc==SET){++count_set;return;}
 if(pc==DIS){++count_disable;return;}
 if(pc==REST){++count_restore;return;}
 if(pc==STOP)return;
 ++count_forbidden;throw std::runtime_error("unexpected guest function dispatch");
}
bool handle_syscall(CPUContext&ctx){
 if(ctx.pc!=STOP){++count_forbidden;throw std::runtime_error("unexpected syscall PC");}
 ++count_stop;ctx.is_running=false;throw Stop{};
}
void interpret_step(CPUContext&){++count_forbidden;throw std::runtime_error("PPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t a){uint32_t val=read_value(a);actual.push_back({true,16,a,val&0xffffu});return uint16_t(val);}
uint32_t HW_Reg_Read32(uint32_t a){uint32_t val=read_value(a);actual.push_back({true,32,a,val});return val;}
void HW_Reg_Write16(uint32_t a,uint16_t v){actual.push_back({false,16,a,v});}
void HW_Reg_Write32(uint32_t a,uint32_t v){actual.push_back({false,32,a,v});}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try {
 check(argc==2,"usage: native-mask PRIVATE_DOL");
 nwii::loader::Executable image;check(image.load_dol(argv[1])&&image.entry_point==ENTRY,"wrong original-private DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr std::array<Case,12> cases{{
  {0,0,0,0x8130u}, {0x007f8000u,0,0,0x8130u},
  {0x007f8000u,0x007f8000u,0,0x0130u}, {0x007f8000u,0,0x007f8000u,0x8130u},
  {0x007f8000u,0x00010000u,0,0x0130u}, {0x80000000u,0,0,0x8130u},
  {0x04000000u,0,0,0x0130u}, {0x00800000u,0,0,0x8130u},
  {0x00080000u,0,0,0x0130u}, {0x00010000u,0,0,0x8130u},
  {0x00004000u,0,0,0x0130u}, {0xfffffff0u,0,0,0x8130u},
 }};
 for(size_t test=0;test<cases.size();++test){
  const Case c=cases[test];actual.clear();
  ctx->pc=ENTRY;ctx->is_running=true;ctx->lr=STOP;ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->gpr[3]=c.argument;ctx->msr=c.msr;
  ctx->gpr[29]=0x29292929u;ctx->gpr[30]=0x30303030u;ctx->gpr[31]=0x31313131u;
  ctx->mmu.write32(0x800000c4u,c.old_mask);ctx->mmu.write32(0x800000c8u,c.other_mask);
  ctx->mmu.write32(SP-40u,0xabcdef02u);ctx->mmu.write32(SP-36u,0xabcdeff0u);
  const auto before_mask=count_mask,before_disable=count_disable,before_restore=count_restore,before_set=count_set,before_stop=count_stop;
  bool ended=false;try{run_game(*ctx);}catch(const Stop&){ended=true;}
  check(ended&&ctx->pc==STOP&&!ctx->is_running,"original __OSMaskInterrupts did not return");
  check(count_mask==before_mask+1&&count_disable==before_disable+1&&count_restore==before_restore+1&&count_stop==before_stop+1,"original nested dispatch/count mismatch");
  check(ctx->gpr[1]==SP&&ctx->lr==STOP&&ctx->gpr[13]==R13,"original function return/stack corruption");
  check(ctx->gpr[29]==0x29292929u&&ctx->gpr[30]==0x30303030u&&ctx->gpr[31]==0x31313131u,"original callee-saved registers changed");
  check(ctx->msr==c.msr,"original OSRestoreInterrupts failed to restore prior MSR EE bit");
  check(ctx->mmu.read32(SP-40u)==0xabcdef02u&&ctx->mmu.read32(SP-36u)==0xabcdeff0u,"guest stack canary corrupted");
  check(ctx->mmu.read32(0x800000c4u)==(c.old_mask|c.argument)&&ctx->mmu.read32(0x800000c8u)==c.other_mask,"mask low-memory updates mismatch");
  check(ctx->gpr[3]==c.old_mask,"original mask helper failed to return previous mask");
  uint32_t selected=c.argument&~(c.old_mask|c.other_mask),mask_all=c.argument|c.old_mask|c.other_mask;
  std::vector<Transaction> oracle;unsigned groups=0;
  while(selected){
   check(++groups<=7,"mask oracle selected more than seven banks");
   selected=expected_bank(selected,mask_all,oracle);
  }
  check(count_set==before_set+groups,"original SetInterruptMask calls do not match selected banks");
  check(actual.size()==oracle.size(),"original MMIO event count mismatch");
  for(size_t i=0;i<oracle.size();++i){
   check(actual[i].read==oracle[i].read&&actual[i].bits==oracle[i].bits&&actual[i].address==oracle[i].address&&actual[i].value==oracle[i].value,
         "original interrupt mask MMIO address, width, order or value mismatch");
  }
 }
 check(count_forbidden==0,"unexpected original function or PPC interpreter invoked");
 std::cout<<"PASS: "<<assertions<<" V67 original Wii __OSMaskInterrupts native assertions over "<<cases.size()<<" guest-state cases, no interpreter fallback\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V67 native test failure: "<<e.what()<<'\n';return 1;}
