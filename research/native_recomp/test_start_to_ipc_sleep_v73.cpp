// Recovered V63 native contract: original DSP bootstrap staging and real installed SC vector.
// Runs private original DOL code only when caller explicitly supplies it.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include "exi_id_test_device_v56.h"
#include "exi_sram_test_device_v60.h"
#include "native_sc_vector_v63.h"
#include "dsp_boot_device_v64.h"
#include "wii_ios_bus.h"
#include "native_idle_cache_sc.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
// NWiiRecomp generated function bodies use C++ linkage, unlike run_game.
void func_80000C00(nwii::runtime::CPUContext&);
namespace {
constexpr uint32_t START=0x8000403cu, POST_OWNER=0x80529718u, POST_SYNTH=0x8052a844u;
constexpr uint32_t OS_RET_OWNER=0x8052a4fcu, OS_RET_SYNTH=0x80520694u;
constexpr uint32_t OSINIT=0x80520670u, SAVE20=0x805450e8u;
constexpr uint32_t TIME=0x8052a844u, GETTIME=0x8052a824u;
constexpr uint32_t INT_DISABLE=0x805265acu, INT_RESTORE=0x805265d4u, EXEC=0x80523b1cu, PERF=0x804b7964u;
constexpr uint32_t MFHID0=0x804b7920u,MTHID0=0x804b7928u,SPEC=0x804b7a00u,NONIEEE=0x804b7a28u,HID4=0x804b7a30u,REPORT=0x80522f00u;
constexpr uint32_t START_OS_RET_OWNER=0x80004160u, START_OS_RET_SYNTH=0x80004060u;
constexpr uint32_t OS_INIT_FLAG=0x8070dafcu, SYNTH_OS_MARKER=0x80037004u;
constexpr uint32_t DATA_RETURN=0x80004058u,DBINIT=0x804e5020u;
constexpr uint32_t TABLE=0x80006420u, INIT=0x80004238u;
constexpr uint32_t FLUSH=0x80004304u, COPY=0x80004338u,FILL=0x80004388u,SET=0x8000443cu;
constexpr uint32_t EXI=0x804ef9bcu,MASK=0x8052693cu,HANDLER=0x805265f8u,ID=0x804efd7cu,CACHE=0x80522540u,ERR=0x805230b8u,DBG=0x804e50b8u;
constexpr uint32_t L2_READ=0x804b7930u,L2_WRITE=0x804b7938u;
constexpr uint32_t ICE=0x805223bcu,DCE=0x80522280u;
constexpr uint32_t ORIGINAL_SP=0x80751cb8u,SYNTH_SP=0x80060000u;
constexpr uint32_t R13=0x8070e8e0u,ID_CACHE=R13-3824u,BOOT_BASE=R13-3512u,BOOT_RECORD=R13-3516u;
constexpr uint32_t ARENA_LO=0x80521d60u,ARENA_HI=0x80521d48u;
constexpr uint32_t MEM2_LO=0x80521d68u,MEM2_HI=0x80521d50u,IPC=0x8052ae80u;
constexpr uint32_t EXCEPTION=0x80520bf4u,EXC_SOURCE_WORD=0x80520f28u;
constexpr uint32_t DCFLUSH=0x80522320u,ICINVALID=0x80522378u;
constexpr uint32_t MARK=0x804e50a0u,EXC_TEMPLATE_DST=0x80520f18u;
constexpr uint32_t SOURCE_TEMPLATE=0x80520ec0u,ORACLE_GUEST=0x90050000u;
constexpr uint32_t SYSCALL=0x805290c8u,SYSCALL_SOURCE=0x805290a8u;
constexpr uint32_t SYSCALL_DEST=0x80000c00u,SYSCALL_LEN=28u;
constexpr uint32_t ALARM=0x805210ccu,GETEXC=0x80520eb0u,
    SETEXC=0x80520e9cu,SHUTDOWN=0x80527b4cu;
constexpr uint32_t ALARM_HANDLER=0x805217bcu,SHUTDOWN_NODE=0x8060bcb8u;
constexpr uint32_t INTERRUPT=0x8052661cu,IRQ_STOP=0x8052664cu;
constexpr uint32_t IRQ_TABLE=0x80003040u,IRQ_GLOBAL=R13-3408u;
constexpr uint32_t SETMASK=0x805266e0u,SETMASK_RETURN=0x805266a4u;
constexpr uint32_t CONTEXT=0x80522eb8u,CONTEXT_HANDLER=0x80522e34u;
constexpr uint32_t CONTEXT_WORD=0x800000d8u;
constexpr uint32_t LOW_MASK_PRE=0x800000c0u,LOW_MASK_A=0x800000c4u,
  LOW_MASK_B=0x800000c8u,LOW_MASK_POST=0x800000ccu;
constexpr uint32_t MODULE=0x80526d30u,MODULE_PRE=0x800030c4u,
    MODULE_LO=0x800030c8u,MODULE_MID=0x800030ccu,
    MODULE_HI=0x800030d0u,MODULE_POST=0x800030d4u;
constexpr uint32_t SI_DATA=0x80619a60u,SLOT=0x806fe340u,TYPE_DATA=SI_DATA+24u,
   TYPE_TIME=SLOT+160u,SI_COMMAND=R13-3144u,TYPE_CALLBACK=0x805327f8u;
constexpr uint32_t BUS_CLOCK=243000000u,TYPE_DELAY=3948u,SRAM=0x806f52c0u;
constexpr uint32_t THREAD=0x806f5318u,IDLE_CONTEXT=THREAD+1048u,STACK_BOTTOM=0x80711cb8u,
   THREAD_FRAME=ORIGINAL_SP-8u-80u-32u,THREAD_CALLBACK_PTR=0x8070a908u;
constexpr uint32_t STACK_MAGIC=0xdeadbabeu;
constexpr uint32_t M1_ARENA_HI=0x81700000u,M2_ARENA_HI=0x93380000u,ARENA_FLUSH_BYTES=0x40000u;
constexpr uint32_t M1_ARENA_LO(unsigned n){return 0x81680000u+n*32u;}
constexpr uint32_t M2_ARENA_LO(unsigned n){return 0x93300000u+n*64u;}
constexpr uint64_t FLUSH_LINES=ARENA_FLUSH_BYTES/32u;
constexpr uint32_t REPORT_DATA=0x8060b7a8u,REPORT_SMALL=0x8070a898u;
constexpr uint32_t REPORT_BYTES=600u,REPORT_SMALL_BYTES=24u;
constexpr std::array<uint32_t,4> console_expected{{0x10000002u,17u,0x10000010u,0x10000021u}};
constexpr std::array<uint32_t,4> console_revisions{{0u,1u,0u,17u}};
struct BootReportCall {uint32_t lr,fmt;std::array<uint32_t,3> args;unsigned nargs;};
constexpr uint32_t MI_NODE=0x8060d030u,MI_FLAG=R13-3400u,MI_HANDLER=0x8052707cu;
constexpr uint32_t MEM1_BYTES=0x01800000u,MEM2_BYTES=0x04000000u,MEM2_MAP_HI=0x93400000u;
constexpr std::array<std::pair<uint32_t,uint32_t>,32> expected_bat_writes{{
 {536,0},{537,2},{536,0x800001ffu},{528,0},{529,2},{528,0x800001ffu},
 {540,0},{541,0x01000002u},{540,0x810000ffu},{532,0},{533,0x01000002u},{532,0x810000ffu},
 {568,0},{569,0x10000002u},{568,0x900003ffu},{560,0},{561,0},
 {570,0},{571,0x1000002au},{570,0xd00007ffu},{562,0},{563,0},
 {572,0},{573,0x12000002u},{572,0x920001ffu},{564,0},{565,0},
 {574,0},{575,0x13000002u},{574,0x9300007fu},{566,0},{567,0}
}};
constexpr uint32_t DSP_SRC=0x8060bcc8u,DSP_STAGING=0x81000000u,DSP_BACKUP=0x816fff80u,DSP_SIZE=128u;
constexpr uint32_t AUDIO_FRAME=ORIGINAL_SP-8u-80u-16u,RESET_FRAME=AUDIO_FRAME-32u;
constexpr uint32_t CLOCK_REG=0x0d800180u,RESET_REG=0x0d8001d0u,CONFIG_REG=0x0d8001ccu;
constexpr uint32_t CLOCK_SEED=0x13579bdfu,RESET_SEED=0xfedcba98u,CONFIG_SEED=0xa5a55a5au;
constexpr uint32_t RESET_OFF=RESET_SEED&0x3fffffffu,RESET_STAGE2=RESET_OFF&~0x10000000u,
    RESET_STAGE3=RESET_STAGE2|0x40000000u,RESET_ON=RESET_STAGE3|0x80000000u;
constexpr std::array<std::pair<uint32_t,uint32_t>,6> audio_reads_expected{{
  {CLOCK_REG,CLOCK_SEED},{RESET_REG,RESET_SEED},{CONFIG_REG,CONFIG_SEED},
  {RESET_REG,RESET_OFF},{RESET_REG,RESET_STAGE2},{RESET_REG,RESET_STAGE3}}};
constexpr std::array<std::pair<uint32_t,uint32_t>,6> audio_writes_expected{{
  {CLOCK_REG,(CLOCK_SEED|0x100u)&~0x80u},{RESET_REG,RESET_OFF},
  {CONFIG_REG,(CONFIG_SEED&0xf8000000u)|0x04b0ffceu},{RESET_REG,RESET_STAGE2},
  {RESET_REG,RESET_STAGE3},{RESET_REG,RESET_ON}}};
constexpr std::array<uint32_t,5> wait_starts{{0x80521e18u,0x80521ea8u,0x80521ef4u,0x80521f44u,0x80521f94u}},
    wait_polls{{0x80521e2cu,0x80521ebcu,0x80521f08u,0x80521f58u,0x80521fa8u}},
    wait_min_ticks{{6075u,6075u,60750u,60750u,60750u}};
constexpr uint32_t ALARM_HEAD=R13-3496u,SHUTDOWN_HEAD=R13-3376u,
    SHUTDOWN_TAIL=R13-3372u;
constexpr uint32_t VECTOR_DEST=0x80000100u,VECTOR_LEN=0x98u;
constexpr uint32_t MEM2_LO_HINT=0x80003124u,MEM2_HI_HINT=0x80003128u;
constexpr uint32_t MEM2_LO_GLOBAL=R13-16396u,MEM2_HI_GLOBAL=R13-3468u;
constexpr uint32_t IPC_LO_GLOBAL=R13-16336u,IPC_HI_GLOBAL=R13-3352u;
constexpr uint32_t IPC_LO_INPUT=0x80003130u,IPC_HI_INPUT=0x80003134u;
constexpr uint32_t LO_GLOBAL=R13-16400u,HI_GLOBAL=R13-3472u;
constexpr uint32_t BOOT_FALLBACK=R13-3520u,BOOT_FIELD=R13-3216u;
constexpr uint32_t BOOT_MODE=R13-16864u,BOOT_HINT=0x8000310cu;
struct ExceptionStop {};
uint64_t checks=0;
void check(bool result,const char*why){if(!result)throw std::runtime_error(why);++checks;}
uint32_t random32(uint32_t&state){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
struct Span {uint32_t start,size;};
std::vector<Span> zero_table(nwii::runtime::CPUContext&ctx){
  std::vector<Span> v;
  for(unsigned i=0;i<4;++i){
    const uint32_t at=TABLE+0x90+8*i;
    const uint32_t address=ctx.mmu.read32(at),size=ctx.mmu.read32(at+4);
    if(size==0)break;
    check(address>=0x80000000u&&size<=1024*1024u,"BSS table range outside test limit");
    v.push_back({address,size});
  }
  return v;
}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static std::array<uint64_t,5> data_calls{};
static uint64_t l2_reads=0,l2_writes=0,ic_calls=0,dc_calls=0,cache_calls=0;
static uint64_t post_stops=0,db_entries=0,os_entries=0,save_entries=0,unknown_calls=0,interpreter_calls=0;
static std::array<uint64_t,2> external_stubs{};
static uint64_t time_entries=0, gettime_entries=0, disable_entries=0, restore_entries=0;
static uint32_t observed_stop_pc=0;
static uint64_t time_global_checks=0;
static uint64_t exec_entries=0;
static std::array<uint64_t,6> perf_entries{};
static std::array<uint64_t,5> hardware_entries{};
static std::array<uint64_t,2> arena_entries{};
static std::array<uint64_t,2> mem2_entries{};
static uint64_t ipc_entries=0;
static uint64_t exception_entries=0;
static uint64_t marker_entries=0;
static uint64_t dcflush_entries=0,icinvalid_entries=0;
static uint64_t syscall_entries=0;
static uint64_t alarm_entries=0,alarm_get_entries=0,
    alarm_set_entries=0,shutdown_entries=0,module_entries=0;
static uint64_t irq_entries=0,irq_memset_entries=0,irq_fill_entries=0;
static uint64_t irq_disable_entries=0;
static uint64_t setmask_entries=0;
static uint64_t irq_restore_entries=0,irq_setexc_entries=0;
static uint64_t context_entries=0,context_setexc_entries=0,context_debug_entries=0;
static uint64_t cache_os_entries=0, exi_entries=0, mask_entries=0;
static uint64_t mask_disable_entries=0, mask_restore_entries=0;
static uint64_t handler_entries=0,id_entries=0;
static ExiIdTestDevice id_device;
static ExiSramTestDevice sram_device;
static CPUContext* sram_ctx=nullptr;
static uint32_t sram_command_ptr=0;
static uint64_t sram_entries=0,sram_dma_entries=0,sram_invalidate_entries=0,sram_unlock_entries=0,sram_config_unlock_entries=0;
static uint64_t thread_entries=0,thread_clear_entries=0,thread_context_entries=0,thread_callback_entries=0,thread_sp_entries=0;
static bool audio_active=false;
static uint32_t report_trial=0,report_ctr=0;
static unsigned arena_phase=0,arena_getters=0,arena_reset_calls=0,arena_reset_reads=0,
    arena_zero_calls=0,arena_flush_calls=0,arena_sc_calls=0;
 static unsigned enable_entries=0;
 static uint32_t enable_before=0;
 static bool ipc69_active=false;
 // Native owner-test RAM adapter: IOS sees physical MEM1/MEM2 only.
 // MMIO, cached CPU aliases and ranges crossing banks are rejected.
 class OwnerIosMemory final:public undercover::wii::IosMemory{
 public:
   CPUContext* cpu=nullptr;
   bool valid(uint32_t a,uint32_t n)const override{
     if(!cpu||!n)return false;
     const uint64_t end=uint64_t(a)+n;
     if(!(end<=MEM1_BYTES||(a>=0x10000000u&&end<=uint64_t(0x10000000u)+MEM2_BYTES)))return false;
     auto* first=cpu->mmu.get_ptr(a|0x80000000u);
     return first&&cpu->mmu.get_ptr((a+n-1u)|0x80000000u)==first+n-1u;
   }
   uint8_t read8(uint32_t a)const override{
     check(valid(a,1),"native IOS requested unmapped physical RAM read");
     return cpu->mmu.read8(a|0x80000000u);
   }
   void write8(uint32_t a,uint8_t v)override{
     check(valid(a,1),"native IOS requested unmapped physical RAM write");
     cpu->mmu.write8(a|0x80000000u,v);
   }
 };
 static OwnerIosMemory ipc70_ram;
 static undercover::wii::IosBus ipc70_bus(ipc70_ram);
 static unsigned ipc69_step=0,ipc69_os_get=0,ipc69_disable=0,ipc69_restore=0,ipc69_bank=0,ipc69_mail=0;
 static uint32_t ipc69_lo=0,ipc69_hi=0,ipc69_size=0,ipc69_handler=0,ipc69_mask=0,ipc69_msg=0,ipc69_msr=0;
 static std::array<uint32_t,32> ipc69_gprs{},ipc69_irqs{};
 static constexpr uint32_t IPC69_LIMIT=0x10000u;
 static bool seed_stm_data(CPUContext&,uint32_t,unsigned);
 static void ipc69_entry(uint32_t addr,CPUContext& ctx){
   if(addr==0x805194c4u){
     check(!ipc69_active&&enable_entries==1u&&ctx.msr==(enable_before|0x8000u)&&ctx.gpr[3]==0u&&
           ctx.lr==0x8052094cu&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&arena_sc_calls==2u,
           "IPC client must follow verified original interrupt enable");
     // Restore the original initialized SDA words missing from the reduced
     // fixture before IPCCltInit owns them. In particular the heap handle
     // is subsequently written by the authentic heap creation call.
     // Never reseed these words after guest initialization or at a branch.
     for(int32_t offset:{-16664,-16660}){
       const uint32_t address=ctx.gpr[13]+uint32_t(offset);
       check(ctx.mmu.read32(address)==0u,"IPC initial SDA fixture word unexpectedly populated");
       check(seed_stm_data(ctx,address,4u)&&ctx.mmu.read32(address)!=0u,
             "IPC initialized SDA data unavailable from authenticated owner");
     }
     ipc69_active=true;
     ipc69_lo=ctx.mmu.read32(IPC_LO_INPUT);ipc69_hi=ctx.mmu.read32(IPC_HI_INPUT);
     check(ipc69_lo==ctx.mmu.read32(IPC_LO_GLOBAL)&&ipc69_hi==ctx.mmu.read32(IPC_HI_GLOBAL)&&
           ipc69_lo%32u==0u&&ipc69_hi-ipc69_lo>IPC69_LIMIT,"IPC original OS buffer bounds differ");
     ipc69_msr=ctx.msr;
     for(unsigned r=0;r<32u;++r){ipc69_gprs[r]=ctx.gpr[r];ipc69_irqs[r]=ctx.mmu.read32(IRQ_TABLE+4u*r);}
     ipc69_mask=ctx.mmu.read32(LOW_MASK_A);
     check(ipc69_mask==0xf7fff7f0u&&ctx.mmu.read32(LOW_MASK_B)==0u,"IPC initial interrupt mask differs");
     auto* p=ctx.mmu.get_ptr(ipc69_lo);
     check(p&&ctx.mmu.get_ptr(ipc69_lo+IPC69_LIMIT-1u)==p+IPC69_LIMIT-1u,"test IPC heap not contiguous");
     std::memset(p,0x6bu,IPC69_LIMIT);
     ctx.mmu.write8(ipc69_lo-1u,0xd3u);ctx.mmu.write8(ipc69_lo+IPC69_LIMIT,0x3du);
     return;
   }
   constexpr std::array<uint32_t,9> targets{{0x80518fc8u,0x80519084u,0x8051907cu,0x8051aa04u,
     0x8051908cu,0x805265f8u,0x805269bcu,0x8051906cu,0x8051af28u}};
   constexpr std::array<uint32_t,9> lr{{0x805194f8u,0x805194fcu,0x80519508u,0x80519524u,
     0x80519530u,0x80519540u,0x80519548u,0x80519554u,0x80519558u}};
   if(ipc69_step<targets.size()&&addr==targets[ipc69_step]&&ctx.lr==lr[ipc69_step]){
     const unsigned step=ipc69_step++;
     if(step==1u)check(ipc69_os_get==2u,"IPC main initializer did not consult both OS buffer bounds");
     if(step==2u)check(ctx.gpr[3]==ipc69_lo,"IPC buffer low getter returned wrong pointer");
     if(step==3u){
       check(ctx.gpr[3]==ipc69_lo&&ctx.gpr[4]>=32u&&ctx.gpr[4]<IPC69_LIMIT&&ctx.gpr[4]%32u==0u,
             "IPC native heap create ABI: bounded aligned base and length expected");
       ipc69_size=ctx.gpr[4];
     }
     if(step==4u){
       check(ipc69_disable==1u&&ipc69_restore==1u&&ctx.gpr[3]==ipc69_lo+ipc69_size,
             "IPC heap allocator or next free buffer pointer differs");
       bool changed=false;for(unsigned i=0;i<32u;++i)changed|=ctx.mmu.read8(ipc69_lo+i)!=0x6bu;
       check(changed&&ctx.mmu.read8(ipc69_lo-1u)==0xd3u&&ctx.mmu.read8(ipc69_lo+ipc69_size)==0x6bu,
             "IPC heap metadata did not initialize within allocation");
     }
     if(step==5u){
       check(ctx.gpr[3]==27u&&ctx.gpr[4]>=0x80519094u&&ctx.gpr[4]<0x805194c4u&&
             !(ctx.gpr[4]&3u)&&ctx.mmu.read32(IRQ_TABLE+27u*4u)==0u,
             "IPC IRQ registration ABI differs");
       ipc69_handler=ctx.gpr[4];
       check(ipc69_handler==0x80519094u||ipc69_handler==0x805190c0u||ipc69_handler==0x80519318u,
             "IPC registered handler not in authenticated function inventory");
       std::cout<<"V72_IRQ_HANDLER candidate="<<(ipc69_handler==0x80519094u?1u:ipc69_handler==0x805190c0u?2u:3u)<<std::endl;
     }
     if(step==6u)check(ctx.gpr[3]==0x10u&&ctx.mmu.read32(IRQ_TABLE+27u*4u)==ipc69_handler,
                       "IPC native unmask must follow IRQ handler registration");
     if(step==7u){
       check(ctx.gpr[3]==1u&&(ctx.gpr[4]&0x30u)!=0u&&!(ctx.gpr[4]&~0x3fu),
             "IPC mailbox control write ABI differs");
       ipc69_msg=ctx.gpr[4];
     }
     if(step==8u)check(ipc69_mail==1u,"IPC profiler init preceded mailbox control write");
     return;
   }
   if(addr==0x8052ae70u||addr==0x8052ae78u){
     check(ipc69_step==1u&&ipc69_os_get<2u&&ctx.lr==(ipc69_os_get?0x80518fecu:0x80518fe4u),
           "IPC OS buffer getter order differs");
     ++ipc69_os_get;return;
   }
   if(addr==INT_DISABLE){
     check((ctx.lr==0x8051aa2cu||ctx.lr==0x805269dcu)&&(ctx.msr&0x8000u),
           "IPC nested interrupt disable callsite/state differs");
     ++ipc69_disable;return;
   }
   if(addr==INT_RESTORE){
     check((ctx.lr==0x8051ab14u||ctx.lr==0x80526a1cu)&&!(ctx.msr&0x8000u)&&ctx.gpr[3]==1u,
           "IPC nested interrupt restore callsite/state differs");
     ++ipc69_restore;return;
   }
   if(addr==SETMASK){
     check(ipc69_step==7u&&ctx.lr==0x80526a0cu&&ctx.gpr[3]==0x10u,
           "IPC original interrupt mask bank call differs");
     ++ipc69_bank;return;
   }
   check(false,"unexpected original IPC client native dependency");
 }
static bool arena_active=false;
static uint32_t arena_low(unsigned phase){return phase==1u?M1_ARENA_LO(report_trial):M2_ARENA_LO(report_trial);}
static uint32_t arena_high(unsigned phase){return phase==1u?M1_ARENA_HI:M2_ARENA_HI;}
static uint32_t arena_clear_lr(unsigned phase){return phase==1u?0x80520020u:0x805201fcu;}
static uint32_t arena_flush_lr(unsigned phase){return phase==1u?0x8052002cu:0x80520208u;}
static uint32_t reset_seed(){return 0x100u+report_trial*8u;}
static uint64_t expected_zero_lines(unsigned phase){
  uint64_t sum=0;for(unsigned i=1;i<=phase;++i)sum+=(arena_high(i)-arena_low(i))/32u;
  return sum;
}
static void verify_arena_bytes(CPUContext& c,unsigned phase){
  const uint32_t lo=arena_low(phase),hi=arena_high(phase);
  auto* p=c.mmu.get_ptr(lo);auto* last=c.mmu.get_ptr(hi-1u);
  check(p&&last==p+(hi-lo)-1u,"bounded arena range not contiguous guest RAM");
  for(uint32_t i=0;i<hi-lo;++i)check(p[i]==0u,"original dcbz arena retained nonzero RAM");
  check(c.mmu.read8(lo-1u)==0x91u&&c.mmu.read8(hi)==(phase==1u?0xb2u:0x92u),
        "original arena zero loop crossed adjacent RAM canaries");
}
static unsigned report_entries=0,report_calls=0,console_entries=0,report_getters=0;
static std::array<uint8_t,REPORT_BYTES> report_data{};
static std::array<uint8_t,REPORT_SMALL_BYTES> report_small{};
static std::array<BootReportCall,10> expected_report{};
static uint32_t private_report_word(unsigned offset){
  return (uint32_t(report_data.at(offset))<<24)|(uint32_t(report_data.at(offset+1))<<16)|
         (uint32_t(report_data.at(offset+2))<<8)|report_data.at(offset+3);
}
static uint32_t bcd(unsigned v){return (v/10u)*16u+v%10u;}
static void setup_report(CPUContext& c,unsigned trial){
  report_trial=trial;report_entries=report_calls=console_entries=report_getters=report_ctr=0;
  const unsigned mode=trial%4u;
  c.mmu.write32(0x8000002cu,mode?0x10000002u:0u);
  c.mmu.write16(0x800030e6u,mode==1u?2u:0x8000u);
  c.mmu.write32(0x80003118u,mode>=2u?0x08000000u:0x04000000u);
  c.mmu.write32(0x80003138u,console_revisions[mode]);
  const uint32_t a=4u+trial,b=10u+trial,d=33u+trial;
  c.mmu.write32(0x80003140u,(a<<16)|(b<<8)|d);
  const unsigned day=trial+1u,month=trial%12u+1u,year=2000u+trial;
  c.mmu.write32(0x80003144u,(bcd(day)<<16)|(bcd(month)<<8)|bcd(trial));
  uint32_t console_lr=0x8052055cu,console_fmt=REPORT_DATA+328u,console_arg=console_expected[mode];unsigned console_nargs=1;
  if(mode==1u){console_lr=0x8052047cu;console_fmt=REPORT_DATA+152u;console_nargs=0;}
  if(mode>=2u){
    const unsigned index=console_arg-0x10000008u;
    report_ctr=private_report_word(496u+4u*index);
    if(report_ctr!=0x8052054cu){
      constexpr std::array<uint32_t,6> targets{{0x805204ecu,0x805204fcu,0x8052050cu,0x8052051cu,0x8052052cu,0x8052053cu}};
      const auto it=std::find(targets.begin(),targets.end(),report_ctr);
      check(it!=targets.end(),"original console table selected unknown local target");
      console_fmt=REPORT_DATA+244u+12u*unsigned(it-targets.begin());
      console_lr=report_ctr+12u;console_nargs=0;
    }
  }
  expected_report={{{0x805203ecu,REPORT_DATA+72u,{},0},
    {0x80520400u,REPORT_DATA+88u,{REPORT_DATA+112u,REPORT_DATA+124u,0},2},
    {0x8052040cu,REPORT_DATA+136u,{},0},
    {console_lr,console_fmt,{console_arg,0,0},console_nargs},
    {0x805205acu,REPORT_DATA+384u,{a,b,d},3},
    {0x805205f8u,REPORT_DATA+412u,{day,month,year},3},
    {0x80520618u,REPORT_DATA+424u,{88u,0,0},1},
    {0x80520638u,REPORT_DATA+440u,{M1_ARENA_LO(trial),M1_ARENA_HI,0},2},
    {0x80520658u,REPORT_DATA+468u,{M2_ARENA_LO(trial),M2_ARENA_HI,0},2},
    {0x80520908u,R13-16436u,{REPORT_DATA,0,0},1}}};
}
static void check_private_report_string(CPUContext& c,uint32_t addr){
  const bool main=addr>=REPORT_DATA&&addr<REPORT_DATA+496u;
  check(main||(addr>=REPORT_SMALL&&addr<REPORT_SMALL+REPORT_SMALL_BYTES),"original report format pointer outside authenticated data");
  const uint32_t base=main?REPORT_DATA:REPORT_SMALL,limit=main?496u:REPORT_SMALL_BYTES;
  for(unsigned i=addr-base;i<limit;++i){
    const uint8_t v=main?report_data[i]:report_small[i];
    check(c.mmu.read8(base+i)==v,"original report format byte differs from authenticated owner data");
    if(!v)return;
  }
  check(false,"original report string not bounded by initialized data");
}
static bool mi_active=false;
static unsigned mi_writes=0,mi_handlers=0,mi_trampolines=0,mi_maps=0;
static uint64_t mi_entries=0,mi_map_entries=0,mi_shutdown_entries=0,mi_unmask_entries=0,mi_hid_reads=0,mi_hid_writes=0;
static uint32_t mi_hid_before=0;
static DspBootDevice dsp;
static CPUContext* dsp_ctx=nullptr;
static std::array<uint8_t,64> aram{};
static unsigned dsp_wait_polls=0;
static uint32_t dsp_wait_start=0,dsp_wait_delta=0,dsp_wait_previous=0;
static bool dsp_wait_started=false,dsp_wait_finished=false;
static void finish_dsp_wait(){
  check(dsp_wait_started&&!dsp_wait_finished&&dsp_wait_polls>1u&&
        dsp_wait_previous<2194u&&dsp_wait_delta>=2194u&&dsp_wait_delta<2258u,
        "original inter-ARAM DMA delay did not reach 2194 guest ticks");
  dsp_wait_finished=true;
}
static std::array<uint8_t,128> dsp_image{},dsp_original_ram{};
static std::array<uint8_t,28> sc_vector{};
static uint64_t dsp_arena_entries=0,dsp_copy_entries=0,dsp_flush_entries=0,sc_entries=0,sc_vector_entries=0;
static unsigned audio_read_count=0,audio_write_count=0,wait_index=0;
static uint32_t wait_start_tick=0,last_wait_delta=0,previous_wait_delta=0;
static bool wait_started=false;
static uint64_t audio_entries=0,reset_entries=0;
static std::array<unsigned,5> wait_counts{};
static void finish_wait(){
  check(wait_index<5u&&wait_started&&wait_counts[wait_index]>1u&&
        previous_wait_delta<wait_min_ticks[wait_index]&&
        last_wait_delta>=wait_min_ticks[wait_index]&&last_wait_delta<wait_min_ticks[wait_index]+64u,
        "original Hollywood hold interval outside native timebase bound");
  ++wait_index;wait_started=false;
}
static uint32_t last_csr=0;
static uint64_t lock_entries=0,select_entries=0,imm_entries=0,
    sync_entries=0,deselect_entries=0,irqmask_entries=0,revision_entries=0;
static uint32_t response_id=0,version_pointer=0;
static unsigned probe_channel=0,probe_reads=0;
static uint64_t probe_entries=0,version_entries=0,version_report_entries=0;
static uint32_t si_version_pointer=0,si_expected=0,si_clock=0,si_busy=0;
static unsigned si_phase=0,si_polls=0,si_channel=0,si_read_phase=0;
static uint64_t si_type_entries=0,si_transfer_entries=0,si_start_entries=0;
static std::array<uint64_t,4> si_type_times{};
static uint64_t si_entries=0,si_rate_entries=0,si_tv_entries=0,si_xy_entries=0,
                si_handler_entries=0,si_unmask_entries=0,si_version_entries=0,si_report_entries=0;
static std::array<unsigned,3> exi_busy{0u,0u,0u};
static std::vector<std::pair<uint32_t,uint32_t>> exi_reads;
static std::vector<std::pair<uint32_t,uint32_t>> mmio_reads;
static uint64_t unexpected_mmio=0;
static std::vector<std::pair<uint32_t,uint32_t>> mmio_writes;
static uint64_t exception_restore_entries=0;
static uint64_t exception_epilogue_debug_entries=0;
static uint32_t cache_sync_entry=0,cache_isync_entry=0;
 static const nwii::loader::Executable* stm70_owner=nullptr;
 static bool stm70_entered=false;
 static unsigned stm70_open=0;
 static uint32_t stm70_path=0;
 static unsigned open71_profile=0,open71_alloc=0,open71_alloc_disable=0,open71_alloc_restore=0,open71_flush=0,open71_sc=0,open71_submit=0;
 static uint32_t open71_path_len=0,open71_flush_base=0,open71_flush_len=0,open71_stack=0;
 static uint64_t open71_flush_before=0;
 static bool submit72_active=false;
 static unsigned submit72_flush=0,submit72_sc=0,submit72_disable=0,submit72_message=0,submit72_x1=0,submit72_ack=0;
 static uint32_t submit72_base=0,submit72_len=0,submit72_phys=0;
 static uint64_t submit72_flush_before=0;
 static uint32_t sleep73_queue=0,sleep73_sp=0;
 static unsigned sleep73_init=0,sleep73_entry=0,sleep73_disable=0,sleep73_select=0;
 static uint32_t original_word(uint32_t pc){
   check(stm70_owner!=nullptr,"STM private original source not provided");
   for(const auto& sec:stm70_owner->sections){
     if(!sec.is_bss&&sec.is_text&&sec.address<=pc&&uint64_t(pc)+4u<=uint64_t(sec.address)+sec.data.size()){
       auto i=pc-sec.address;
       return uint32_t(sec.data[i])<<24|uint32_t(sec.data[i+1])<<16|uint32_t(sec.data[i+2])<<8|uint32_t(sec.data[i+3]);
     }
   }
   throw std::runtime_error("STM original text outside authenticated source");
 }
 static bool seed_stm_data(CPUContext&ctx,uint32_t addr,unsigned n){
   for(const auto& sec:stm70_owner->sections){
     if(!sec.is_bss&&!sec.is_text&&sec.address<=addr&&uint64_t(addr)+n<=uint64_t(sec.address)+sec.data.size()){
       for(unsigned i=0;i<n;++i)ctx.mmu.write8(addr+i,sec.data[addr-sec.address+i]);
       return true;
     }
   }
   return false;
 }
 static void stm70_entry(CPUContext& ctx){
   check(!stm70_entered&&ctx.lr==0x80520968u&&ctx.gpr[1]==ipc69_gprs[1],
         "original OSInit STM entry ABI differs");
       check(ipc69_active&&ipc69_step==9u&&ipc69_os_get==2u&&ipc69_disable==2u&&ipc69_restore==2u&&
             ipc69_bank==1u&&ipc69_mail==1u&&ctx.msr==ipc69_msr,
             "original IPC client initialization return state or dependency counts differ");
       using Bus=undercover::wii::IosBus;using Mail=undercover::wii::IpcMailbox;using Irq=undercover::wii::HollywoodIrq;
       check(ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL)==(ipc69_msg&0x39u)&&
             !ipc70_bus.external_irq_level()&&!ipc70_bus.services().event_pending(),
             "IPC startup mailbox readback or idle reply state differs");
       check((ipc70_bus.read32(Bus::IPC+Irq::PPC_MASK).value_or(0u)&Irq::IPC_PPC)!=0u,
             "original startup failed to enable native Hollywood IPC interrupt route");
       check(ctx.gpr[1]==ipc69_gprs[1]&&ctx.gpr[2]==ipc69_gprs[2]&&ctx.gpr[13]==ipc69_gprs[13],
             "IPC native return corrupted ABI stack or SDA registers");
       for(unsigned r=14;r<32u;++r)check(ctx.gpr[r]==ipc69_gprs[r],"IPC native return corrupted nonvolatile GPR");
       for(unsigned i=0;i<32u;++i)check(ctx.mmu.read32(IRQ_TABLE+4u*i)==(i==27u?ipc69_handler:ipc69_irqs[i]),
             "IPC original IRQ handler table changed unexpected slot");
       check(ctx.mmu.read32(LOW_MASK_A)==(ipc69_mask&~0x10u)&&ctx.mmu.read32(LOW_MASK_B)==0u,
             "IPC original unmask changed unrelated interrupt bits");
       check(ctx.mmu.read8(ipc69_lo-1u)==0xd3u&&ctx.mmu.read8(ipc69_lo+IPC69_LIMIT)==0x3du,
             "IPC heap test buffer boundary overwritten");
       for(uint32_t i=ipc69_size;i<IPC69_LIMIT;++i)check(ctx.mmu.read8(ipc69_lo+i)==0x6bu,"IPC heap wrote beyond reserved size");
   stm70_entered=true;
   // Seed only initialized SDA operands of the authenticated prefix.
   // Previously initialized runtime state is checked before this step;
   // no return values, branches or instructions are patched here.
   for(uint32_t pc=0x8052b034u;pc<0x8052b08cu;pc+=4u){
     const auto op=original_word(pc);const auto major=op>>26,ra=(op>>16)&31u;
     if((ra==2u||ra==13u)&&(major==32u||major==34u||major==40u||major==42u)){
       const uint32_t addr=ctx.gpr[ra]+uint32_t(int32_t(int16_t(op&0xffffu)));
       const unsigned n=major==32u?4u:major==34u?1u:2u;
       (void)seed_stm_data(ctx,addr,n);
     }
   }
 }
 static void stm70_open_entry(CPUContext& ctx){
   check(stm70_entered&&stm70_open==0u&&ctx.lr==0x8052b090u&&ctx.gpr[4]==0u,
         "STM first IOS_Open callsite or mode differs");
   stm70_path=ctx.gpr[3];
   check(stm70_path>=0x80000000u&&stm70_path<0x81800000u,
         "STM IOS_Open pathname pointer outside MEM1");
   std::string path;
   for(unsigned i=0;i<64u;++i){
     check(seed_stm_data(ctx,stm70_path+i,1),"STM IOS_Open pathname outside original initialized data");
     const auto ch=ctx.mmu.read8(stm70_path+i);
     if(!ch)break;
     path.push_back(char(ch));
   }
   check(path=="/dev/stm/immediate"||path=="/dev/stm/eventhook",
         "STM original IOS_Open did not select a documented device path");
   open71_path_len=uint32_t(path.size()+1u);open71_stack=ctx.gpr[1];
   ++stm70_open;
 }
static bool open71_ram(uint32_t addr,uint32_t n){
   const uint32_t physical=addr&0x3fffffffu;
   return n&&((physical<0x01800000u&&uint64_t(physical)+n<=0x01800000ull)||
      (physical>=0x10000000u&&uint64_t(physical)+n<=0x14000000ull));
 }
 static bool open71_request_pointer(CPUContext&ctx,uint32_t addr){
   if(!addr||(addr&3u)||!open71_ram(addr,32u))return false;
   const uint32_t cached=(addr&0x3fffffffu)|0x80000000u;
   if(ctx.mmu.read32(cached)!=1u)return false;
   return (ctx.mmu.read32(cached+12u)&0x3fffffffu)==(stm70_path&0x3fffffffu)&&ctx.mmu.read32(cached+16u)==0u;
 }
 static bool open71_trace(uint32_t addr,CPUContext&ctx){
   if(!stm70_open)return false;
   if(addr==0x8051ad38u){
     check(open71_profile==0u&&ctx.lr==0x8051998cu&&ctx.gpr[1]<open71_stack,
           "native IOS_Open allocator tail entry differs");
     ++open71_profile;return true;
   }
   if(addr==0x8051ab34u){
     check(open71_profile<=1u&&open71_alloc==0u&&ctx.lr==0x8051998cu&&
           ctx.gpr[4]>=64u&&ctx.gpr[4]<=0x1000u,
           "native IOS_Open allocator entry ABI differs");
     ++open71_alloc;return true;
   }
   if(addr==INT_DISABLE&&ctx.lr==0x8051ab64u){
     check(open71_alloc==1u&&open71_alloc_disable==0u&&(ctx.msr&0x8000u),
           "native IOS allocator interrupt disable differs");
     ++open71_alloc_disable;return true;
   }
   if(addr==INT_RESTORE&&ctx.lr==0x8051ad14u){
     check(open71_alloc_disable==1u&&open71_alloc_restore==0u&&!(ctx.msr&0x8000u),
           "native IOS allocator interrupt restore differs");
     ++open71_alloc_restore;return true;
   }
   if(addr==0x805222c0u){
     check(open71_alloc==1u&&open71_alloc_disable==1u&&open71_alloc_restore==1u&&open71_flush==0u&&ctx.lr==0x80519a1cu,
           "native IOS_Open cache flush callsite differs");
     open71_flush_base=ctx.gpr[3];open71_flush_len=ctx.gpr[4];
     const uint32_t physical=open71_flush_base&0x3fffffffu,path=stm70_path&0x3fffffffu;
     check(open71_ram(open71_flush_base,open71_flush_len)&&open71_flush_len<=0x1000u&&
           physical<=path&&uint64_t(path)+open71_path_len<=uint64_t(physical)+open71_flush_len,
           "native IOS_Open flush does not cover the original pathname");
     open71_flush_before=ctx.guest_flush_count;++open71_flush;return true;
   }
   if(addr==0x80000c00u){
     check(open71_flush==1u&&open71_sc==0u&&ctx.lr==0x80519a1cu&&ctx.srr0==0x805222ecu&&
           ctx.pc==0x80000c00u&&!(ctx.msr&0x8000u),
           "native IOS_Open did not enter installed syscall vector");
     return true;
   }
   if(addr==0x805195ecu){
     check(open71_alloc==1u&&open71_alloc_restore==1u&&open71_flush==1u&&open71_sc==1u&&open71_submit==0u&&
           ctx.lr==0x80519a3cu&&ctx.gpr[1]<open71_stack&&ctx.msr==ipc69_msr,
           "native IOS_Open did not reach synchronous submission with preserved MSR");
     unsigned request_mask=0,command_mask=0,path_mask=0;
     for(unsigned r=3;r<=10;++r){
       if(open71_request_pointer(ctx,ctx.gpr[r]))request_mask|=1u<<(r-3u);
       if(ctx.gpr[r]==1u)command_mask|=1u<<(r-3u);
       if(ctx.gpr[r]&&(ctx.gpr[r]&0x3fffffffu)==(stm70_path&0x3fffffffu))path_mask|=1u<<(r-3u);
     }
     std::cout<<"V71_REQUEST_SHAPE request="<<request_mask<<" command="<<command_mask<<" path="<<path_mask<<std::endl;
     check(request_mask!=0u||(command_mask!=0u&&path_mask!=0u),"native IOS_Open submission argument format not recognized");
     ++open71_submit;submit72_active=true;return true;
   }
   return false;
 }
// Original-free predicate-only audit of direct SDA reads. Owner bytes and
 // runtime values remain private. Restrict to the synchronous submit body
 // and queue helper; no data writes, branch forcing or register mutation.
 static void submit72_audit(CPUContext&ctx,unsigned phase){
   for(const auto& span:std::array<std::pair<uint32_t,uint32_t>,2>{{
        {0x805195ecu,0x240u},{0x8051afe0u,0x80u}}}){
     for(uint32_t pc=span.first;pc<span.first+span.second;pc+=4u){
       const auto op=original_word(pc),major=op>>26,ra=(op>>16)&31u;
       if((ra!=2u&&ra!=13u)||(major!=32u&&major!=34u&&major!=40u&&major!=42u))continue;
       const uint32_t a=ctx.gpr[ra]+uint32_t(int32_t(int16_t(op)));
       const unsigned n=major==32u?4u:major==34u?1u:2u;
       if(!open71_ram(a,n))continue;
       bool initialized=false,orig_nonzero=false,live_nonzero=false,match=true;
       for(const auto& sec:stm70_owner->sections){
         if(sec.is_bss||sec.is_text||sec.address>a||uint64_t(a)+n>uint64_t(sec.address)+sec.data.size())continue;
         initialized=true;
         for(unsigned i=0;i<n;++i){
           const auto initial=sec.data[a-sec.address+i],live=ctx.mmu.read8(a+i);
           orig_nonzero|=initial!=0;live_nonzero|=live!=0;match&=initial==live;
         }
         break;
       }
       if(!initialized){for(unsigned i=0;i<n;++i)live_nonzero|=ctx.mmu.read8(a+i)!=0;match=false;}
       std::cout<<"V72_SDA phase="<<phase<<" site="<<std::hex<<pc<<" addr="<<a<<std::dec
                <<" width="<<n<<" init="<<initialized<<" initial_nz="<<orig_nonzero
                <<" live_nz="<<live_nonzero<<" equal="<<match<<std::endl;
     }
   }
 }
 static bool submit72_trace(uint32_t addr,CPUContext&ctx){
   if(!submit72_active)return false;
   if(addr==0x805293b0u){
     check(ctx.lr==0x80519630u,"IPC submission native queue initializer callsite differs");
     submit72_audit(ctx,0u);
     sleep73_queue=ctx.gpr[3];
     check(sleep73_init==0u&&(sleep73_queue&3u)==0u&&open71_ram(sleep73_queue,8u),
           "original request queue initializer pointer invalid");
     ++sleep73_init;return true;
   }
   if(addr==0x805222c0u){
     check(ctx.lr==0x8051963cu&&submit72_flush==0u,"IPC request flush callsite differs");
     submit72_base=ctx.gpr[3];submit72_len=ctx.gpr[4];
     check(open71_ram(submit72_base,submit72_len)&&submit72_len>=32u&&submit72_len<=0x1000u,
           "IPC request flush span invalid");
     submit72_flush_before=ctx.guest_flush_count;++submit72_flush;return true;
   }
   if(addr==0x80000c00u){
     check(submit72_flush==1u&&submit72_sc==0u&&ctx.lr==0x8051963cu&&ctx.srr0==0x805222ecu,
           "IPC request cache syscall vector not reached");
     return true;
   }
   if(addr==INT_DISABLE){
     if(sleep73_entry){
       check(ctx.lr==0x8052a44cu&&sleep73_disable==0u&&!(ctx.msr&0x8000u),
             "original OSSleepThread nested interrupt disable differs");
       ++sleep73_disable;return true;
     }
     check(ctx.lr==0x80519640u&&submit72_sc==1u&&submit72_disable==0u&&(ctx.msr&0x8000u),
           "IPC request interrupt-disable state differs");
     ++submit72_disable;return true;
   }
   if(addr==0x8051afe0u){
     check(ctx.lr==0x805196d4u&&submit72_disable==1u,"IPC queue helper callsite differs");
     return true;
   }
   if(addr==0x8051906cu||addr==0x8051905cu){
     check(submit72_disable==1u&&!(ctx.msr&0x8000u)&&
           (ctx.lr==0x80519780u||ctx.lr==0x805197b8u||ctx.lr==0x805197c8u),
           "IPC send register helper callsite differs");
     return true;
   }
   if(addr==0x8052a430u){
     using Bus=undercover::wii::IosBus;using Mail=undercover::wii::IpcMailbox;
     using Irq=undercover::wii::HollywoodIrq;using IOS=undercover::wii::StmIos;
     submit72_audit(ctx,1u);
     std::cout<<"V72_SEND_STATE lr="<<(ctx.lr==0x805197d8u)
               <<" msg="<<submit72_message<<" x1="<<submit72_x1<<" ee="<<bool(ctx.msr&0x8000u)
               <<" flush="<<submit72_flush<<" disable="<<submit72_disable
               <<" ack="<<submit72_ack<<std::endl;
     check(ctx.lr==0x805197d8u,"original IPC thread sleep callsite differs");
     check(submit72_message==1u,"original IPC thread sleep reached without PPCMSG");
     check(submit72_x1==1u,"original IPC thread sleep reached without X1");
     check(submit72_ack==0u,"original IPC ACK already serviced before boundary");
     check(!(ctx.msr&0x8000u),"original IPC thread sleep entered with interrupts enabled");
     const uint32_t request=submit72_phys;
     check(ipc70_ram.valid(request,64u)&&!(request&31u)&&
           ipc70_ram.read32(request)==IOS::Open,"actual mailbox message is not an aligned IOS_Open request");
     const uint32_t path=ipc70_ram.read32(request+12u),mode=ipc70_ram.read32(request+16u);
     check(path==(stm70_path&0x3fffffffu)&&mode==0u&&ipc70_ram.valid(path,open71_path_len),
           "original IOS request wire pathname or mode differs");
     const uint32_t flush=submit72_base&0x3fffffffu;
     check(flush<=request&&uint64_t(request)+32u<=uint64_t(flush)+submit72_len,
           "original submission failed to flush IPC wire header");
     std::string name;
     for(unsigned i=0;i<open71_path_len-1u;++i)name.push_back(char(ipc70_ram.read8(path+i)));
     const auto device=name=="/dev/stm/immediate"?IOS::Device::Immediate:IOS::Device::Event;
     check(name=="/dev/stm/immediate"||name=="/dev/stm/eventhook","actual wire pathname not a documented STM device");
     check(ipc70_bus.tick()==IOS::Pump::Ack&&ipc70_bus.services().queued_replies()==1u&&
           ipc70_bus.services().is_open(0u,device),"native IOS did not accept the actual original device open");
     const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u);
     check(!(ctrl&Mail::X1)&&(ctrl&Mail::Y2)&&
           (ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG).value_or(0u)&Irq::IPC_PPC)&&
           !ipc70_bus.external_exception_pending(ctx.msr)&&ipc70_ram.read32(request)==IOS::Open,
           "native IOS ACK flag, IRQ latch or request preservation differs");
     ++submit72_ack;
     check(sleep73_init==1u&&ctx.gpr[3]==sleep73_queue&&ctx.mmu.read32(sleep73_queue)==0u&&
           ctx.mmu.read32(sleep73_queue+4u)==0u&&ctx.mmu.read32(0x800000e4u)==THREAD&&
           ctx.mmu.read16(THREAD+712u)==2u,
           "original OSSleepThread did not receive initialized empty queue and running default thread");
     sleep73_sp=ctx.gpr[1];++sleep73_entry;return true;
   }
   if(addr==0x80529718u){
     using Bus=undercover::wii::IosBus;using Mail=undercover::wii::IpcMailbox;using IOS=undercover::wii::StmIos;
     check(sleep73_entry==1u&&sleep73_disable==1u&&sleep73_select==0u&&ctx.lr==OS_RET_OWNER&&
           ctx.gpr[1]<sleep73_sp&&!(ctx.msr&0x8000u),
           "original scheduler entry ABI or nested interrupt state differs");
     const auto st=ctx.mmu.read16(THREAD+712u);
     const bool head=ctx.mmu.read32(sleep73_queue)==THREAD,tail=ctx.mmu.read32(sleep73_queue+4u)==THREAD;
     const bool queue=ctx.mmu.read32(THREAD+732u)==sleep73_queue;
     const bool links=ctx.mmu.read32(THREAD+736u)==0u&&ctx.mmu.read32(THREAD+740u)==0u;
     std::cout<<"V73_WAIT_STATE waiting="<<(st==4u)<<" head="<<head<<" tail="<<tail
              <<" queue="<<queue<<" links="<<links<<" force0="<<(ctx.gpr[3]==0u)<<std::endl;
     check(st==4u&&head&&tail&&queue&&links&&ctx.mmu.read32(0x800000e4u)==THREAD,
           "original OSSleepThread failed to enroll default thread as WAITING");
     check(ctx.gpr[3]==0u,"original scheduler force argument differs");
     check(ipc70_bus.services().queued_replies()==1u&&ipc70_ram.read32(submit72_phys)==IOS::Open&&
           (ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL).value_or(0u)&Mail::Y2)&&
           ipc70_bus.external_irq_level()&&!ipc70_bus.external_exception_pending(ctx.msr),
           "native IOS ACK or unopened reply changed during original wait queue insertion");
     ++sleep73_select;return true;
   }
   check(false,"unexpected original IPC submission dependency");return true;
 }
void trace_call(uint32_t addr, CPUContext&ctx){
   if(submit72_trace(addr,ctx))return;
   if(addr==0x8052b034u){stm70_entry(ctx);return;}
   if(addr==0x80519944u){stm70_open_entry(ctx);return;}
   if(open71_trace(addr,ctx))return;
   if(ipc69_active||addr==0x805194c4u){ipc69_entry(addr,ctx);return;}
  constexpr std::array<uint32_t,5> data{INIT,FLUSH,COPY,FILL,SET};
  const auto it=std::find(data.begin(),data.end(),addr);
  if(it!=data.end()){
    ++data_calls[static_cast<size_t>(it-data.begin())];
    if(addr==COPY&&(ctx.lr==0x80522024u||ctx.lr==0x80522038u)){
      bool backup=ctx.lr==0x80522024u;
      check(ctx.gpr[1]==AUDIO_FRAME&&ctx.gpr[3]==(backup?DSP_BACKUP:DSP_STAGING)&&
            ctx.gpr[4]==(backup?DSP_STAGING:DSP_SRC)&&ctx.gpr[5]==DSP_SIZE,
            "original DSP staging memcpy ABI differs");
      for(unsigned i=0;i<DSP_SIZE;++i)
        check(ctx.mmu.read8(DSP_STAGING+i)==dsp_original_ram[i]&&
              (backup||ctx.mmu.read8(DSP_BACKUP+i)==dsp_original_ram[i]),
              "original DSP staging backup not made before overwriting RAM");
      ++dsp_copy_entries;
    }
    if(addr==COPY&&ctx.lr==0x805221a0u){
      check(dsp.complete()&&dsp_wait_finished&&ctx.gpr[1]==AUDIO_FRAME&&
            ctx.gpr[3]==DSP_STAGING&&ctx.gpr[4]==DSP_BACKUP&&ctx.gpr[5]==DSP_SIZE,
            "original audio restore copy ABI or DSP completion differs");
      for(unsigned i=0;i<DSP_SIZE;++i)
        check(ctx.mmu.read8(DSP_STAGING+i)==dsp_image[i]&&
              ctx.mmu.read8(DSP_BACKUP+i)==dsp_original_ram[i],
              "original staging or backup corrupted before audio restore");
      ++dsp_copy_entries;
    }
    if(addr==SET && ctx.lr==IRQ_STOP){
      check(ctx.gpr[3]==IRQ_TABLE && ctx.gpr[4]==0u && ctx.gpr[5]==128u,
            "original IRQ memset received incorrect destination/zero/count");
      ++irq_memset_entries;
    }
    if(addr==FILL && ctx.gpr[3]==IRQ_TABLE){
      check(ctx.lr==0x80004454u,
            "original IRQ __fill_mem reached via incorrect guest BL return");
      ++irq_fill_entries;
    }
  }
  else if(addr==CACHE){
    ++cache_calls;
    check(ctx.lr==0x800042fcu || ctx.lr==0x805208c4u,
          "original Wii cache initializer guest callsite LR incorrect");
    if(ctx.lr==0x805208c4u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u,
            "original OSInit second cache call guest stack frame incorrect");
      ++cache_os_entries;
    }
  }
  else if(addr==EXI){
    check(ctx.lr==0x805208c8u && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original Wii EXIInit caller LR or OSInit guest SP differs");
    ++exi_entries;
  }
  else if(addr==MASK){
    if(ctx.lr==0x80527718u){
      check(mi_active&&ctx.gpr[3]==0xf0000000u&&mi_writes==2u,
            "original MI mask arguments differ");
    }else if(ctx.lr==0x804efa18u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u && ctx.gpr[3]==0x007f8000u,
            "original EXIInit interrupt mask call changed");
    }else{
      check(ctx.lr==0x804ee900u && ctx.gpr[3]==0x00410000u,
            "EXI lock/unlock original nested interrupt mask changed");
    }
    ++mask_entries;
  }
  else if(addr==HANDLER){
    if(mi_active){
      check(mi_handlers<5u&&ctx.lr==0x80527728u+12u*mi_handlers&&
            ctx.gpr[3]==mi_handlers&&ctx.gpr[4]==MI_HANDLER&&
            ctx.mmu.read32(IRQ_TABLE+4u*mi_handlers)==0u,
            "original memory protection IRQ registration order differs");
      ++mi_handlers;return;
    }
    if(ctx.lr==0x80532100u){
      check(ctx.gpr[3]==20u&&ctx.gpr[4]==0x80531b34u&&
            ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u&&
            ctx.mmu.read32(IRQ_TABLE+80u)==0u&&si_phase==2u,
            "original SI IRQ registration ABI/order changed");
      ++si_handler_entries;
      return;
    }
    constexpr std::array<uint32_t,8> sites{{
      0x804efa40u,0x804efa50u,0x804efa60u,0x804efa6cu,
      0x804efa78u,0x804efa84u,0x804efa90u,0x804efa9cu}};
    constexpr std::array<uint32_t,8> handlers{{
      0x804ef61cu,0x804ef6d4u,0x804ef8ecu,0x804ef61cu,
      0x804ef6d4u,0x804ef8ecu,0x804ef61cu,0x804ef6d4u}};
    const size_t i=static_cast<size_t>(handler_entries%8u);
    check(ctx.lr==sites[i]+4u && ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u,
          "original Wii EXI setter return PC or stack frame differs");
    check(ctx.gpr[3]==9u+i && ctx.gpr[4]==handlers[i],
          "original Wii EXI handler registration vector/callee differs");
    check(ctx.mmu.read32(IRQ_GLOBAL)==IRQ_TABLE &&
          ctx.mmu.read32(IRQ_TABLE+4u*(9u+uint32_t(i)))==0u,
          "original EXI handler table entry must start zero");
    ++handler_entries;
  }
  else if(addr==ID){
    if(ctx.lr==0x804efafcu||ctx.lr==0x804efb34u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u&&ctx.gpr[4]==0u&&
            ctx.gpr[3]==(ctx.lr==0x804efafcu?0u:1u)&&
            ctx.gpr[5]==ctx.gpr[1]+8u&&id_device.complete(),
            "original EXI removable-device ID call ABI/order changed");
      check(ctx.mmu.read32(ID_CACHE)==response_id,
            "first uncached EXI ID was lost before card probes");
      ++id_entries;
      return;
    }
    check(ctx.lr==0x804efab0u && ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u,
          "original EXIGetID caller LR or guest SP changed");
    check(ctx.gpr[3]==0u && ctx.gpr[4]==2u && ctx.gpr[5]==ID_CACHE,
          "original EXIGetID arguments do not match channel-zero cached-ID request");
    check(ctx.mmu.read32(ID_CACHE)==0u,
          "original EXIGetID must begin uncached after authentic BSS clear");
    // The upper IRQ-table canary aliases the original EXI timestamp word.
    // Check it before the legitimate original EXIProbe clears that word.
    check(ctx.mmu.read32(0x8000303cu)==0xDEADBEEFu&&
          ctx.mmu.read8(IRQ_TABLE+128u)==0xC5u&&
          ctx.mmu.read32(MODULE_PRE)==0x6A6A6A6Au,
          "native IRQ/module initializer corrupted neighboring canaries before EXI probes");
    for(uint32_t n=0;n<64u;n+=4u)
      check(ctx.mmu.read32(0x806f1560u+n)==0u,"original EXI BSS state not zero at discovery entry");
    id_device.begin(last_csr);
    ++id_entries;
  }
  else if(addr==0x804ef09cu){
    check(ctx.lr==0x804efdecu&&ctx.gpr[3]<=1u&&
          ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u-64u,
          "original EXIProbe nested call ABI differs");
    check(id_device.complete()&&ctx.gpr[3]==probe_channel&&probe_reads==0u,
          "original removable device probes occurred out of order");
    ++probe_entries;
  }
  else if(addr==0x80521018u){
    if(ctx.lr==0x805320a0u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u&&ctx.gpr[3]==si_version_pointer,
            "original SI version registration ABI changed");
      ++si_version_entries;
      return;
    }
    check(ctx.lr==0x804efb60u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u&&
          ctx.gpr[3]==version_pointer&&probe_channel==2u&&probe_reads==0u,
          "original EXI version registration did not follow both no-card probes");
    check(ctx.mmu.read32(0x800030c0u)==0u&&ctx.mmu.read32(0x800030c4u)==0u,
          "original no-card probes did not clear low-memory time stamps");
    ++version_entries;
  }
  else if(addr==0x80532080u){
    check(ctx.lr==0x805208ccu&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&
          ctx.mmu.read32(R13-3148u)==0u&&probe_channel==2u,
          "original SIInit entry ABI or cold start flag differs");
    ++si_entries;
  }
  else if(addr==0x80532d6cu){
    check(ctx.lr==0x805320d4u&&ctx.gpr[3]==0u&&
          ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u,
          "original SI sampling-rate call ABI differs");
    for(uint32_t i=0;i<4u;++i)
      check(ctx.mmu.read32(0x806fe340u+32u*i)==0xffffffffu,
            "original SI packet slots not initialized to idle");
    check(ctx.mmu.read32(0x80619a64u)==0u,
          "original SI polling state was not cleared");
    ++si_rate_entries;
  }
  else if(addr==0x80536bf8u){
    check(ctx.lr==0x80532dacu&&ctx.mmu.read32(R13-3000u)==0u,
          "original SI video-format dispatch did not begin from zeroed globals");
    ++si_tv_entries;
  }
  else if(addr==0x8053238cu){
    check(ctx.lr==0x80532e20u&&ctx.gpr[3]==(si_expected>>16)&&
          ctx.gpr[4]==((si_expected>>8)&0xffu),
          "original SI sampling table did not calculate expected XY values");
    ++si_xy_entries;
  }
  else if(addr==0x805269bcu){
    if(mi_active){
      check(ctx.lr==0x80527778u&&ctx.gpr[3]==0x08000000u&&mi_maps==2u&&
            ctx.bat_write_count==expected_bat_writes.size(),"original MI unmask before BAT initialization");
      ++mi_unmask_entries;return;
    }
    check(ctx.lr==0x80532108u&&ctx.gpr[3]==0x800u&&si_phase==2u&&
          ctx.mmu.read32(IRQ_TABLE+80u)==0x80531b34u,
          "original SI interrupt unmask call differs");
    ++si_unmask_entries;
  }
  else if(addr==0x80532aa8u){
    const unsigned ch=si_channel;
    check(ch<4u&&ctx.lr==0x80532110u+8u*ch&&ctx.gpr[3]==ch&&
          ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u&&
          ctx.mmu.read32(TYPE_DATA+4u*ch)==8u&&ctx.mmu.read32(SLOT+32u*ch)==0xffffffffu,
          "original SI type discovery entry ABI/order or cold initialized data differs");
    if(ch==0u)check(ctx.ctr==ctx.mmu.read32(0x8061a890u)&&si_phase==3u,
                    "SI type discovery preceded sampling/IRQ setup");
    else check(ctx.mmu.read32(SI_DATA)==0u&&si_phase==6u,
               "first original SI type transfer not active before subsequent discovery");
    ++si_type_entries;
  }
  else if(addr==0x8053268cu){
    const unsigned ch=si_channel;
    check(ch<4u&&ctx.lr==0x80532c38u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u-32u&&
          ctx.gpr[3]==ch&&ctx.gpr[4]==SI_COMMAND&&ctx.gpr[5]==1u&&
          ctx.gpr[6]==TYPE_DATA+4u*ch&&ctx.gpr[7]==3u&&
          ctx.gpr[8]==TYPE_CALLBACK&&ctx.gpr[9]==0u&&ctx.gpr[10]==TYPE_DELAY,
          "original SI type transfer command/response ABI differs");
    check(ctx.mmu.read32(SI_COMMAND)==0u&&ctx.mmu.read32(TYPE_DATA+4u*ch)==128u&&
          ctx.mmu.read32(SLOT+32u*ch)==0xffffffffu&&
          ctx.mmu.read64(SLOT+128u+8u*ch)==0u,
          "original SI type request did not use zero command, busy type or cold last-transfer time");
    si_type_times[ch]=ctx.mmu.read64(TYPE_TIME+8u*ch);
    check(si_type_times[ch]>TYPE_DELAY&&
          (ch==0u||si_type_times[ch]>si_type_times[ch-1]),
          "original SI type request did not store increasing native timebase timestamps");
    ++si_transfer_entries;
  }
  else if(addr==0x80532140u){
    const unsigned ch=si_channel;
    check(ch<4u&&ctx.lr==0x8053279cu&&ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u-32u-64u&&
          ctx.gpr[3]==ch&&ctx.gpr[4]==SI_COMMAND&&ctx.gpr[5]==1u&&
          ctx.gpr[6]==TYPE_DATA+4u*ch&&ctx.gpr[7]==3u&&ctx.gpr[8]==TYPE_CALLBACK&&
          ctx.mmu.read32(SI_DATA)==(ch?0u:0xffffffffu),
          "original immediate SI transfer ABI or active channel differs");
    ++si_start_entries;++si_channel;
  }
  else if(addr==0x805203c4u){
    check(mi_active&&ctx.lr==0x805208f8u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&
          ctx.mmu.read32(MI_FLAG)==1u&&mi_maps==2u,"original boot-report must follow memory protection return");
    check(ctx.srr0==0x80527600u&&(ctx.srr1&0x30u)==0x30u,
          "original MI second rfi did not return before reporting");
    ++report_entries;
  }
  else if(addr==0x8051ffc8u||addr==0x805201a4u){
    const unsigned phase=addr==0x8051ffc8u?1u:2u;
    check(report_entries==1u&&report_calls==10u&&report_getters==6u&&
          phase==arena_phase+1u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&
          ctx.lr==(phase==1u?0x80520940u:0x80520944u)&&ctx.mmu.read32(0x806f4f0cu)==0u,
          "original cold arena clear entry ABI or reset parameters differ");
    if(phase==1u){
      check(ctx.ctr==report_ctr,"original boot report CTR changed before arena entry");
      for(unsigned i=0;i<DSP_SIZE;++i)
        check(ctx.mmu.read8(DSP_BACKUP+i)==dsp_original_ram[i]&&
              ctx.mmu.read8(DSP_STAGING+i)==dsp_original_ram[i],
              "original DSP staging RAM not restored before arena clear");
    }else verify_arena_bytes(ctx,1u);
    arena_active=true;arena_phase=phase;
  }
  else if(addr==0x805285d0u){
    check(arena_active&&arena_reset_calls+1u==arena_phase&&ctx.gpr[1]==AUDIO_FRAME&&
          ctx.lr==(arena_phase==1u?0x8051ffe0u:0x805201bcu),
          "original arena reset-code query callsite differs");
    ++arena_reset_calls;
  }
  else if(addr==0x8052234cu){
    check(arena_active&&arena_phase==arena_zero_calls+1u&&ctx.lr==arena_clear_lr(arena_phase)&&
          ctx.gpr[1]==AUDIO_FRAME&&ctx.gpr[3]==arena_low(arena_phase)&&
          ctx.gpr[4]==arena_high(arena_phase)-arena_low(arena_phase)&&
          ctx.guest_dcbz_trace.count==expected_zero_lines(arena_phase-1u)&&arena_reset_reads==arena_phase,
          "original DCZeroRange cold-path ABI or preceding progress differs");
    ++arena_zero_calls;
  }
  else if(addr==0x80521d40u){
    check(arena_active&&arena_phase==1u&&ctx.gpr[1]==AUDIO_FRAME&&
          ((arena_getters==1u&&ctx.lr==0x8051fff4u)||(arena_getters==2u&&ctx.lr==0x8051fffcu)),
          "original MEM1 arena low getter order differs");
    ++arena_getters;
  }
  else if(addr==0x8051fd44u){
    check(report_entries==1u&&report_calls==3u&&ctx.lr==0x80520410u&&
          ctx.mmu.read32(BOOT_BASE)==0x80000000u,"original console classification call ABI differs");
    ++console_entries;
  }
  else if(addr==0x8052701cu){
    check(report_trial%4u!=0u&&ctx.lr==0x8051fec8u&&console_entries==1u,
          "original console classification read MEM2 size outside selected path");
  }
  else if(addr==0x80527034u||addr==0x80527028u||addr==0x80521d18u||addr==0x80521d30u||
          addr==0x80521d20u||addr==0x80521d38u){
    if(arena_active){
      check(arena_phase==2u&&ctx.gpr[1]==AUDIO_FRAME&&
        ((arena_getters==3u&&addr==0x80521d20u&&ctx.lr==0x805201c8u)||
         (arena_getters==4u&&addr==0x80521d38u&&ctx.lr==0x805201d0u)||
         (arena_getters==5u&&addr==0x80521d38u&&ctx.lr==0x805201d8u)),
        "original MEM2 arena getter call order differs");
      ++arena_getters;return;
    }
    constexpr std::array<uint32_t,6> pcs{{0x80527034u,0x80527028u,0x80521d18u,0x80521d30u,0x80521d20u,0x80521d38u}};
    constexpr std::array<uint32_t,6> lrs{{0x805205fcu,0x80520604u,0x8052061cu,0x80520624u,0x8052063cu,0x80520644u}};
    check(report_entries==1u&&report_getters<pcs.size()&&addr==pcs[report_getters]&&ctx.lr==lrs[report_getters],
          "original report size/arena getter call order differs");
    ++report_getters;
  }
  else if(addr==0x804b79dcu){
    if(ctx.lr==0x80520fc4u||ctx.lr==0x80522464u)return; // earlier authentic paired-single/cache reads
    check(ctx.lr==0x805208dcu&&dsp.complete()&&ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original post-audio HID2 read ABI differs");
    mi_hid_before=ctx.hid2;++mi_hid_reads;
  }
  else if(addr==0x804b79e4u){
    if(ctx.lr==0x80520fccu||ctx.lr==0x80522524u)return; // earlier authentic paired-single/cache writes
    check(ctx.lr==0x805208e4u&&ctx.gpr[3]==(mi_hid_before&~0x40000000u),
          "original OSInit HID2 mask differs");
    ++mi_hid_writes;
  }
  else if(addr==0x805276d4u){
    check(ctx.lr==0x805208f4u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&dsp.complete()&&
          ctx.mmu.read32(MI_FLAG)==0u&&ctx.hid2==(mi_hid_before&~0x40000000u),
          "original memory protection init cold entry differs");
    mi_active=true;++mi_entries;
  }
  else if(addr==0x80527568u){
    check(mi_active&&mi_handlers==5u&&ctx.lr==0x80527770u&&ctx.gpr[3]==0x000ba2cfu&&
          ctx.mmu.read32(0x80003100u)==MEM1_BYTES&&ctx.mmu.read32(0x80003104u)==MEM1_BYTES&&
          ctx.mmu.read32(0x8000311cu)==MEM2_BYTES&&ctx.mmu.read32(0x80003120u)==MEM2_MAP_HI&&
          ctx.mmu.read32(SHUTDOWN_TAIL)==MI_NODE,"original memory mapper input or shutdown registration differs");
    ++mi_map_entries;
  }
  else if(addr==0x80527550u){
    check(mi_active&&mi_trampolines<2u&&
          ctx.lr==(mi_trampolines?0x80527600u:0x805275d0u)&&
          ctx.gpr[3]==(mi_trampolines?0x80527144u:0x805270c4u),
          "original memory map physical trampoline ABI differs");
    ++mi_trampolines;
  }
  else if(addr==0x805270c4u||addr==0x80527144u){
    check(mi_active&&mi_maps<2u&&mi_trampolines==mi_maps+1u&&
          addr==(mi_maps?0x80527144u:0x805270c4u)&&
          ctx.srr0==(addr&0x3fffffffu)&&!(ctx.msr&0x30u)&&
          ctx.lr==(mi_maps?0x80527600u:0x805275d0u)&&
          ctx.bat_write_count==(mi_maps?12u:0u),
          "original rfi physical mapping entry state differs");
    ++mi_maps;
  }
  else if(addr==0x80521d28u){
    if(arena_active){
      check(arena_phase==1u&&arena_getters==0u&&ctx.lr==0x8051ffecu&&ctx.gpr[1]==AUDIO_FRAME,
            "original MEM1 arena high getter call order differs");
      ++arena_getters;return;
    }
    if(ctx.lr==0x8052218cu){
      check(ctx.gpr[1]==AUDIO_FRAME&&dsp.complete()&&dsp_wait_finished&&
            ctx.mmu.read32(HI_GLOBAL)==0x81700000u,
            "original second arena lookup must follow completed DSP reset");
      ++dsp_arena_entries;return;
    }
    check(ctx.lr==0x80522014u&&ctx.gpr[1]==AUDIO_FRAME&&audio_active&&
          audio_read_count==6u&&audio_write_count==6u&&ctx.mmu.read32(HI_GLOBAL)==0x81700000u,
          "original DSP backup arena lookup ABI differs");
    finish_wait();check(wait_index==5u,"original audio reset delays not finished before DSP staging");
    audio_active=false;++dsp_arena_entries;
  }
  else if(addr==0x805222c0u){
    if(arena_active){
      check(arena_phase==arena_flush_calls+1u&&ctx.lr==arena_flush_lr(arena_phase)&&
            ctx.gpr[1]==AUDIO_FRAME&&ctx.gpr[3]==arena_high(arena_phase)-ARENA_FLUSH_BYTES&&
            ctx.gpr[4]==ARENA_FLUSH_BYTES&&ctx.guest_flush_count==87u+(arena_phase-1u)*FLUSH_LINES&&
            ctx.guest_dcbz_trace.count==expected_zero_lines(arena_phase),
            "original arena DCFlushRange ABI or dcbz count differs");
      verify_arena_bytes(ctx,arena_phase);++arena_flush_calls;return;
    }
    check(ctx.lr==0x80522044u&&ctx.gpr[1]==AUDIO_FRAME&&ctx.gpr[3]==DSP_STAGING&&
          ctx.gpr[4]==DSP_SIZE&&ctx.guest_flush_count==83u,
          "original DSP cache flush ABI or prior cache count differs");
    for(unsigned i=0;i<DSP_SIZE;++i)
      check(ctx.mmu.read8(DSP_STAGING+i)==dsp_image[i]&&ctx.mmu.read8(DSP_BACKUP+i)==dsp_original_ram[i],
            "original DSP data or backup differs before cache flush");
    ++dsp_flush_entries;
  }
  else if(addr==0x80000c00u){
    check(ctx.srr0==0x805222ecu&&ctx.pc==0x80000c00u&&
          ctx.lr==(arena_active?arena_flush_lr(arena_phase):0x80522044u)&&
          ctx.guest_flush_count==87u+(arena_active?arena_phase*FLUSH_LINES:0u)&&
          ctx.gpr[1]==AUDIO_FRAME&&!(ctx.msr&0x8000u),
          "native installed SC vector entry ABI differs");
    ++sc_vector_entries;
  }
  else if(addr==0x80521fecu){
    check(ctx.lr==0x805208d8u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&
          ctx.mmu.read32(0x800000e4u)==THREAD,"original audio init did not follow thread init");
    check(ctx.mmu.read32(STACK_BOTTOM)==STACK_MAGIC&&
          ctx.mmu.read32(THREAD_FRAME)==ORIGINAL_SP-8u-80u,
          "thread stack sentinel or frame backchain changed before audio");
    for(uint32_t a=STACK_BOTTOM+4u;a<THREAD_FRAME;a+=4u)
      check(ctx.mmu.read32(a)==0u,"original thread did not scrub entire unused stack before audio");
    audio_active=true;++audio_entries;
  }
  else if(addr==0x80521dccu){
    check(audio_active&&ctx.lr==0x80522010u&&ctx.gpr[1]==AUDIO_FRAME&&ctx.gpr[3]==1u,
          "original audio reset mode or caller ABI differs");
    ++reset_entries;
  }
  else if(addr==0x8052a83cu){
    if(dsp.active()){
      check(ctx.gpr[1]==AUDIO_FRAME&&dsp.acks==1u&&dsp.transfers==1u&&
            dsp.phase==DspBootDevice::Phase::dma_source,
            "original DSP delay must occur between acknowledged DMA operations");
      const uint32_t now=uint32_t(ctx.read_timebase());
      if(ctx.lr==0x805220ccu){
        check(!dsp_wait_started,"original DSP delay started twice");
        dsp_wait_started=true;dsp_wait_start=now;
      }else{
        check(ctx.lr==0x805220d4u&&dsp_wait_started,"original DSP delay poll caller differs");
        dsp_wait_previous=dsp_wait_delta;dsp_wait_delta=now-dsp_wait_start;
        check(dsp_wait_delta>dsp_wait_previous&&++dsp_wait_polls<1000u,
              "original DSP delay did not progress");
      }
      return;
    }
    check(audio_active&&wait_index<5u&&ctx.gpr[1]==RESET_FRAME,
          "original Hollywood delay timebase helper outside reset");
    const uint32_t now=uint32_t(ctx.read_timebase());
    if(ctx.lr==wait_starts[wait_index]){
      check(!wait_started&&audio_write_count==wait_index+2u,
            "original Hollywood delay started before expected reset writes");
      wait_started=true;wait_start_tick=now;last_wait_delta=previous_wait_delta=0u;
    }else{
      check(ctx.lr==wait_polls[wait_index]&&wait_started,
            "original Hollywood reset timebase poll callsite differs");
      previous_wait_delta=last_wait_delta;last_wait_delta=now-wait_start_tick;
      check(last_wait_delta>previous_wait_delta&&++wait_counts[wait_index]<8000u,
            "original Hollywood delay failed to make bounded progress");
    }
  }
  else if(addr==0x8052912cu){
    check(ctx.lr==0x805208d4u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&sram_device.complete()&&
          ctx.mmu.read32(SRAM+72u)==0u,"original thread init must follow SRAM return");
    const uint32_t trial=response_id-0xBEEF0010u;
    check(ctx.mmu.read32(CONTEXT_WORD)==0u&&ctx.mmu.read32(CONTEXT_WORD-4u)==0xacce5500u+trial&&
          ctx.mmu.read32(CONTEXT_WORD+4u)==0xd15c0a00u+trial&&
          ctx.mmu.read32(LOW_MASK_PRE)==0x1952A052u,
          "prior context and IRQ initialization clobbered low-memory canaries before thread init");
    check(ctx.mmu.read8(STACK_BOTTOM)==0xC5u,
          "prior BSS clear overran into initial thread stack");
    for(unsigned i=0;i<1048u+424u;++i)
      check(ctx.mmu.read8(THREAD+i)==0u,"thread or idle context not zero at original init entry");
    ++thread_entries;
  }
  else if(addr==0x80522af4u){
    const bool initial=ctx.lr==0x805291a0u;
    check((initial||ctx.lr==0x80529390u)&&ctx.gpr[1]==THREAD_FRAME&&
          ctx.gpr[3]==(initial?THREAD:IDLE_CONTEXT),
          "original thread context clear argument/LR differs");
    if(initial)check(ctx.mmu.read32(CONTEXT_WORD)==THREAD&&
      ctx.mmu.read16(THREAD+712u)==2u&&ctx.mmu.read16(THREAD+714u)==1u,
      "original running thread state was not initialized before context clear");
    ++thread_clear_entries;
  }
  else if(addr==0x805228ccu){
    check(ctx.lr==0x805291a8u&&ctx.gpr[3]==THREAD&&ctx.gpr[1]==THREAD_FRAME&&
          ctx.mmu.read32(CONTEXT_WORD)==0u,
          "original OSSetCurrentContext not called after initial context clear");
    ++thread_context_entries;
  }
  else if(addr==0x80529128u){
    check(ctx.lr==0x805291e0u&&ctx.ctr==0x80529128u&&ctx.gpr[12]==0x80529128u&&
          ctx.gpr[1]==THREAD_FRAME&&ctx.gpr[3]==0u&&ctx.gpr[4]==THREAD&&
          ctx.mmu.read32(THREAD_CALLBACK_PTR)==0x80529128u&&
          ctx.mmu.read32(0x800000d4u)==THREAD&&ctx.mmu.read32(LOW_MASK_PRE)==(THREAD&0x3fffffffu)&&
          (ctx.msr&0x2002u)==2u,
          "original thread switch callback or active CPU context ABI differs");
    check(ctx.mmu.read32(THREAD+772u)==ORIGINAL_SP&&ctx.mmu.read32(THREAD+776u)==STACK_BOTTOM&&
          ctx.mmu.read32(STACK_BOTTOM)==STACK_MAGIC,
          "original initial thread stack bounds/magic not installed");
    ++thread_callback_entries;
  }
  else if(addr==0x80522a8cu){
    check(ctx.lr==0x805291e8u&&ctx.gpr[1]==THREAD_FRAME&&ctx.mmu.read32(0x800000e4u)==THREAD,
          "original thread current stack pointer query ABI differs");
    ++thread_sp_entries;
  }
  else if(addr==0x80528754u){
    check(ctx.lr==0x805208d0u&&ctx.gpr[1]==ORIGINAL_SP-8u-80u&&si_phase==6u&&si_channel==4u,
          "original SRAMInit did not follow completed SIInit");
    check(ctx.mmu.read32(0x806f156cu)==0u&&ctx.mmu.read32(0x806f1570u)==4u&&
          ctx.mmu.read32(0x806f1574u)==ID_CACHE&&ctx.mmu.read32(0x806f1578u)==2u,
          "original uncached EXI state was not preserved until SRAM initialization");
    for(unsigned i=0;i<80u;++i)check(ctx.mmu.read8(SRAM+i)==0u,"SRAM control block not zero after authentic BSS clear");
    sram_ctx=&ctx;sram_device.begin();++sram_entries;
  }
  else if(addr==0x80522294u){
    check(ctx.lr==0x80528788u&&ctx.gpr[3]==SRAM&&ctx.gpr[4]==64u&&
          ctx.guest_data_invalidate_count==0u,"original SRAM DMA cache invalidation ABI differs");
    ++sram_invalidate_entries;
  }
  else if(addr==0x804eeca4u){
    check(ctx.lr==0x80528828u&&ctx.gpr[3]==0u&&ctx.gpr[4]==SRAM&&ctx.gpr[5]==64u&&
          ctx.gpr[6]==0u&&ctx.gpr[7]==0u&&ctx.mmu.read32(0x806f156cu)==0x14u&&
          sram_device.phase==ExiSramTestDevice::command_synced,
          "original SRAM EXIDma arguments or phase differ");
    check(ctx.guest_data_invalidate_count==2u&&ctx.guest_data_invalidate_lines[0]==SRAM&&
          ctx.guest_data_invalidate_lines[1]==SRAM+32u,
          "original SRAM DMA destination cache lines not invalidated before transfer");
    ++sram_dma_entries;
  }
  else if(addr==0x804efc7cu){
    check(ctx.lr==0x80528864u&&ctx.gpr[3]==0u&&sram_device.complete()&&
          ctx.mmu.read32(0x806f156cu)==0x10u,"original SRAM EXI unlock order differs");
    ++sram_unlock_entries;
  }
  else if(addr==0x80528954u){
    check((ctx.lr==0x805288bcu||ctx.lr==0x80528928u)&&ctx.gpr[3]==0u&&ctx.gpr[4]==20u&&
          ctx.mmu.read32(SRAM+72u)==1u&&ctx.mmu.read32(SRAM+76u)==1u,
          "original SRAM configuration read lock/unchanged unlock differs");
    ++sram_config_unlock_entries;
  }
  else if(addr==0x804efb80u){
    if(ctx.lr==0x80528798u){
      check(ctx.gpr[3]==0u&&ctx.gpr[4]==1u&&ctx.gpr[5]==0u&&sram_device.phase==ExiSramTestDevice::ready,
            "original SRAM EXI lock ABI differs");
      ++lock_entries;return;
    }
    check(ctx.lr==0x804eff04u&&ctx.gpr[3]==0u&&ctx.gpr[4]==2u&&ctx.gpr[5]==0u,
          "original EXIGetID lock arguments differ");
    ++lock_entries;
  }
  else if(addr==0x804ef3ecu){
    if(ctx.lr==0x805287b8u){
      check(ctx.gpr[3]==0u&&ctx.gpr[4]==1u&&ctx.gpr[5]==3u&&
            ctx.mmu.read32(0x806f156cu)==0x10u,"original SRAM EXI select ABI differs");
      ++select_entries;return;
    }
    check(ctx.lr==0x804eff20u&&ctx.gpr[3]==0u&&ctx.gpr[4]==2u&&ctx.gpr[5]==0u&&
          ctx.mmu.read32(0x806f156cu)==0x10u,
          "original EXI select did not follow successful lock");
    ++select_entries;
  }
  else if(addr==0x804ee984u){
    if(ctx.lr==0x805287f4u){
      check(ctx.gpr[3]==0u&&ctx.gpr[5]==4u&&ctx.gpr[6]==1u&&ctx.gpr[7]==0u&&
            ctx.mmu.read32(ctx.gpr[4])==0x20000100u&&ctx.mmu.read32(0x806f156cu)==0x14u,
            "original SRAM immediate command ABI differs");
      sram_command_ptr=ctx.gpr[4];++imm_entries;return;
    }
    const bool write=ctx.lr==0x804eff4cu;
    check((write||ctx.lr==0x804eff84u)&&ctx.gpr[3]==0u&&ctx.gpr[7]==0u&&
          ctx.gpr[5]==(write?2u:4u)&&ctx.gpr[6]==(write?1u:0u)&&
          ctx.mmu.read32(0x806f156cu)==0x14u,
          "original EXI immediate request or selected state changed");
    if(write)check(ctx.mmu.read32(ctx.gpr[4])==0u,"original EXI ID command must be zero");
    else check(ctx.gpr[4]==ID_CACHE,"original EXI ID destination differs");
    ++imm_entries;
  }
  else if(addr==0x804eed9cu){
    if(ctx.lr==0x80528804u||ctx.lr==0x8052883cu){
      const bool dma=ctx.lr==0x8052883cu;
      check(ctx.gpr[3]==0u&&ctx.mmu.read32(0x806f156cu)==(dma?0x15u:0x16u),
            "original SRAM sync transfer flags differ");
      ++sync_entries;return;
    }
    check((ctx.lr==0x804eff60u||ctx.lr==0x804eff98u)&&ctx.gpr[3]==0u&&
          ctx.mmu.read32(0x806f156cu)==0x16u,
          "original EXI sync did not see pending selected transaction");
    ++sync_entries;
  }
  else if(addr==0x804ef51cu){
    if(ctx.lr==0x80528850u){
      check(ctx.gpr[3]==0u&&ctx.mmu.read32(0x806f156cu)==0x14u&&
            sram_device.phase==ExiSramTestDevice::synced,"original SRAM deselect before DMA synchronization");
      ++deselect_entries;return;
    }
    check(ctx.lr==0x804effacu&&ctx.gpr[3]==0u&&ctx.mmu.read32(ID_CACHE)==response_id&&
          ctx.mmu.read32(0x806f156cu)==0x14u,
          "EXI deselect occurred before original ID response copy");
    ++deselect_entries;
  }
  else if(addr==0x804ee894u){
    check((ctx.lr==0x804efc58u||ctx.lr==0x804effecu||ctx.lr==0x804efce4u)&&ctx.gpr[3]==0u&&
          ctx.gpr[4]==0x806f1560u,
          "original EXI lock/unlock interrupt mask arguments differ");
    ++irqmask_entries;
  }
  else if(addr==0x80521008u){
    check(ctx.lr==0x804eef5cu,"original EXI sync hardware revision callsite differs");
    ++revision_entries;
  }
  else if(addr==L2_READ)++l2_reads;
  else if(addr==L2_WRITE)++l2_writes;
  else if(addr==ICE)++ic_calls;
  else if(addr==DCE)++dc_calls;
  else if(addr==OSINIT){++os_entries;}
  else if(addr==SAVE20){++save_entries;}
  else if(addr==TIME){++time_entries;}
  else if(addr==GETTIME){++gettime_entries;}
  else if(addr==0x805265c0u){
     check(ctx.mmu.read32(0x80000048u)==0x004e5090u && ctx.lr==0x80520948u && ctx.gpr[1]==ORIGINAL_SP-8u-80u &&
           !(ctx.msr&0x8000u) && arena_sc_calls==2u && enable_entries==0u,
           "original interrupt enable entry ABI/order differs");
     enable_before=ctx.msr;++enable_entries;
   }
   else if(addr==INT_DISABLE){
    ++disable_entries;
    // This entry is the *second* disable call, from original OSInit at B4.
    // The authentic system-time return registers must have been stored by
    // original PPC at AC and B0 before the helper receives control.
    if(ctx.lr==0x8052695cu){
      check(ctx.gpr[1]<ORIGINAL_SP-8u-80u-32u,
            "nested mask interrupt disable stack frame missing");
      ++mask_disable_entries;
    }
    if(ctx.lr==0x80526678u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u,
            "original IRQ interrupt-disable nested guest SP changed");
      ++irq_disable_entries;
    }
    if(ctx.lr==0x805206b8u){
      check(ctx.mmu.read32(0x8070db30u)==ctx.gpr[3],
            "original system time high word differs before second interrupt disable");
      check(ctx.mmu.read32(0x8070db34u)==ctx.gpr[4],
            "original system time low word differs before second interrupt disable");
      ++time_global_checks;
    }
  }
  else if(addr==INT_RESTORE){
    if(ctx.lr==0x8052699cu){
      check(ctx.gpr[1]<ORIGINAL_SP-8u-80u-32u,
            "nested mask interrupt restore stack frame missing");
      ++mask_restore_entries;
    }
    if(ctx.lr==0x805266b4u){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u,
            "original IRQ OSRestoreInterrupts received incorrect nested guest SP");
      ++irq_restore_entries;
    }
    ++restore_entries;
  }
  else if(addr==EXEC){
    check(ctx.lr==0x805206c0u, "original execparams called with wrong return LR");
    ++exec_entries;
  }
  else if(addr>=PERF && addr<PERF+48 && (addr-PERF)%8==0){
    const unsigned i=(addr-PERF)/8;
    check(ctx.lr==0x805206c8u+8u*i,
          "original perf helper guest BL return address changed");
    check(ctx.gpr[3]==0u,
          "original MMCR/PMC helper argument is not zero");
    ++perf_entries[i];
  }
  else if(addr==HID4){
    check(ctx.lr==0x805206f8u && ctx.gpr[3]==0x83900000u,
          "original HID4 call did not receive authentic OSInit argument");
    ++hardware_entries[0];
  }
  else if(addr==SPEC){
    check(ctx.lr==0x805206fcu,
          "original speculation call has incorrect guest return LR");
    ++hardware_entries[1];
  }
  else if(addr==NONIEEE){
    check(ctx.lr==0x80520700u,
          "original non-IEEE FP helper has incorrect guest return LR");
    ++hardware_entries[2];
  }
  else if(addr==MFHID0 && ctx.lr==0x804b7a10u){
    ++hardware_entries[3];
  }
  else if(addr==MTHID0 && ctx.lr==0x804b7a18u){
    ++hardware_entries[4];
  }
  else if(addr==ARENA_LO){
    check(ctx.lr==0x805207ecu,"original OSSetMEM1ArenaLo return LR incorrect");
    ++arena_entries[0];
  }
  else if(addr==ARENA_HI){
    check(ctx.lr==0x80520818u,"original OSSetMEM1ArenaHi return LR incorrect");
    ++arena_entries[1];
  }
  else if(addr==MEM2_LO){
    check(ctx.lr==0x80520890u,
          "original OSSetMEM2ArenaLo return LR incorrect");
    ++mem2_entries[0];
  }
  else if(addr==MEM2_HI){
    check(ctx.lr==0x805208a4u,
          "original OSSetMEM2ArenaHi return LR incorrect");
    ++mem2_entries[1];
  }
  else if(addr==IPC){
    check(ctx.lr==0x805208a8u,"genuine original IPC-buffer return LR changed");
    ++ipc_entries;
  }
  else if(addr==EXCEPTION){
    check(ctx.lr==0x805208acu,
          "original OSExceptionInit call did not preserve guest return LR");
    ++exception_entries;
  }
  else if(addr==MARK){
    check(ctx.lr==0x80520cf4u,
          "authentic original exception-mark BL guest return LR changed");
    // Each original exception-vector iteration probes its own index.
    // The zero-mask fast path reaches this helper once per vector.
    check(ctx.gpr[3]==uint32_t(marker_entries%15u),
          "original Wii exception mark helper vector index is out of sequence");
    ++marker_entries;
  }
  else if(addr==SYSCALL){
    check(ctx.lr==0x805208b0u,
          "original OSInit __OSInitSystemCall native call LR incorrect");
    check(ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original syscall installer entered with wrong OSInit frame");
    ++syscall_entries;
  }
  else if(addr==ALARM){
    check(ctx.lr==0x805208b4u && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original OSInit->__OSInitAlarm guest LR or stack frame differs");
    ++alarm_entries;
  }
  else if(addr==GETEXC){
    check(ctx.lr==ALARM+0x14u,
          "original __OSGetExceptionHandler callsite LR incorrect");
    ++alarm_get_entries;
  }
  else if(addr==SETEXC){
    if(ctx.lr==ALARM+0x3cu){
      ++alarm_set_entries;
    }else if(ctx.lr==0x805266c4u){
      check(ctx.gpr[3]==4u && ctx.gpr[4]==0x80526ce0u,
            "original IRQ vector 4 exception-handler registration changed");
      ++irq_setexc_entries;
    }else if(ctx.lr==CONTEXT+0x1cu){
      check(ctx.gpr[3]==7u && ctx.gpr[4]==CONTEXT_HANDLER,
            "original Wii context exception-vector 7 arguments differ");
      ++context_setexc_entries;
    }else{
      check(false,"unexpected IRQ/ALARM original exception handler setter LR");
    }
  }
  else if(addr==SHUTDOWN){
    if(mi_active){
      check(ctx.lr==0x80527764u&&ctx.gpr[3]==MI_NODE&&mi_handlers==5u&&
            ctx.mmu.read32(MI_NODE)==0x80527040u&&ctx.mmu.read32(MI_NODE+4u)==127u,
            "original MI shutdown registration ABI differs");
      ++mi_shutdown_entries;return;
    }
    check(ctx.lr==ALARM+0x48u,
          "original shutdown registration callsite LR incorrect");
    ++shutdown_entries;
  }
  else if(addr==MODULE){
    check(ctx.lr==0x805208b8u && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original __OSModuleInit native entry LR/OSInit frame incorrect");
    ++module_entries;
  }
  else if(addr==INTERRUPT){
    check(ctx.lr==0x805208bcu && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "native original __OSInterruptInit entry LR/OSInit SP incorrect");
    ++irq_entries;
  }
  else if(addr==SETMASK){
    if(ctx.lr==0x80526a0cu){
      check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-16u-32u&&
            ctx.gpr[3]==(mi_active?0x08000000u:0x800u)&&ctx.gpr[4]==(mi_active?0xf7fff7f0u:0xfffff7f0u),
            "original SI unmask nested PI bank arguments differ");
    }else check(ctx.lr==SETMASK_RETURN && ctx.gpr[1]==ORIGINAL_SP-8u-80u-32u,
          "original SetInterruptMask native BL return or IRQ stack incorrect");
    ++setmask_entries;
  }
  else if(addr==CONTEXT){
    check(ctx.lr==0x805208c0u &&
          ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original Wii __OSContextInit call LR or OSInit guest frame differs");
    ++context_entries;
  }
  else if(addr==DCFLUSH){
    check(ctx.lr==(dcflush_entries%16u==15u?0x80529104u:0x80520da8u),
          "original exception/syscall DCFlushRangeNoSync BL return LR changed");
    // One cumulative cache-ordering baseline, taken at the first handler.
    if(ctx.guest_flush_count==0u){
      cache_sync_entry=ctx.guest_sync_count;
      cache_isync_entry=ctx.guest_isync_count;
    }
    ++dcflush_entries;
  }
  else if(addr==ICINVALID){
    check(ctx.lr==(icinvalid_entries%16u==15u?0x80529114u:0x80520db8u),
          "original exception/syscall ICInvalidateRange BL return LR changed");
    ++icinvalid_entries;
  }
  else if(addr==0x80545134u){
    check(ctx.lr==0x80520e64u,
          "original Wii _restgpr_20 did not receive epilogue BL return LR");
    check(ctx.gpr[29]==15u && ctx.gpr[28]==EXC_SOURCE_WORD,
          "original Wii completed exception loop not observed at restore entry");
    check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-64u,
          "original Wii exception stack pointer incorrect before _restgpr_20");
    ++exception_restore_entries;
  }
  else if(addr==DBINIT){
    ++db_entries;
    check(ctx.lr==0x8000415cu || ctx.lr==0x8000405cu, "DBInit guest LR mismatch");
  }
}
bool handle_syscall(CPUContext&ctx){
  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;
  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x8051963cu){
    check(submit72_flush==1u&&submit72_sc==0u,"IPC request unexpected cache syscall sequence");
    const uint64_t lines=((submit72_base&31u)+uint64_t(submit72_len)+31u)/32u;
    check(ctx.guest_flush_count==submit72_flush_before+lines,"IPC request cache line count differs");
    const uint32_t msr=ctx.msr,lr=ctx.lr,hid=ctx.hid0,ctr=ctx.ctr;const auto gp=ctx.gpr;
    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),
           [](auto& c){func_80000C00(c);});
    check(ctx.msr==msr&&ctx.lr==lr&&ctx.hid0==hid&&ctx.ctr==ctr,"IPC cache syscall did not preserve state");
    for(unsigned r=0;r<32u;++r)if(r!=9u&&r!=10u)check(ctx.gpr[r]==gp[r],"IPC cache syscall clobbered unrelated register");
    ++submit72_sc;return true;
  }
  if(own&&ctx.pc==0x805222e8u&&ctx.lr==0x80519a1cu){
    check(open71_flush==1u&&open71_sc==0u,"IOS_Open unexpected cache syscall sequence");
    const uint64_t lines=((open71_flush_base&31u)+uint64_t(open71_flush_len)+31u)/32u;
    check(ctx.guest_flush_count==open71_flush_before+lines,"native IOS_Open data cache line count differs");
    const uint32_t hid=ctx.hid0,msr=ctx.msr,lr=ctx.lr,ctr=ctx.ctr;
    const auto gp=ctx.gpr;
    native_idle_cache_sc(ctx,SYSCALL_DEST,sc_vector,!ipc70_bus.external_irq_level(),
        [](auto& c){func_80000C00(c);});
    check(ctx.hid0==hid&&ctx.msr==msr&&ctx.lr==lr&&ctx.ctr==ctr&&
          ctx.gpr[9]==hid&&ctx.gpr[10]==(hid|8u),"IOS_Open cache syscall clobbered CPU state");
    for(unsigned r=0;r<32u;++r)
      if(r!=9u&&r!=10u)check(ctx.gpr[r]==gp[r],"IOS_Open cache syscall clobbered unrelated GPR");
    ++open71_sc;return true;
  }
  if(own&&ctx.pc==0x805222e8u){
    check(ctx.lr==(arena_active?arena_flush_lr(arena_phase):0x80522044u)&&
          ctx.guest_flush_count==87u+(arena_active?arena_phase*FLUSH_LINES:0u)&&ctx.gpr[1]==AUDIO_FRAME,
          "original cache flush did not reach authentic syscall");
    const uint32_t hid=ctx.hid0,msr=ctx.msr,lr=ctx.lr,ctr=ctx.ctr;
    const auto gp=ctx.gpr;
    boot_native_sc(ctx,SYSCALL_DEST,sc_vector,[](auto& c){func_80000C00(c);});
    check(ctx.hid0==hid&&ctx.msr==msr&&ctx.lr==lr&&ctx.ctr==ctr&&
          ctx.gpr[9]==hid&&ctx.gpr[10]==(hid|8u),
          "original SC cache vector did not preserve state and restore HID0");
    for(unsigned i=0;i<32;++i)
      if(i!=9u&&i!=10u)check(ctx.gpr[i]==gp[i],"original SC vector clobbered unrelated GPR");
    ++sc_entries;
    if(arena_active){
      check(arena_sc_calls+1u==arena_phase&&arena_flush_calls==arena_phase,
            "original arena cache flush syscall order differs");
      ++arena_sc_calls;
    }else{dsp_ctx=&ctx;dsp.begin();}
    return true;
  }
  if(ctx.pc==(own?POST_OWNER:POST_SYNTH)){
     if(own){
       check(stm70_entered&&stm70_open==1u&&open71_submit==1u&&submit72_ack==1u&&sleep73_select==1u&&ctx.lr==OS_RET_OWNER&&
             !(ctx.msr&0x8000u)&&ctx.gpr[1]<open71_stack&&ctx.gpr[1]>=ipc69_gprs[1]-0x400u,
             "original IOS_Open request did not reach native ACK and enrolled thread scheduler boundary");
     }
    if(own)check(arena_active&&arena_phase==2u&&arena_getters==6u&&arena_reset_reads==2u&&
                 arena_reset_calls==2u&&arena_zero_calls==2u&&arena_flush_calls==2u&&arena_sc_calls==2u,
                 "original cold MEM1/MEM2 arena clear incomplete at OSInit return");
    if(own)check(report_entries==1u&&report_calls==10u&&console_entries==1u&&report_getters==6u,
                 "original boot report incomplete at OSInit return");
    if(own)check(mi_active&&mi_writes==3u&&mi_handlers==5u&&mi_trampolines==2u&&mi_maps==2u&&ctx.mmu.read32(MI_FLAG)==1u,
                 "original memory protection initialization incomplete at OSInit return");
    if(own)check(wait_index==5u&&audio_write_count==6u&&!audio_active&&dsp.complete()&&dsp_wait_finished,
                 "audio return reached before completed original DSP handshake");
    check(ctx.lr==(own?OS_RET_OWNER:OS_RET_SYNTH),"wrong guest LR at V26 owner or synthetic stop");
    check(own?(ctx.gpr[1]<ORIGINAL_SP-8u-80u&&ctx.gpr[1]>=ORIGINAL_SP-8u-80u-0x400u):ctx.gpr[1]==SYNTH_SP-8u-96u,
          "original Wii interrupt epilogue failed to restore OSInit guest frame");
    observed_stop_pc=ctx.pc;
    ++post_stops;ctx.is_running=false;
    if(own)throw ExceptionStop{};  // prevent synthetic BLR after exact guest PC
    return true;}
  if(ctx.pc==REPORT){
    if(report_entries){
      check(own&&report_calls<expected_report.size(),"unexpected original boot report call");
      const auto& e=expected_report[report_calls];
      check(ctx.lr==e.lr&&ctx.gpr[3]==e.fmt&&ctx.cr[1].eq==0,
            "original boot report format/callsite/varargs flags differ");
      check(ctx.gpr[1]==(report_calls==9u?ORIGINAL_SP-8u-80u:ORIGINAL_SP-8u-96u),
            "original boot report stack frame differs");
      check_private_report_string(ctx,e.fmt);
      for(unsigned i=0;i<e.nargs;++i)
        check(ctx.gpr[4u+i]==e.args[i],"original boot report argument differs");
      if(report_calls==1u){check_private_report_string(ctx,ctx.gpr[4]);check_private_report_string(ctx,ctx.gpr[5]);}
      if(report_calls==9u)check_private_report_string(ctx,ctx.gpr[4]);
      if(report_calls==3u)check(ctx.ctr==report_ctr,"original console report computed branch target differs");
      ++report_calls;return true;
    }
    if(ctx.lr==0x805320a0u){
      check(own&&ctx.gpr[3]==R13-16436u&&ctx.gpr[4]==si_version_pointer,
            "original SI version registration tail-call ABI changed");
      ++si_report_entries;return true;
    }
    check(own&&ctx.lr==0x804efb60u&&ctx.gpr[3]==R13-16436u&&
          ctx.gpr[4]==version_pointer,
          "original EXI version registration tail-call ABI changed");
    ++version_report_entries;
    return true; // Explicit test-only logging sink, not an OSReport implementation.
  }
  if(ctx.pc==DBG){
    ++external_stubs[0];
    // Count the authentic terminal OSExceptionInit BL at 0x80520E58
    // separately from other bounded debug-service invocations in __start.
    if(ctx.lr==0x80520e5cu)++exception_epilogue_debug_entries;
    if(ctx.lr==CONTEXT+0x38u)++context_debug_entries;
    return true;
  }
  if(ctx.pc==ERR){
    check(ctx.gpr[3]==1u,"OSSetErrorHandler exception index differs");
    ++external_stubs[1];return true;
  }
  ++unknown_calls;throw std::runtime_error("unexpected syscall/native Wii service");
}
void interpret_step(CPUContext&){++interpreter_calls;throw std::runtime_error("interpreter fallback");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){
  ++interpreter_calls;
  throw std::runtime_error("unexpected micro interpreter fallback");
}
void note_null_call(uint32_t,uint32_t){
  ++unknown_calls;
  throw std::runtime_error("unexpected null indirect EXI callback");
}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t addr){
  if(dsp.active()){
    const auto value=dsp.read16(addr,[](uint32_t src,uint32_t dest,uint32_t n){
      check(dsp_ctx&&src==0x01000000u&&dest==0u&&n==32u&&
            dsp_ctx->guest_flush_count==87u,"DSP ARAM DMA without original staged cache flush");
      for(unsigned i=0;i<n;++i){
        const auto v=dsp_ctx->mmu.read8(0x80000000u+src+i);
        check(v==dsp_image[i],"DSP ARAM DMA source differs from original staged bytes");
        aram[dest+i]=v;
      }
    });
    mmio_reads.emplace_back(addr,value);return value;
  }
  if(addr==0x0c00206cu){
    check(probe_channel==2u&&si_phase==0u,
          "original SI sampled VI clock outside expected phase");
    mmio_reads.emplace_back(addr,si_clock);
    return uint16_t(si_clock);
  }
  // Deterministic owner-game test oracle only. No working PI/IOS device.
  if(addr!=0x0c00500au){
    ++unexpected_mmio;throw std::runtime_error("unrecognized Wii MMIO read16");
  }
  mmio_reads.emplace_back(addr,0xf7f7u);
  return 0xf7f7u;
}
uint32_t HW_Reg_Read32(uint32_t addr){
   if(submit72_active){
     const auto result=ipc70_bus.read32(addr);
     check(result.has_value(),"original IPC send unsupported MMIO read");
     mmio_reads.emplace_back(addr,*result);return *result;
   }
   if(ipc69_active){
     check(addr==0x0c003004u||addr==0x0d000034u,"unexpected IPC mask MMIO read");
     for(auto it=mmio_writes.rbegin();it!=mmio_writes.rend();++it)if(it->first==addr){
       const auto actual=ipc70_bus.read32(addr);
       check(actual&&*actual==it->second,"original IPC mask MMIO bus readback differs from trace");
       mmio_reads.emplace_back(addr,*actual);return *actual;
     }
     check(false,"IPC mask read without initialized register");
   }
  if(arena_active){
    check(addr==0x0c003024u&&arena_reset_reads+1u==arena_phase&&arena_reset_calls==arena_phase,
          "original arena reset-code PI MMIO read differs");
    ++arena_reset_reads;const uint32_t v=reset_seed();mmio_reads.emplace_back(addr,v);return v;
  }
  if(audio_active){
    check(audio_read_count<audio_reads_expected.size()&&audio_read_count==audio_write_count&&
          addr==audio_reads_expected[audio_read_count].first,
          "unexpected Hollywood clock/reset register read");
    if(audio_read_count>=2u)finish_wait();
    const uint32_t value=audio_reads_expected[audio_read_count++].second;
    mmio_reads.emplace_back(addr,value);return value;
  }
  if(sram_device.active()){
    const auto value=sram_device.read(addr,[](uint32_t dest,const auto&bytes){
      check(sram_ctx&&dest==SRAM,"SRAM DMA attempted an unexpected guest address");
      for(unsigned i=0;i<bytes.size();++i){
        check(sram_ctx->mmu.read8(dest+i)==0u,"SRAM DMA guest data changed before hardware completion");
        sram_ctx->mmu.write8(dest+i,bytes[i]);
      }
    });
    mmio_reads.emplace_back(addr,value);return value;
  }
  if(id_device.complete()){
    if(probe_channel==2u){
      if(si_phase==3u&&si_read_phase==0u){
        check(addr==0x0d006438u&&si_channel==1u,
              "original SI first start did not read channel status");
        ++si_read_phase;mmio_reads.emplace_back(addr,0x0f123456u);return 0x0f123456u;
      }
      if(si_phase==5u&&si_read_phase==1u){
        check(addr==0x0d006434u,"original SI start did not read transfer control");
        ++si_read_phase;mmio_reads.emplace_back(addr,0u);return 0u;
      }
      check(addr==0x0d006434u&&si_phase==1u&&++si_polls<=8u,
            "original SI transfer busy polling address/order invalid");
      const uint32_t value=si_busy?1u:0u;
      if(si_busy)--si_busy;
      mmio_reads.emplace_back(addr,value);return value;
    }
    check(probe_channel<2u&&addr==ExiIdTestDevice::CSR+20u*probe_channel&&probe_reads==0u,
          "unexpected MMIO read after uncached ID transaction");
    ++probe_channel;
    mmio_reads.emplace_back(addr,0u); // Both removable-card slots empty.
    return 0u;
  }
  if(id_device.active()){
    const uint32_t value=id_device.read(addr);
    mmio_reads.emplace_back(addr,value);
    return value;
  }
  constexpr std::array<uint32_t,3> exi_registers{
    0x0d00680cu,0x0d006820u,0x0d006834u};
  for(size_t i=0;i<exi_registers.size();++i){
    if(addr==exi_registers[i]){
      const bool busy=exi_busy[i]>0u;
      if(busy)--exi_busy[i];
      const uint32_t value=0x2000u+uint32_t(i)*0x10u+(busy?1u:0u);
      exi_reads.emplace_back(addr,value);
      mmio_reads.emplace_back(addr,value);
      if(exi_reads.size()>64u)
        throw std::runtime_error("unbounded synthetic EXI busy polls");
      return value;
    }
  }
  uint32_t value=0;
  switch(addr){
    case 0x0d006c00u:value=0x12345678u;break;
    case 0x0d006800u:value=0x98765432u;break;
    case 0x0d006814u:value=0xaabbccddu;break;
    case 0x0d006828u:value=0xdeadbeefu;break;
    default:++unexpected_mmio;throw std::runtime_error("unrecognized Wii MMIO read32");
  }
  mmio_reads.emplace_back(addr,value);return value;
}
void HW_Reg_Write16(uint32_t addr,uint16_t value){
  if(mi_active){
    constexpr std::array<std::pair<uint32_t,uint16_t>,3> expected{{{0x0c004020u,0},{0x0c004010u,255},{0x0c00401cu,16}}};
    check(mi_writes<expected.size()&&std::make_pair(addr,value)==expected[mi_writes],
          "original memory interface register write differs");
    ++mi_writes;mmio_writes.emplace_back(addr,value);return;
  }
  if(dsp.active()){dsp.write16(addr,value);mmio_writes.emplace_back(addr,value);return;}
  if(addr!=0x0c00401cu && addr!=0x0c00500au){
    ++unexpected_mmio;throw std::runtime_error("unrecognized Wii MMIO write16");
  }
  mmio_writes.emplace_back(addr,uint32_t(value));
}
void HW_Reg_Write32(uint32_t addr,uint32_t value){
   if(submit72_active){
     using Bus=undercover::wii::IosBus;using Mail=undercover::wii::IpcMailbox;
     const auto reg=addr>=Bus::MIRROR?addr-Bus::MIRROR:addr-Bus::IPC;
     if(reg==Mail::PPCMSG){
       check(submit72_message==0u&&ipc70_ram.valid(value,64u)&&!(value&31u),
             "original PPCMSG writes invalid request pointer");
       submit72_phys=value;++submit72_message;
     }else if(reg==Mail::PPCCTRL){
       check(submit72_message==1u&&submit72_x1==0u&&(value&Mail::X1),
             "original PPCCTRL does not submit X1 after request pointer");
       ++submit72_x1;
     }else check(false,"unexpected original IPC submission register write");
     check(ipc70_bus.write32(addr,value),"native IOS bus rejected original request register write");
     mmio_writes.emplace_back(addr,value);return;
   }
   using Bus=undercover::wii::IosBus;using Irq=undercover::wii::HollywoodIrq;
   if(addr==Bus::PI_MASK||addr==Bus::IPC+Irq::PPC_MASK||addr==Bus::MIRROR+Irq::PPC_MASK)
     check(ipc70_bus.write32(addr,value),"native IOS interrupt bus rejected original mask write");
   if(ipc69_active){
     if(addr==0x0d000004u||addr==0x0d800004u){
       check(ipc69_step==8u&&ipc69_mail==0u&&value==ipc69_msg,"IPC mailbox write value/order differs");
       check(ipc70_bus.write32(addr,value),"native IOS bus rejected original mailbox control write");
       ++ipc69_mail;
     }else check(ipc69_step==7u&&(addr==0x0c003004u||addr==0x0d000034u),"unexpected IPC mask MMIO write");
     mmio_writes.emplace_back(addr,value);return;
   }
  if(dsp.active()){
    if(addr==DspBootDevice::DMA_SOURCE&&dsp.acks==1u)finish_dsp_wait();
    dsp.write32(addr,value);mmio_writes.emplace_back(addr,value);return;
  }
  if(audio_active){
    check(audio_write_count<audio_writes_expected.size()&&audio_read_count==audio_write_count+1u&&
          std::make_pair(addr,value)==audio_writes_expected[audio_write_count],
          "original Hollywood clock/reset write mask, value or order differs");
    ++audio_write_count;mmio_writes.emplace_back(addr,value);return;
  }
  if(sram_device.active()){
    sram_device.write(addr,value);mmio_writes.emplace_back(addr,value);return;
  }
  if(id_device.complete()){
    check(probe_channel==2u,"SI write before EXI probes completed");
    if(si_phase==0u)
      check(addr==0x0d006430u&&value==si_expected,
            "original SI polling register write differs");
    else if(si_phase==1u)
      check(addr==0x0d006434u&&value==0x80000000u&&si_busy==0u&&si_polls>0u,
            "original SI completion-clear write before idle status");
    else if(si_phase==2u)
      check(addr==0x0c003004u&&value==0xf8u,
            "original SI IRQ enable PI mask differs");
    else if(si_phase==3u)
      check(addr==0x0d006438u&&value==0x0f000000u&&si_read_phase==1u,
            "original SI channel status write-one-to-clear mask differs");
    else if(si_phase==4u)
      check(addr==0x0d006480u&&value==0u,"original SI first immediate command word differs");
    else if(si_phase==5u)
      check(addr==0x0d006434u&&value==0xc0010301u&&si_read_phase==2u,
            "original SI first command/response lengths, IRQ enable or start bit differ");
    else check(false,"unexpected SI MMIO write while subsequent type transfers queued");
    ++si_phase;mmio_writes.emplace_back(addr,value);return;
  }
  if(id_device.active()){
    id_device.write(addr,value);
    mmio_writes.emplace_back(addr,value);
    return;
  }
  if(addr==ExiIdTestDevice::CSR)last_csr=value;
  if(addr!=0x0c003004u && addr!=0x0d000034u &&
     addr!=0x0d006c00u && addr!=0x0d006800u &&
     addr!=0x0d006814u && addr!=0x0d006828u){
    ++unexpected_mmio;throw std::runtime_error("unrecognized Wii MMIO write32");
  }
  mmio_writes.emplace_back(addr,value);
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv){
  if(argc!=4)return 2;
  const bool owner=std::string(argv[2])=="owner";
  if(!owner&&std::string(argv[2])!="synthetic")return 2;
  nwii::loader::Executable exe;
  check(exe.load_dol(argv[1]),"test DOL load failed");
  check(exe.entry_point==START&&exe.sections.size()==(owner?18u:8u),"unexpected DOL image layout");
  nwii::loader::Executable original;
  if(owner){
    check(original.load_dol(argv[3])&&original.entry_point==START,"authenticated STM original source load failed");
    nwii::runtime::stm70_owner=&original;
  }
  auto ctx=std::make_unique<nwii::runtime::CPUContext>();
  unsigned table_count=0;
  for(const auto&sec:exe.sections){
    if(!sec.is_bss&&!sec.is_text&&sec.address==TABLE){
      check(sec.size==0xb0u,"invalid copied relocation table");
      for(size_t i=0;i<sec.data.size();++i)ctx->mmu.write8(TABLE+uint32_t(i),sec.data[i]);
      ++table_count;
    }
  }
  check(table_count==1,"required DOL data table missing");
  std::vector<uint8_t> original_handler;
  if(owner){
    unsigned handlers=0;
    for(const auto&sec:exe.sections){
      if(!sec.is_bss&&!sec.is_text&&sec.address==ORACLE_GUEST){
        check(sec.size==VECTOR_LEN && sec.data.size()==VECTOR_LEN,
              "private original exception-vector template oracle has invalid size");
        original_handler.assign(sec.data.begin(),sec.data.end());
        ++handlers;
      }
    }
    check(handlers==1 && original_handler.size()==VECTOR_LEN,
          "missing unique owner-original handler template in private DOL");
  }
  // Source-backed original exception template word from the PRIVATE fixture.
  // NWiiRuntime's minimal test MMU does not automatically map all PPC text.
  uint32_t exception_word=0;
  if(owner){
    unsigned matches=0;
    for(const auto& sec:exe.sections){
      if(!sec.is_bss && sec.address<=EXC_SOURCE_WORD &&
         uint64_t(EXC_SOURCE_WORD)+4u<=uint64_t(sec.address)+sec.size){
        const size_t off=EXC_SOURCE_WORD-sec.address;
        check(off+4<=sec.data.size(),
              "original exception literal not in private DOL memory span");
        exception_word=(uint32_t(sec.data[off])<<24)|
                       (uint32_t(sec.data[off+1])<<16)|
                       (uint32_t(sec.data[off+2])<<8)|
                        uint32_t(sec.data[off+3]);
        ++matches;
      }
    }
    check(matches==1,"original exception template word missing/ambiguous");
  }
  std::array<uint8_t,SYSCALL_LEN> original_syscall{};
  if(owner){
    unsigned sources=0;
    for(const auto& section:exe.sections){
      if(!section.is_bss && section.address<=SYSCALL_SOURCE &&
         uint64_t(SYSCALL_SOURCE)+SYSCALL_LEN<=
           uint64_t(section.address)+section.data.size()){
        const size_t off=SYSCALL_SOURCE-section.address;
        for(size_t i=0;i<original_syscall.size();++i)
          original_syscall[i]=section.data[off+i];
        ++sources;
      }
    }
    check(sources==1,
          "V51 private owner syscall handler source is not mapped uniquely");
  }
  if(owner){
    unsigned version_sources=0;
    for(const auto&sec:exe.sections){
      if(!sec.is_bss&&!sec.is_text&&sec.address==0x8070a748u){
        check(sec.data.size()==4u,"private EXI version pointer size differs");
        for(uint32_t i=0;i<4u;++i)ctx->mmu.write8(sec.address+i,sec.data[i]);
        ++version_sources;
      }
    }
    check(version_sources==1u,"missing exact owner EXI initialized data");
    nwii::runtime::version_pointer=ctx->mmu.read32(0x8070a748u);
    check(nwii::runtime::version_pointer>=0x80000000u&&
          nwii::runtime::version_pointer<0x81800000u,
          "owner EXI version pointer outside guest RAM");
  }
  if(owner){
    unsigned si_sources=0;
    for(const auto&sec:exe.sections){
      if(!sec.is_bss&&!sec.is_text&&
         (sec.address==0x8070aa70u||sec.address==0x80619a60u||sec.address==0x8061a890u)){
        check(sec.data.size()==(sec.address==0x8070aa70u?4u:sec.address==0x80619a60u?0x88u:36u),
              "private SI initialized data span differs");
        for(size_t i=0;i<sec.data.size();++i)ctx->mmu.write8(sec.address+uint32_t(i),sec.data[i]);
        ++si_sources;
      }
    }
    check(si_sources==3u,"missing owner SI version, sample and jump-table data");
    nwii::runtime::si_version_pointer=ctx->mmu.read32(0x8070aa70u);
    check(nwii::runtime::si_version_pointer>=0x80000000u&&
          nwii::runtime::si_version_pointer<0x81800000u,
          "owner SI version pointer outside guest RAM");
  }
  if(owner){
    unsigned thread_data=0;
    for(const auto&sec:exe.sections)
      if(!sec.is_bss&&!sec.is_text&&sec.address==THREAD_CALLBACK_PTR){
        check(sec.data.size()==4u,"original thread initialized pointer size differs");
        for(unsigned i=0;i<4;++i)ctx->mmu.write8(sec.address+i,sec.data[i]);
        ++thread_data;
      }
    check(thread_data==1u&&ctx->mmu.read32(THREAD_CALLBACK_PTR)==0x80529128u,
          "original thread initialized callback pointer not loaded");
  }
  if(owner){
    nwii::runtime::sc_vector=original_syscall;
    unsigned image_sources=0;
    for(const auto&sec:exe.sections)
      if(!sec.is_bss&&!sec.is_text&&sec.address==DSP_SRC){
        check(sec.data.size()==DSP_SIZE,"private DSP bootstrap data size differs");
        for(unsigned i=0;i<DSP_SIZE;++i){
          nwii::runtime::dsp_image[i]=sec.data[i];ctx->mmu.write8(DSP_SRC+i,sec.data[i]);
        }
        ++image_sources;
      }
    check(image_sources==1u,"missing authenticated original DSP bootstrap data");
  }
  std::array<uint8_t,16> mi_node{};
  if(owner){
    unsigned n=0;
    for(const auto&sec:exe.sections)if(!sec.is_text&&!sec.is_bss&&sec.address==MI_NODE){
      check(sec.data.size()==mi_node.size(),"original MI shutdown node size differs");
      std::copy(sec.data.begin(),sec.data.end(),mi_node.begin());++n;
    }
    check(n==1u,"original MI shutdown node missing");
  }
  if(owner){
    unsigned n=0;
    for(const auto&sec:exe.sections)if(!sec.is_text&&!sec.is_bss){
      if(sec.address==REPORT_DATA){
        check(sec.data.size()==REPORT_BYTES,"original boot report data size differs");
        std::copy(sec.data.begin(),sec.data.end(),nwii::runtime::report_data.begin());++n;
      }else if(sec.address==REPORT_SMALL){
        check(sec.data.size()==REPORT_SMALL_BYTES,"original report small data size differs");
        std::copy(sec.data.begin(),sec.data.end(),nwii::runtime::report_small.begin());++n;
      }
    }
    check(n==2u,"original boot report data sections missing");
  }
  const auto zero=zero_table(*ctx);
  check(zero.size()==(owner?3u:2u),"wrong zero-table mode/count");
  if(owner){
    check(zero[0].start==0x8061e900u&&zero[0].size==950236,"wrong owner BSS range 0");
    check(zero[1].start==0x8070ab60u&&zero[1].size==13164,"wrong owner BSS range 1");
    check(zero[2].start==0x80711c80u&&zero[2].size==56,"wrong owner BSS range 2");
  }
  uint32_t seed=0x9e3779b9u;
  const unsigned trials=owner?16u:16u;
  for(unsigned trial=0;trial<trials;++trial){
    auto&c=*ctx;
    if(owner){
      // Reload the authenticated initialized SI memory on every independent boot.
      for(const auto&sec:exe.sections)
        if(!sec.is_bss&&!sec.is_text&&sec.address==SI_DATA)
          for(size_t i=0;i<sec.data.size();++i)c.mmu.write8(sec.address+uint32_t(i),sec.data[i]);
      c.mmu.write32(0x800000f8u,BUS_CLOCK);
      c.tb_freq=BUS_CLOCK/4u;
    }
    for(auto&g:c.gpr)g=random32(seed);
    const bool ic_on=(trial&4u)==0,dc_on=(trial&2u)==0,l2_on=(trial&1u)==0;
    const uint32_t msr0=random32(seed)&~0x2000u;
    c.msr=msr0;
    c.hid0=(random32(seed)&0x00ff0000u)|(ic_on?0x8000u:0u)|(dc_on?0x4000u:0u);
    const uint32_t expected_hid0=c.hid0|0xc800u;
    c.hid2=random32(seed)&~0xa0000000u;
    const uint32_t expected_hid2=c.hid2|0xa0000000u;
    for(auto&q:c.gqr)q=0xffffffffu;
    const uint32_t old_l2=(random32(seed)&0xff00u)|(l2_on?0x80000000u:0);
    c.l2cr=old_l2;c.l2cr_busy_polls=0;
    c.mmcr0=0x12345678u; c.mmcr1=0x9abcdef0u;
    c.hid4=random32(seed);
    for(unsigned k=0;k<4;++k)c.pmc[k]=0x10000u+k;
    const uint32_t ps_addr=owner?0x8070db08u:0x80034000u;
    const uint32_t fp_addr=owner?0x8070db10u:0x80034100u;
    const float expected_ps=static_cast<float>(-3.25-(trial%13)*.25);
    c.mmu.write_f32(ps_addr,1.5f+float(trial%11)*.125f);
    c.mmu.write_f32(ps_addr+4,expected_ps);
    const uint32_t fpscr=random32(seed);
    const uint64_t fpbits=0x3ff0000000000000ull|fpscr;
    c.mmu.write64(fp_addr,fpbits);
    c.mmu.write64(0x80034110u,fpbits);
    double expected_scalar=0;
    std::memcpy(&expected_scalar,&fpbits,sizeof(fpbits));
    for(unsigned k=0;k<32;++k){c.fpr[k]=0;c.ps1[k]=0;}
    c.fpscr=0xffffffffu;
    if(owner){
      for(const auto&span:zero){
        auto*ptr=c.mmu.get_ptr(span.start);
        check(ptr!=nullptr,"original BSS span outside MMU");
        std::memset(ptr,0x35+trial,span.size);
        c.mmu.write8(span.start-1,0xB5);
        c.mmu.write8(span.start+span.size,0xC5);
      }
      // Seed FP memory AFTER poisoning BSS, as FPR seed belongs to BSS.
      c.mmu.write_f32(ps_addr,1.5f+float(trial%11)*.125f);
      c.mmu.write_f32(ps_addr+4,expected_ps);
      c.mmu.write64(fp_addr,fpbits);
    } else {
      c.mmu.write32(0x80036000u,0xDEADBEEFu);
      c.mmu.write32(0x80036004u,0xDEADBEEFu);
    }
    const uint32_t sp=owner?ORIGINAL_SP:SYNTH_SP;
    c.gpr[1]=sp;
    c.pc=START;c.lr=0x80009998u;c.is_running=true;
    const auto before_data=nwii::runtime::data_calls;
    const auto before_ic=nwii::runtime::ic_calls, before_dc=nwii::runtime::dc_calls;
    const auto before_cache=nwii::runtime::cache_calls;
    const auto before_stubs=nwii::runtime::external_stubs;
    const auto before_terminal_debug=nwii::runtime::exception_epilogue_debug_entries;
    const auto before_stop=nwii::runtime::post_stops;
    const auto before_db=nwii::runtime::db_entries;
    const auto before_os=nwii::runtime::os_entries;
    const auto before_save=nwii::runtime::save_entries;
    const auto before_time=nwii::runtime::time_entries;
    const auto before_gettime=nwii::runtime::gettime_entries;
    const auto before_disable=nwii::runtime::disable_entries;
    const auto before_restore=nwii::runtime::restore_entries;
    const auto before_time_global=nwii::runtime::time_global_checks;
    const auto before_hardware=nwii::runtime::hardware_entries;
    const auto before_arena=nwii::runtime::arena_entries;
    const auto before_mem2=nwii::runtime::mem2_entries;
    const auto before_ipc=nwii::runtime::ipc_entries;
    const auto before_exception=nwii::runtime::exception_entries;
    const auto before_marker=nwii::runtime::marker_entries;
    const auto before_exception_restore=nwii::runtime::exception_restore_entries;
    const auto before_exec=nwii::runtime::exec_entries;
    const auto before_perf=nwii::runtime::perf_entries;
    // Diagnostics are reset per trial; they do not affect guest cache state.
    c.guest_flush_count=0;c.guest_invalidate_count=0;
    c.guest_sync_count=0;c.guest_isync_count=0;
    c.guest_data_invalidate_count=0;
    nwii::runtime::sram_device.reset(SRAM,trial);nwii::runtime::sram_ctx=nullptr;
    nwii::runtime::sram_command_ptr=0;
    const auto before_sram=nwii::runtime::sram_entries;
    const auto before_sram_dma=nwii::runtime::sram_dma_entries;
    const auto before_sram_cache=nwii::runtime::sram_invalidate_entries;
    const auto before_sram_unlock=nwii::runtime::sram_unlock_entries;
    const auto before_sram_cfg=nwii::runtime::sram_config_unlock_entries;
    const auto before_thread=nwii::runtime::thread_entries;
    const auto before_thread_clear=nwii::runtime::thread_clear_entries;
    const auto before_thread_context=nwii::runtime::thread_context_entries;
    const auto before_thread_callback=nwii::runtime::thread_callback_entries;
    const auto before_thread_sp=nwii::runtime::thread_sp_entries;
    nwii::runtime::audio_active=false;nwii::runtime::mi_active=false;
    nwii::runtime::report_entries=0;nwii::runtime::report_calls=0;
    nwii::runtime::arena_active=false;nwii::runtime::arena_phase=0;nwii::runtime::arena_getters=0;
    nwii::runtime::arena_reset_calls=nwii::runtime::arena_reset_reads=nwii::runtime::arena_zero_calls=0;
    nwii::runtime::arena_flush_calls=nwii::runtime::arena_sc_calls=0;
     nwii::runtime::enable_entries=0;nwii::runtime::enable_before=0;
     nwii::runtime::ipc69_active=false;
     nwii::runtime::ipc70_ram.cpu=&c;nwii::runtime::ipc70_bus.reset();
     nwii::runtime::stm70_entered=false;nwii::runtime::stm70_open=0;nwii::runtime::stm70_path=0;
     nwii::runtime::open71_alloc=nwii::runtime::open71_alloc_disable=nwii::runtime::open71_alloc_restore=0;
     nwii::runtime::open71_profile=nwii::runtime::open71_flush=nwii::runtime::open71_sc=nwii::runtime::open71_submit=0;
     nwii::runtime::open71_path_len=nwii::runtime::open71_flush_base=nwii::runtime::open71_flush_len=nwii::runtime::open71_stack=0;
     nwii::runtime::open71_flush_before=0;
     nwii::runtime::submit72_active=false;
     nwii::runtime::submit72_flush=nwii::runtime::submit72_sc=nwii::runtime::submit72_disable=0;
     nwii::runtime::submit72_message=nwii::runtime::submit72_x1=nwii::runtime::submit72_ack=0;
     nwii::runtime::submit72_base=nwii::runtime::submit72_len=nwii::runtime::submit72_phys=0;
     nwii::runtime::submit72_flush_before=0;
     nwii::runtime::sleep73_queue=nwii::runtime::sleep73_sp=0;
     nwii::runtime::sleep73_init=nwii::runtime::sleep73_entry=nwii::runtime::sleep73_disable=nwii::runtime::sleep73_select=0;
     nwii::runtime::ipc69_step=nwii::runtime::ipc69_os_get=nwii::runtime::ipc69_disable=nwii::runtime::ipc69_restore=0;
     nwii::runtime::ipc69_bank=nwii::runtime::ipc69_mail=0;
     nwii::runtime::ipc69_lo=nwii::runtime::ipc69_hi=nwii::runtime::ipc69_size=nwii::runtime::ipc69_handler=0;
    c.guest_dcbz_trace.clear();
    nwii::runtime::mi_writes=nwii::runtime::mi_handlers=nwii::runtime::mi_maps=nwii::runtime::mi_trampolines=0;
    const auto before_mi=nwii::runtime::mi_entries,before_mi_map=nwii::runtime::mi_map_entries,
      before_mi_shutdown=nwii::runtime::mi_shutdown_entries,before_mi_unmask=nwii::runtime::mi_unmask_entries,
      before_hid_read=nwii::runtime::mi_hid_reads,before_hid_write=nwii::runtime::mi_hid_writes;
    c.bat_write_count=0;
    for(unsigned i=0;i<c.bat_registers.size();++i)c.bat_registers[i]=0xbeef0000u+i+trial*32u;
    nwii::runtime::dsp.reset(trial);nwii::runtime::dsp_ctx=nullptr;
    nwii::runtime::aram.fill(0xa7u);
    nwii::runtime::dsp_wait_started=nwii::runtime::dsp_wait_finished=false;
    nwii::runtime::dsp_wait_polls=0;nwii::runtime::dsp_wait_delta=0;nwii::runtime::dsp_wait_previous=0;
    nwii::runtime::audio_read_count=nwii::runtime::audio_write_count=nwii::runtime::wait_index=0;
    nwii::runtime::wait_started=false;nwii::runtime::wait_counts.fill(0);
    const auto before_audio=nwii::runtime::audio_entries;
    const auto before_audio_reset=nwii::runtime::reset_entries;
    const auto before_dsp_arena=nwii::runtime::dsp_arena_entries;
    const auto before_dsp_copy=nwii::runtime::dsp_copy_entries;
    const auto before_dsp_flush=nwii::runtime::dsp_flush_entries;
    const auto before_sc=nwii::runtime::sc_entries;
    const auto before_sc_vector=nwii::runtime::sc_vector_entries;
    if(owner){
      for(const auto& [lo,hi]:std::array<std::pair<uint32_t,uint32_t>,2>{{
        {M1_ARENA_LO(trial),M1_ARENA_HI},{M2_ARENA_LO(trial),M2_ARENA_HI}}}){
        auto* p=c.mmu.get_ptr(lo);
        check(p&&c.mmu.get_ptr(hi-1u)==p+hi-lo-1u,"test arena does not fit contiguous guest RAM");
        std::memset(p,0x5d+trial,hi-lo);c.mmu.write8(lo-1u,0x91u);c.mmu.write8(hi,0x92u);
      }
      for(unsigned i=0;i<DSP_SIZE;++i){
        const auto v=uint8_t(17u*i+trial*13u+9u);
        nwii::runtime::dsp_original_ram[i]=v;c.mmu.write8(DSP_STAGING+i,v);
        c.mmu.write8(DSP_BACKUP+i,uint8_t(v^0xffu));
      }
      for(uint32_t addr:{DSP_STAGING,DSP_BACKUP}){
        c.mmu.write8(addr-1u,0xa1u);c.mmu.write8(addr+DSP_SIZE,0xb2u);
      }
    }
    const auto before_dcflush=nwii::runtime::dcflush_entries;
    const auto before_icinvalid=nwii::runtime::icinvalid_entries;
    const auto before_syscall=nwii::runtime::syscall_entries;
    const auto before_alarm=nwii::runtime::alarm_entries;
    const auto before_alarm_get=nwii::runtime::alarm_get_entries;
    const auto before_alarm_set=nwii::runtime::alarm_set_entries;
    const auto before_shutdown=nwii::runtime::shutdown_entries;
    const auto before_module=nwii::runtime::module_entries;
    const auto before_irq=nwii::runtime::irq_entries;
    const auto before_irq_memset=nwii::runtime::irq_memset_entries;
    const auto before_irq_fill=nwii::runtime::irq_fill_entries;
    const auto before_irq_disable=nwii::runtime::irq_disable_entries;
    const auto before_setmask=nwii::runtime::setmask_entries;
    const auto before_irq_restore=nwii::runtime::irq_restore_entries;
    const auto before_irq_setexc=nwii::runtime::irq_setexc_entries;
    const auto before_cache_os=nwii::runtime::cache_os_entries;
    const auto before_exi=nwii::runtime::exi_entries;
    const auto before_mask=nwii::runtime::mask_entries;
    const auto before_handlers=nwii::runtime::handler_entries;
    const auto before_id=nwii::runtime::id_entries;
    nwii::runtime::response_id=0xBEEF0010u+trial;
    nwii::runtime::id_device.reset(nwii::runtime::response_id,trial%4u,(trial/4u)%4u);
    nwii::runtime::last_csr=0;
    nwii::runtime::probe_channel=0;
    nwii::runtime::probe_reads=0;
    nwii::runtime::si_phase=0;nwii::runtime::si_polls=0;
    nwii::runtime::si_channel=0;nwii::runtime::si_read_phase=0;
    nwii::runtime::si_type_times.fill(0);
    const auto before_si_types=nwii::runtime::si_type_entries;
    const auto before_si_transfers=nwii::runtime::si_transfer_entries;
    const auto before_si_starts=nwii::runtime::si_start_entries;
    nwii::runtime::si_clock=trial&1u;nwii::runtime::si_busy=trial%4u;
    nwii::runtime::si_expected=(uint32_t(c.mmu.read16(0x80619a88u))*(1u+(trial&1u))<<16)|
                               (uint32_t(c.mmu.read8(0x80619a8au))<<8);
    const auto before_si=nwii::runtime::si_entries;
    const auto before_si_rate=nwii::runtime::si_rate_entries;
    const auto before_si_tv=nwii::runtime::si_tv_entries;
    const auto before_si_xy=nwii::runtime::si_xy_entries;
    const auto before_si_handler=nwii::runtime::si_handler_entries;
    const auto before_si_unmask=nwii::runtime::si_unmask_entries;
    const auto before_si_version=nwii::runtime::si_version_entries;
    const auto before_si_report=nwii::runtime::si_report_entries;
    const auto before_probes=nwii::runtime::probe_entries;
    const auto before_versions=nwii::runtime::version_entries;
    const auto before_version_reports=nwii::runtime::version_report_entries;
    const auto before_locks=nwii::runtime::lock_entries;
    const auto before_selects=nwii::runtime::select_entries;
    const auto before_imms=nwii::runtime::imm_entries;
    const auto before_syncs=nwii::runtime::sync_entries;
    const auto before_deselects=nwii::runtime::deselect_entries;
    const auto before_irqmasks=nwii::runtime::irqmask_entries;
    const auto before_revisions=nwii::runtime::revision_entries;
    const auto before_mask_disable=nwii::runtime::mask_disable_entries;
    const auto before_mask_restore=nwii::runtime::mask_restore_entries;
    nwii::runtime::exi_busy=(trial%6u==2u)?
        std::array<unsigned,3>{1u,1u,2u}:
        (trial%6u==4u?std::array<unsigned,3>{0u,0u,1u}:
                       std::array<unsigned,3>{0u,0u,0u});
    nwii::runtime::exi_reads.clear();
    const auto before_context=nwii::runtime::context_entries;
    const auto before_context_setexc=nwii::runtime::context_setexc_entries;
    const auto before_context_debug=nwii::runtime::context_debug_entries;
    const auto before_mmio=nwii::runtime::mmio_writes.size();
    const auto before_mmio_reads=nwii::runtime::mmio_reads.size();
    c.mmu.write32(0x800000f4u,0);
    const uint32_t arena_hint=owner?M1_ARENA_LO(trial):0x80102000u+(trial*0x100u);
    c.mmu.write32(BOOT_HINT,arena_hint);
    c.mmu.write32(0x80003110u,0u); // no MEM1 arena-high hint
    const uint32_t mem2_low_hint=owner?M2_ARENA_LO(trial):0x90002000u+trial*0x100u;
    const uint32_t mem2_high_hint=owner?M2_ARENA_HI:0x93500000u+trial*0x100u;
    c.mmu.write32(MEM2_LO_HINT,mem2_low_hint);
    c.mmu.write32(MEM2_HI_HINT,mem2_high_hint);
    const uint32_t ipc_lo=0x90003000u+trial*0x120u;
    const uint32_t ipc_hi=0x93600000u+trial*0x120u;
    c.mmu.write32(IPC_LO_INPUT,ipc_lo);
    c.mmu.write32(IPC_HI_INPUT,ipc_hi);
    c.mmu.write32(IPC_LO_INPUT-4u,0xD13ACAFEu);
    c.mmu.write32(IPC_HI_INPUT+4u,0xBABE1234u);
    if(owner){
      nwii::runtime::setup_report(c,trial);
      for(unsigned i=0;i<REPORT_BYTES;++i)c.mmu.write8(REPORT_DATA+i,nwii::runtime::report_data[i]);
      for(unsigned i=0;i<REPORT_SMALL_BYTES;++i)c.mmu.write8(REPORT_SMALL+i,nwii::runtime::report_small[i]);
      c.mmu.write32(0x80003100u,MEM1_BYTES);c.mmu.write32(0x80003104u,MEM1_BYTES);
      c.mmu.write32(0x8000311cu,MEM2_BYTES);c.mmu.write32(0x80003120u,MEM2_MAP_HI);
      for(unsigned i=0;i<mi_node.size();++i)c.mmu.write8(MI_NODE+i,mi_node[i]);
      c.mmu.write32(MI_NODE-4u,0xa1a1a1a1u);c.mmu.write32(MI_NODE+16u,0xb2b2b2b2u);
      c.mmu.write32(0x80000060u,1u+trial); // original exception fast path
      for(uint32_t i=0;i<VECTOR_LEN;++i)
        c.mmu.write8(SOURCE_TEMPLATE+i,original_handler[i]);
      c.mmu.write32(EXC_SOURCE_WORD,exception_word);
      c.mmu.write32(EXC_TEMPLATE_DST,0xDADAC0DEu);
      c.mmu.write32(EXC_TEMPLATE_DST-4u,0x42434342u);
      c.mmu.write32(EXC_TEMPLATE_DST+4u,0x47494947u);
      // This MMU test has no original game's vector offset .data mapped.
      // Provide synthetic offsets and adjacent canaries for all fifteen
      // guest vectors; their payloads still come from the owner's DOL.
      for(uint32_t vector=0;vector<15u;++vector){
        const uint32_t dest=VECTOR_DEST+vector*0x100u;
        c.mmu.write32(0x8060bbe0u+4u*vector,0x100u+vector*0x100u);
        c.mmu.write8(dest-1u,0xB6u);
        for(uint32_t i=0;i<VECTOR_LEN;++i)c.mmu.write8(dest+i,0xD3u);
        c.mmu.write8(dest+VECTOR_LEN,0xB7u);
        c.mmu.write32(0x80003000u+4u*vector,0xBEEA0000u+vector);
      }
      c.mmu.write32(0x8000303cu,0xDEADBEEFu);
      // The synthetic MMU maps text-as-data only when explicitly seeded.
      // Use the owner-original, SHA-authenticated 28-byte syscall stub.
      for(uint32_t i=0;i<SYSCALL_LEN;++i)
        c.mmu.write8(SYSCALL_SOURCE+i,original_syscall[i]);
      c.mmu.write8(SYSCALL_SOURCE-1u,0xABu);
      c.mmu.write8(SYSCALL_SOURCE+SYSCALL_LEN,0xBCu);
      // Independently authored alarm and shutdown-list test inputs.
      // __init_data clears BSS during native continuous __start as normal.
      c.mmu.write32(ALARM_HEAD,0x11112222u+trial);
      c.mmu.write32(ALARM_HEAD+4u,0x33334444u+trial);
      c.mmu.write32(SHUTDOWN_HEAD,0u);
      c.mmu.write32(SHUTDOWN_TAIL,0u);
      c.mmu.write32(SHUTDOWN_NODE,0xFACA0000u+trial);
      c.mmu.write32(SHUTDOWN_NODE+4u,100u+trial);
      c.mmu.write32(SHUTDOWN_NODE+8u,0xAACA0000u+trial);
      c.mmu.write32(SHUTDOWN_NODE+12u,0xBBCA0000u+trial);
      // The former adjacent canary is the genuine DSP image's first word.
      // Reload authenticated bytes instead of replacing them with a canary.
      for(unsigned i=0;i<DSP_SIZE;++i)c.mmu.write8(DSP_SRC+i,nwii::runtime::dsp_image[i]);
      // Authored per-trial module globals/canaries, verifying the exact
      // three-word owner-original low-memory zeroing without overrun.
      c.mmu.write32(MODULE_PRE,0x6A6A6A6Au);
      c.mmu.write32(0x800030c0u,0xBADD1000u+trial);
      c.mmu.write32(MODULE_LO,0xB0000001u+trial*0x101u);
      c.mmu.write32(MODULE_MID,0xB0000002u+trial*0x101u);
      c.mmu.write32(MODULE_HI,0xB0000003u+trial*0x101u);
      c.mmu.write32(MODULE_POST,0x7B7B7B7Bu);
      // Table begins immediately after the existing 15 exception pointers.
      for(uint32_t i=0;i<128u;++i)
        c.mmu.write8(IRQ_TABLE+i,uint8_t((trial*0x13u+i*7u+3u)&0xffu));
      c.mmu.write8(IRQ_TABLE+128u,0xC5u);
      c.mmu.write32(LOW_MASK_PRE,0x1952A052u);
      c.mmu.write32(LOW_MASK_A,0xAC000001u+trial);
      c.mmu.write32(LOW_MASK_B,0xAC000101u+trial);
      c.mmu.write32(LOW_MASK_POST,0x4952A052u);
      c.mmu.write32(CONTEXT_WORD-4u,0xacce5500u+trial);
      c.mmu.write32(CONTEXT_WORD,0xe58c0000u+trial);
      c.mmu.write32(CONTEXT_WORD+4u,0xd15c0a00u+trial);
    }
    c.mmu.write32(0x80000030u,0u); // no alternate heap override
    c.mmu.write32(0x80000034u,0);
    c.mmu.write32(0x80000044u,0xbadc0ffeu);
    c.mmu.write32(0x80000048u,0xaabbccddu);
    c.mmu.write32(0x80037000u,0xbaadf00du);
    c.mmu.write32(SYNTH_OS_MARKER,0xbaadf00du);
    c.mmu.write32(OS_INIT_FLAG,0u);
    if(owner){
      // Seed only the unused initial stack. The original thread initializer
      // must clear it (including any old nested startup stack frames).
      for(uint32_t a=STACK_BOTTOM+4u;a<THREAD_FRAME;a+=4u)
        c.mmu.write32(a,0xA5A50000u^(a+trial));
      c.mmu.write32(0x800000e4u,0u);
      c.mmu.write32(0x800000e0u,0xC0FFEE00u+trial);
    }
    const auto before_inst=c.inst_count;
    bool exception_stop=false;
    if(owner){
      try{run_game(c);}catch(const ExceptionStop&){exception_stop=true;}
      check(exception_stop,"exception initialization did not reach exact test-only syscall");
    }else run_game(c);
    if(nwii::runtime::observed_stop_pc!=(owner?POST_OWNER:POST_SYNTH) || c.is_running){std::cerr<<std::hex<<"V26 TRACE PC="<<c.pc<<" LR="<<c.lr<<" r1="<<c.gpr[1]<<" r5="<<c.gpr[5]<<" r6="<<c.gpr[6]<<" r7="<<c.gpr[7]<<" r14="<<c.gpr[14]<<" r15="<<c.gpr[15]<<" running="<<c.is_running<<std::dec<<" dbentries="<<nwii::runtime::db_entries<<" stops="<<nwii::runtime::post_stops<<" inst="<<c.inst_count<<"\n";}
    check(!c.is_running && nwii::runtime::observed_stop_pc==(owner?POST_OWNER:POST_SYNTH),
          "native syscall callback did not observe exact test-only PowerPC instruction PC");
    check(c.lr==(owner?OS_RET_OWNER:OS_RET_SYNTH),"guest LR after original time/interrupt service changed");
     if(owner){
       // Earlier V68 end-state checks remain in the unmodified V68 runner.
       // IPC uses new stack frames, small-data globals, and IRQ slots.
       check(nwii::runtime::ipc69_active&&nwii::runtime::ipc69_step==9u&&
             nwii::runtime::db_entries==before_db+1u&&nwii::runtime::os_entries==before_os+1u,
             "continuous startup did not execute original IPC client");
       nwii::runtime::verify_arena_bytes(c,1u);nwii::runtime::verify_arena_bytes(c,2u);
       check(c.guest_dcbz_trace.count==nwii::runtime::expected_zero_lines(2u)&&
             c.bat_write_count==expected_bat_writes.size()&&
             c.mmu.read32(IPC_LO_GLOBAL)==ipc_lo&&c.mmu.read32(IPC_HI_GLOBAL)==ipc_hi&&
             c.mmu.read32(IPC_LO_INPUT)==ipc_lo&&c.mmu.read32(IPC_HI_INPUT)==ipc_hi&&
             c.mmu.read32(OS_INIT_FLAG)==1u&&c.mmu.read32(STACK_BOTTOM)==STACK_MAGIC&&
             c.mmu.read32(sp-4u)==START_OS_RET_OWNER&&c.mmu.read32(sp-8u)==0xffffffffu,
             "IPC client disturbed earlier arena, BAT, OS buffer, or startup stack state");
       check(nwii::runtime::unexpected_mmio==0u&&c.inst_count>before_inst+100u,
             "IPC client unexpected hardware access or no native progress");
       continue;
     }
    check(nwii::runtime::db_entries==before_db+1,"translated DBInit not entered exactly once");
    check(nwii::runtime::os_entries==before_os+1,"translated OSInit prefix never entered");
    check(nwii::runtime::save_entries==before_save+(owner?2u:1u),"original nested GPR-save helper call count differs");
    check(c.mmu.read32(sp-4)==(owner?START_OS_RET_OWNER:START_OS_RET_SYNTH),
          "OSInit prologue failed to save caller LR");
    // Original OSExceptionInit has returned after restoring its own 64-byte
    // frame. The OSInit frame itself is still live at this bounded checkpoint.
    const auto current_frame=sp-8u-(owner?80u:96u);
    check(c.gpr[1]==current_frame,"OSInit guest frame pointer changed");
    if(owner){
      check(nwii::runtime::time_entries==before_time+13, "original OS time service was not called");
      check(nwii::runtime::gettime_entries==before_gettime+13, "original OS timebase helper missing");
      check(nwii::runtime::disable_entries==before_disable+60, "original system-time and IRQ interrupt-disable helpers missing");
      check(nwii::runtime::restore_entries==before_restore+59,
            "original time and IRQ restore interrupt functions missing");
       check(nwii::runtime::irq_restore_entries==before_irq_restore+1u,
             "owner-original IRQ restore BL not called once");
       check(nwii::runtime::irq_setexc_entries==before_irq_setexc+1u,
             "owner-original IRQ handler-vector 4 setter not called once");
       check(nwii::runtime::context_entries==before_context+1u &&
             nwii::runtime::context_setexc_entries==before_context_setexc+1u &&
             nwii::runtime::context_debug_entries==before_context_debug+1u,
             "original Wii OSContextInit handler/debug native calls differ");
       check(c.mmu.read32(CONTEXT_WORD)==0u,
             "genuine original Wii OSContextInit did not clear low-memory context");
       check(c.mmu.read32(CONTEXT_WORD-4u)==THREAD&&
             c.mmu.read32(CONTEXT_WORD+4u)==THREAD&&
             c.mmu.read32(0x800000e0u)==THREAD&&c.mmu.read32(0x800000e4u)==THREAD,
             "original thread init did not install current context/thread and active queue");
       check(nwii::runtime::thread_entries==before_thread+1u&&
             nwii::runtime::thread_clear_entries==before_thread_clear+2u&&
             nwii::runtime::thread_context_entries==before_thread_context+1u&&
             nwii::runtime::thread_callback_entries==before_thread_callback+1u&&
             nwii::runtime::thread_sp_entries==before_thread_sp+1u,
             "original thread context/indirect callback dependency count differs");
       std::array<uint8_t,1048> expected_thread{};
       auto thread_word=[&](unsigned off,uint32_t v){
         for(unsigned i=0;i<4;++i)expected_thread[off+i]=uint8_t(v>>(24u-8u*i));
       };
       thread_word(712u,0x00020001u);thread_word(720u,16u);thread_word(724u,16u);
       thread_word(728u,0xffffffffu);thread_word(772u,ORIGINAL_SP);thread_word(776u,STACK_BOTTOM);
       for(unsigned i=0;i<expected_thread.size();++i)
         check(c.mmu.read8(THREAD+i)==expected_thread[i],
               "original default thread context or scheduler queue byte differs");
       check(c.mmu.read32(STACK_BOTTOM)==STACK_MAGIC&&
             c.mmu.read32(AUDIO_FRAME)==ORIGINAL_SP-8u-80u,
             "original stack sentinel or audio frame backchain differs");
       for(uint32_t a=STACK_BOTTOM+4u;a<RESET_FRAME;a+=4u)
         check(c.mmu.read32(a)==0u,"audio reset overwrote inactive initial thread stack");
       check(nwii::runtime::audio_entries==before_audio+1u&&
             nwii::runtime::reset_entries==before_audio_reset+1u&&
             nwii::runtime::wait_index==5u&&nwii::runtime::audio_read_count==6u&&
             nwii::runtime::audio_write_count==6u,
             "original audio clock/reset helper did not return after all five waits");
       check(nwii::runtime::dsp_arena_entries==before_dsp_arena+2u&&
             nwii::runtime::dsp_copy_entries==before_dsp_copy+3u&&
             nwii::runtime::dsp_flush_entries==before_dsp_flush+1u&&
             nwii::runtime::sc_entries==before_sc+3u&&
             nwii::runtime::sc_vector_entries==before_sc_vector+3u,
             "original DSP staging/SC native dependencies did not execute exactly once");
       check(nwii::runtime::mi_entries==before_mi+1u&&nwii::runtime::mi_map_entries==before_mi_map+1u&&
             nwii::runtime::mi_shutdown_entries==before_mi_shutdown+1u&&nwii::runtime::mi_unmask_entries==before_mi_unmask+1u&&
             nwii::runtime::mi_hid_reads==before_hid_read+1u&&nwii::runtime::mi_hid_writes==before_hid_write+1u,
             "original memory protection dependency count differs");
       std::array<uint32_t,32> bat_expected{};
       for(unsigned i=0;i<bat_expected.size();++i)bat_expected[i]=0xbeef0000u+i+trial*32u;
       check(c.bat_write_count==expected_bat_writes.size(),"original BAT write count differs");
       for(unsigned i=0;i<expected_bat_writes.size();++i){
         auto [spr,val]=expected_bat_writes[i];
         check(c.bat_write_sprs[i]==spr&&c.bat_write_values[i]==val,"original ordered BAT SPR write differs");
         bat_expected[c.bat_index(spr)]=val;
       }
       check(c.bat_registers==bat_expected&&c.srr0==0x805222ecu&&(c.srr1&0x30u)==0x30u,
             "original final BAT registers or second rfi return differs");
       check(nwii::runtime::dsp.complete()&&nwii::runtime::dsp_wait_finished,
             "original DSP device did not finish both DMA transfers and resets");
       for(unsigned i=0;i<64u;++i)
         check(nwii::runtime::aram[i]==(i<32u?nwii::runtime::dsp_image[i]:0xa7u),
               "DSP ARAM DMA bytes or untouched neighboring bytes differ");
       for(unsigned i=0;i<DSP_SIZE;++i)
         check(c.mmu.read8(DSP_STAGING+i)==nwii::runtime::dsp_original_ram[i]&&
               c.mmu.read8(DSP_SRC+i)==nwii::runtime::dsp_image[i]&&
               c.mmu.read8(DSP_BACKUP+i)==0u,
               "original DSP staging or preserved RAM backup differs");
       check(c.mmu.read8(DSP_STAGING-1u)==0xa1u&&c.mmu.read8(DSP_STAGING+DSP_SIZE)==0xb2u&&
             c.mmu.read8(DSP_BACKUP-1u)==0u&&c.mmu.read8(DSP_BACKUP+DSP_SIZE)==0xb2u,
             "original DSP scratch and subsequent arena clear canaries differ");
       nwii::runtime::verify_arena_bytes(c,1u);nwii::runtime::verify_arena_bytes(c,2u);
       check(c.guest_dcbz_trace.count==nwii::runtime::expected_zero_lines(2u)&&
             c.guest_dcbz_trace.first==M1_ARENA_LO(trial)&&c.guest_dcbz_trace.last==M2_ARENA_HI-32u,
             "original dcbz first/last/count differs across both guest arenas");
       check(c.mmu.read32(0x8000301cu)==CONTEXT_HANDLER,
             "original Wii exception handler 7 was not installed");
      check(nwii::runtime::time_global_checks==before_time_global+1,
            "original time was not stored before the second interrupt call");
      check(nwii::runtime::exec_entries==before_exec+1,
            "original __OSGetExecParams function was not entered");
      for(unsigned i=0;i<before_hardware.size();++i)
        check(nwii::runtime::hardware_entries[i]==before_hardware[i]+1,
              "original HID4/speculation/FP helper execution count changed");
      check(c.hid4==0x83900000u,"authentic OSInit HID4 value was not written");
      check(c.gpr[13]==R13,"original continuous startup r13 small-data base differs");
      // r3 is a PowerPC caller-saved register. The cache helpers may
      // overwrite it; verify their actual line operations and memory bounds
      // below instead of asserting a post-call register value.
      check(nwii::runtime::syscall_entries==before_syscall+1u,
            "original __OSInitSystemCall was not dispatched exactly once");
      check(nwii::runtime::alarm_entries==before_alarm+1u &&
            nwii::runtime::alarm_get_entries==before_alarm_get+1u &&
            nwii::runtime::alarm_set_entries==before_alarm_set+1u &&
            nwii::runtime::shutdown_entries==before_shutdown+1u,
            "original Wii alarm/exception/shutdown native function dispatch count differs");
      check(nwii::runtime::module_entries==before_module+1u,
            "genuine Wii __OSModuleInit native dispatch not observed exactly once");
      check(nwii::runtime::irq_entries==before_irq+1u &&
            nwii::runtime::irq_memset_entries==before_irq_memset+1u &&
            nwii::runtime::irq_fill_entries==before_irq_fill+1u,
            "native __OSInterruptInit/memset/__fill_mem dispatch counts differ");
      check(nwii::runtime::irq_disable_entries==before_irq_disable+1u,
            "original IRQ interrupt-disable PPC helper not entered exactly once");
      // The genuine __OSInterruptInit mask loop calls SetInterruptMask once
      // for each of seven controller mask banks. Independently confirmed by
      // owner-private direct-entry V55/V56 tests.
      check(nwii::runtime::setmask_entries==before_setmask+9u,
            "owner-original SetInterruptMask not dispatched seven times");
      check(c.mmu.read32(IRQ_GLOBAL)==IRQ_TABLE,
            "original Wii __OSInterruptInit failed to install IRQ table pointer");
      check(c.gpr[29]==0u && c.gpr[30]==0x806f4f00u &&
            c.gpr[31]==0x8060b7a8u,
            "original EXIInit return failed to restore OSInit nonvolatile registers");
      check(c.mmu.read32(LOW_MASK_A)==0xF7FFF7F0u &&
            c.mmu.read32(LOW_MASK_B)==0u,
            "original Wii IRQ mask state computation wrote unexpected low-memory words");
      check(c.mmu.read32(LOW_MASK_PRE)==(THREAD&0x3fffffffu) &&
            c.mmu.read32(LOW_MASK_POST)==0x4952A052u,
            "original interrupt low-memory masking overran surrounding canaries");
      const std::array<std::pair<uint32_t,uint32_t>,57> expected_writes{{
        {0x0c003004u,0xf0u},{0x0d000034u,0x40000000u},
        {0x0c00401cu,0u},{0x0c00500au,0xf607u},
        {0x0d006c00u,0x12345650u},{0x0d006800u,0x98765030u},
        {0x0d006814u,0xaabbc0d0u},{0x0d006828u,0xdeadbee0u},
        {0x0c003004u,0xf0u},
        {0x0d006800u,0u},{0x0d006814u,0u},
        {0x0d006828u,0u},{0x0d006800u,0x2000u},
        {ExiIdTestDevice::CSR,0x200u},{ExiIdTestDevice::DATA,0u},
        {ExiIdTestDevice::CR,0x15u},{ExiIdTestDevice::CR,0x31u},
        {ExiIdTestDevice::CSR,0u},
        {0x0d006430u,nwii::runtime::si_expected},
        {0x0d006434u,0x80000000u},{0x0c003004u,0xf8u},
        {0x0d006438u,0x0f000000u},{0x0d006480u,0u},{0x0d006434u,0xc0010301u},
        {ExiSramTestDevice::CSR,0x130u},{ExiSramTestDevice::DATA,0x20000100u},
        {ExiSramTestDevice::CR,0x35u},{ExiSramTestDevice::MAR,SRAM},
        {ExiSramTestDevice::LEN,64u},{ExiSramTestDevice::CR,3u},{ExiSramTestDevice::CSR,0u},
        audio_writes_expected[0],audio_writes_expected[1],audio_writes_expected[2],
        audio_writes_expected[3],audio_writes_expected[4],audio_writes_expected[5],
        {DspBootDevice::INFO,0x43u},{DspBootDevice::CONTROL,0x8acu},
        {DspBootDevice::CONTROL,0x805u},{DspBootDevice::CPU_MAIL,0u},
        {DspBootDevice::DMA_SOURCE,0x01000000u},{DspBootDevice::DMA_DEST,0u},
        {DspBootDevice::DMA_COUNT,32u},{DspBootDevice::CONTROL,0x824u},
        {DspBootDevice::DMA_SOURCE,0x01000000u},{DspBootDevice::DMA_DEST,0u},
        {DspBootDevice::DMA_COUNT,32u},{DspBootDevice::CONTROL,0x824u},
        {DspBootDevice::CONTROL,4u},{DspBootDevice::CONTROL,0u},
        {DspBootDevice::CONTROL,4u},{DspBootDevice::CONTROL,0x8acu},{DspBootDevice::CONTROL,0x805u},
        {0x0c004020u,0u},{0x0c004010u,255u},{0x0c00401cu,16u}
      }};
      constexpr std::array<std::pair<uint32_t,uint32_t>,5> expected_reads{{
        {0x0c00500au,0xf7f7u},{0x0d006c00u,0x12345678u},
        {0x0d006800u,0x98765432u},{0x0d006814u,0xaabbccddu},
        {0x0d006828u,0xdeadbeefu}
      }};
      check(nwii::runtime::mmio_writes.size()==before_mmio+expected_writes.size(),
            "original SetInterruptMask native MMIO write count differs");
      std::vector<std::pair<uint32_t,uint32_t>> transfer_reads{{ExiIdTestDevice::CSR,0x2000u}};
      for(unsigned i=0;i<trial%4u;++i)transfer_reads.emplace_back(ExiIdTestDevice::CR,0x15u);
      transfer_reads.emplace_back(ExiIdTestDevice::CR,0x14u);
      transfer_reads.emplace_back(ExiIdTestDevice::HWREV,1u);
      for(unsigned i=0;i<(trial/4u)%4u;++i)transfer_reads.emplace_back(ExiIdTestDevice::CR,0x31u);
      transfer_reads.emplace_back(ExiIdTestDevice::CR,0x30u);
      transfer_reads.emplace_back(ExiIdTestDevice::DATA,nwii::runtime::response_id);
      transfer_reads.emplace_back(ExiIdTestDevice::HWREV,1u);
      transfer_reads.emplace_back(ExiIdTestDevice::CSR,0x200u);
      transfer_reads.emplace_back(ExiIdTestDevice::CSR,0u);
      transfer_reads.emplace_back(ExiIdTestDevice::CSR+20u,0u);
      transfer_reads.emplace_back(0x0c00206cu,trial&1u);
      for(unsigned n=0;n<trial%4u;++n)transfer_reads.emplace_back(0x0d006434u,1u);
      transfer_reads.emplace_back(0x0d006434u,0u);
      transfer_reads.emplace_back(0x0d006438u,0x0f123456u);
      transfer_reads.emplace_back(0x0d006434u,0u);
      transfer_reads.emplace_back(ExiSramTestDevice::CSR,0u);
      for(unsigned n=0;n<trial%4u;++n)transfer_reads.emplace_back(ExiSramTestDevice::CR,0x35u);
      transfer_reads.emplace_back(ExiSramTestDevice::CR,0x34u);
      transfer_reads.emplace_back(ExiSramTestDevice::REV,1u);
      for(unsigned n=0;n<(trial/4u)%4u;++n)transfer_reads.emplace_back(ExiSramTestDevice::CR,3u);
      transfer_reads.emplace_back(ExiSramTestDevice::CR,2u);
      transfer_reads.emplace_back(ExiSramTestDevice::REV,1u);
      transfer_reads.emplace_back(ExiSramTestDevice::CSR,0x130u);
      transfer_reads.insert(transfer_reads.end(),audio_reads_expected.begin(),audio_reads_expected.end());
      using D=DspBootDevice;
      auto dr=[&](uint32_t reg,uint32_t v){transfer_reads.emplace_back(reg,v);};
      dr(D::CONTROL,0x804u);
      for(unsigned i=0;i<trial%4u;++i)dr(D::CONTROL,0x805u);
      dr(D::CONTROL,0x804u);
      if(trial&1u){dr(D::MAIL_H,0x8000u);dr(D::MAIL_L,0u);}
      dr(D::MAIL_H,0u);dr(D::MAIL_L,0u);
      for(unsigned dma=0;dma<2;++dma){
        for(unsigned i=0;i<(dma?trial%4u:(trial/4u)%4u);++i)dr(D::CONTROL,0xa04u);
        dr(D::CONTROL,0x824u);
      }
      dr(D::CONTROL,0x804u);
      for(unsigned i=0;i<trial%4u;++i)dr(D::CONTROL,0x404u);
      dr(D::CONTROL,4u);dr(D::CONTROL,4u);
      for(unsigned i=0;i<(trial/4u)%4u;++i)dr(D::MAIL_H,0u);
      dr(D::MAIL_H,0x8123u);dr(D::MAIL_L,0x4567u);
      dr(D::CONTROL,0u);dr(D::CONTROL,0x804u);
      for(unsigned i=0;i<(trial/4u)%4u;++i)dr(D::CONTROL,0x805u);
      dr(D::CONTROL,0x804u);
      transfer_reads.emplace_back(0x0c003024u,0x100u+trial*8u);
      transfer_reads.emplace_back(0x0c003024u,0x100u+trial*8u);
      const size_t transfer_at=before_mmio_reads+expected_reads.size()+nwii::runtime::exi_reads.size();
      check(nwii::runtime::mmio_reads.size()==transfer_at+transfer_reads.size(),
            "original EXI ID immediate read count differs");
      for(size_t i=0;i<transfer_reads.size();++i)
        check(nwii::runtime::mmio_reads.at(transfer_at+i)==transfer_reads[i],
              "original EXI ID MMIO read order/value differs");
      for(size_t i=0;i<expected_writes.size();++i)
        check(nwii::runtime::mmio_writes.at(before_mmio+i)==expected_writes[i],
              "original SetInterruptMask MMIO write destination/value/order differs");
      for(size_t i=0;i<expected_reads.size();++i)
        check(nwii::runtime::mmio_reads.at(before_mmio_reads+i)==expected_reads[i],
              "original SetInterruptMask MMIO read destination/value/order differs");
      check(nwii::runtime::exi_entries==before_exi+1u,
            "continuous original OSInit did not enter EXIInit exactly once");
      check(nwii::runtime::mask_entries==before_mask+6u &&
            nwii::runtime::mask_disable_entries==before_mask_disable+6u &&
            nwii::runtime::mask_restore_entries==before_mask_restore+6u,
            "native EXI did not execute original mask and interrupt-state helpers once");
      check(c.mmu.read32(LOW_MASK_A)==0xf7fff7f0u &&
            c.mmu.read32(LOW_MASK_B)==0u,
            "original EXI mask helper corrupted earlier startup IRQ masks");
      check(nwii::runtime::id_device.complete()&&
            nwii::runtime::probe_entries==before_probes+2u&&
            nwii::runtime::version_entries==before_versions+1u&&
            nwii::runtime::version_report_entries==before_version_reports+1u&&
            nwii::runtime::probe_channel==2u,
            "original EXIInit did not finish both probes and version registration");
      check(nwii::runtime::id_entries==before_id+3u &&
            c.mmu.read32(ID_CACHE)==nwii::runtime::response_id,
            "original EXISync failed to copy hardware-provided ID to guest cache");
      check(nwii::runtime::lock_entries==before_locks+2u&&
            nwii::runtime::select_entries==before_selects+2u&&
            nwii::runtime::imm_entries==before_imms+3u&&
            nwii::runtime::sync_entries==before_syncs+4u&&
            nwii::runtime::deselect_entries==before_deselects+2u&&
            nwii::runtime::irqmask_entries==before_irqmasks+4u&&
            nwii::runtime::revision_entries==before_revisions+4u,
            "original EXI ID transaction dependencies did not execute exact call counts");
      check(c.mmu.read32(0x806f156cu)==0u&&c.mmu.read32(0x806f1570u)==0u&&
            c.mmu.read32(0x806f1574u)==nwii::runtime::sram_command_ptr&&c.mmu.read32(0x806f1578u)==1u,
            "original SRAM EXI transfer metadata or final unlocked state differs");
      check(nwii::runtime::sram_entries==before_sram+1u&&nwii::runtime::sram_dma_entries==before_sram_dma+1u&&
            nwii::runtime::sram_invalidate_entries==before_sram_cache+1u&&nwii::runtime::sram_unlock_entries==before_sram_unlock+1u&&
            nwii::runtime::sram_config_unlock_entries==before_sram_cfg+2u&&nwii::runtime::sram_device.complete(),
            "original SRAM initialization did not finish each read-only dependency");
      for(unsigned i=0;i<64u;++i)
        check(c.mmu.read8(SRAM+i)==nwii::runtime::sram_device.bytes[i],
              "original SRAM DMA buffer differs from supplied device payload");
      check(c.mmu.read32(SRAM+64u)==64u&&c.mmu.read32(SRAM+68u)==0u&&
            c.mmu.read32(SRAM+72u)==0u&&c.mmu.read32(SRAM+76u)==1u,
            "original SRAM size, interrupt state, unlocked flag or read result differs");
      check(nwii::runtime::si_entries==before_si+1u&&
            nwii::runtime::si_rate_entries==before_si_rate+1u&&
            nwii::runtime::si_tv_entries==before_si_tv+1u&&
            nwii::runtime::si_xy_entries==before_si_xy+1u&&
            nwii::runtime::si_handler_entries==before_si_handler+1u&&
            nwii::runtime::si_unmask_entries==before_si_unmask+1u&&
            nwii::runtime::si_version_entries==before_si_version+1u&&
            nwii::runtime::si_report_entries==before_si_report+1u&&
            nwii::runtime::si_phase==6u&&nwii::runtime::si_polls==trial%4u+1u,
            "original SI sampling and interrupt dependency calls differ");
      check(c.mmu.read32(R13-3136u)==0u&&c.mmu.read32(R13-3148u)==1u&&
            c.mmu.read32(SI_DATA+4u)==nwii::runtime::si_expected&&
            c.mmu.read32(SI_DATA)==0u&&c.mmu.read32(SI_DATA+8u)==3u&&
            c.mmu.read32(SI_DATA+12u)==TYPE_DATA&&c.mmu.read32(SI_DATA+16u)==TYPE_CALLBACK,
            "original SIInit did not set init flag, active channel or transfer metadata");
      check(nwii::runtime::si_type_entries==before_si_types+4u&&
            nwii::runtime::si_transfer_entries==before_si_transfers+4u&&
            nwii::runtime::si_start_entries==before_si_starts+4u&&
            nwii::runtime::si_channel==4u&&nwii::runtime::si_read_phase==2u,
            "original SI type/transfer calls or first hardware transaction counts differ");
      for(unsigned i=0;i<4u;++i){
        const auto slot=SLOT+32u*i;
        check(c.mmu.read32(TYPE_DATA+4u*i)==128u&&
              c.mmu.read64(TYPE_TIME+8u*i)==nwii::runtime::si_type_times[i]&&
              c.mmu.read64(SLOT+128u+8u*i)==0u,
              "original SI type status, time or last transfer timestamp differs");
        if(i==0u){
          check(c.mmu.read32(slot)==0xffffffffu,
                "original immediate channel-zero transfer was incorrectly queued");
          for(uint32_t n=4;n<32;n+=4)
            check(c.mmu.read32(slot+n)==0u,"immediate channel-zero packet slot polluted");
        }else{
          const std::array<uint32_t,8> packet{{i,SI_COMMAND,1u,TYPE_DATA+4u*i,3u,
            TYPE_CALLBACK,0u,TYPE_DELAY}};
          for(unsigned n=0;n<packet.size();++n)
            check(c.mmu.read32(slot+4u*n)==packet[n],
                  "original SI queued controller packet or requested fire time differs");
        }
      }
      check(nwii::runtime::handler_entries==before_handlers+8u,
            "original EXIInit did not register exactly eight Wii interrupt handlers");
      std::array<unsigned,3> pending=(trial%6u==2u)?
          std::array<unsigned,3>{1u,1u,2u}:
          (trial%6u==4u?std::array<unsigned,3>{0u,0u,1u}:
                         std::array<unsigned,3>{0u,0u,0u});
      constexpr std::array<uint32_t,3> exi_registers{
          0x0d00680cu,0x0d006820u,0x0d006834u};
      std::vector<std::pair<uint32_t,uint32_t>> expected_exi;
      for(unsigned spins=0;spins<16u;++spins){
        bool retry=false;
        for(size_t i=0;i<exi_registers.size();++i){
          const bool busy=pending[i]>0u;
          if(busy)--pending[i];
          expected_exi.emplace_back(exi_registers[i],
                                    0x2000u+uint32_t(i)*0x10u+(busy?1u:0u));
          if(busy){retry=true;break;}
        }
        if(!retry)break;
      }
      check(nwii::runtime::exi_busy==std::array<unsigned,3>{0u,0u,0u},
            "EXI polling did not drain explicit synthetic busy schedule");
      check(nwii::runtime::exi_reads==expected_exi,
            "original EXI polling read order or supplied status values differ");
      for(size_t i=0;i<expected_exi.size();++i)
        check(nwii::runtime::mmio_reads[before_mmio_reads+expected_reads.size()+i]==expected_exi[i],
              "integrated EXI status read not preserved in MMIO transaction history");
      check(nwii::runtime::unexpected_mmio==0u,
            "unplanned Wii MMIO access occurred during startup");
      check(c.mmu.read32(0x8000303cu)==0xDEADBEEFu &&
            c.mmu.read32(IRQ_TABLE+128u)==0u,
            "original EXI probes failed to clear aliased timestamp or changed IRQ lower canary");
      constexpr std::array<uint32_t,8> expected_irq_handlers{{
        0x804ef61cu,0x804ef6d4u,0x804ef8ecu,0x804ef61cu,
        0x804ef6d4u,0x804ef8ecu,0x804ef61cu,0x804ef6d4u}};
      for(uint32_t i=0;i<128u;++i){
        const uint32_t vector=i/4u;
        const uint32_t value=(vector>=9u && vector<17u)?
            expected_irq_handlers[vector-9u]:(vector<5u?MI_HANDLER:(vector==20u?0x80531b34u:0u));
        const uint8_t expected=uint8_t(value>>(24u-8u*(i%4u)));
        check(c.mmu.read8(IRQ_TABLE+i)==expected,
              "original EXI handler register wrote unexpected IRQ table bytes");
      }
      check(c.mmu.read32(MODULE_LO)==0u &&
            c.mmu.read32(MODULE_MID)==0u &&
            c.mmu.read32(MODULE_HI)==0u,
            "original Wii module initializer failed to clear three low-memory globals");
      check(c.mmu.read32(MODULE_PRE)==0u &&
            c.mmu.read32(0x800030c0u)==0u &&
            c.mmu.read32(MODULE_POST)==0x7B7B7B7Bu,
            "original Wii module initializer corrupted neighboring low memory");
      check(nwii::runtime::dcflush_entries==before_dcflush+16u,
            "original exception/syscall DCFlushRangeNoSync not dispatched sixteen times");
      check(nwii::runtime::icinvalid_entries==before_icinvalid+16u,
            "original exception/syscall ICInvalidateRange not dispatched sixteen times");
      check(c.guest_flush_count==87u+2u*FLUSH_LINES && c.guest_invalidate_count==83u,
            "original exception/syscall guest cache-operation counts differ");
      check(c.guest_sync_count-nwii::runtime::cache_sync_entry==35u &&
            c.guest_isync_count-nwii::runtime::cache_isync_entry==35u,
            "original exception/syscall PPC sync/isync ordering differs");
      check(c.guest_flush_lines.size()>=83u &&
            c.guest_invalidate_lines.size()>=83u,
            "native guest cache trace cannot hold 83 original lines");
      for(uint32_t i=0;i<75u;++i){
        const uint32_t vector=i/5u,line=i%5u;
        const uint32_t pc=VECTOR_DEST+vector*0x100u+line*32u;
        check(c.guest_flush_lines[i]==pc,
              "original Wii 15-vector data-cache line ordering incorrect");
        check(c.guest_invalidate_lines[i]==pc,
              "original Wii 15-vector instruction-cache ordering incorrect");
      }
      for(uint32_t line=0;line<8u;++line){
        const uint32_t addr=SYSCALL_DEST+32u*line;
        check(c.guest_flush_lines[75u+line]==addr,
              "original syscall data-cache flush line ordering incorrect");
        check(c.guest_invalidate_lines[75u+line]==addr,
              "original syscall instruction-cache line ordering incorrect");
      }
      for(unsigned i=0;i<4u;++i)
        check(c.guest_flush_lines[83u+i]==DSP_STAGING+32u*i,"original DSP cache flush line differs");
      check(c.guest_last_flush==M2_ARENA_HI-32u &&
            c.guest_last_invalidate==SYSCALL_DEST+0xe0u,
            "original Wii last syscall cache-maintenance line differs");
      check(c.ctr==0u,"original arena flush CTR loop did not exhaust counter");
      check(nwii::runtime::marker_entries==before_marker+15u,
            "authentic __DBIsExceptionMarked not dispatched for every vector");
      check(nwii::runtime::exception_restore_entries==before_exception_restore+1u,
            "original Wii _restgpr_20 was not executed exactly once");
      check(c.gpr[29]==0u&&c.gpr[31]==0x8060b7a8u,
            "EXI epilogue failed to restore the OSInit caller's GPRs");
      check(c.mmu.read32(R13-3552u)==0x80003000u,
            "original Wii exception handler-table global was not installed");
      check(c.mmu.read32(0x8070d8a0u)==0x80000040u &&
            c.mmu.read32(0x80000044u)==0u,
            "original debug marker pointer or zero mask changed");
      check(c.mmu.read32(EXC_TEMPLATE_DST)==0x60000000u,
            "original PPC template clearing loop did not store exactly one NOP");
      check(c.mmu.read32(EXC_TEMPLATE_DST-4u)==0x42434342u &&
            c.mmu.read32(EXC_TEMPLATE_DST+4u)==0x47494947u,
            "original PPC template-clearing loop corrupted neighboring canaries");
      check(nwii::runtime::exception_entries==before_exception+1,
            "genuine OSExceptionInit original entry not reached exactly once");
      check(nwii::runtime::exception_epilogue_debug_entries==before_terminal_debug+1u,
            "V51 original OSExceptionInit terminal DBPrintf BL callback not observed once");
      check(nwii::runtime::external_stubs[0]>=before_stubs[0]+2u,
            "V51 no bounded DBPrintf callback observed during native startup");
      check(c.gpr[28]==0u && c.gpr[27]==0u,
            "original Wii _restgpr_20 did not restore caller r27/r28");
      check(c.mmu.read32(0x80000060u)==1u+trial,
            "exception source low-memory branch flag changed");
      std::vector<uint8_t> expected_handler=original_handler;
      auto expected_word=[&](uint32_t pc,uint32_t value){
        check(pc>=SOURCE_TEMPLATE && uint64_t(pc)+4u<=uint64_t(SOURCE_TEMPLATE)+VECTOR_LEN,
              "original handler test oracle word outside private template");
        const uint32_t offset=pc-SOURCE_TEMPLATE;
        for(unsigned j=0;j<4;++j)
          expected_handler[offset+j]=uint8_t(value>>(24u-8u*j));
      };
      expected_word(EXC_TEMPLATE_DST-4u,0x42434342u);
      expected_word(EXC_TEMPLATE_DST,0x60000000u);
      expected_word(EXC_TEMPLATE_DST+4u,0x47494947u);
      check(c.mmu.read8(VECTOR_DEST-1u)==0xB6u &&
            c.mmu.read8(VECTOR_DEST+VECTOR_LEN)==0xB7u,
            "original exception-vector memcpy overwrote neighboring guest memory");
      for(uint32_t i=0;i<VECTOR_LEN;++i)
        check(c.mmu.read8(SOURCE_TEMPLATE+i)==expected_handler[i],
              "original Wii handler source template changed across vector loop");
      check(c.mmu.read32(EXC_SOURCE_WORD)==exception_word,
            "original exception-vector template word not restored after loop");
      for(uint32_t vector=0;vector<15u;++vector){
        const uint32_t dest=VECTOR_DEST+vector*0x100u;
        check(c.mmu.read32(0x8060bbe0u+4u*vector)==0x100u+vector*0x100u,
              "original exception vector offset test inputs were overwritten");
        check(c.mmu.read8(dest-1u)==0xB6u &&
              c.mmu.read8(dest+VECTOR_LEN)==0xB7u,
              "original Wii exception-vector copy crossed canary memory");
        check(c.mmu.read32(0x80003000u+vector*4u)==
                (vector==4u?0x80526ce0u:(vector==7u?CONTEXT_HANDLER:(vector==8u?ALARM_HANDLER:0x80520f5cu))),
              "original __OSInitAlarm exception-vector dispatch table entry incorrect");
        for(uint32_t i=0;i<VECTOR_LEN;++i){
          uint8_t expected=expected_handler[i];
          constexpr uint32_t MARK_OFFSET=EXC_SOURCE_WORD-SOURCE_TEMPLATE;
          if(i>=MARK_OFFSET && i<MARK_OFFSET+4u)
            expected=uint8_t((exception_word|vector)>>(24u-8u*(i-MARK_OFFSET)));
          if(vector==11u && i<SYSCALL_LEN)
            expected=original_syscall[i]; // original syscall vector overlays handler 11
          check(c.mmu.read8(dest+i)==expected,
                "native original Wii vector differs from owner-original handler template");
        }
      }
      check(c.mmu.read32(0x8000303cu)==0xDEADBEEFu,
            "original Wii exception handler table wrote a sixteenth entry");
      check(c.mmu.read32(ALARM_HEAD)==0u &&
            c.mmu.read32(ALARM_HEAD+4u)==0u,
            "original __OSInitAlarm failed to reset its alarm list head");
      check(c.mmu.read32(SHUTDOWN_HEAD)==SHUTDOWN_NODE &&
            c.mmu.read32(SHUTDOWN_TAIL)==MI_NODE&&
            c.mmu.read32(MI_NODE+8u)==0u&&c.mmu.read32(MI_NODE+12u)==SHUTDOWN_NODE&&
            c.mmu.read32(MI_NODE)==0x80527040u&&c.mmu.read32(MI_NODE+4u)==127u&&
            c.mmu.read32(MI_NODE-4u)==0xa1a1a1a1u&&c.mmu.read32(MI_NODE+16u)==0xb2b2b2b2u,
            "original Wii alarm shutdown callback was not registered");
      check(c.mmu.read32(SHUTDOWN_NODE+8u)==MI_NODE &&
            c.mmu.read32(SHUTDOWN_NODE+12u)==0u &&
            c.mmu.read32(SHUTDOWN_NODE+4u)==100u+trial,
            "original Wii shutdown-list node links/priority incorrect");
      check(c.mmu.read32(SHUTDOWN_NODE)==0xFACA0000u+trial &&
            c.mmu.read32(SHUTDOWN_NODE+16u)==
               ((uint32_t(nwii::runtime::dsp_image[0])<<24)|(uint32_t(nwii::runtime::dsp_image[1])<<16)|
                (uint32_t(nwii::runtime::dsp_image[2])<<8)|nwii::runtime::dsp_image[3]),
            "original shutdown registration overwrote adjacent fields");
      for(uint32_t i=0;i<SYSCALL_LEN;++i){
        check(c.mmu.read8(SYSCALL_DEST+i)==original_syscall[i],
              "native Wii syscall vector byte differs from private owner original");
        check(c.mmu.read8(SYSCALL_SOURCE+i)==original_syscall[i],
              "native Wii syscall-vector source was changed");
      }
      check(c.mmu.read8(SYSCALL_SOURCE-1u)==0xABu &&
            c.mmu.read8(SYSCALL_SOURCE+SYSCALL_LEN)==0xBCu,
            "original syscall handler copy changed adjacent source bytes");
      check(c.mmu.read8(SYSCALL_DEST+VECTOR_LEN)==0xB7u,
            "original syscall handler copy clobbered handler neighbor");
      // After OSExceptionInit returned, the original syscall initializer
      // legitimately reuses this formerly exception-owned LR stack slot.
      // The direct-entry V51 ABI test independently verifies this reuse.
      // The original alarm initializer reuses the 16-byte syscall stack
      // frame and saves the newer OSInit BL return at the same LR slot.
      // The authentic second __OSCacheInit call reuses this former nested LR
      // spill. The independent direct-entry V59 ABI regression corroborates it.
      // Memory protection reuses the original audio function's 16-byte frame.
      check(c.mmu.read32((sp-8u)-76u)==0x80520944u,
            "original boot report prologue saved incorrect caller LR");
      check(c.mmu.read32((sp-8u)-88u)==0x806f4f00u &&
            c.mmu.read32((sp-8u)-84u)==0x8060b7a8u,
            "original exception save helper corrupted OSInit r30/r31");
      check(nwii::runtime::ipc_entries==before_ipc+1,
            "authentic original IPC-buffer initializer not entered exactly once");
      check(c.mmu.read32(IPC_LO_GLOBAL)==ipc_lo &&
            c.mmu.read32(IPC_HI_GLOBAL)==ipc_hi,
            "original IPC-buffer low-memory pointers not copied into OS globals");
      check(c.mmu.read32(IPC_LO_INPUT)==ipc_lo &&
            c.mmu.read32(IPC_HI_INPUT)==ipc_hi,
            "original IPC-buffer initializer changed its input pointer words");
      check(c.mmu.read32(IPC_LO_INPUT-4u)==0xD13ACAFEu &&
            c.mmu.read32(IPC_HI_INPUT+4u)==console_revisions[trial%4u],
            "original IPC helper corrupted adjacent low-memory canaries");
      check(nwii::runtime::arena_entries[0]==before_arena[0]+1 &&
            nwii::runtime::arena_entries[1]==before_arena[1]+1,
            "original MEM1 low/high arena setters were not both executed");
      check(nwii::runtime::mem2_entries[0]==before_mem2[0]+1 &&
            nwii::runtime::mem2_entries[1]==before_mem2[1]+1,
            "authentic MEM2 low/high arena setter entry counts changed");
      check(c.mmu.read32(MEM2_LO_GLOBAL)==mem2_low_hint,
            "original MEM2 low arena global differs");
      check(c.mmu.read32(MEM2_HI_GLOBAL)==mem2_high_hint,
            "original MEM2 high arena global differs");
      check(c.mmu.read32(MEM2_LO_HINT)==mem2_low_hint &&
            c.mmu.read32(MEM2_HI_HINT)==mem2_high_hint,
            "original MEM2 low/high hints were modified");
      check(c.mmu.read32(LO_GLOBAL)==arena_hint,
            "original MEM1 low arena setter ignored low-memory hint");
      check(c.mmu.read32(HI_GLOBAL)==0x81700000u,
            "original MEM1 high arena setter ignored expected fallback");
      check(c.mmu.read32(BOOT_HINT)==arena_hint &&
            c.mmu.read32(0x80003110u)==0u,
            "original low-memory MEM1 arena input hints modified");
      check(c.mmu.read32(BOOT_BASE)==0x80000000u,
            "original low-memory boot base global differs");
      check(c.mmu.read32(BOOT_RECORD)==0u,
            "empty original OS boot info pointer was not cleared");
      check(c.mmu.read32(BOOT_MODE)==1u,
            "original OS boot mode initialized incorrectly");
      check(c.mmu.read32(BOOT_FALLBACK)==0u,
            "empty OS boot fallback global changed");
      check(c.mmu.read32(BOOT_FIELD)==0u,
            "empty OS boot field changed");
      check(c.mmu.read32(0x800000f4u)==0u &&
            c.mmu.read32(0x80000034u)==0u,
            "original low-memory boot input flags changed");
      check((c.hid0 & 0x200u)!=0,"original speculation-disable HID0 bit not set");
      for(unsigned k=0;k<6;++k)
        check(nwii::runtime::perf_entries[k]==before_perf[k]+1,
              "original MMCR/PMC helper was not called exactly once");
      check(c.mmcr0==0u && c.mmcr1==0u,
            "authentic MMCR0/MMCR1 register writes did not execute");
      for(auto reg:c.pmc)
        check(reg==0u, "authentic performance counter write did not execute");
      // Read the two original store instructions from the *private* test DOL,
      // without embedding their instruction words in public source.
      // High/low time-store assertions were checked *before* the B4
      // interrupt helper overwrote r3 and potentially other volatile GPRs.
      check(c.mmu.read32(OS_INIT_FLAG)==1u,"original OS init-once guard flag not set");
      check(c.gpr[25]==0u && c.gpr[21]==0u && c.gpr[23]==0u,
            "original Wii _restgpr_20 did not restore caller r21/r23/r25");
      for(unsigned reg=20;reg<32;++reg){
        const auto spill=c.mmu.read32((sp-8u)-48u+(reg-20u)*4u);
        check(spill==(reg==31?0x80004044u:0u),
              "original _savegpr_20 spilled unexpected preserved GPR state");
      }
      check(c.mmu.read32(0x80000044u)==0,"original startup low-memory clear failed");
      check(c.mmu.read32(0x80000048u)==0x004e5090u,"original DBInit OS debug pointer wrong");
      check(c.mmu.read32(0x8070d8a0u)==0x80000040u,"original DBInit low-memory base wrong");
      check(c.mmu.read32(0x8070d8a4u)==1,"original DBInit initialized flag wrong");
    } else {
      check(c.mmu.read32(0x80037000u)==0x55aau,"synthetic DBInit guest store wrong");
      check(c.mmu.read32(SYNTH_OS_MARKER)==0x707u,"synthetic OSInit guest marker missing");
      check(c.mmu.read32(sp-8u-48u)==c.gpr[24],"synthetic helper spill missing");
      check(c.mmu.read32(0x80000048u)==0xaabbccddu,"synthetic DBInit corrupted low-memory pointer");
    }
    check(c.mmu.read32(sp-8)==0xffffffffu,
          "__start stack backchain corruption");
    check(c.msr==(owner?(((msr0|0x32u)&~0xa000u)|0x8000u):(msr0|0x2000u)),
          "original interrupt-disable MSR.EE side effect changed");
    check(c.hid0==(owner?(expected_hid0|0x200u):expected_hid0) &&
          c.hid2==(owner?(expected_hid2&~0x40000000u):expected_hid2),"cache/HID0/HID2 state changed");
    check(c.fpscr==(owner?(fpscr|0x4u):fpscr),"original non-IEEE FP FPSCR bit differed");
    for(unsigned i=0;i<32;++i){
      check(c.fpr[i]==expected_scalar,"scalar FPR state changed");
      check(c.ps1[i]==expected_ps,"paired-single PS1 state changed");
      check(c.gqr[i%8]==0,"GQR not zeroed");
    }
    check(nwii::runtime::cache_calls==before_cache+(owner?2u:1u),
          "native Wii cache initializer must execute from both __start and OSInit");
    if(owner)check(nwii::runtime::cache_os_entries==before_cache_os+1u,
                   "original OSInit second native cache call not entered");
    check(nwii::runtime::ic_calls==before_ic+(owner?(ic_on?0u:1u):1u),"ICEnable branch count differs");
    check(nwii::runtime::dc_calls==before_dc+(owner?(dc_on?0u:1u):1u),"DCEnable branch count differs");
    check(nwii::runtime::external_stubs[1]>=before_stubs[1]+1,
          "original cache initializer error-handler callback was not observed");
    check(nwii::runtime::post_stops==before_stop+1,"no bounded OSInit stop");
    check(nwii::runtime::data_calls[0]==before_data[0]+1,"native __init_data not entered");
    check(c.inst_count>before_inst+100,"too few guest instructions executed");
    if(owner){
      const std::array<uint64_t,5> expected{1,0,19,4,4};
      for(unsigned i=0;i<5;++i)
        check(nwii::runtime::data_calls[i]-before_data[i]==expected[i],"unexpected data helper call count");
      for(const auto&span:zero){
        const auto*ptr=c.mmu.get_ptr(span.start);
        for(uint32_t i=0;i<span.size;++i){
          const uint32_t address=span.start+i;
          const bool db_global=address>=0x8070d8a0u && address<0x8070d8a8u;
          const bool os_global=address>=OS_INIT_FLAG && address<OS_INIT_FLAG+4u;
          const bool time_global=address>=0x8070db30u && address<0x8070db38u;
          const bool boot_global=address>=BOOT_BASE && address<BOOT_BASE+4u;
          const bool arena_global=address>=HI_GLOBAL && address<HI_GLOBAL+4u;
          const bool mem2_high_global=address>=MEM2_HI_GLOBAL && address<MEM2_HI_GLOBAL+4u;
          const bool ipc_high_global=address>=IPC_HI_GLOBAL && address<IPC_HI_GLOBAL+4u;
          const bool exception_table_global=address>=R13-3552u && address<R13-3552u+4u;
          const bool shutdown_global=address>=SHUTDOWN_HEAD && address<SHUTDOWN_TAIL+4u;
           const bool irq_global=address>=IRQ_GLOBAL && address<IRQ_GLOBAL+4u;
          const bool id_cache_global=address>=ID_CACHE && address<ID_CACHE+4u;
          const bool exi_transfer_metadata=address>=0x806f1570u&&address<0x806f157cu;
          const bool si_slot=address>=SLOT&&address<SLOT+128u;
          const bool si_type_time=address>=TYPE_TIME&&address<TYPE_TIME+32u;
          const bool si_init_flag=address>=R13-3148u&&address<R13-3148u+4u;
          const bool sram_state=address>=SRAM&&address<SRAM+80u;
          const bool thread_state=address>=THREAD&&address<THREAD+1048u;
          const bool mi_state=address>=MI_FLAG&&address<MI_FLAG+4u;
          if(!db_global&&!os_global&&!time_global&&!boot_global&&!arena_global&&!mem2_high_global&&!ipc_high_global&&!exception_table_global&&!shutdown_global&&!irq_global&&!id_cache_global&&!exi_transfer_metadata&&!si_slot&&!si_type_time&&!si_init_flag&&!sram_state&&!thread_state&&!mi_state)
            check(ptr[i]==0,"original BSS byte not zero");
        }
        check(c.mmu.read8(span.start-1)==0xB5,"BSS underrun canary clobbered");
        if(span.start+span.size==STACK_BOTTOM)
          check(c.mmu.read32(STACK_BOTTOM)==STACK_MAGIC,"original thread stack sentinel missing after BSS");
        else check(c.mmu.read8(span.start+span.size)==0xC5,"BSS overrun canary clobbered");
      }
    } else {
      check(c.mmu.read32(0x80036000u)==0,"synthetic translated store did not run");
      check(c.mmu.read32(0x80036004u)==0xDEADBEEFu,"synthetic store overran neighboring word");
    }
  }
  check(nwii::runtime::unknown_calls==0&&nwii::runtime::interpreter_calls==0,"unexpected syscall/interpreter fallback");
  std::cout<<std::dec<<"PASS: "<<checks<<" V73 recovered continuous original __start->IOS_Open wait-queue assertions; mode="
           <<(owner?"owner":"synthetic")<<" trials="<<trials<<" stop=0x"<<std::hex<<(owner?POST_OWNER:POST_SYNTH)<<std::dec<<"\n";
}
