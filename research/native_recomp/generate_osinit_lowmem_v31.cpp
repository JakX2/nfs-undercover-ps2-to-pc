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
constexpr uint32_t OSINIT=0x80520670u, STOP=0x80520778u, ALT=0x80520BDCu, REPORT=0x80522F00u;
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
 constexpr std::array<uint32_t,7> guests{OSINIT,GETTIME,DISABLE,EXEC,SAVE,COPY,MFHID0};
 constexpr std::array<uint32_t,7> lengths{REPORT+8-OSINIT,TIME+100-GETTIME,RESTORE+36-DISABLE,36,52,80,HID4+80-MFHID0};
 std::vector<std::pair<uint32_t,uint32_t>> fs,vs;
 for(size_t i=0;i<18;++i){
  const uint32_t off=be32(h.data()+(i<7?0:0x1c)+4*(i<7?i:i-7));
  const uint32_t addr=be32(h.data()+(i<7?0x48:0x64)+4*(i<7?i:i-7));
  const uint32_t n=be32(h.data()+(i<7?0x90:0xac)+4*(i<7?i:i-7));
  if(i<7){require(addr==guests[i]&&n==lengths[i],"wrong private segment geometry");}
  else require(off==0&&addr==0&&n==0,"unexpected extra DOL segment");
  if(i>=7)continue;
  require(off>=256&&(off&3)==0&&uint64_t(off)+n<=uint64_t(bytes),"unsafe DOL section file bounds");
  require(addr>=0x80000000u&&uint64_t(addr)+n<=0x81800000ull,"section outside Wii MEM1");
  for(const auto& [a,b]:fs)require(off>=b || off+n<=a,"overlapping file segments");
  for(const auto& [a,b]:vs)require(addr>=b || addr+n<=a,"overlapping guest segments");
  fs.emplace_back(off,off+n);vs.emplace_back(addr,addr+n);
 }
 require(be32(h.data()+0xe0)==OSINIT,"wrong original OSInit entry");
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
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"private DOL load failed");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({ALT});
 const auto& funcs=analyzer.get_functions();
 for(uint32_t addr:{OSINIT,GETTIME,TIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT,PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40,MFHID0,MTHID0,SPEC,FP,HID4,REPORT})
  require(funcs.count(addr)==1,"missing expected original PPC native function");
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
 // V31 original Wii low-memory boot-info selection, all three paths.
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
 bool bounded_stop=false;for(const auto& ins:os.instructions)if(ins.address==STOP){require(ins.opcode==0x44000002u,"OSInit missing syscall stop");bounded_stop=true;}
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
 std::cout<<"PASS: V31 owner-original OSInit→low-memory boot state native functions="<<funcs.size()<<'\n';
 return 0;
}catch(const std::exception& e){std::cerr<<"V31 generator: "<<e.what()<<'\n';return 1;}
