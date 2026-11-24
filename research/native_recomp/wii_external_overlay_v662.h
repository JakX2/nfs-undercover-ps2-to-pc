#pragma once
#include "loader/loader.h"
#include <cstdint>
#include <stdexcept>
#include <vector>
#include <utility>
namespace undercover::wii {
// Translation-only overlay for the original cold-installed external exception
// vector. The DOL must be authenticated by the caller. Runtime entry must
// independently authenticate the guest-installed bytes; this is not delivery.
inline constexpr uint32_t IrqVector=0x80000500u,IrqSource=0x80520ec0u,
    IrqTable=0x8060bbe0u,IrqSize=152u;
inline uint32_t irq_word(const std::vector<uint8_t>& b,unsigned i){
    return uint32_t(b.at(i))<<24|uint32_t(b.at(i+1))<<16|
        uint32_t(b.at(i+2))<<8|uint32_t(b.at(i+3));
}
inline std::vector<uint8_t> irq_span(const nwii::loader::Executable& exe,
                                     uint32_t addr,uint32_t size,bool text){
    std::vector<uint8_t> bytes;
    for(const auto& sec:exe.sections){
        const uint64_t end=uint64_t(sec.address)+sec.size;
        if(end>0x100000000ull||(sec.is_bss?(!sec.data.empty()||sec.is_text):sec.data.size()!=sec.size))
            throw std::runtime_error("IRQ section geometry");
        if(!sec.size||sec.address>=uint64_t(addr)+size||addr>=end)continue;
        if(sec.is_bss||sec.is_text!=text||sec.address>addr||uint64_t(addr)+size>end||!bytes.empty())
            throw std::runtime_error("IRQ source mapping");
        const auto offset=addr-sec.address;
        bytes.assign(sec.data.begin()+offset,sec.data.begin()+offset+size);
    }
    if(bytes.size()!=size)throw std::runtime_error("IRQ source missing");
    return bytes;
}
inline std::vector<uint8_t> external_overlay_image(const nwii::loader::Executable& exe){
    auto image=irq_span(exe,IrqSource,IrqSize,true);
    const auto table=irq_span(exe,IrqTable,60,false);
    for(unsigned i=0;i<15;++i){
        const uint32_t a=irq_word(table,4*i);
        if(a<0x100u||a>0x3000u-256u||(a&31u))throw std::runtime_error("IRQ vector table");
        for(unsigned j=0;j<i;++j){const auto b=irq_word(table,4*j);
            if(a<b+IrqSize&&b<a+IrqSize)throw std::runtime_error("IRQ vector overlap");}
    }
    // Same original installation transformation as V462 and V76. V76
    // authenticated index 4; refuse rather than silently change this route.
    if(irq_word(table,16)!=0x500u)throw std::runtime_error("IRQ vector slot");
    image[0x58]=0x60;image[0x59]=image[0x5a]=image[0x5b]=0;
    image[0x6b]|=4u;
    // A PC-relative immediate branch must still point into the copied body.
    for(unsigned i=0;i<IrqSize;i+=4){
        const uint32_t w=irq_word(image,i),major=w>>26;
        if((major==18u||major==16u)&&!(w&2u)){
            const uint32_t raw=major==18u?w&0x03fffffcu:w&0xfffcu;
            const int64_t disp=int64_t(raw)-((raw&(major==18u?0x02000000u:0x8000u))?(major==18u?0x04000000u:0x10000u):0u);
            const int64_t target=int64_t(i)+disp;
            if(target<0||target>=IrqSize)throw std::runtime_error("IRQ nonrelocatable branch");
        }
    }
    return image;
}
inline void add_external_overlay(nwii::loader::Executable& exe){
    auto image=external_overlay_image(exe);
    for(const auto& sec:exe.sections)
        if(sec.size&&sec.address<uint64_t(IrqVector)+IrqSize&&IrqVector<uint64_t(sec.address)+sec.size)
            throw std::runtime_error("IRQ translation overlay conflict");
    exe.sections.push_back({IrqVector,IrqSize,std::move(image),true,false});
}
}
