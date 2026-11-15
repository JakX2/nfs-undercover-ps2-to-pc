// Owner-original Wii OSInit low-memory boot-info handoff with verified native helpers.
// Generated game-derived C++ stays in an ephemeral private directory.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t OSINIT=0x80520670u, STOP=0x80520DA4u,EXC_BEGIN=0x80520CA8u,FIRSTSTOP=0x80520CDCu,MARK=0x804E50A0u,IPC=0x8052AE80u, EXCEPTION=0x80520BF4u, DEBUGSTOP=0x80520C44u, POSTSTOP=0x805208ACu, ALT=0x80520BDCu, REPORT=0x80522F00u;
constexpr uint32_t DATA_GUEST=0x90050000u, TEMPLATE_SIZE=0x98u, MEMCPY_SOURCE=0x80520EC0u;
constexpr uint32_t ARENA_LO=0x80521D60u,ARENA_HI=0x80521D48u, MEM2_LO=0x80521D68u,MEM2_HI=0x80521D50u;
constexpr uint32_t TIME=0x8052A844u,GETTIME=0x8052A824u,DISABLE=0x805265ACu;
constexpr uint32_t RESTORE=0x805265D4u, EXEC=0x80523B1Cu,SAVE=0x805450E8u,COPY=0x80004338u,PERF=0x804B7964u,
                   MFHID0=0x804B7920u, MTHID0=0x804B7928u, SPEC=0x804B7A00u,
                   FP=0x804B7A28u, HID4=0x804B7A30u;
void require(bool b,const std::string& why){if(!b)throw std::runtime_error(why);}
uint32_t be32(const uint8_t* p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
uint32_t target(uint32_t op,uint32_t pc,bool link){
 require(op>>26==18 && bool(op&1)==link,"unexpected guest branch opcode/link");
 int32_t d=static_cast<int32_t>(op&0x03fffffcu);
 if(d&0x02000000)d-=0x04000000;
 return (op&2)?uint32_t(d):pc+uint32_t(d);
}
void verify_dol(const std::filesystem::path& file){
 std::ifstream f(file,std::ios::binary|std::ios::ate);
 require(bool(f),"missing private DOL");
 auto bytes=f.tellg();require(bytes>=256&&bytes<1024*1024,"private slice file size out of bounds");
 f.seekg(0);std::array<uint8_t,256> h{};
 require(bool(f.read(reinterpret_cast<char*>(h.data()),256)),"truncated DOL header");
 constexpr std::array<uint32_t,7> guests{OSINIT,GETTIME,DISABLE,SAVE,COPY,MFHID0,MARK};
 constexpr std::array<uint32_t,7> lengths{EXEC+36-OSINIT,IPC+24-GETTIME,RESTORE+36-DISABLE,52,80,HID4+80-MFHID0,24};
 std::vector<std::pair<uint32_t,uint32_t>> fs,vs;
 for(size_t i=0;i<18;++i){
  const uint32_t off=be32(h.data()+(i<7?0:0x1c)+4*(i<7?i:i-7));
  const uint32_t addr=be32(h.data()+(i<7?0x48:0x64)+4*(i<7?i:i-7));
  const uint32_t n=be32(h.data()+(i<7?0x90:0xac)+4*(i<7?i:i-7));
  if(i<7){require(addr==guests[i]&&n==lengths[i],"wrong private segment geometry");}
  else if(i==7)require(addr==DATA_GUEST&&n==TEMPLATE_SIZE,"invalid private template-oracle data section");
  else require(off==0&&addr==0&&n==0,"unexpected extra DOL segment");
  if(i>=8)continue;
  require(off>=256&&(off&3)==0&&uint64_t(off)+n<=uint64_t(bytes),"unsafe DOL section file bounds");
  if(i<7)require(addr>=0x80000000u&&uint64_t(addr)+n<=0x81800000ull,"text section outside Wii MEM1");
  else require(addr>=0x90000000u&&uint64_t(addr)+n<=0x94000000ull,"private template data outside Wii MEM2");
  for(const auto& [a,b]:fs)require(off>=b || off+n<=a,"overlapping file segments");
  for(const auto& [a,b]:vs)require(addr>=b || addr+n<=a,"overlapping guest segments");
  fs.emplace_back(off,off+n);vs.emplace_back(addr,addr+n);
 }
 require(be32(h.data()+0xe0)==OSINIT,"wrong original OSInit entry");
}
uint64_t hash_guest_range(const std::filesystem::path& file,uint32_t guest,uint32_t count){
 std::ifstream in(file,std::ios::binary);
 require(bool(in),"cannot open bounded private Wii image");
 std::array<uint8_t,256> h{};
 require(bool(in.read(reinterpret_cast<char*>(h.data()),h.size())),"short private DOL header");
 for(unsigned i=0;i<8;++i){
  const unsigned idx=i<7?i:i-7;
  const uint32_t offset=be32(h.data()+(i<7?0u:0x1cu)+idx*4u);
  const uint32_t address=be32(h.data()+(i<7?0x48u:0x64u)+idx*4u);
  const uint32_t size=be32(h.data()+(i<7?0x90u:0xacu)+idx*4u);
  if(address<=guest && uint64_t(guest)+count<=uint64_t(address)+size){
   in.seekg(offset+(guest-address));
   uint64_t hash=0xcbf29ce484222325ULL;
   for(uint32_t j=0;j<count;++j){
    char byte=0;
    require(bool(in.get(byte)),"private PPC span truncated");
    hash=(hash^static_cast<uint8_t>(byte))*0x100000001b3ULL;
   }
   return hash;
  }
 }
 throw std::runtime_error("private PPC span not mapped in DOL");
}
void call(const nwii::analyzer::Function& f,uint32_t site,uint32_t destination,bool link){
 bool found=false;
 for(const auto& ins:f.instructions)if(ins.address==site){
  require(target(ins.opcode,site,link)==destination,"original helper call edge changed");found=true;
 }
 require(found,"required guest callsite not emitted");
}
}
int main(int argc,char** argv)try{
 require(argc==3,"usage: generator PRIVATE.DOL EMPTY_DIR");
 const std::filesystem::path out=argv[2];
 require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"output must be an existing empty directory");
 verify_dol(argv[1]);
 // Pinned original-memory and new exception-template control-flow spans.
 // No original proprietary instruction bytes are embedded in this file.
 // These hashes do not embed or publish the proprietary instruction bytes.
 require(hash_guest_range(argv[1],0x80520778u,0xA0u)==0x7CB52713F78E998AULL,
         "original MEM1 arena decision instructions mutated");
 require(hash_guest_range(argv[1],ARENA_LO,8u)==0xAD07D28C2FA00A6FULL,
         "original MEM1 low setter mutated");
 require(hash_guest_range(argv[1],ARENA_HI,8u)==0x83DB8A0654AAD50AULL,
         "original MEM1 high setter mutated");
 require(hash_guest_range(argv[1],0x80520818u,0x8cu)==0x563547C9D2B36D13ULL,
         "original MEM2 arena decision instructions mutated");
 require(hash_guest_range(argv[1],MEM2_LO,8u)==0x8C683A47DCF468E3ULL,
         "original MEM2 low setter mutated");
 require(hash_guest_range(argv[1],MEM2_HI,8u)==0x514ADD19ADBFB3B6ULL,
         "original MEM2 high setter mutated");
 require(hash_guest_range(argv[1],IPC,24u)==0x0681BB6336A400EDULL,
         "original IPC buffer initialization function mutated");
 require(hash_guest_range(argv[1],EXCEPTION,DEBUGSTOP-EXCEPTION)==0x641A7099333A4650ULL,
         "authentic OSExceptionInit entry/stack prologue mutated");
 require(hash_guest_range(argv[1],DEBUGSTOP+8,EXC_BEGIN-DEBUGSTOP-8)==0x80E73439D5BD5FC7ULL,
         "authentic exception initial branch or state setup mutated");
 require(hash_guest_range(argv[1],0x80520F28u,4u)==0x3820B63C4F205A0DULL,
         "original exception-template source word mutated");
 require(hash_guest_range(argv[1],EXC_BEGIN,FIRSTSTOP-EXC_BEGIN)==0x20C9C8A5B430BD8FULL,
         "original pre-mark exception branch mutated");
 require(hash_guest_range(argv[1],0x80520CE4u,0x80520D80u-0x80520CE4u)==0x01D1DCB4D7272177ULL,
         "original pre-second-mark exception branch mutated");
 require(hash_guest_range(argv[1],0x80520D80u,0x24u)==0x51C47C11E5B17D24ULL,
         "original exception-vector target and memcpy instructions mutated");
 require(hash_guest_range(argv[1],DATA_GUEST,TEMPLATE_SIZE)==0x2578204771B7EB49ULL,
         "private original exception-vector template source mutated");
 require(hash_guest_range(argv[1],MARK,24u)==0x172F67A051957DA5ULL,
         "original __DBIsExceptionMarked helper mutated");

 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"private DOL load failed");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({ALT});
 const auto& funcs=analyzer.get_functions();
 for(uint32_t addr:{OSINIT,GETTIME,TIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT,PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40,MFHID0,MTHID0,SPEC,FP,HID4,REPORT,ARENA_LO,ARENA_HI,MEM2_LO,MEM2_HI,IPC,EXCEPTION,MARK})
  require(funcs.count(addr)==1,"missing expected original PPC native function");
 
 require(funcs.size()==32u,"V42 expected 32 bounded native function entries including 4 guarded address operands");
 for(uint32_t addr:{ARENA_LO,ARENA_HI}){
  const auto& f=funcs.at(addr).instructions;
  require(f.size()==2u&&f.back().opcode==0x4e800020u,"original MEM1 arena setter incomplete");
  const uint32_t word=f[0].opcode;
  require((word>>26)==36u&&((word>>21)&31u)==3u&&((word>>16)&31u)==13u,
          "unexpected MEM1 arena write operand");
  const int32_t disp=static_cast<int16_t>(word&0xffffu);
  require(disp==(addr==ARENA_LO?-16400:-3472),"MEM1 global displacement changed");
 }
 const auto& os=funcs.at(OSINIT);
 require(!os.instructions.empty()&&os.instructions[0].opcode==0x9421FFB0u, "original OSInit frame prologue changed");
 call(os,OSINIT+0x10,SAVE,true);
 call(os,OSINIT+0x38,TIME,true);
 call(os,OSINIT+0x44,DISABLE,true);
 call(os,OSINIT+0x4c,EXEC,true);
 constexpr std::array<uint32_t,6> perf_sprs{952,956,953,954,957,958};
 for(size_t i=0;i<perf_sprs.size();++i){
  const uint32_t pc=PERF+static_cast<uint32_t>(8*i);
  call(os,OSINIT+0x54u+static_cast<uint32_t>(8*i),pc,true);
  const auto& helper=funcs.at(pc).instructions;
  require(helper.size()==2&&helper[1].opcode==0x4e800020u,
          "original performance-register helper incomplete");
  const uint32_t opcode=helper[0].opcode;
  require(opcode>>26==31 && ((opcode>>1)&0x3ff)==467 &&
          ((opcode>>21)&31)==3 &&
          (((opcode>>11)&31)<<5 | ((opcode>>16)&31))==perf_sprs[i],
          "original PPC mtspr mapping/operand changed");
 }

 call(funcs.at(TIME),TIME+0x20,GETTIME,true);
 call(funcs.at(TIME),TIME+0x3c,RESTORE,true);
 call(funcs.at(EXEC),EXEC+20,COPY,false);
 for(uint32_t pc:{ALT,REPORT}){
  const auto& f=funcs.at(pc);
  require(f.instructions.size()==2&&f.instructions[0].opcode==0x44000002u&&
          f.instructions[1].opcode==0x4e800020u,"synthetic stop location changed");
 }
 // Additional genuine Wii hardware and FP setup calls.
 call(os,0x805206f4u,HID4,true);
 call(os,0x805206f8u,SPEC,true);
 call(os,0x805206fcu,FP,true);
 call(funcs.at(SPEC),SPEC+0x0cu,MFHID0,true);
 call(funcs.at(SPEC),SPEC+0x14u,MTHID0,true);
 const auto& hid4=funcs.at(HID4).instructions;
 require(hid4.size()==20u && hid4.back().opcode==0x4e800020u,
         "original PPCMthid4 function incomplete");
 require(hid4[3].opcode==0x54600001u && hid4[6].opcode==0x4182000cu &&
         hid4[13].opcode==0x67ff8000u,
         "original HID4 high-bit guard or report-fallback merge changed");
 call(funcs.at(HID4),HID4+0x30u,REPORT,true);
 for(uint32_t pc:{MFHID0,MTHID0}){
  const auto& body=funcs.at(pc).instructions;
  require(body.size()==2u && body.back().opcode==0x4e800020u,
          "original HID0 accessor incomplete");
  const auto op=body.front().opcode;
  require(op>>26==31 && ((op>>1)&0x3ffu)==(pc==MFHID0?339u:467u) &&
          ((((op>>11)&31u)<<5)|((op>>16)&31u))==1008u,
          "HID0 SPR access changed");
 }
 for(uint32_t pc:{HID4+0x1cu,HID4+0x38u}){
  bool found=false;
  for(const auto& ins:hid4)if(ins.address==pc){
   const uint32_t op=ins.opcode;
   require(op>>26==31&&((op>>1)&0x3ffu)==467u&&
           ((((op>>11)&31u)<<5)|((op>>16)&31u))==1011u,
           "HID4 SPR mapping changed");found=true;
  }
  require(found,"HID4 original instruction missing");
 }
 const auto& spec=funcs.at(SPEC).instructions;
 require(spec.size()==10u && spec[4].opcode==0x60630200u && spec.back().opcode==0x4e800020u,
         "original speculative-execution control incomplete");
 const auto& fp=funcs.at(FP).instructions;
 require(fp.size()==2u&&fp.front().opcode==0xffa0004cu&&
         fp.back().opcode==0x4e800020u,"original non-IEEE FP setup changed");
 // V32 original Wii low-memory boot-info selection, all three paths.
 // No surrogate service calls or branch changes are allowed in this interval.
 auto guest_ins=[&](uint32_t pc)->uint32_t {
   for(const auto& ins:os.instructions)if(ins.address==pc)return ins.opcode;
   throw std::runtime_error("missing original Wii OSInit low-memory instruction");
 };
 for(const auto& [pc,opcode] : std::array<std::pair<uint32_t,uint32_t>,8>{{
     {0x80520700u,0x38000000u}, {0x80520704u,0x3c808000u},
     {0x80520718u,0x2c050000u}, {0x8052071cu,0x41820028u},
     {0x80520740u,0x48000028u}, {0x8052074cu,0x4182001cu},
     {0x80520768u,0x38000001u}, {0x8052076cu,0x3c808000u}}})
   require(guest_ins(pc)==opcode,"original low-memory branch/selector changed");
 constexpr std::array<std::pair<uint32_t,uint32_t>,18> lowmem_access{{
     {0x80520708u,0x908DF248u},{0x8052070cu,0x900DF244u},
     {0x80520710u,0x900DBE20u},{0x80520714u,0x80A400F4u},
     {0x80520724u,0x906DF244u},{0x80520728u,0x80050024u},
     {0x8052072cu,0x900DF370u},{0x80520730u,0x8005000cu},
     {0x80520734u,0x980430e8u},{0x80520738u,0x800DF370u},
     {0x8052073cu,0x980430e9u},{0x80520744u,0x80040034u},
     {0x80520750u,0x886430e8u},{0x80520758u,0x906DF240u},
     {0x8052075cu,0x900DF244u},{0x80520760u,0x880430e9u},
     {0x80520764u,0x900DF370u},{0x80520770u,0x900DBE20u}}};
 for(const auto& [pc,opcode]:lowmem_access)
   require(guest_ins(pc)==opcode,"original low-memory source load/store changed");
 require(guest_ins(0x80520774u)==0x8064310cu &&
         guest_ins(0x80520720u)==0x3865000cu &&
         guest_ins(0x80520748u)==0x2c000000u &&
         guest_ins(0x80520754u)==0x380DF240u,
         "original low-memory boot address arithmetic changed");
 // The new original branch tree selects guest MEM1 arena bounds.
 call(os,0x805207e8u,ARENA_LO,true);
 call(os,0x80520814u,ARENA_HI,true);
 call(os,0x8052088cu,MEM2_LO,true);
 call(os,0x805208a0u,MEM2_HI,true);
 call(os,0x805208a4u,IPC,true);
 call(os,0x805208a8u,EXCEPTION,true);
 require(guest_ins(POSTSTOP)==0x44000002u,"unimplemented OSInit system-call service not guarded");
 const auto& exc=funcs.at(EXCEPTION).instructions;
 require(!exc.empty()&&exc.front().address==EXCEPTION&&exc.front().opcode==0x9421FFC0u,
         "missing authentic exception prologue");
 call(funcs.at(EXCEPTION),EXCEPTION+0x10u,SAVE,true);
 call(funcs.at(EXCEPTION),0x80520CC4u,MARK,true);
 call(funcs.at(EXCEPTION),0x80520CF0u,MARK,true);
 call(funcs.at(EXCEPTION),0x80520D98u,COPY,true);
 // V42 intentionally stops BEFORE the original DCFlushRangeNoSync call.
 const auto& marked=funcs.at(MARK).instructions;
 require(marked.size()==6u && marked.front().opcode==0x808DEFC0u &&
         marked[4].opcode==0x7C630038u && marked.back().opcode==0x4E800020u,
         "original exception mark bit-mask function incomplete");
 bool found_stop=false,found_debug=false,found_first=false,found_second=false;
 for(const auto& ins:exc){
   if(ins.address==STOP){require(ins.opcode==0x44000002u,"missing exception normal boundary");found_stop=true;}
   if(ins.address==FIRSTSTOP){require(ins.opcode==0x44000002u,"missing first debug boundary");found_first=true;}
   if(ins.address==0x80520D08u){require(ins.opcode==0x44000002u,"missing second debug boundary");found_second=true;}
   if(ins.address==DEBUGSTOP){require(ins.opcode==0x44000002u,"missing exception DBPrintf guard");found_debug=true;}
 }
 require(found_stop&&found_debug&&found_first&&found_second,"exception branches are not safely bounded");
 auto required_opcode=[&](const std::vector<nwii::analyzer::Instruction>& f,uint32_t pc,uint32_t op){
   for(const auto& ins:f)if(ins.address==pc){
     require(ins.opcode==op,"synthetic exception stop/return changed"); return;
   }
   throw std::runtime_error("missing bounded exception syscall/return");
 };
 required_opcode(exc,DEBUGSTOP+4,0x4e800020u);
 required_opcode(exc,STOP+4,0x4e800020u);
 required_opcode(exc,0x80520D0Cu,0x7ea5ab78u); // original live continuation after second debug guard
 required_opcode(exc,FIRSTSTOP+4,0x480000d8u); // original branch following guarded debug service
 required_opcode(os.instructions,POSTSTOP+4,0x4e800020u);
 for(uint32_t pc:{0x80520E98u,0x80520E9Cu,0x80520EC0u,0x80520F58u}){
   const auto& f=funcs.at(pc).instructions;
   require(!f.empty()&&f.front().opcode==0x44000002u,
           "analyzer-conservative address target must fail closed");
 }

 const auto& ipc=funcs.at(IPC).instructions;
 require(ipc.size()==6 && ipc.back().opcode==0x4e800020u,
         "original IPC-buffer helper incomplete");
 const auto opcode_field=[](uint32_t w,unsigned shift)->uint32_t{return (w>>shift)&31u;};
 require(ipc[0].opcode>>26==15u && opcode_field(ipc[0].opcode,21)==3u &&
         (ipc[0].opcode&0xffffu)==0x8000u,
         "original IPC low-memory base changed");
 constexpr std::array<int32_t,4> ipc_offsets{0x3130,-16336,0x3134,-3352};
 for(unsigned i=1;i<=4;++i){
  const uint32_t op=ipc[i].opcode;
  require((op>>26)==((i&1u)?32u:36u) && opcode_field(op,21)==0u &&
          opcode_field(op,16)==((i&1u)?3u:13u) &&
          static_cast<int16_t>(op&0xffffu)==ipc_offsets[i-1],
          "original IPC buffer load/store layout changed");
 }
 for(const auto& [guest,disp] : std::array<std::pair<uint32_t,int32_t>,2>{{
   {MEM2_LO,-16396},{MEM2_HI,-3468}}}){
   const auto& entries=funcs.at(guest).instructions;
   require(entries.size()==2u&&entries.back().opcode==0x4e800020u,"original MEM2 arena helper incomplete");
   const uint32_t op=entries.front().opcode;
   require(op>>26==36u&&((op>>21)&31u)==3u&&((op>>16)&31u)==13u&&
           static_cast<int16_t>(op&0xffffu)==disp,"original MEM2 write destination or source changed");
 }
 for(const auto& [pc,opcode] : std::array<std::pair<uint32_t,uint32_t>,8>{{
   {0x80520818u,0x3c608000u},{0x8052081cu,0x80633124u},
   {0x80520820u,0x2c030000u},{0x80520828u,0x3ca08075u},
   {0x80520890u,0x3c608000u},{0x80520894u,0x80633128u},
   {0x80520898u,0x2c030000u},{0x8052089cu,0x41820008u}}})
   require(guest_ins(pc)==opcode,"original MEM2 low-memory selection instruction changed");
 for(const auto& [pc,opcode]:std::array<std::pair<uint32_t,uint32_t>,4>{{
   {0x80520778u,0x2c030000u},{0x80520780u,0x3c608075u},
   {0x80520784u,0x38633cc0u},{0x80520810u,0x38630000u}}})
   require(guest_ins(pc)==opcode,"original MEM1 arena selection changed");
 bool bounded_stop=false;for(const auto& ins:os.instructions)if(ins.address==POSTSTOP){require(ins.opcode==0x44000002u,"OSInit missing post-exception syscall guard");bounded_stop=true;}
 require(bounded_stop,"OSInit continuation stop missing");
 require(funcs.at(EXEC).instructions.size()==9u,"original OSGetExecParams incomplete");
 const auto& e=funcs.at(EXEC).instructions;
 require(e[0].opcode==0x3CA08000u&&e[1].opcode==0x808530F0u&&
         e[4].opcode==0x38A0001Cu&&e[6].opcode==0x38000000u&&
         e[7].opcode==0x90030000u,"original OSGetExecParams memory effects changed");
 const auto& get=funcs.at(GETTIME).instructions;
 require(get[0].opcode==0x7C6D42E6u&&get[1].opcode==0x7C8C42E6u&&
         get[2].opcode==0x7CAD42E6u,"original timebase high-low-high loop changed");
 bool flag=false,low=false,high=false;
 for(const auto& ins:os.instructions){
   if(ins.address==OSINIT+0x34){require(ins.opcode==0x900DF21Cu,"original OSInit flag store changed");flag=true;}
   if(ins.address==OSINIT+0x3C){require(ins.opcode==0x908DF254u,"original OSInit low time store changed");low=true;}
   if(ins.address==OSINIT+0x40){require(ins.opcode==0x906DF250u,"original OSInit high time store changed");high=true;}
 }
 require(flag&&low&&high,"original OSInit global stores missing");
 require(funcs.at(COPY).instructions.size()==20u,"original memcpy incomplete");
 require(funcs.at(GETTIME).instructions.size()==6u,"original OSGetTime incomplete");
 require(funcs.at(TIME).instructions.size()==25u,"original system-time function incomplete");
 require(funcs.at(DISABLE).instructions.size()==5u,"original interrupt disable incomplete");
 require(funcs.at(RESTORE).instructions.size()==9u,"original interrupt restore incomplete");
 require(funcs.at(SAVE).instructions.size()==13u,"original save-gpr helper incomplete");
 for(uint32_t addr:{GETTIME,TIME,DISABLE,RESTORE,EXEC,SAVE,COPY}){
   const auto& ins=funcs.at(addr).instructions;
   require(!ins.empty()&&ins.back().opcode==0x4e800020u,
           "original Wii helper missing terminal BLR");
 }
 nwii::recomp::RecompilerConfig config;config.output_dir=out.string();config.split_output=false;
 nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
 const auto outputs=recomp.generate_cpp(OSINIT);
 require(outputs.size()==1&&outputs[0]=="output.cpp","unexpected generated C++ layout");
 std::cout<<"PASS: V42 original Wii exception-vector memcpy natively dispatched, functions="<<funcs.size()<<'\n';
 return 0;
}catch(const std::exception& e){std::cerr<<"V42 generator: "<<e.what()<<'\n';return 1;}
