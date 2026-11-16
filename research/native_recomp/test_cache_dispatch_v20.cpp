// Original-free behavioral specification for NWiiRecomp's genuine dispatcher.
// Game-derived output.cpp is created only privately by owner-local generator.
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>

#ifndef V20_OWNER
#define V20_OWNER 0
#endif
namespace {
constexpr uint32_t ENTRY=0x8000403cu, POST_START=ENTRY+8;
constexpr uint32_t CACHE=0x80522540u, L2READ=0x804b7930u, L2WRITE=0x804b7938u;
constexpr uint32_t ERR=0x805230b8u, DBG=0x804e50b8u, ICE=0x805223bcu, DCE=0x80522280u;
constexpr uint32_t STACK_OWNER=0x80751cb8u,STACK_SYN=0x80060000u;
constexpr std::array<uint32_t,4> MOCK_OS{ICE,DCE,DBG,ERR};
uint64_t checks=0;
void ck(bool test,const char*what){if(!test)throw std::runtime_error(what);++checks;}
uint32_t rand32(uint32_t& state){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint64_t cache_entries=0,l2reads=0,l2writes=0,other_funcs=0;
static uint32_t syscall_n=0,post_stops=0,unexpected=0,fallbacks=0;
static std::array<uint32_t,4> stub_counts{};
static double expected_scalar=0,expected_ps1=0;
static uint32_t expected_fpscr=0;
void trace_call(uint32_t pc,CPUContext& ctx){
    if(pc==CACHE){++cache_entries;ck(ctx.lr==0x800042fcu,"cache caller LR differs");}
    else if(pc==L2READ)++l2reads;
    else if(pc==L2WRITE)++l2writes;
    else ++other_funcs;
}
bool handle_syscall(CPUContext& ctx){
    ++syscall_n;
    if(ctx.pc==POST_START){++post_stops;ctx.is_running=false;return true;}
    for(unsigned k=0;k<MOCK_OS.size();++k){
        if(ctx.pc==MOCK_OS[k]){
            ++stub_counts[k];
            // Explicit OS stubs only. Original cache code NEVER replaced here.
            if(ctx.pc==ERR)ck(ctx.gpr[3]==1,"OSSetErrorHandler requested wrong exception index");
            return true;
        }
    }
    ++unexpected;throw std::runtime_error("unexpected synthetic syscall or Wii service");
}
void interpret_step(CPUContext&){++fallbacks;throw std::runtime_error("unexpected interpreter fallback");}
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
extern "C" void run_game(nwii::runtime::CPUContext& ctx);
int main(){
  auto context=std::make_unique<nwii::runtime::CPUContext>();
  uint32_t rng=0x57491386u;
  const unsigned count=128;
  for(unsigned n=0;n<count;++n){
    auto& ctx=*context;
    const bool i_on=(n&4u)==0;
    const bool d_on=(n&2u)==0;
    const bool l2_on=(n&1u)==0;
    for(auto& g:ctx.gpr)g=rand32(rng);
    const uint32_t msr0=rand32(rng)&~0x2000u;
    ctx.msr=msr0;
    const uint32_t hid0_initial=(rand32(rng)&0x00ff0000u) & ~(0x4000u|0x8000u);
    ctx.hid0=hid0_initial | (i_on?0x8000u:0u) | (d_on?0x4000u:0u);
    const uint32_t hid0_expected=ctx.hid0 | 0x00000800u;
    ctx.hid2=rand32(rng)&~0xa0000000u;
    const uint32_t hid2_expected=ctx.hid2|0xa0000000u;
    for(auto& q:ctx.gqr)q=0xffffffffu;
    const uint32_t l2_old=(rand32(rng)&0x0000ff00u) | (l2_on?0x80000000u:0u);
    ctx.l2cr=l2_old;ctx.l2cr_busy_polls=0;
    const uint32_t ps_addr=V20_OWNER?0x8070db08u:0x80034000u;
    const uint32_t fp_addr=V20_OWNER?0x8070db10u:0x80034100u;
    nwii::runtime::expected_ps1=-3.75-(n%13)*0.125;
    ctx.mmu.write_f32(ps_addr,1.5f+float(n%11)*0.125f);
    ctx.mmu.write_f32(ps_addr+4,static_cast<float>(nwii::runtime::expected_ps1));
    nwii::runtime::expected_fpscr=rand32(rng);
    const uint64_t fpbits=0x3ff0000000000000ull|nwii::runtime::expected_fpscr;
    ctx.mmu.write64(fp_addr,fpbits);
    ctx.mmu.write64(0x80034110u,fpbits);
    std::memcpy(&nwii::runtime::expected_scalar,&fpbits,sizeof(fpbits));
    for(unsigned i=0;i<32;++i){ctx.fpr[i]=0.0;ctx.ps1[i]=0.0;}
    ctx.fpscr=0xffffffffu;
    ctx.is_running=true;
    ctx.pc=ENTRY;
    ctx.lr=0x80009998u;
    const auto before_read=nwii::runtime::l2reads;
    const auto before_write=nwii::runtime::l2writes;
    const auto before_call=nwii::runtime::cache_entries;
    const auto before_stubs=nwii::runtime::stub_counts;
    const auto before_stop=nwii::runtime::post_stops;
    const auto before_inst=ctx.inst_count;
    run_game(ctx);
    ck(!ctx.is_running&&ctx.pc==POST_START,"original startup did not reach final bounded stop");
    ck(ctx.lr==POST_START,"original hardware initializer did not restore return address");
    ck(ctx.gpr[1]==(V20_OWNER?STACK_OWNER:STACK_SYN),"startup stack incorrect after cache init");
    ck(ctx.msr==(msr0|0x2000u),"cache initializer failed to preserve guest MSR");
    ck(ctx.hid0==hid0_expected,"HID0 changed unexpectedly");
    ck(ctx.hid2==hid2_expected,"paired-single HID2 bits wrong");
    ck(ctx.fpscr==nwii::runtime::expected_fpscr,"actual FPR initializer FPSCR changed");
    for(unsigned k=0;k<32;++k){
      ck(ctx.fpr[k]==nwii::runtime::expected_scalar,"FPR bank differs after cache init");
      ck(ctx.ps1[k]==nwii::runtime::expected_ps1,"paired-single half differs after cache init");
    }
    for(auto& q:ctx.gqr)ck(q==0,"GQR not cleared by PSInit");
    ck(nwii::runtime::cache_entries==before_call+1,"cache function wasn't dispatched");
    ck(nwii::runtime::post_stops==before_stop+1,"missing final synthetic stop");
    ck(nwii::runtime::l2reads>before_read,"original L2CR helper was not called");
    ck(V20_OWNER ? (l2_on ? nwii::runtime::l2writes==before_write : nwii::runtime::l2writes>before_write)
                 : nwii::runtime::l2writes>before_write,
       "original L2CR helper write count differs from cache-enable branch");
    ck(ctx.inst_count>before_inst+50,"too few native PowerPC instructions ran");
    ck(ctx.l2cr_busy_polls==0,"L2 invalidate still busy after native return");
    ck((ctx.read_l2cr()&1u)==0,"L2IP status remains set after cache loop");
    ck((ctx.l2cr&0x80000000u)!=0,"cache initializer did not leave L2 enabled");
    ck((ctx.l2cr&0x0000ff00u)==(l2_old&0x0000ff00u),"L2CR unrelated bits were clobbered");
    if(V20_OWNER){
      ck(nwii::runtime::stub_counts[0]==before_stubs[0]+(i_on?0u:1u),"unexpected ICEnable boundary count");
      ck(nwii::runtime::stub_counts[1]==before_stubs[1]+(d_on?0u:1u),"unexpected DCEnable boundary count");
      ck(nwii::runtime::stub_counts[2]==before_stubs[2]+1u+(i_on?0u:1u)+(d_on?0u:1u)+(l2_on?0u:1u),
         "unexpected debug helper branch count");
      ck(nwii::runtime::stub_counts[3]==before_stubs[3]+1,"error handler not registered once");
      ck((ctx.l2cr&0x00200000u)==0,"L2I invalidate command left set");
      ck(l2_on || nwii::runtime::l2writes>=before_write+5,"L2 invalidation register sequence shortened");
    }else{
      ck(nwii::runtime::stub_counts[0]==before_stubs[0]+1,"synthetic IC enable test call missing");
      ck(nwii::runtime::stub_counts[1]==before_stubs[1]+1,"synthetic DC enable test call missing");
      ck(nwii::runtime::stub_counts[2]==before_stubs[2]+1,"synthetic debug call missing");
      ck(nwii::runtime::stub_counts[3]==before_stubs[3]+1,"synthetic handler call missing");
    }
  }
  ck(nwii::runtime::unexpected==0&&nwii::runtime::fallbacks==0,"unexpected Wii OS fallback");
  ck(nwii::runtime::post_stops==count,"wrong number of bounded starts");
  std::cout<<std::dec<<"PASS: "<<checks<<" V20 native "<<(V20_OWNER?"original":"synthetic")
           <<" cache assertions; starts="<<count<<" L2CR_reads="<<nwii::runtime::l2reads
           <<" L2CR_writes="<<nwii::runtime::l2writes<<" OS_stubs="<<nwii::runtime::syscall_n<<"\n";
}
