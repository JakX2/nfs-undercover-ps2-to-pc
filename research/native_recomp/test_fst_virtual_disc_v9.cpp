// All fixture data is synthetic. Tests Wii FST parsing and runtime disc mapping.
#include "runtime/validated_fst_v9.h"
#include "runtime/virtual_disc.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace nwii::runtime;
namespace fs=std::filesystem;
static int assertions=0;
static void check(bool value, const std::string& why) {
    if(!value) throw std::runtime_error(why);
    ++assertions;
}
static void put32(std::vector<uint8_t>& b, size_t index,uint32_t v) {
    b.at(index)=v>>24; b.at(index+1)=v>>16; b.at(index+2)=v>>8; b.at(index+3)=v;
}
static std::vector<uint8_t> fixture() {
    std::string names;
    // Construct with explicit NULs, not a single C string.
    names=std::string("NFS",3)+'\0'+"ZDIR.BIN"+'\0'+"GLOBAL"+'\0'+"GAMEPLAY.BIN"+'\0';
    std::vector<uint8_t> v(5*12+names.size(),0);
    v[0]=1; put32(v,8,5); // root directory with five entries
    v[12]=1;put32(v,12+8,3); // NFS directory; parent 0
    v[24+1]=0;v[24+2]=0;v[24+3]=4;put32(v,24+4,0x1000);put32(v,24+8,4);
    v[36]=1;v[36+3]=13;put32(v,36+8,5);
    v[48+3]=20;put32(v,48+4,0x2000);put32(v,48+8,6);
    std::copy(names.begin(),names.end(),v.begin()+60);
    return v;
}
static void write_file(const fs::path& path, const std::vector<uint8_t>& data) {
    fs::create_directories(path.parent_path());
    std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(data.data()),data.size());
}
static void write_file(const fs::path& path, const std::string& data) {
    write_file(path, std::vector<uint8_t>(data.begin(),data.end()));
}
int main(int argc,char** argv) {
    if (argc!=3) return 2;
    const std::string mode = argv[2];
    if (mode != "wii" && mode != "gc" && mode != "invalid" && mode != "missing") return 2;
    auto fst=fixture();
    ValidatedFstV9 parsed;
    std::string why;
    check(parse_validated_fst_v9(fst,true,parsed,why),why);
    check(parsed.entries==5,"five entries");
    check(parsed.files.size()==2,"two files");
    check(parsed.files[0].guest_path=="NFS/ZDIR.BIN","first guest path");
    check(parsed.files[0].disc_offset==0x4000,"Wii offset shift");
    check(parsed.files[0].size==4,"first size");
    check(parsed.files[1].guest_path=="GLOBAL/GAMEPLAY.BIN","second guest path");
    check(parsed.files[1].disc_offset==0x8000,"second shift");
    check(parse_validated_fst_v9(fst,false,parsed,why),"GC mode");
    check(parsed.files[1].disc_offset==0x2000,"GC offset no shift");
    auto reject=[&](std::vector<uint8_t> src, const std::string& name) {
        check(!parse_validated_fst_v9(src,true,parsed,why),name);
        check(!why.empty(),name+" diagnostic");
    };
    {auto x=fst;x[0]=0;reject(x,"file root");}
    {auto x=fst;put32(x,4,1);reject(x,"bad root parent");}
    {auto x=fst;put32(x,8,9000);reject(x,"count overflow");}
    {auto x=fst;x[24+3]=uint8_t(fst.size());reject(x,"bad name offset");}
    {auto x=fst;put32(x,12+4,1);reject(x,"bad dir parent");}
    {auto x=fst;put32(x,12+8,6);reject(x,"bad dir end");}
    {auto x=fst;put32(x,12+8,1);reject(x,"invalid empty dir end");}
    {auto x=fst;x[24]=3;reject(x,"invalid type");}
    {auto x=fst;x[60+4]='.';x[60+5]='.';x[60+6]=0;reject(x,"dot dot name");}
    {auto x=fst;x[60+4]='/';reject(x,"embedded separator");}
    {auto x=fst;x[60+4]=':';reject(x,"colon name");}
    {auto x=fst;x.back()='X';reject(x,"unterminated name");}
    {auto x=fst;x.resize(5*12);reject(x,"no string table");}
    // Disc load integration. No copyrighted files or fake game content.
    fs::path root=argv[1];fs::remove_all(root);
    std::vector<uint8_t> boot(0x440,0);
    if (mode != "gc") put32(boot,0x18,0x5D1C9EA3);
    else put32(boot,0x1c,0xC2339F3D);
    put32(boot,0x424,mode == "gc" ? 0x10000 : 0x4000);
    while(fst.size()%4) fst.push_back(0);
    put32(boot,0x428,uint32_t(fst.size()/4));
    write_file(root/"sys/boot.bin",boot);
    if (mode == "invalid") fst[12+3] = 0xff;  // corrupt directory name
    write_file(root/"sys/fst.bin",fst);
    write_file(root/"files/nfs/zdir.bin","ABCD");
    if (mode != "missing") write_file(root/"files/global/gameplay.bin","WHEELS");
    auto& disc=VirtualDisc::get();
    if (mode == "invalid") {
        check(!disc.init(root.string()),"malformed FST must reject disc init");
        check(!disc.valid(),"invalid FST must leave VirtualDisc invalid");
        fs::remove_all(root);
        std::cout << "PASS: " << assertions << " synthetic invalid-FST assertions\n";
        return 0;
    }
    check(disc.init(root.string()),"virtual disc init");
    check(disc.valid(),"disc valid");
    check(disc.is_wii() == (mode != "gc"),"correct platform magic");
    check(disc.mapped_fst_files()==(mode == "missing" ? 1u : 2u),"correct FST file count");
    check(disc.unmapped_fst_files()==(mode == "missing" ? 1u : 0u),"correct missing FST count");
    std::array<uint8_t,8> bytes{};
    const uint32_t file_off = mode == "gc" ? 0x1000 : 0x4000;
    const uint32_t gameplay_off = mode == "gc" ? 0x2000 : 0x8000;
    check(disc.read(file_off,4,bytes.data())==4,"ZDIR read count");
    check(std::string(bytes.begin(),bytes.begin()+4)=="ABCD","ZDIR data");
    if (mode != "missing") {
        check(disc.read(gameplay_off,6,bytes.data())==6,"GAMEPLAY read count");
        check(std::string(bytes.begin(),bytes.begin()+6)=="WHEELS","GAMEPLAY data");
    } else {
        check(disc.read(gameplay_off,6,bytes.data())==0,"missing file remains unmapped");
    }
    check(disc.read(file_off+2,6,bytes.data())==2,"partial read count");
    check(bytes[0]=='C'&&bytes[1]=='D'&&bytes[2]==0,"partial read zero gap");
    check(disc.read(0x10000,4,bytes.data())==4,"FST offset mapping");
    check(bytes[0]==1 && bytes[1]==0,"FST bytes");
    fs::remove_all(root);
    std::cout << "PASS: " << assertions << " synthetic FST parser/VirtualDisc assertions\n";
}
