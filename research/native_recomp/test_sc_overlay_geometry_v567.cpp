#include "wii_sc_overlay_v561.h"
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using nwii::loader::Executable;
using nwii::loader::Section;
static void need(bool b){if(!b)throw std::runtime_error("V567 regression");}
static void word(std::vector<uint8_t>& v,unsigned offset,uint32_t w){
    for(unsigned i=0;i<4;++i)v.at(offset+i)=uint8_t(w>>(24-8*i));
}
static Executable fixture(){
    Executable e;
    std::vector<uint8_t> body(ScSize);
    for(unsigned i=0;i<ScSize;i+=4)word(body,i,0x60000000u);
    word(body,4,0x4c00012cu);word(body,ScSize-4,0x4c000064u);
    e.sections.push_back({ScSource,ScSize,body,true,false});return e;
}
static bool same(const Section& a,const Section& b){
    return a.address==b.address&&a.size==b.size&&a.data==b.data&&a.is_text==b.is_text&&a.is_bss==b.is_bss;
}
static void reject(Executable e,std::string_view why){
    const auto before=e.sections;bool rejected=false;
    try{add_sc_overlay(e);}catch(const std::runtime_error& err){rejected=err.what()==why;}
    need(rejected&&before.size()==e.sections.size());
    for(unsigned i=0;i<before.size();++i)need(same(before[i],e.sections[i]));
}
int main(){
    auto e=fixture();
    // Half-open range boundaries: adjacent BSS must not obstruct the copy.
    e.sections.push_back({ScVector-4,4,{},false,true});
    e.sections.push_back({ScVector+ScSize,4,{},false,true});
    e.sections.push_back({ScVector+4,0,{},false,true});
    const auto before=e.sections;
    add_sc_overlay(e);
    need(e.sections.size()==before.size()+1);
    for(unsigned i=0;i<before.size();++i)need(same(before[i],e.sections[i]));
    need(same(e.sections.back(),{ScVector,ScSize,before[0].data,true,false}));
    reject(e,"SC translation overlay conflict");
    for(unsigned i=0;i<3;++i){auto f=fixture();
        const uint32_t a=i==0?ScVector-3:i==1?ScVector:ScVector+ScSize-1;
        f.sections.push_back({a,4,{},false,true});reject(f,"SC translation overlay conflict");}
    {auto f=fixture();f.sections.push_back({ScVector,4,std::vector<uint8_t>(4),false,false});reject(f,"SC translation overlay conflict");}
    {auto f=fixture();f.sections[0].size--;reject(f,"SC section geometry");}
    {auto f=fixture();f.sections.push_back({0xffffffffu,2,{},false,true});reject(f,"SC section geometry");}
    {auto f=fixture();f.sections.push_back({ScVector,4,{0},false,true});reject(f,"SC section geometry");}
    {auto f=fixture();f.sections.push_back({ScSource+4,4,{},false,true});reject(f,"SC source overlap");}
    {auto f=fixture();f.sections.push_back(f.sections[0]);reject(f,"SC source ambiguous");}
    {auto f=fixture();f.sections.clear();reject(f,"SC source missing");}
    {auto f=fixture();word(f.sections[0].data,0,0x48000004u);reject(f,"SC vector control flow");}
    {auto f=fixture();word(f.sections[0].data,0,0x44000002u);reject(f,"SC vector control flow");}
    {auto f=fixture();word(f.sections[0].data,0,0x4c000064u);reject(f,"SC vector control flow");}
    {auto f=fixture();word(f.sections[0].data,ScSize-4,0x60000000u);reject(f,"SC vector return");}
    std::cout<<"V567_SC_GEOMETRY accepted=1 refusals=15 unchanged_on_rejection=1\n";
}
