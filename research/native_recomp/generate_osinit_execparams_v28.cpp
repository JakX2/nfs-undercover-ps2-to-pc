// Owner-original Wii OSInit prefix → original time/interrupt/exec-params dispatcher.
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
constexpr uint32_t OSINIT=0x80520670u, STOP=0x805206C0u, ALT=0x80520BDCu;
constexpr uint32_t TIME=0x8052A844u,GETTIME=0x8052A824u,DISABLE=0x805265ACu;
constexpr uint32_t RESTORE=0x805265D4u, EXEC=0x80523B1Cu,SAVE=0x805450E8u,COPY=0x80004338u;
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
 constexpr std::array<uint32_t,6> guests{OSINIT,GETTIME,DISABLE,EXEC,SAVE,COPY};
 constexpr std::array<uint32_t,6> lengths{ALT+8-OSINIT,TIME+100-GETTIME,RESTORE+36-DISABLE,36,52,80};
 std::vector<std::pair<uint32_t,uint32_t>> fs,vs;
 for(size_t i=0;i<18;++i){
  const uint32_t off=be32(h.data()+(i<7?0:0x1c)+4*(i<7?i:i-7));
  const uint32_t addr=be32(h.data()+(i<7?0x48:0x64)+4*(i<7?i:i-7));
  const uint32_t n=be32(h.data()+(i<7?0x90:0xac)+4*(i<7?i:i-7));
  if(i<6){require(addr==guests[i]&&n==lengths[i],"wrong private segment geometry");}
  else require(off==0&&addr==0&&n==0,"unexpected extra DOL segment");
  if(i>=6)continue;
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
 for(uint32_t addr:{OSINIT,GETTIME,TIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT})
  require(funcs.count(addr)==1,"missing expected original PPC native function");
 const auto& os=funcs.at(OSINIT);
 require(!os.instructions.empty()&&os.instructions[0].opcode==0x9421FFB0u, "original OSInit frame prologue changed");
 call(os,OSINIT+0x10,SAVE,true);
 call(os,OSINIT+0x38,TIME,true);
 call(os,OSINIT+0x44,DISABLE,true);
 call(os,OSINIT+0x4c,EXEC,true);
 call(funcs.at(TIME),TIME+0x20,GETTIME,true);
 call(funcs.at(TIME),TIME+0x3c,RESTORE,true);
 call(funcs.at(EXEC),EXEC+20,COPY,false);
 for(uint32_t pc:{ALT}){
  const auto& f=funcs.at(pc);
  require(f.instructions.size()==2&&f.instructions[0].opcode==0x44000002u&&
          f.instructions[1].opcode==0x4e800020u,"synthetic stop location changed");
 }
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
 std::cout<<"PASS: V28 owner-original OSInit→exec-params native functions="<<funcs.size()<<'\n';
 return 0;
}catch(const std::exception& e){std::cerr<<"V28 generator: "<<e.what()<<'\n';return 1;}
