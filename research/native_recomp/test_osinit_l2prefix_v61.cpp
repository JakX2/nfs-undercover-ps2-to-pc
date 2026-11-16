// Original-free test of the genuine Wii OSInit -> exception -> syscall -> alarm chain.
// Private extracted code and original DOL stay off GitHub and out of test source.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <vector>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
constexpr uint32_t OSINIT=0x80520670u,STOP=0x805225ECu,L2_ENABLED_STOP=0x80522644u,L2_READ=0x804B7930u,L2_WRITE=0x804B7938u,FIRSTSTOP=0x80520CDCu,SECONDDEBUG=0x80520D08u,MARK=0x804E50A0u,DCFLUSH=0x80522320u,ICINVALID=0x80522378u,IPC=0x8052AE80u,EXCEPTION=0x80520BF4u,DEBUGSTOP=0x80520C44u,
   EXC_SOURCE_WORD=0x80520F28u, ALT=0x80520BDCu,REPORT=0x80522F00u;
constexpr uint32_t TIME=0x8052A844u,GETTIME=0x8052A824u,DISABLE=0x805265ACu;
constexpr uint32_t RESTORE=0x805265D4u,EXEC=0x80523B1Cu,SAVE=0x805450E8u,COPY=0x80004338u,PERF=0x804B7964u,
                   MFHID0=0x804B7920u,MTHID0=0x804B7928u,
                   SPEC=0x804B7A00u,NONIEEE=0x804B7A28u,HID4=0x804B7A30u,ARENA_LO=0x80521D60u,ARENA_HI=0x80521D48u,MEM2_LO=0x80521D68u,MEM2_HI=0x80521D50u;
constexpr uint32_t SYSCALL=0x805290C8u,SYSCALL_SRC=0x805290A8u,DBPRINTF=0x804E50B8u,RESTGPR=0x80545134u;
constexpr uint32_t MODULE=0x80526D30u, CONTEXT=0x80522EB8u;
constexpr uint32_t CACHE=0x80522540u,IC_ENABLE=0x805223BCu,DC_ENABLE=0x80522280u;
constexpr uint32_t INTERRUPT=0x8052661Cu,MEMSET=0x8000443Cu,FILL=0x80004388u;
constexpr uint32_t IRQ_TABLE=0x80003040u,IRQ_GLOBAL=0x8070E8E0u-3408u;
constexpr uint32_t ALARM=0x805210CCu,GETEXC=0x80520EB0u,SETEXC=0x80520E9Cu,
 SHUTDOWN=0x80527B4Cu,ALARM_HANDLER=0x805217BCu,SHUTDOWN_NODE=0x8060BCB8u;
constexpr uint32_t SYSCALL_DEST=0x80000C00u;
constexpr uint32_t SOURCE_TEMPLATE=0x80520EC0u, ORACLE=0x90050000u, VECTOR_DEST=0x80000100u, VECTOR_LEN=0x98u;
constexpr uint32_t SP=0x80082000u, R13=0x8070E8E0u, INITFLAG=0x8070DAFCu;
constexpr uint32_t ALARM_HEAD=R13-3496u,SHUTDOWN_HEAD=R13-3376u,SHUTDOWN_TAIL=R13-3372u;
constexpr uint32_t DEST=0x806F4F00u,SOURCE=0x80038000u,TIMEHI=0x8070DB30u;
// Boot-state globals are indexed from the original guest r13 small-data pointer.
constexpr uint32_t BOOT_BASE=R13-3512u, BOOT_RECORD=R13-3516u;
constexpr uint32_t BOOT_FALLBACK=R13-3520u, BOOT_MODE=R13-16864u;
constexpr uint32_t BOOT_FIELD=R13-3216u, BOOT_HINT=0x8000310cu;
constexpr uint32_t BOOT_SOURCE=0x8003D000u;
constexpr uint32_t LO_GLOBAL=R13-16400u,HI_GLOBAL=R13-3472u;
constexpr uint32_t MEM1_HI_HINT=0x80003110u;
constexpr uint32_t MEM2_LO_HINT=0x80003124u,MEM2_HI_HINT=0x80003128u;
constexpr uint32_t MEM2_LO_GLOBAL=R13-16396u,MEM2_HI_GLOBAL=R13-3468u;
constexpr uint32_t IPC_LO_HINT=0x80003130u,IPC_HI_HINT=0x80003134u;
constexpr uint32_t IPC_LO_GLOBAL=R13-16336u,IPC_HI_GLOBAL=R13-3352u;
struct ReportStop {};
struct NativeStop {};
struct FirstMarkStop {};
struct SecondDebugStop {};
struct DebugStop {};
uint64_t assertions=0;
void check(bool b,const char* text){if(!b)throw std::runtime_error(text);++assertions;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0,forbidden=0,debug_callbacks=0;
static uint32_t expected_stop=STOP;
// Only records guest-written MMIO transactions; this is NOT a model of PI/IOS.
static std::vector<std::pair<uint32_t,uint32_t>> guest_mmio_writes;
static uint32_t unexpected_mmio=0;
static std::vector<std::pair<uint32_t,uint32_t>> guest_mmio_reads;
static uint64_t target_time=0;
static uint32_t call_counts[53]{};
void trace_call(uint32_t pc,CPUContext& ctx){
 constexpr uint32_t symbols[53]={OSINIT,TIME,GETTIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT,
  PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40,MFHID0,MTHID0,SPEC,NONIEEE,HID4,REPORT,ARENA_LO,ARENA_HI,MEM2_LO,MEM2_HI,IPC,EXCEPTION,0x80520E98u,0x80520E9Cu,0x80520EC0u,0x80520F58u,MARK,DCFLUSH,ICINVALID,DBPRINTF,RESTGPR,SYSCALL,ALARM,GETEXC,SHUTDOWN,MODULE,INTERRUPT,MEMSET,FILL,0x805266E0u,CONTEXT,CACHE,IC_ENABLE,DC_ENABLE,L2_READ,L2_WRITE,0x804B7910u,0x804B7918u};
 for(size_t i=0;i<53;++i)if(pc==symbols[i]){
   ++call_counts[i];
   // Deterministic test-only virtual-clock start; not a production runtime override.
   if(pc==GETTIME)ctx.inst_count=target_time;
   return;
 }
 throw std::runtime_error("unplanned original Wii function entered");
}
bool handle_syscall(CPUContext& ctx){
 if(ctx.pc==DBPRINTF){++debug_callbacks;return true;} // TEST-ONLY HLE, never claim original DBPrintf
 if(ctx.pc!=expected_stop){++forbidden;throw std::runtime_error("unexpected guest syscall stop at "+std::to_string(ctx.pc)+" expected "+std::to_string(expected_stop));}
 ++stops;ctx.is_running=false;
 if(ctx.pc==STOP || ctx.pc==L2_ENABLED_STOP)throw NativeStop{};
 if(ctx.pc==FIRSTSTOP)throw FirstMarkStop{};
 if(ctx.pc==SECONDDEBUG)throw SecondDebugStop{};
 if(ctx.pc==DEBUGSTOP)throw DebugStop{};
 if(ctx.pc==REPORT)throw ReportStop{}; // stop before original OSReport can return
 return true;
}
void interpret_step(CPUContext&){++forbidden;throw std::runtime_error("PPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t addr){
 if(addr!=0x0C00500Au){++unexpected_mmio;throw std::runtime_error("unexpected Wii 16-bit MMIO read");}
 guest_mmio_reads.emplace_back(addr,0xF7F7u);return 0xF7F7u;
}
uint32_t HW_Reg_Read32(uint32_t addr){
 uint32_t val=0;
 switch(addr){
  case 0x0D006C00u:val=0x12345678u;break;
  case 0x0D006800u:val=0x98765432u;break;
  case 0x0D006814u:val=0xAABBCCDDu;break;
  case 0x0D006828u:val=0xDEADBEEFu;break;
  default:++unexpected_mmio;throw std::runtime_error("unexpected Wii 32-bit MMIO read");
 }
 guest_mmio_reads.emplace_back(addr,val);return val;
}
void HW_Reg_Write16(uint32_t addr,uint16_t val){
 if(addr!=0x0C00401Cu&&addr!=0x0C00500Au){++unexpected_mmio;throw std::runtime_error("unexpected Wii 16-bit MMIO write");}
 guest_mmio_writes.emplace_back(addr,val);
}
void HW_Reg_Write32(uint32_t addr,uint32_t value){
 if(addr!=0x0C003004u && addr!=0x0D000034u &&
    addr!=0x0D006C00u && addr!=0x0D006800u && addr!=0x0D006814u && addr!=0x0D006828u){
   ++unexpected_mmio;throw std::runtime_error("unrecognized Wii interrupt MMIO write");
 }
 guest_mmio_writes.emplace_back(addr,value);
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
 check(argc==2,"usage: original-native-test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"wrong bounded OSInit DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 // A private DOL data segment holds the original exception-vector handler
 // template, independently of executable analyzer safety guards. Seed the
 // MMU from those SHA-pinned owner-derived bytes, never from hardcoded game
 // code. This mirrors what a real DOL loader must do before OSInit.
 std::vector<uint8_t> original_template;
 for(const auto& sec:exe.sections){
  if(sec.address==ORACLE && !sec.is_text && !sec.is_bss){
   check(sec.data.size()==VECTOR_LEN,"unexpected private template data length");
   original_template.assign(sec.data.begin(),sec.data.end());
  }
 }
 check(original_template.size()==VECTOR_LEN,"missing private original handler template");
 std::array<uint8_t,28> original_syscall{};
 bool found_syscall=false;
 for(const auto& sec:exe.sections)if(!sec.is_bss &&
     sec.address<=SYSCALL_SRC &&
     uint64_t(SYSCALL_SRC)+0x80u<=uint64_t(sec.address)+sec.data.size()){
   const size_t at=SYSCALL_SRC-sec.address;
   for(size_t i=0;i<original_syscall.size();++i)original_syscall[i]=sec.data[at+i];
   found_syscall=true;
 }
 check(found_syscall,"missing owner-original syscall template source in private test image");
 for(uint32_t i=0;i<VECTOR_LEN;++i){
   ctx->mmu.write8(SOURCE_TEMPLATE+i,original_template[i]);
 }
 for(uint32_t i=0;i<original_syscall.size();++i)
   ctx->mmu.write8(SYSCALL_SRC+i,original_syscall[i]);
 // The original exception prologue reads a text-resident handler template
 // through lwzu. The test loader currently does not automatically install
 // all original DOL sections into MMU RAM: seed this owner-private word from
 // the private slice, without embedding copyrighted bytes in the test source.
 bool found_template=false;
 uint32_t template_word=0;
 for(const auto& sec:exe.sections){
   if(sec.address<=EXC_SOURCE_WORD &&
      uint64_t(EXC_SOURCE_WORD)+4<=uint64_t(sec.address)+sec.data.size()){
     const size_t pos=EXC_SOURCE_WORD-sec.address;
     template_word=uint32_t(sec.data[pos])<<24 | uint32_t(sec.data[pos+1])<<16 |
         uint32_t(sec.data[pos+2])<<8 | uint32_t(sec.data[pos+3]);
     found_template=true;
   }
 }
 check(found_template,"missing owner-private exception code-data literal");
 constexpr std::array<uint32_t,6> source{0u,0x7fffffffu,SOURCE,0x80000000u,0u,0x7fffffffu};
 constexpr std::array<uint64_t,6> clocks{0x0000000000100000ull,0x00000001fffffffcull,
       0x00000000fffffff0ull,0x0000000200000004ull,0x0000000300000001ull,0x0000000100001234ull};
 constexpr std::array<uint64_t,6> offsets{0x0000000000000000ull,0x0000000200000050ull,
       0x00000003ffffffe0ull,0x00000001fffffffdull,0x0000000000000300ull,0x00000000ffffff00ull};
 for(size_t run=0;run<source.size();++run){
  for(unsigned i=0;i<28;++i)
    check(ctx->mmu.read8(SYSCALL_SRC+i)==original_syscall[i],
          "original syscall handler source modified by preceding run");
  const uint32_t ptr=source[run];const bool copied=ptr>=0x80000000u;
  const uint32_t msr=(run&1)?0x2000u:0xA000u;
  constexpr uint32_t SAVED_LR=0x8000BEEFu;
  // Owner-original table at r24 uses vector offsets; index zero maps 0x100.
  // Seed only independently stated test values, without embedding table data.
  for(uint32_t index=0;index<15;++index)
    ctx->mmu.write32(0x8060BBE0u+4u*index,0x100u+index*0x100u);
  ctx->mmu.write32(INITFLAG,0);
  ctx->mmu.write32(0x80000060u,0x00000001u+uint32_t(run));
  // The alarm handler and shutdown registration now run after the native
  // system-call initializer on normal exception initialization paths.
  ctx->mmu.write32(ALARM_HEAD,0x11112222u+uint32_t(run));
  ctx->mmu.write32(ALARM_HEAD+4u,0x33334444u+uint32_t(run));
  ctx->mmu.write32(SHUTDOWN_HEAD,0);
  ctx->mmu.write32(SHUTDOWN_TAIL,0);
  ctx->mmu.write32(SHUTDOWN_NODE,0xFACA0000u+uint32_t(run));
  ctx->mmu.write32(SHUTDOWN_NODE+4u,100u+uint32_t(run));
  ctx->mmu.write32(SHUTDOWN_NODE+8u,0xAACA0000u+uint32_t(run));
  ctx->mmu.write32(SHUTDOWN_NODE+12u,0xBBCA0000u+uint32_t(run));
  ctx->mmu.write32(SHUTDOWN_NODE+16u,0xCCCA0000u+uint32_t(run));
  ctx->mmu.write32(EXC_SOURCE_WORD,template_word);
  // Seed a complete exception-vector destination plus canaries.
  for(uint32_t vector=0;vector<15;++vector){
    const uint32_t base=VECTOR_DEST+vector*0x100u;
    ctx->mmu.write8(base-1u,0xB6u);
    for(uint32_t i=0;i<VECTOR_LEN;++i)ctx->mmu.write8(base+i,0xD3u);
    ctx->mmu.write8(base+VECTOR_LEN,0xB7u);
    ctx->mmu.write32(0x80003000u+vector*4u,0xBEEA0000u+vector);
  }
  ctx->mmu.write32(0x8000303cu,0xDEADBEEFu);
  const uint8_t interrupt_seed=uint8_t(0x31u+run*17u);
  for(uint32_t i=0;i<128;++i)
    ctx->mmu.write8(IRQ_TABLE+i,uint8_t(interrupt_seed+i*3u));
  ctx->mmu.write8(IRQ_TABLE+128u,0xC5u);
  const uint32_t irq_global_seed=0xCE00F000u+uint32_t(run);
  ctx->mmu.write32(IRQ_GLOBAL,irq_global_seed);
  ctx->mmu.write32(IRQ_GLOBAL-4u,0xB0B0B0B0u);
  ctx->mmu.write32(IRQ_GLOBAL+4u,0xC1C1C1C1u);
  for(unsigned k=0;k<12;++k)ctx->mmu.write32(SP-128u+k*4,0xC0C0C0C0u);
  ctx->mmu.write32(0x800030F0u,ptr);
  // Six startup shapes: neither boot source, legacy fallback,
  // explicit boot-info record, and a boot record overriding fallback flags.
  const uint32_t boot=run<2?0u:BOOT_SOURCE+static_cast<uint32_t>((run-2)*0x100u);
  const bool legacy=(run&1u)!=0;
  const uint8_t legacy_byte0=uint8_t(0x65u+run),legacy_byte1=uint8_t(0x85u+run);
  const uint32_t boot_word0=(run==2?1u:0xABCD1200u+uint32_t(run*11+9));
  const uint32_t boot_word1=0xCAFE5600u+uint32_t(run*13+0x42);
  const uint32_t arena_hint=(run==0||run==2||run==4||run==5)?0u:0x80102000u+uint32_t(run*0x100u);
  const uint32_t high_hint=(run==3)?0x81720000u:((run==5)?0x81760000u:0u);
  const uint32_t expected_lo=arena_hint?arena_hint:(run==2?0x80751CC0u:((run==5)?0x80001234u:0x80753CC0u));
  const uint32_t expected_hi=high_hint?high_hint:(legacy?1u:0x81700000u);
  constexpr std::array<uint32_t,6> mem2_lows{0u,0x90000000u,0x900007ffu,
                                              0x90000800u,0x90010000u,0x80004000u};
  constexpr std::array<uint32_t,6> mem2_highs{0u,0x93400000u,0u,
                                               0x93a00000u,0x93f00000u,0x93b00000u};
  const uint32_t mem2_lo=mem2_lows[run],mem2_hi=mem2_highs[run];
  const uint32_t expected_mem2_lo=mem2_lo?((mem2_lo>=0x90000000u&&mem2_lo<0x90000800u)?0x90000800u:mem2_lo):0xA5A5A5A5u;
  const uint32_t expected_mem2_hi=mem2_hi?mem2_hi:0xB5B5B5B5u;
  // 0x80000030 controls the original alternate aligned-heap path.
  ctx->mmu.write32(0x80000030u,run==5?0x80001234u:0u);
  ctx->mmu.write32(MEM1_HI_HINT,high_hint);
  ctx->mmu.write32(MEM2_LO_HINT,mem2_lo);
  ctx->mmu.write32(MEM2_HI_HINT,mem2_hi);
  const uint32_t ipc_lo=run==0?0u:(0x90000100u+uint32_t(run*0x100u));
  const uint32_t ipc_hi=run==1?0u:(0x93FFF000u-uint32_t(run*0x1000u));
  ctx->mmu.write32(IPC_LO_HINT,ipc_lo);
  ctx->mmu.write32(IPC_HI_HINT,ipc_hi);
  ctx->mmu.write32(IPC_LO_GLOBAL,0xFAFA1616u);
  ctx->mmu.write32(IPC_HI_GLOBAL,0xBEBE2929u);
  ctx->mmu.write32(IPC_LO_GLOBAL-4u,0xDEADC0DEu);
  ctx->mmu.write32(IPC_HI_GLOBAL+4u,0xFACECAFEu);
  ctx->mmu.write32(0x800000F4u,boot);
  ctx->mmu.write32(0x80000034u,legacy?1u:0u);
  ctx->mmu.write8(0x800030E8u,legacy_byte0);
  ctx->mmu.write8(0x800030E9u,legacy_byte1);
  ctx->mmu.write32(BOOT_HINT,arena_hint);
  if(boot){
    ctx->mmu.write32(boot+12u,boot_word0);
    ctx->mmu.write32(boot+36u,boot_word1);
    ctx->mmu.write8(boot+8u,0xDAu);
    ctx->mmu.write8(boot+40u,0xDBu);
  }
  ctx->mmu.write32(BOOT_BASE,0x6F6F6F6Fu);
  ctx->mmu.write32(BOOT_RECORD,0x6E6E6E6Eu);
  ctx->mmu.write32(BOOT_FALLBACK,0x6D6D6D6Du);
  ctx->mmu.write32(BOOT_FIELD,0x6C6C6C6Cu);
  ctx->mmu.write32(BOOT_MODE,0x6B6B6B6Bu);
  ctx->mmu.write32(LO_GLOBAL,0xA1A1A1A1u);
  ctx->mmu.write32(HI_GLOBAL,0xB2B2B2B2u);
  ctx->mmu.write32(LO_GLOBAL-4u,0xC3C3C3C3u);
  // V32 used adjacent MEM2 globals as canaries; V37 now seeds actual outputs.
  ctx->mmu.write32(HI_GLOBAL+4u,0xB5B5B5B5u);
  ctx->mmu.write32(LO_GLOBAL+4u,0xA5A5A5A5u);
  ctx->mmu.write32(MEM2_LO_GLOBAL+4u,0xC5C5C5C5u);
  ctx->mmu.write32(MEM2_HI_GLOBAL+4u,0xD5D5D5D5u);

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
  ctx->hid0=0x05000000u + uint32_t(run);
  ctx->hid4=0x00012345u + uint32_t(run);
  ctx->fpscr=0xA0000000u + uint32_t(run);
  const uint32_t initial_hid0=ctx->hid0;
  const uint32_t initial_fpscr=ctx->fpscr;
  ctx->mmcr0=0xFFFF0001u+uint32_t(run);
  ctx->mmcr1=0x0000FFFFu+uint32_t(run);
  for(size_t i=0;i<4;++i)ctx->pmc[i]=0xBEEFAA01u+uint32_t(run*4+i);
  // Independently seeded low-memory interrupt-mask words and neighboring canaries.
  constexpr uint32_t LOW_MASK_A=0x800000C4u,LOW_MASK_B=0x800000C8u;
  const uint32_t irq_seed=0xC0DE0000u+uint32_t(run);
  constexpr uint32_t CONTEXT_WORD=0x800000D8u;
  const uint32_t context_seed=0xE58C0000u+uint32_t(run);
  ctx->mmu.write32(CONTEXT_WORD-4u,0xACCE5500u+uint32_t(run));
  ctx->mmu.write32(CONTEXT_WORD,context_seed);
  ctx->mmu.write32(CONTEXT_WORD+4u,0xD15C0A00u+uint32_t(run));
  ctx->mmu.write32(LOW_MASK_A-4u,0x1952A052u);
  ctx->mmu.write32(LOW_MASK_A,irq_seed+1u);
  ctx->mmu.write32(LOW_MASK_B,irq_seed+2u);
  ctx->mmu.write32(LOW_MASK_B+4u,0x4952A052u);
  nwii::runtime::guest_mmio_writes.clear();
  nwii::runtime::guest_mmio_reads.clear();
  ctx->gpr[13]=R13;
  ctx->gpr[1]=SP;ctx->lr=SAVED_LR;ctx->pc=OSINIT;ctx->msr=msr;
  ctx->is_running=true;
  const uint32_t initial_l2cr=0x00010020u+uint32_t(run*0x1000u);
  ctx->l2cr=initial_l2cr;
  nwii::runtime::target_time=clocks[run];
  // Genuine __DBIsExceptionMarked uses this r13-relative pointer to a debug
  // structure with a mark-bit mask at +4. Seed only independently authored data.
  constexpr uint32_t DB_GLOBAL=R13-4160u, DB_STRUCT=0x80045000u;
  const uint32_t dbmask=(run&1u)?0xFFFFFFFFu:0u;
  ctx->mmu.write32(DB_GLOBAL,DB_STRUCT);
  ctx->mmu.write32(DB_STRUCT,0x19283746u);
  ctx->mmu.write32(DB_STRUCT+4u,dbmask);
  // Independent sentinel words for original __OSModuleInit low-memory globals.
  constexpr uint32_t MODULE_PRE=0x800030C4u, MODULE_LO=0x800030C8u;
  constexpr uint32_t MODULE_MID=0x800030CCu, MODULE_HI=0x800030D0u;
  constexpr uint32_t MODULE_POST=0x800030D4u;
  const uint32_t module_seed=0xB0000000u+uint32_t(run*0x101u);
  ctx->mmu.write32(MODULE_PRE,0x6A6A6A6Au);
  ctx->mmu.write32(MODULE_LO,module_seed+1u);
  ctx->mmu.write32(MODULE_MID,module_seed+2u);
  ctx->mmu.write32(MODULE_HI,module_seed+3u);
  ctx->mmu.write32(MODULE_POST,0x7B7B7B7Bu);
  const uint32_t before_flush=ctx->guest_flush_count;
  const uint32_t before_invalidate=ctx->guest_invalidate_count;
  const uint32_t before_sync=ctx->guest_sync_count;
  const uint32_t before_isync=ctx->guest_isync_count;
  const uint32_t stops=nwii::runtime::stops;
  const uint32_t before_dbprintf=nwii::runtime::debug_callbacks;
  std::array<uint32_t,53> before{};
  for(size_t i=0;i<before.size();++i)before[i]=nwii::runtime::call_counts[i];
  const bool marked_first=(run==1u || run>=3u);
  const bool debug_branch=(dbmask&1u)!=0u;
  constexpr uint32_t VECTOR_TEMPLATE=0x80520F18u;
  ctx->mmu.write32(VECTOR_TEMPLATE-4u,0x42434342u);
  ctx->mmu.write32(VECTOR_TEMPLATE,0x11224488u);
  ctx->mmu.write32(VECTOR_TEMPLATE+4u,0x47494947u);
  nwii::runtime::expected_stop=debug_branch?FIRSTSTOP:STOP;
  bool exact_stop=false;
  try{run_game(*ctx);}
  catch(const NativeStop&){if(!debug_branch)exact_stop=true;}
  catch(const FirstMarkStop&){if(debug_branch)exact_stop=true;}
  check(exact_stop,"original OSInit missing expected exception-mark terminal syscall");
  check(!ctx->is_running&&ctx->pc==(debug_branch?FIRSTSTOP:STOP),
        "wrong original exception-mark guest syscall boundary");
  check(nwii::runtime::stops==stops+1,"missing original OSInit continuation stop");
  check(ctx->gpr[1]==(debug_branch?SP-144u:SP-96u),
        "original exception return failed to restore the nested guest stack frame");
  check(nwii::runtime::debug_callbacks-before_dbprintf==(debug_branch?0u:4u),
        "unresolved DBPrintf test-only callback count changed");
  check(ctx->mmu.read32(SP-76u)==(debug_branch?0x805208ACu:0x805208C4u),
        "genuine nested exception/syscall LR slot reuse differs");
  check(ctx->mmu.read32(0x80000060u)==0x00000001u+uint32_t(run),"exception changed low-memory branch flag");
  std::vector<uint8_t> expected_handler=original_template;
  auto expected_word=[&](uint32_t address,uint32_t value){
    const uint32_t at=address-SOURCE_TEMPLATE;
    check(at+4<=expected_handler.size(),"test oracle word outside original handler");
    for(unsigned j=0;j<4;++j)expected_handler[at+j]=uint8_t(value>>(24-8*j));
  };
  expected_word(VECTOR_TEMPLATE-4u,0x42434342u);
  expected_word(VECTOR_TEMPLATE,debug_branch?0x11224488u:0x60000000u);
  expected_word(VECTOR_TEMPLATE+4u,0x47494947u);
  const uint32_t expected_vectors=debug_branch?0u:15u;
  const uint32_t expected_cache_lines=expected_vectors*5u+(debug_branch?0u:8u);
  check(ctx->guest_flush_count-before_flush==expected_cache_lines,
        "original dcbf loop skipped or repeated cache-line operations");
  check(ctx->guest_invalidate_count-before_invalidate==expected_cache_lines,
        "original icbi loop skipped or repeated cache-line operations");
  check(ctx->guest_sync_count-before_sync==(expected_vectors*2u+(debug_branch?0u:9u)),
        "original sync call ordering missing or duplicated");
  check(ctx->guest_isync_count-before_isync==expected_vectors+(debug_branch?0u:2u),
        "original isync call ordering missing or duplicated");
  if(!debug_branch){
    check(ctx->guest_flush_lines.size()>=256u && ctx->guest_invalidate_lines.size()>=256u,
          "V49 guest cache-line trace capacity must cover all 15 exception vectors");
    for(uint32_t i=0;i<expected_cache_lines;++i){
      const uint32_t vector=i/5u;
      const uint32_t line=i%5u;
      const uint32_t expected=i<75u?
           VECTOR_DEST+vector*0x100u+line*32u:
           SYSCALL_DEST+((i-75u)*32u);
      check(ctx->guest_flush_lines[before_flush+i]==expected,
            "dcbf line address or iteration order differs");
      check(ctx->guest_invalidate_lines[before_invalidate+i]==expected,
            "icbi line address or iteration order differs");
    }
    check(ctx->guest_last_flush==SYSCALL_DEST+0xe0u &&
          ctx->guest_last_invalidate==SYSCALL_DEST+0xe0u,
          "original cache-line maintenance last address differs");
  }
  for(uint32_t vector=0;vector<15;++vector)
    check(ctx->mmu.read32(0x8060BBE0u+4u*vector)==0x100u+vector*0x100u,
          "original exception-vector offset table was modified");
  check(ctx->mmu.read8(VECTOR_DEST-1u)==0xB6u&&
        ctx->mmu.read8(VECTOR_DEST+VECTOR_LEN)==0xB7u,
        "original vector memcpy wrote outside the 0x98-byte handler");
  for(uint32_t vector=0;vector<15;++vector){
    const uint32_t base=VECTOR_DEST+vector*0x100u;
    check(ctx->mmu.read8(base-1u)==0xB6u&&
          ctx->mmu.read8(base+VECTOR_LEN)==0xB7u,
          "original exception-vector copy corrupted a neighboring address");
    check(ctx->mmu.read32(0x80003000u+vector*4u)==
          (debug_branch?0xBEEA0000u+vector:(vector==4u?0x80526CE0u:(vector==7u?0x80522E34u:(vector==8u?ALARM_HANDLER:0x80520F5Cu)))),
          "original 15-entry exception-handler dispatch table incorrect");
    for(uint32_t i=0;i<VECTOR_LEN;++i){
      uint8_t expected=debug_branch?0xD3u:expected_handler[i];
      const uint32_t mark_offset=EXC_SOURCE_WORD-SOURCE_TEMPLATE;
      if(!debug_branch && i>=mark_offset && i<mark_offset+4u){
        const uint32_t marked_template_word=template_word|vector;
        expected=uint8_t(marked_template_word>>(24u-8u*(i-mark_offset)));
      }
      if(!debug_branch && vector==11u && i<28u)
        expected=original_syscall[i]; // original syscall vector overlays vector 11
      check(ctx->mmu.read8(base+i)==expected,
            "original exception-vector byte differs from per-index source template");
    }
  }
  if(!debug_branch){
    for(uint32_t i=0;i<28u;++i)
      check(ctx->mmu.read8(SYSCALL_DEST+i)==original_syscall[i],
            "original Wii syscall vector copy does not match owner instruction bytes");
    check(ctx->mmu.read8(SYSCALL_DEST+0x98u)==0xB7u,
          "original syscall cache operation wrote outside copied handler");
  }
  check(ctx->mmu.read32(0x8000303cu)==0xDEADBEEFu,
        "original handler-table setup exceeded 15 entries");
  if(!debug_branch){
    check(ctx->mmu.read32(R13-3552u)==0x80003000u,
          "original OS exception-handler table global not initialized");
    check(ctx->gpr[29]==0x1CA00000u+(uint32_t(run)<<16)+29u,
          "original interrupt epilogue did not restore caller r29");
    check(ctx->mmu.read32(EXC_SOURCE_WORD)==template_word,
          "original exception vector setup failed to restore source template word");
  }
  for(uint32_t i=0;i<VECTOR_LEN;++i)
    check(ctx->mmu.read8(SOURCE_TEMPLATE+i)==expected_handler[i],
          "original exception handler template source was modified");
  if(debug_branch)
    check(ctx->gpr[28]==EXC_SOURCE_WORD && ctx->gpr[27]==template_word,
          "original exception template LWZU did not read owner text word");
  else
    check(ctx->gpr[28]==0x1CA00000u+(uint32_t(run)<<16)+28u &&
          ctx->gpr[27]==0x1CA00000u+(uint32_t(run)<<16)+27u,
          "original _restgpr_20 failed to restore the exception callee-saved registers");
  if(debug_branch)
    check(ctx->gpr[25]==0x98u&&ctx->gpr[21]==4u&&ctx->gpr[23]==0x60000000u,
          "original exception setup arithmetic differs");
  else
    check(ctx->gpr[25]==0x1CA00000u+(uint32_t(run)<<16)+25u &&
          ctx->gpr[21]==0x1CA00000u+(uint32_t(run)<<16)+21u &&
          ctx->gpr[23]==0x1CA00000u+(uint32_t(run)<<16)+23u,
          "original exception register restoration failed");
  for(unsigned k=0;k<10;++k){
    uint32_t expected=0x1CA00000u+(uint32_t(run)<<16)+20u+k;
    if(!debug_branch){
      // Original interrupt prologue and original memset/__fill_mem reuse older
      // exception-frame slots. Verify the *actual* nested Wii ABI values.
      if(k==0u)expected=SP-112u; // nested stack backlink
      if(k==3u)expected=0x80000000u; // register-save scratch from original fill
      if(k==4u||k==8u)expected=SP-80u; // frame links from nested helpers
      if(k==5u)expected=INTERRUPT+0x30u; // original memset return address
    }
    check(ctx->mmu.read32(SP-128u+k*4)==expected,
          "exception/interrupt nested guest stack frame content differs");
  }
  check(ctx->mmu.read32(SP-88u)==0x806F4F00u && ctx->mmu.read32(SP-84u)==0x8060B7A8u,
        "exception _savegpr_20 saved original OSInit r30/r31 incorrectly");
  check(ctx->mmu.read32(SP+4)==SAVED_LR,"original caller LR was not saved");
  if(!debug_branch){
    check(ctx->mmu.read32(ALARM_HEAD)==0u && ctx->mmu.read32(ALARM_HEAD+4u)==0u,
          "original alarm list was not reset by __OSInitAlarm");
    check(ctx->mmu.read32(SHUTDOWN_HEAD)==SHUTDOWN_NODE&&
          ctx->mmu.read32(SHUTDOWN_TAIL)==SHUTDOWN_NODE,
          "original alarm shutdown callback was not registered");
    check(ctx->mmu.read32(SHUTDOWN_NODE+8u)==0u&&
          ctx->mmu.read32(SHUTDOWN_NODE+12u)==0u&&
          ctx->mmu.read32(SHUTDOWN_NODE+4u)==100u+uint32_t(run),
          "original shutdown-list node links or priority incorrect");
    check(ctx->mmu.read32(SHUTDOWN_NODE)==0xFACA0000u+uint32_t(run)&&
          ctx->mmu.read32(SHUTDOWN_NODE+16u)==0xCCCA0000u+uint32_t(run),
          "original alarm shutdown registration overran its node");
  }else{
    check(ctx->mmu.read32(ALARM_HEAD)==0x11112222u+uint32_t(run)&&
          ctx->mmu.read32(ALARM_HEAD+4u)==0x33334444u+uint32_t(run)&&
          ctx->mmu.read32(SHUTDOWN_HEAD)==0u&&ctx->mmu.read32(SHUTDOWN_TAIL)==0u,
          "unexecuted exception-debug branch unexpectedly initialized alarms");
  }
  // The original module initializer writes exactly three 32-bit guest globals.
  // Debug-marked paths stop before this function and must leave seeds intact.
  check(ctx->mmu.read32(MODULE_LO)==(debug_branch?module_seed+1u:0u)&&
        ctx->mmu.read32(MODULE_MID)==(debug_branch?module_seed+2u:0u)&&
        ctx->mmu.read32(MODULE_HI)==(debug_branch?module_seed+3u:0u),
        "genuine __OSModuleInit failed to clear module globals");
  check(ctx->mmu.read32(CONTEXT_WORD)==(debug_branch?context_seed:0u),
        "original __OSContextInit failed to clear current-context low-memory word");
  check(ctx->mmu.read32(CONTEXT_WORD-4u)==0xACCE5500u+uint32_t(run) &&
        ctx->mmu.read32(CONTEXT_WORD+4u)==0xD15C0A00u+uint32_t(run),
        "original __OSContextInit overwrote adjacent low-memory words");
  if(!debug_branch){
    check(ctx->mmu.read32(0x8000301Cu)==0x80522E34u,
          "original context exception handler 7 not registered");
  }
  check(ctx->mmu.read32(IRQ_GLOBAL)==(debug_branch?irq_global_seed:IRQ_TABLE),
        "original interrupt-table pointer global differs");
  check(ctx->mmu.read32(LOW_MASK_A-4u)==0x1952A052u &&
        ctx->mmu.read32(LOW_MASK_B+4u)==0x4952A052u,
        "original interrupt low-memory mask initialization overran canaries");
  check(ctx->mmu.read32(LOW_MASK_A)==(debug_branch?irq_seed+1u:0xFFFFFFF0u) &&
        ctx->mmu.read32(LOW_MASK_B)==(debug_branch?irq_seed+2u:0u),
        "original interrupt low-memory mask writes differ");
  check(nwii::runtime::guest_mmio_writes.size()==(debug_branch?0u:9u),
        "original Wii hardware register transaction count differs");
  if(!debug_branch){
    check(nwii::runtime::guest_mmio_writes.at(0)==std::make_pair(0x0C003004u,0xF0u),
          "original first MMIO write target/value differs");
    check(nwii::runtime::guest_mmio_writes.at(1)==std::make_pair(0x0D000034u,0x40000000u),
          "original second MMIO write target/value differs");
    check(ctx->gpr[4]==0x80000000u && ctx->gpr[5]==0x80003000u &&
          ctx->gpr[6]==0u && ctx->gpr[3]==(initial_l2cr|0x00200000u) &&
          ctx->gpr[29]==0x1CA00000u+(uint32_t(run)<<16)+29u && ctx->gpr[30]==0x2000u,
          "original interrupt-disable/mask register results differ");
    check(ctx->msr==0x30u,
          "original PPCMtmsr did not set temporary L2 initialization mode");
  }
  check(nwii::runtime::guest_mmio_reads.size()==(debug_branch?0u:5u),
        "original native mask loop MMIO read count changed");
  if(!debug_branch){
    constexpr std::array<std::pair<uint32_t,uint32_t>,9> expected_writes{{
      {0x0C003004u,0xF0u},{0x0D000034u,0x40000000u},
      {0x0C00401Cu,0u},{0x0C00500Au,0xF607u},
      {0x0D006C00u,0x12345650u},{0x0D006800u,0x98765030u},
      {0x0D006814u,0xAABBC0D0u},{0x0D006828u,0xDEADBEE0u},
      {0x0C003004u,0xF0u}
    }};
    constexpr std::array<std::pair<uint32_t,uint32_t>,5> expected_reads{{
      {0x0C00500Au,0xF7F7u},
      {0x0D006C00u,0x12345678u},
      {0x0D006800u,0x98765432u},
      {0x0D006814u,0xAABBCCDDu},
      {0x0D006828u,0xDEADBEEFu}
    }};
    for(size_t i=0;i<expected_writes.size();++i)
      check(nwii::runtime::guest_mmio_writes[i]==expected_writes[i],
            "integrated original SetInterruptMask MMIO write target/value/order differs");
    for(size_t i=0;i<expected_reads.size();++i)
      check(nwii::runtime::guest_mmio_reads[i]==expected_reads[i],
            "integrated original SetInterruptMask MMIO read target/value/order differs");
  }
  check(nwii::runtime::unexpected_mmio==0u,"unexpected Wii MMIO access");
  check(ctx->mmu.read32(IRQ_GLOBAL-4u)==0xB0B0B0B0u &&
        ctx->mmu.read32(IRQ_GLOBAL+4u)==0xC1C1C1C1u,
        "original interrupt setup corrupted adjacent globals");
  check(ctx->mmu.read32(0x8000303cu)==0xDEADBEEFu &&
        ctx->mmu.read8(IRQ_TABLE+128u)==0xC5u,
        "original interrupt memset overran table boundary");
  for(uint32_t i=0;i<128u;++i){
    const uint8_t expected=debug_branch?uint8_t(interrupt_seed+i*3u):0u;
    check(ctx->mmu.read8(IRQ_TABLE+i)==expected,
          "original PPC __fill_mem interrupt table byte differs");
  }
  if(!debug_branch){
    check(ctx->gpr[31]==0x8060BD48u,
          "original interrupt epilogue did not restore caller r31");
    check(ctx->mmu.read32(SP-92u)==0x1CA00000u+(uint32_t(run)<<16)+29u,
          "interrupt prefix failed to save caller r29");
    check(ctx->mmu.read32(SP-88u)==0x806F4F00u &&
          ctx->mmu.read32(SP-84u)==0x8060B7A8u,
          "interrupt prefix failed to save original OSInit r30/r31");
  }
  check(ctx->mmu.read32(MODULE_PRE)==0x6A6A6A6Au&&
        ctx->mmu.read32(MODULE_POST)==0x7B7B7B7Bu,
        "original module initializer overwrote adjacent low-memory canary");
  check(ctx->mmu.read32(INITFLAG)==1,"OSInit one-time global not set");
  check((ctx->msr&0x8000u)==0,"original second interrupt disable not executed");
  check(ctx->msr==(debug_branch?(msr&~0x8000u):0x30u),
        "original L2 setup MSR change/exception stop state differs");
  check(ctx->gpr[13]==R13,"OSInit guest small-data pointer changed");
  check(ctx->gpr[3]==(debug_branch?0x8060BC38u:(initial_l2cr|0x00200000u)),
        "original exception vector setup final return operand or debug branch differs");
  check(ctx->mmu.read32(VECTOR_TEMPLATE-4u)==0x42434342u &&
        ctx->mmu.read32(VECTOR_TEMPLATE+4u)==0x47494947u,
        "original template-clear loop overran its four-byte test buffer");
  check(ctx->mmu.read32(VECTOR_TEMPLATE)==(debug_branch?0x11224488u:0x60000000u),
        "original exception template loop did not clear precisely one word");
  if(!debug_branch)check(ctx->ctr==0u,"original vector-template loops did not exhaust CTR");
  check(ctx->mmu.read32(DB_GLOBAL)==DB_STRUCT&&ctx->mmu.read32(DB_STRUCT+4)==dbmask,
        "debug mark inputs modified by original exception check");
  check(ctx->mmu.read32(EXC_SOURCE_WORD)==template_word,
        "original exception-template word unexpectedly modified");
  check(ctx->mmu.read32(IPC_LO_GLOBAL)==ipc_lo && ctx->mmu.read32(IPC_HI_GLOBAL)==ipc_hi,
        "original IPC globals not initialized from low memory");
  check(ctx->mmu.read32(IPC_LO_HINT)==ipc_lo && ctx->mmu.read32(IPC_HI_HINT)==ipc_hi,
        "original IPC source values were modified");
  check(ctx->mmu.read32(IPC_LO_GLOBAL-4u)==0xDEADC0DEu &&
        ctx->mmu.read32(IPC_HI_GLOBAL+4u)==0xFACECAFEu,
        "original IPC initialization overwrote adjacent memory");
  check(ctx->mmu.read32(BOOT_HINT)==arena_hint&&ctx->mmu.read32(MEM1_HI_HINT)==high_hint,
        "original arena hint inputs changed");
  check(ctx->mmu.read32(LO_GLOBAL)==expected_lo,"original MEM1 low setter result differs");
  check(ctx->mmu.read32(HI_GLOBAL)==expected_hi,"original MEM1 high setter result differs");
  check(ctx->mmu.read32(LO_GLOBAL-4u)==0xC3C3C3C3u&&
        ctx->mmu.read32(MEM2_HI_GLOBAL+4u)==0xD5D5D5D5u,
        "MEM2 setter overwrote outer global canary");
  check(ctx->mmu.read32(MEM2_LO_HINT)==mem2_lo&&ctx->mmu.read32(MEM2_HI_HINT)==mem2_hi,
        "original MEM2 arena hints changed");
  check(ctx->mmu.read32(MEM2_LO_GLOBAL)==expected_mem2_lo,
        "original MEM2 low arena result differs");
  check(ctx->mmu.read32(MEM2_HI_GLOBAL)==expected_mem2_hi,
        "original MEM2 high arena result differs");
  check(ctx->mmu.read32(BOOT_BASE)==0x80000000u,"original OS boot base pointer changed");
  check(ctx->mmu.read32(BOOT_MODE)==1u,"original OS boot mode flag should be one");
  check(ctx->mmu.read32(0x800000F4u)==boot,"low-memory boot pointer modified");
  check(ctx->mmu.read32(0x80000034u)==(legacy?1u:0u),"low-memory legacy flag modified");
  if(boot){
    check(ctx->mmu.read32(BOOT_RECORD)==boot+12u,"original OS boot-info pointer wrong");
    check(ctx->mmu.read32(BOOT_FIELD)==boot_word1,"original boot-info secondary word wrong");
    check(ctx->mmu.read32(BOOT_FALLBACK)==0x6D6D6D6Du,"boot-info path touched fallback word");
    check(ctx->mmu.read8(0x800030E8u)==uint8_t(boot_word0),"boot-info first flag byte wrong");
    check(ctx->mmu.read8(0x800030E9u)==uint8_t(boot_word1),"boot-info second flag byte wrong");
    check(ctx->mmu.read32(boot+12u)==boot_word0&&ctx->mmu.read32(boot+36u)==boot_word1,
          "source boot-info words changed");
    check(ctx->mmu.read8(boot+8u)==0xDAu&&ctx->mmu.read8(boot+40u)==0xDBu,
          "source boot-info guards changed");
  } else if(legacy){
    check(ctx->mmu.read32(BOOT_RECORD)==BOOT_FALLBACK,"fallback boot pointer wrong");
    check(ctx->mmu.read32(BOOT_FIELD)==legacy_byte1,"fallback secondary boot byte wrong");
    check(ctx->mmu.read32(BOOT_FALLBACK)==legacy_byte0,"fallback primary boot byte wrong");
    check(ctx->mmu.read8(0x800030E8u)==legacy_byte0&&ctx->mmu.read8(0x800030E9u)==legacy_byte1,
          "fallback changed original low-memory bytes");
  } else {
    check(ctx->mmu.read32(BOOT_RECORD)==0u,"empty boot record pointer not cleared");
    check(ctx->mmu.read32(BOOT_FIELD)==0x6C6C6C6Cu,"empty boot path modified field");
    check(ctx->mmu.read32(BOOT_FALLBACK)==0x6D6D6D6Du,"empty boot path modified fallback");
    check(ctx->mmu.read8(0x800030E8u)==legacy_byte0&&ctx->mmu.read8(0x800030E9u)==legacy_byte1,
          "empty boot path modified low-memory bytes");
  }

  check(ctx->mmcr0==0&&ctx->mmcr1==0,"original MMCR0/MMCR1 zeroing failed");
  check(ctx->hid4==0x83900000u,"genuine original HID4 init write failed");
  check(ctx->hid0==(initial_hid0|(debug_branch?0x200u:0xC200u)),"original PPCDisableSpeculation HID0 bit preservation failed");
  check(ctx->fpscr==(initial_fpscr|0x4u),"original mtfsb1(29) FPSCR bit mapping failed");
  for(size_t i=0;i<4;++i)check(ctx->pmc[i]==0,"original PMC register zeroing failed");
  const uint64_t stamp=(uint64_t(ctx->mmu.read32(TIMEHI))<<32)|ctx->mmu.read32(TIMEHI+4);
  const uint64_t low=clocks[run]+offsets[run];
  check(stamp>=low+1 && stamp<=low+48,"OSInit timestamp outside original timebase window");
  const uint32_t expected_entries[53]={
    1,
    1,
    1,
    (debug_branch?2u:3u),
    (debug_branch?1u:2u),
    1,
    2,
    (copied?1u:0u)+expected_vectors+(debug_branch?0u:1u),
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    (debug_branch?1u:3u),
    1,
    1,
    1,
    1,
    0,
    1,
    1,
    (mem2_lo?1u:0u),
    (mem2_hi?1u:0u),
    1u,
    1u,
    0,
    (debug_branch?0u:3u),
    0,
    0,
    (debug_branch?1u:(marked_first?30u:15u)),
    expected_vectors+(debug_branch?0u:1u),
    expected_vectors+(debug_branch?0u:1u),
    (debug_branch?0u:4u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:7u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u),
    (debug_branch?0u:4u),
    (debug_branch?0u:3u),
    (debug_branch?0u:1u),
    (debug_branch?0u:1u)};
  for(size_t i=0;i<53;++i){
    const auto observed=nwii::runtime::call_counts[i]-before[i];
    if(observed!=expected_entries[i])
      std::cerr << "GUEST CALL MISMATCH run=" << run << " index=" << i
                << " observed=" << observed << " expected=" << expected_entries[i] << "\n";
    check(observed==expected_entries[i], "wrong number of original guest function dispatches");
  }
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
 // Independent native PowerPC OSRestoreInterrupts cases. Its first
 // argument controls the *new* EE bit; its return value is the *old* EE bit.
 // Preserve all other MSR flags and verify the whole original helper returns.
 for(uint32_t old_ee:{0u,0x8000u}){
  for(uint32_t requested:{0u,1u}){
   for(uint32_t flags:{0x00002000u,0xAC140011u,0x00000000u}){
    const uint32_t old_msr=(flags&~0x8000u)|old_ee;
    const uint32_t new_msr=(old_msr&~0x8000u)|(requested?0x8000u:0u);
    ctx->gpr[1]=SP;
    ctx->gpr[3]=requested;
    ctx->gpr[4]=0xFACED00Du;
    ctx->gpr[5]=0xABCD0123u;
    ctx->gpr[6]=0x6789ABCDu;
    ctx->msr=old_msr;
    ctx->lr=STOP;
    ctx->pc=RESTORE;
    ctx->is_running=true;
    nwii::runtime::expected_stop=STOP;
    const auto old_calls=nwii::runtime::call_counts[4];
    const auto old_stops=nwii::runtime::stops;
    bool ended=false;
    try{run_game(*ctx);}catch(const NativeStop&){ended=true;}
    check(ended&&!ctx->is_running&&ctx->pc==STOP,
          "direct original OSRestoreInterrupts did not reach guest return boundary");
    check(nwii::runtime::stops==old_stops+1u&&
          nwii::runtime::call_counts[4]==old_calls+1u,
          "direct original OSRestoreInterrupts dispatch count incorrect");
    check(ctx->gpr[3]==(old_ee?1u:0u),
          "original OSRestoreInterrupts returned incorrect previous EE state");
    check(ctx->msr==new_msr&&ctx->gpr[4]==old_msr&&ctx->gpr[5]==new_msr,
          "original OSRestoreInterrupts changed unrelated MSR bits or temporaries");
    check(ctx->gpr[1]==SP&&ctx->gpr[6]==0x6789ABCDu&&ctx->lr==STOP,
          "original OSRestoreInterrupts changed guest stack or unrelated state");
   }
  }
 }
 // Independent direct calls to the genuine original 24-byte module
 // initializer. Distinct nonzero inputs ensure we test semantic writes, not
 // only already-cleared globals inherited from another startup scenario.
 for(unsigned trial=0;trial<3u;++trial){
   constexpr uint32_t MOD=0x800030C8u;
   const uint32_t seed=0xE1100000u+trial*0x101u;
   ctx->mmu.write32(MOD-4u,0x01234567u+trial);
   ctx->mmu.write32(MOD+0u,seed+1u);
   ctx->mmu.write32(MOD+4u,seed+2u);
   ctx->mmu.write32(MOD+8u,seed+3u);
   ctx->mmu.write32(MOD+12u,0x89ABCDEFu+trial);
   ctx->gpr[0]=seed+10u;
   ctx->gpr[3]=seed+11u;
   ctx->gpr[4]=seed+12u;
   ctx->gpr[1]=SP;
   ctx->msr=0xA000u;
   ctx->pc=MODULE;
   ctx->lr=STOP;
   ctx->is_running=true;
   const uint32_t before_module=nwii::runtime::call_counts[40];
   const uint32_t before_stop=nwii::runtime::stops;
   nwii::runtime::expected_stop=STOP;
   bool expected=false;
   try{run_game(*ctx);}catch(const NativeStop&){expected=true;}
   check(expected&&!ctx->is_running&&ctx->pc==STOP,
         "direct original OS module initializer did not return to test stop");
   check(nwii::runtime::call_counts[40]==before_module+1u,
         "direct module helper did not dispatch exactly once");
   check(nwii::runtime::stops==before_stop+1u,
         "direct original module helper stop not observed");
   for(unsigned i=0;i<3u;++i)
     check(ctx->mmu.read32(MOD+i*4u)==0u,
           "direct original module initializer failed to clear a seeded global");
   check(ctx->mmu.read32(MOD-4u)==0x01234567u+trial&&
         ctx->mmu.read32(MOD+12u)==0x89ABCDEFu+trial,
         "direct original module initializer overran its 12-byte destination");
   check(ctx->gpr[0]==0u&&ctx->gpr[3]==0x80000000u,
         "module li/lis guest operand results differ");
   check(ctx->gpr[4]==seed+12u&&ctx->gpr[1]==SP&&ctx->msr==0xA000u,
         "module initializer corrupted an unrelated register or interrupt state");
   check(ctx->lr==STOP,"module direct call return LR changed");
 }
 // Direct original __OSContextInit regressions: not just a memory word that
 // was already zero in the integrated path. All normal paths must call the
 // original handler-register setter and return through the original epilogue.
 for(unsigned trial=0; trial<4u; ++trial){
   const uint32_t old=0xC083A000u+(trial*0x1111u);
   const uint32_t stack_guard=0xBEEF5700u+trial;
   const uint32_t msr=0x2000u+(trial&1u?0x8000u:0u);
   ctx->mmu.write32(0x800000D4u,stack_guard);
   ctx->mmu.write32(0x800000D8u,old);
   ctx->mmu.write32(0x800000DCu,stack_guard+1u);
   ctx->mmu.write32(0x8000301Cu,0xDEAD7100u+trial);
   ctx->gpr[1]=SP;
   ctx->gpr[13]=R13;
   ctx->gpr[3]=0x12340000u+trial;
   ctx->gpr[6]=0x60007000u+trial;
   ctx->pc=CONTEXT;
   ctx->lr=STOP;
   ctx->msr=msr;
   ctx->is_running=true;
   nwii::runtime::expected_stop=STOP;
   const uint32_t prior_ctx=nwii::runtime::call_counts[45];
   const uint32_t prior_set=nwii::runtime::call_counts[28];
   const uint32_t prior_print=nwii::runtime::call_counts[34];
   const uint32_t prior_callback=nwii::runtime::debug_callbacks;
   const uint32_t prior_stop=nwii::runtime::stops;
   bool ended=false;
   try{run_game(*ctx);}catch(const NativeStop&){ended=true;}
   check(ended && ctx->pc==STOP && !ctx->is_running,
         "original context helper did not return to guest stop");
   check(ctx->mmu.read32(0x800000D8u)==0u &&
         ctx->mmu.read32(0x800000D4u)==stack_guard &&
         ctx->mmu.read32(0x800000DCu)==stack_guard+1u,
         "direct context initialization overwrote canaries or left context pointer uncleared");
   check(ctx->mmu.read32(0x8000301Cu)==0x80522E34u,
         "direct original __OSSetExceptionHandler did not install handler 7");
   check(nwii::runtime::call_counts[45]==prior_ctx+1u &&
         nwii::runtime::call_counts[28]==prior_set+1u &&
         nwii::runtime::call_counts[34]==prior_print+1u &&
         nwii::runtime::debug_callbacks==prior_callback+1u &&
         nwii::runtime::stops==prior_stop+1u,
         "direct original context call/DBPrintf callback counts differ");
   check(ctx->gpr[1]==SP && ctx->lr==STOP && ctx->gpr[13]==R13 &&
         ctx->mmu.read32(SP+4u)==STOP,
         "direct context helper failed to restore LR and guest stack");
   check(ctx->gpr[3]==0x8060C138u && ctx->gpr[4]==0x80000000u &&
         ctx->gpr[6]==0x60007000u+trial && ctx->msr==msr,
         "direct context initializer register or MSR semantics differ");
 }
 // The original exception branch checks low memory at 0x80000060.
 // A zero value enters an OS debug/copy path we have not implemented. The
 // fixture substitutes a strict test-only syscall before the real DBPrintf;
 // no original exception-vector copy/flush is claimed or allowed to run.
 nwii::runtime::expected_stop=DEBUGSTOP;
 ctx->mmu.write32(0x80000060u,0u);
 ctx->mmu.write32(EXC_SOURCE_WORD,template_word);
 ctx->mmu.write32(0x80000100u,0x0DD0D0D0u);
 ctx->gpr[1]=SP-80u;ctx->gpr[13]=R13;
 ctx->lr=0x805208ACu;ctx->pc=EXCEPTION;ctx->is_running=true;
 const uint32_t before_exception=nwii::runtime::call_counts[26];
 const uint32_t before_debug=nwii::runtime::stops;
 bool stopped_at_debug=false;
 try{run_game(*ctx);}catch(const DebugStop&){stopped_at_debug=true;}
 check(stopped_at_debug,"zero low-memory exception path escaped the DBPrintf boundary");
 check(ctx->pc==DEBUGSTOP&&!ctx->is_running,"unexpected debug branch syscall PC");
 check(nwii::runtime::call_counts[26]==before_exception+1u&&
       nwii::runtime::stops==before_debug+1u,"original exception debug path not traced");
 check(ctx->gpr[1]==SP-144u && ctx->mmu.read32(SP-76u)==0x805208ACu,
       "original exception debug branch stack or LR incorrect");
 check(ctx->mmu.read32(0x80000100u)==0x0DD0D0D0u,
       "unimplemented exception vector copy unexpectedly modified memory");
 // Exercise the *second* original __DBIsExceptionMarked call when the first
 // boot-record check falls through and the debug mask is set. The real
 // DBPrintf service is rejected at its instruction address, not HLE-returned.
 nwii::runtime::expected_stop=SECONDDEBUG;
 ctx->mmu.write32(0x80000060u,1u);
 ctx->mmu.write32(BOOT_RECORD,0u);
 ctx->mmu.write32(R13-4160u,0x80045000u);
 ctx->mmu.write32(0x80045004u,1u);
 ctx->gpr[1]=SP-80u;ctx->gpr[13]=R13;
 ctx->lr=0x805208ACu;ctx->pc=EXCEPTION;ctx->is_running=true;
 const uint32_t second_before=nwii::runtime::stops;
 const uint64_t mark_before=nwii::runtime::call_counts[31];
 bool rejected_second=false;
 try {run_game(*ctx);}catch(const SecondDebugStop&){rejected_second=true;}
 check(rejected_second&&!ctx->is_running&&ctx->pc==SECONDDEBUG,
       "second marked-exception path bypassed DBPrintf fail-closed stop");
 check(nwii::runtime::stops==second_before+1u&&
       nwii::runtime::call_counts[31]==mark_before+1u,
       "original second exception-mark helper not dispatched");
 nwii::runtime::expected_stop=ALT;
 // Independent direct calls prove both original arena-setter functions preserve
 // the input value, do not alias one another, and return through the guest LR.
 nwii::runtime::expected_stop=ALT;
 for(const auto& [entry,global,other]:std::array<std::array<uint32_t,3>,4>{{
       {{ARENA_LO,LO_GLOBAL,HI_GLOBAL}},{{ARENA_HI,HI_GLOBAL,LO_GLOBAL}},
       {{MEM2_LO,MEM2_LO_GLOBAL,LO_GLOBAL}},{{MEM2_HI,MEM2_HI_GLOBAL,HI_GLOBAL}}}}){
  const uint32_t value=(entry==ARENA_LO||entry==MEM2_LO)?0x900BA120u:0x93EABCD0u;
  ctx->mmu.write32(global,0u);
  ctx->mmu.write32(other,0xE7E7E7E7u);
  ctx->gpr[3]=value;ctx->pc=entry;ctx->lr=ALT;
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->is_running=true;
  const size_t count_idx=entry==ARENA_LO?21u:entry==ARENA_HI?22u:entry==MEM2_LO?23u:24u;
  const auto before_call=nwii::runtime::call_counts[count_idx];
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==ALT,"direct original MEM1/MEM2 setter failed to return");
  check(ctx->mmu.read32(global)==value,"original MEM1/MEM2 setter discarded operand");
  check(ctx->mmu.read32(other)==0xE7E7E7E7u,"MEM1/MEM2 setter clobbered other global");
  check(ctx->gpr[3]==value&&ctx->gpr[1]==SP&&ctx->lr==ALT,
        "original MEM1/MEM2 setter damaged guest call convention");
  check(nwii::runtime::call_counts[count_idx]==before_call+1u,
        "missing original MEM1/MEM2 setter native entry");
 }
 // Direct original IPC init must preserve arbitrary pointer words, including zeros.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t seed:{0u,0x90000000u,0x93FFFFF0u}){
  const uint32_t high=seed^0xA5A55A5Au;
  ctx->mmu.write32(IPC_LO_HINT,seed);
  ctx->mmu.write32(IPC_HI_HINT,high);
  ctx->mmu.write32(IPC_LO_GLOBAL,0x11112222u);
  ctx->mmu.write32(IPC_HI_GLOBAL,0x33334444u);
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=ALT;ctx->pc=IPC;
  ctx->is_running=true;
  const auto called=nwii::runtime::call_counts[25];
  run_game(*ctx);
  check(!ctx->is_running && ctx->pc==ALT,"direct original IPC function failed to return");
  check(ctx->mmu.read32(IPC_LO_GLOBAL)==seed && ctx->mmu.read32(IPC_HI_GLOBAL)==high,
        "direct original IPC pointer copy differs");
  check(ctx->gpr[1]==SP && ctx->gpr[13]==R13 && ctx->lr==ALT,
        "direct IPC helper corrupted guest calling convention");
  check(nwii::runtime::call_counts[25]==called+1u,"direct original IPC helper not dispatched");
 }
 // Independent direct calls exercise the original PowerPC slw/and mask
 // at indices 0, 1, 7, 31, 32, and 63. The Wii slw returns zero for
 // shift counts >=32 rather than using a modulo-32 host shift.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t index:{0u,1u,7u,31u,32u,63u}){
  for(uint32_t mask:{0u,0xFFFFFFFFu,0x80000081u}){
   ctx->mmu.write32(R13-4160u,0x80045000u);
   ctx->mmu.write32(0x80045004u,mask);
   ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->gpr[3]=index;
   ctx->lr=ALT;ctx->pc=MARK;ctx->is_running=true;
   const auto before_mark=nwii::runtime::call_counts[31];
   run_game(*ctx);
   const uint32_t bit=index>=32u?0u:(1u<<index);
   check(!ctx->is_running&&ctx->pc==ALT,"direct original DBIsExceptionMarked did not return");
   check(ctx->gpr[3]==(mask&bit),"original PPC exception bit mask differs");
   check(ctx->gpr[1]==SP&&ctx->lr==ALT&&ctx->gpr[13]==R13,
         "original exception marker did not preserve guest ABI");
   check(nwii::runtime::call_counts[31]==before_mark+1u,
         "original marker was not natively dispatched");
  }
 }
 // Six direct authentic __RAS_OSDisableInterrupts_begin calls prove the
 // guest MSR bit-16 disable semantics, return value and non-EE preservation.
 // These run with both already-disabled and enabled guest interrupt states;
 // the synthetic ALT stop is only a return sentinel, not a service stub.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t guest_msr:{0u,0x8000u,0x2000u,0xA000u,0x12345678u,0xFFFFFFFFu}){
   ctx->msr=guest_msr;
   ctx->gpr[0]=0xCADE0011u;ctx->gpr[3]=0xBEEF0013u;
   ctx->gpr[4]=0xBEEF0014u;ctx->gpr[5]=0xBEEF0015u;
   ctx->gpr[1]=SP;ctx->gpr[13]=R13;
   ctx->lr=ALT;ctx->pc=DISABLE;ctx->is_running=true;
   const auto before_disabler=nwii::runtime::call_counts[3];
   const auto before_stop=nwii::runtime::stops;
   run_game(*ctx);
   check(!ctx->is_running&&ctx->pc==ALT&&ctx->lr==ALT,
         "direct authentic interrupt-disabler failed to return to guest sentinel");
   check(nwii::runtime::call_counts[3]==before_disabler+1u&&
         nwii::runtime::stops==before_stop+1u,
         "original interrupt-disabler native dispatch/stop count differs");
   check(ctx->gpr[3]==((guest_msr>>15u)&1u),
         "original mfmsr/rlwinm returned wrong previous interrupt enable flag");
   check(ctx->gpr[4]==(guest_msr&~0x8000u)&&
         ctx->msr==(guest_msr&~0x8000u),
         "original mtmsr changed unexpected guest MSR bits");
   check(ctx->gpr[0]==0xCADE0011u&&ctx->gpr[5]==0xBEEF0015u&&
         ctx->gpr[1]==SP&&ctx->gpr[13]==R13,
         "original interrupt disable helper corrupted unrelated guest registers");
 }
 // Direct calls into each authentic two-instruction PPC helper use nonzero
 // operands. This proves value storage (not unconditional zeroing or no-op).
 nwii::runtime::expected_stop=ALT;
 constexpr std::array<uint32_t,6> perf_addr{PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40};
 for(size_t i=0;i<perf_addr.size();++i){
  ctx->mmcr0=0xACDC1234u;ctx->mmcr1=0xBADA0001u;
  ctx->pmc={0x11111111u,0x22222222u,0x33333333u,0x44444444u};
  const std::array<uint32_t,6> previous{ctx->mmcr0,ctx->mmcr1,
      ctx->pmc[0],ctx->pmc[1],ctx->pmc[2],ctx->pmc[3]};
  const uint32_t value=0xDEAD1001u+uint32_t(i*37);
  ctx->gpr[3]=value;
  ctx->pc=perf_addr[i];ctx->lr=ALT;ctx->is_running=true;
  const uint32_t old_stops=nwii::runtime::stops;
  const uint32_t old_helper_calls=nwii::runtime::call_counts[9+i];
  run_game(*ctx);
  check(!ctx->is_running && ctx->pc==ALT,"direct original mtspr did not reach ALT stop");
  check(nwii::runtime::stops==old_stops+1,"direct original mtspr stop missing");
  check(nwii::runtime::call_counts[9+i]==old_helper_calls+1,"helper dispatched incorrectly");
  check(ctx->gpr[3]==value,"original mtspr corrupted source operand");
  const std::array<uint32_t,6> after{ctx->mmcr0,ctx->mmcr1,
      ctx->pmc[0],ctx->pmc[1],ctx->pmc[2],ctx->pmc[3]};
  for(size_t n=0;n<after.size();++n)
    check(after[n]==(n==i?value:previous[n]),"performance SPR alias or mapping wrong");
 }
 // Original HID4 helper with sign bit set: no OSReport and correct 32-bit write.
 nwii::runtime::expected_stop=ALT;
 ctx->hid4=0x13572468u;
 ctx->gpr[3]=0xBEEF4567u;ctx->gpr[31]=0xDA1E0FAFu;
 ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=HID4;ctx->is_running=true;
 const uint32_t first_stop=nwii::runtime::stops;
 const uint32_t first_hid=nwii::runtime::call_counts[19];
 run_game(*ctx);
 check(!ctx->is_running && ctx->pc==ALT,"direct original HID4 did not return to synthetic ALT");
 check(ctx->hid4==0xBEEF4567u,"direct original HID4 nonzero value lost");
 check(ctx->gpr[3]==0xBEEF4567u&&ctx->gpr[31]==0xDA1E0FAFu,"HID4 callee register corruption");
 check(ctx->gpr[1]==SP&&ctx->lr==ALT,"original HID4 direct stack/LR mismatch");
 check(nwii::runtime::stops==first_stop+1&&nwii::runtime::call_counts[19]==first_hid+1,
       "direct original HID4 call tracing mismatch");
 // HID4 bit31 clear must take the original OSReport branch. We stop there
 // deliberately rather than invent a successful host OSReport implementation.
 nwii::runtime::expected_stop=REPORT;
 ctx->hid4=0x55667788u;ctx->gpr[3]=0x00000505u;
 ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=HID4;ctx->is_running=true;
 const uint32_t report_before=nwii::runtime::call_counts[20];
 bool stopped_at_report=false;
 try { run_game(*ctx); } catch(const ReportStop&) { stopped_at_report=true; }
 check(stopped_at_report,"HID4 bit31-clear branch returned from synthetic OSReport stop");
 check(!ctx->is_running&&ctx->pc==REPORT,"HID4 MSB-clear path did not reach OSReport boundary");
 check(ctx->hid4==0x55667788u,"HID4 register changed before OSReport returned");
 check(nwii::runtime::call_counts[20]==report_before+1,"unverified OSReport branch not traced");
 // Independent direct original speculation control preserves all other HID0 bits.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t seed:{0u,0x40000000u,0xFFFFFFFFu}){
  ctx->hid0=seed;ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=SPEC;ctx->is_running=true;
  run_game(*ctx);
  check(ctx->pc==ALT && !ctx->is_running,"PPCDisableSpeculation did not return normally");
  check(ctx->hid0==(seed|0x200u),"PPCDisableSpeculation damaged other HID0 bits");
  check(ctx->gpr[1]==SP&&ctx->lr==ALT,"PPCDisableSpeculation guest ABI damaged");
 }
 // The original FP mode helper ORs FPSCR bit 2 (PowerPC bit number 29).
 for(uint32_t seed:{0u,0xFFFFFFFFu,0x01230000u}){
  ctx->fpscr=seed;ctx->lr=ALT;ctx->pc=NONIEEE;ctx->is_running=true;
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==ALT,"PPCSetFpNonIEEEMode did not return");
  check(ctx->fpscr==(seed|0x4u),"mtfsb1 29 changed unrelated FPSCR bits");
 }
 // Direct original L1 cache initializer: exercise all four HID0 enable-bit paths.
 // The L2CR helper executes but the L2 setup and wait loops are untested.
 nwii::runtime::expected_stop=STOP;
 for(uint32_t bits:{0u,0x8000u,0x4000u,0xC000u}){
  const bool ic_enable=(bits&0x8000u)==0u;
  const bool dc_enable=(bits&0x4000u)==0u;
  const uint32_t seed=0x1A000000u|bits;
  ctx->hid0=seed;
  const uint32_t initial_l2cr=(0x00012340u+uint32_t(bits)) | (bits==0x4000u?1u:0u);
  ctx->l2cr=initial_l2cr;
  const uint32_t prior_msr=(bits&0x8000u)?0x2000u:0xA000u;
  ctx->msr=prior_msr;
  const uint32_t before_l2_sync=ctx->guest_sync_count;
  const uint32_t before_l2_read=nwii::runtime::call_counts[49];
  const uint32_t before_l2_write=nwii::runtime::call_counts[50];
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->gpr[30]=0x4A3B2C1Du;
  ctx->gpr[31]=0xC5D6E7F8u;ctx->lr=ALT;ctx->pc=CACHE;ctx->is_running=true;
  ctx->mmu.write32(SP-12u,0x1234ABCDu);
  const uint32_t prior_debug=nwii::runtime::debug_callbacks;
  const uint32_t prior_sync=ctx->guest_sync_count;
  const uint32_t prior_isync=ctx->guest_isync_count;
  const uint32_t prior_ic=nwii::runtime::call_counts[47];
  const uint32_t prior_dc=nwii::runtime::call_counts[48];
  const uint32_t prior_mfhid0=nwii::runtime::call_counts[15];
  const uint32_t prior_cache=nwii::runtime::call_counts[46];
  bool ended=false;
  try{run_game(*ctx);}catch(const NativeStop&){ended=true;}
  check(ended && !ctx->is_running && ctx->pc==STOP,"direct original cache initializer did not stop before L2 completion polling");
  check(ctx->hid0==(seed|0xC000u),"original ICEnable/DCEnable failed to preserve other HID0 bits");
  check(ctx->gpr[1]==SP-16u && ctx->mmu.read32(SP+4u)==ALT,
        "original L1 cache initializer stack/LR frame mismatch");
  check(ctx->mmu.read32(SP-4u)==0xC5D6E7F8u && ctx->mmu.read32(SP-8u)==0x4A3B2C1Du,
        "original L1 cache initializer saved-register locations differ");
  check(ctx->mmu.read32(SP-12u)==0x1234ABCDu,"original L1 cache initializer overwrote frame canary");
  check(ctx->gpr[31]==0x8060BD48u && ctx->gpr[30]==prior_msr,
        "original L2 setup global pointer/register state mismatch");
  check(ctx->gpr[3]==(initial_l2cr|0x00200000u) &&
        ctx->l2cr==(initial_l2cr|0x00200000u),
        "original L2 setup did not request the guest L2 invalidate bit");
  check(ctx->msr==0x30u && ctx->gpr[30]==prior_msr,
        "original L2 setup failed to save MSR and enter temporary mode");
  check(ctx->guest_sync_count-before_l2_sync==uint32_t(dc_enable)+6u,
        "original L2 prefix barrier count differs");
  check(nwii::runtime::call_counts[49]-before_l2_read==4u &&
        nwii::runtime::call_counts[50]-before_l2_write==3u,
        "original L2 setup read/write helper call count differs");
  check(nwii::runtime::debug_callbacks-prior_debug==uint32_t(ic_enable)+uint32_t(dc_enable),
        "original L1 cache enabled-branch debug callbacks differ");
  check(ctx->guest_sync_count-prior_sync==uint32_t(dc_enable)+6u,
        "original DCEnable sync ordering differs");
  check(ctx->guest_isync_count-prior_isync==uint32_t(ic_enable),
        "original ICEnable isync ordering differs");
  check(nwii::runtime::call_counts[46]==prior_cache+1u &&
        nwii::runtime::call_counts[47]==prior_ic+uint32_t(ic_enable) &&
        nwii::runtime::call_counts[48]==prior_dc+uint32_t(dc_enable) &&
        nwii::runtime::call_counts[15]==prior_mfhid0+2u,
        "original L1 cache function dispatch graph does not match HID0 conditions");
 }
 // The unmodified original PPCMtl2cr helper stores guest-visible SPR 1017.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t value:{0u,0xffffffffu,0x81234567u,0x01234567u,0x80000001u}){
  const uint32_t before_write=nwii::runtime::call_counts[50];
  ctx->l2cr=~value;ctx->gpr[3]=value;
  ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=L2_WRITE;ctx->is_running=true;
  run_game(*ctx);
  check(!ctx->is_running && ctx->pc==ALT,"original PPCMtl2cr did not return");
  check(ctx->l2cr==value && ctx->gpr[3]==value,
        "original PPCMtl2cr did not preserve the guest value");
  check(ctx->gpr[1]==SP && ctx->lr==ALT,"original PPCMtl2cr corrupted guest return");
  check(nwii::runtime::call_counts[50]==before_write+1u,
        "original PPCMtl2cr did not dispatch once");
 }
 // Direct complete original PPCMfl2cr body reads the actual guest L2CR value.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t value:{0u,0x80000000u,0x01234567u,0xffffffffu,0x7fffffffu}){
  const uint32_t prior=nwii::runtime::call_counts[49];
  ctx->l2cr=value;ctx->gpr[3]=0xbadc0ffeu;
  ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=L2_READ;ctx->is_running=true;
  run_game(*ctx);
  check(ctx->pc==ALT && !ctx->is_running,"original PPCMfl2cr did not return");
  check(ctx->gpr[3]==value && ctx->l2cr==value,
        "original PPCMfl2cr returned a stubbed or corrupted value");
  check(ctx->gpr[1]==SP && ctx->lr==ALT,"original PPCMfl2cr damaged calling convention");
  check(nwii::runtime::call_counts[49]==prior+1u,"original PPCMfl2cr not dispatched once");
 }
 // Bit31 set skips original L2 hardware initialization, independently of lower bits.
 nwii::runtime::expected_stop=L2_ENABLED_STOP;
 for(uint32_t value:{0x80000000u,0xffffffffu,0x92345678u,0x80000001u}){
  ctx->l2cr=value;ctx->hid0=0x1a00c000u;
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;
  ctx->gpr[30]=0x44443333u;ctx->gpr[31]=0x55556666u;
  ctx->lr=ALT;ctx->pc=CACHE;ctx->is_running=true;
  const uint32_t previous=nwii::runtime::stops;
  const uint32_t helper_before=nwii::runtime::call_counts[49];
  bool ended=false;
  try{run_game(*ctx);}catch(const NativeStop&){ended=true;}
  check(ended && !ctx->is_running && ctx->pc==L2_ENABLED_STOP,
        "original L2CR enabled branch did not bypass hardware setup");
  check(ctx->l2cr==value && ctx->gpr[3]==value,
        "L2CR original enabled branch changed the guest register value");
  check(ctx->gpr[1]==SP-16u && ctx->mmu.read32(SP+4u)==ALT,
        "original L2CR enabled branch corrupted guest stack or LR");
  check(nwii::runtime::stops==previous+1u && nwii::runtime::call_counts[49]==helper_before+1u,
        "original L2CR enabled branch skipped/duplicated helper dispatch");
 }
 nwii::runtime::expected_stop=STOP;
 check(nwii::runtime::forbidden==0,"interpreter or unexpected syscall reached");
 std::cout << std::dec << "PASS: " << assertions << " V61 integrated original Wii OSInit through authentic L2 setup prefix assertions, 6 OSInit paths + four direct cache cases, no interpreter fallback\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V61 original test failed: "<<e.what()<<'\n';return 1;}
