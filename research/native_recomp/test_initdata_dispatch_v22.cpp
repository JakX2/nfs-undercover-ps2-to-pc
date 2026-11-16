// Independent semantic regression for privately generated __init_data PPC code.
// Uses real NWiiRuntime CPUContext and MMU; contains no game-derived opcodes.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x80004238u, STOP=0x80004900u, TABLE=0x80006420u;
uint64_t tests=0;
void check(bool cond,const char* err){if(!cond)throw std::runtime_error(err);++tests;}
std::vector<std::pair<uint32_t,uint32_t>> read_zero_table(nwii::runtime::CPUContext& ctx){
 std::vector<std::pair<uint32_t,uint32_t>> entries;
 for(unsigned i=0;i<4;++i){
   const uint32_t address=ctx.mmu.read32(TABLE+0x90+8*i);
   const uint32_t length=ctx.mmu.read32(TABLE+0x94+8*i);
   if(length==0)break;
   check(address>=0x80000000u&&length<=1024*1024u,"unsafe BSS range");
   entries.emplace_back(address,length);
 }
 return entries;
}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0;
static uint32_t unexpected=0;
static uint32_t interpreter_fallback=0;
static std::array<uint64_t,6> entries{};
void trace_call(uint32_t pc,CPUContext&){
  constexpr std::array<uint32_t,6> guest{0x80004238u,0x80004304u,
      0x80004338u,0x80004388u,0x8000443cu,0x80004900u};
  const auto it=std::find(guest.begin(),guest.end(),pc);
  if(it==guest.end())throw std::runtime_error("unexpected native function dispatch PC");
  ++entries[static_cast<size_t>(it-guest.begin())];
}
bool handle_syscall(CPUContext& ctx){
 if(ctx.pc != STOP){++unexpected;throw std::runtime_error("unexpected syscall");}
 ++stops;ctx.is_running=false;return true;
}
void interpret_step(CPUContext&){++interpreter_fallback;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int) {}
void GX_WGPIPE_Write8(uint8_t) {}
void GX_WGPIPE_Write16(uint16_t) {}
void GX_WGPIPE_Write32(uint32_t) {}
void GX_WGPIPE_WriteF32(float) {}
void GX_WGPIPE_WriteF64(double) {}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t) {}
void HW_Reg_Write32(uint32_t,uint32_t) {}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char** argv){
 if(argc!=3){std::cerr<<"Usage: test_initdata_dispatch_v22 PRIVATE_DOL original|synthetic\n";return 2;}
 const bool is_original=std::string(argv[2])=="original";
 if(!is_original&&std::string(argv[2])!="synthetic")return 2;
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1]),"invalid original-derived private DOL");
 check(exe.entry_point==ENTRY,"unexpected entry PC");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 size_t table_sections=0;
 for(const auto& sec:exe.sections){
  if(sec.address==TABLE&&!sec.is_text&&!sec.is_bss){
   check(sec.size==0xb0u,"wrong table section length");
   for(uint32_t i=0;i<sec.size;++i)ctx->mmu.write8(sec.address+i,sec.data.at(i));
   ++table_sections;
  }
 }
 check(table_sections==1,"DOL initializer table missing");
 const auto zero_ranges=read_zero_table(*ctx);
 check(zero_ranges.size()==(is_original?3u:2u),"unexpected BSS entry count");
 if(is_original){
   // Original game table contains in-place copy entries. They must not be
   // relocated when source==destination, and non-BSS guest buffers survive.
   unsigned nonzero_copy=0;
   for(unsigned i=0;i<12;++i){
    const uint32_t a=ctx->mmu.read32(TABLE+i*12u),b=ctx->mmu.read32(TABLE+i*12u+4),size=ctx->mmu.read32(TABLE+i*12u+8);
    if(size==0)break;
    check(a==b,"original owner table is not in-place");
    ++nonzero_copy;
   }
   check(nonzero_copy==11,"original relocation table entry count changed");
 } else {
   const uint32_t SRC=0x80031000u,DST=0x80032000u;
   check(ctx->mmu.read32(TABLE)==SRC&&ctx->mmu.read32(TABLE+4)==DST&&ctx->mmu.read32(TABLE+8)==65,"synthetic copy entry invalid");
 }
 constexpr uint32_t SP=0x80082000u;
 constexpr uint32_t SENTINEL=0x13804230u;
 const unsigned trials=is_original?3:12;
 for(unsigned run=0;run<trials;++run){
   std::vector<uint8_t> expected_copy;
   if(!is_original){
     expected_copy.reserve(65);
     for(unsigned i=0;i<65;++i){
       const uint8_t v=uint8_t((run*13+i*31+7)&255);
       ctx->mmu.write8(0x80031000u+i,v);
       expected_copy.push_back(v);
     }
     for(unsigned i=0;i<67;++i)ctx->mmu.write8(0x80032000u+i,0xD7u);
   }
   for(const auto& [addr,size]:zero_ranges){
     uint8_t* ptr=ctx->mmu.get_ptr(addr);
     check(ptr!=nullptr,"BSS guest range not mapped");
     std::memset(ptr,0x55u+run,size);
     ctx->mmu.write8(addr-1,0xA7u);
     ctx->mmu.write8(addr+size,0xC7u);
   }
   ctx->pc=ENTRY;
   ctx->lr=STOP;
   ctx->gpr[1]=SP;
   for(unsigned i=29;i<32;++i)ctx->gpr[i]=SENTINEL+i+run;
   ctx->is_running=true;
   const uint32_t before=nwii::runtime::stops;
   const auto before_entries=nwii::runtime::entries;
   const uint64_t before_count=ctx->inst_count;
   run_game(*ctx);
   check(!ctx->is_running&&ctx->pc==STOP,"init_data did not reach controlled stop");
   check(ctx->lr==STOP,"guest LR was not restored after data init");
   check(ctx->gpr[1]==SP,"guest SP changed after data init");
   for(unsigned i=29;i<32;++i)check(ctx->gpr[i]==SENTINEL+i+run,"callee-saved guest register changed");
   check(nwii::runtime::stops==before+1,"missing expected stop syscall");
   check(ctx->inst_count>before_count+100,"init_data too few instructions executed");
   const std::array<uint64_t,6> expected_entries{1u,static_cast<uint64_t>(!is_original),
      static_cast<uint64_t>(!is_original),static_cast<uint64_t>(is_original?3:2),
      static_cast<uint64_t>(is_original?3:2),1u};
   for(unsigned i=0;i<expected_entries.size();++i)
     check(nwii::runtime::entries[i]-before_entries[i]==expected_entries[i],
           "unexpected original PPC data init helper dispatch count");
   if(!is_original){
     for(unsigned i=0;i<65;++i)check(ctx->mmu.read8(0x80032000u+i)==expected_copy[i],"memcpy result differs");
     check(ctx->mmu.read8(0x80032000u+65)==0xD7u,"memcpy overwrote destination canary");
     check(ctx->mmu.read8(0x80032000u+66)==0xD7u,"memcpy overran destination");
     for(unsigned i=0;i<65;++i)check(ctx->mmu.read8(0x80031000u+i)==expected_copy[i],"source bytes changed");
   }
   for(const auto& [addr,size]:zero_ranges){
     const auto* ptr=ctx->mmu.get_ptr(addr);
     for(uint32_t i=0;i<size;++i)check(ptr[i]==0,"BSS byte not cleared");
     check(ctx->mmu.read8(addr-1)==0xA7u,"BSS write underflow");
     check(ctx->mmu.read8(addr+size)==0xC7u,"BSS write overflow");
   }
 }
 check(nwii::runtime::unexpected==0&&nwii::runtime::interpreter_fallback==0,"unexpected guest fallback");
 std::cout<<std::dec<<"PASS: "<<tests<<" V22 original PPC __init_data checks, table="<<(is_original?"owner":"synthetic")
          <<" trials="<<trials<<" BSS_ranges="<<zero_ranges.size()<<" native_stop="<<nwii::runtime::stops<<"\n";
}
