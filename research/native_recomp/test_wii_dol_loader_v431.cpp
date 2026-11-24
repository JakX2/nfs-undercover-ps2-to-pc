#include "wii_dol_loader_v431.h"
#include <iostream>
#include <sstream>
#include <string>
#include <stdexcept>
#ifdef V431_PINNED_LOADER
#include "loader/loader.h"
#include <filesystem>
#include <fstream>
using Section=nwii::loader::Section;
#else
struct Section{uint32_t address,size;std::vector<uint8_t> data;bool is_text,is_bss;};
#endif
using undercover::wii::load_strict_dol;
static void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
static void put(std::string& s,unsigned at,uint32_t v){for(unsigned k=0;k<4;++k)s[at+k]=static_cast<char>(uint8_t(v>>(24-8*k)));}
static std::string fixture(){
    std::string s(280,'\0');
    put(s,0,256);put(s,0x48,0x80004000);put(s,0x90,8);
    put(s,0x1c,264);put(s,0x64,0x90001000);put(s,0xac,16);
    put(s,0xd8,0x90000ff0);put(s,0xdc,64);put(s,0xe0,0x80004004);
    put(s,256,0x12345678u);put(s,260,0x87654321u);for(unsigned i=264;i<280;++i)s[i]=static_cast<char>(i-264);
    return s;
}
static bool valid(uint32_t entry,const std::vector<Section>& sections){
    return entry==0x80004004u&&sections.size()==3&&sections[0].address==0x80004000u&&sections[0].size==8&&sections[0].is_text&&!sections[0].is_bss&&sections[0].data==std::vector<uint8_t>{0x12,0x34,0x56,0x78,0x87,0x65,0x43,0x21}&&sections[1].address==0x90001000u&&sections[1].size==16&&!sections[1].is_text&&!sections[1].is_bss&&sections[1].data.size()==16&&sections[1].data[15]==15&&sections[2].address==0x90000ff0u&&sections[2].size==64&&sections[2].is_bss&&sections[2].data.empty();
}
int main(int argc,char** argv){
    uint32_t entry=0;std::vector<Section> sections;
#ifdef V431_PINNED_LOADER
    need(argc==2,"temporary DOL path required");nwii::loader::Executable exe;
    const std::filesystem::path path=argv[1];need(!std::filesystem::exists(path),"existing fixture");
    auto load=[&](const std::string& s){std::ofstream f(path,std::ios::binary|std::ios::trunc);f.write(s.data(),std::streamsize(s.size()));f.close();need(bool(f),"fixture write");bool ok=exe.load_dol(path.string());std::filesystem::remove(path);entry=exe.entry_point;sections=exe.sections;return ok;};
#else
    (void)argc;(void)argv;
    auto load=[&](const std::string& s){std::istringstream stream(s,std::ios::binary);return load_strict_dol(stream,entry,sections);};
#endif
    const auto good=fixture();need(load(good)&&valid(entry,sections),"valid Wii image");
    const std::array<std::pair<unsigned,uint32_t>,13> bad{{{0,0},{0,252},{0x90,12},{0x90,7},{0x48,0x80004001},{0x48,0xcd000000},{0x64,0x80004004},{0x64,0x93fffff8},{0x1c,0xfffffffcu},{0xac,0xffffffffu},{0xd8,0x94000000},{0xe0,0x90001000},{0xe0,0x80004005}}};
    for(auto [at,w]:bad){auto b=good;put(b,at,w);need(!load(b)&&valid(entry,sections),"invalid image changed previous loaded state");}
    for(unsigned n:{0u,255u,256u,263u,264u,279u})need(!load(good.substr(0,n))&&valid(entry,sections),"truncation accepted");
    auto overlap=good;put(overlap,0x1c,260);put(overlap,0xac,16);need(!load(overlap)&&valid(entry,sections),"file overlap accepted");
    need(load(good)&&valid(entry,sections),"reload accumulated sections");
    std::cout<<"PASS: strict transactional Wii DOL loader, valid reload, BSS overlap and 20 invalid images\n";
}
