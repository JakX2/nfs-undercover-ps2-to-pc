#pragma once
#include <array>
#include <cstdint>
#include <istream>
#include <limits>
#include <new>
#include <utility>
#include <vector>

namespace undercover::wii {
// Wii/GC cached guest RAM only. This is an opt-in DOL loader, not an ELF,
// Wii U or REL loader. BSS may encompass initialized sections: the pinned
// runtime clears BSS first, then copies the initialized bytes.
template<class Section>
bool load_strict_dol(std::istream& stream,uint32_t& entry,std::vector<Section>& sections){
    constexpr uint64_t MaxFile=128ull*1024u*1024u;
    struct Row{uint32_t offset,address,size;bool text;};
    auto ram=[](uint32_t a,uint32_t n){
        const uint64_t end=uint64_t(a)+n;
        return n&&((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull));
    };
    auto overlap=[](uint32_t a,uint32_t an,uint32_t b,uint32_t bn){return uint64_t(a)<uint64_t(b)+bn&&uint64_t(b)<uint64_t(a)+an;};
    try {
        stream.seekg(0,std::ios::end);
        const auto length=stream.tellg();
        if(length<std::streamoff(256)||length>std::streamoff(MaxFile))return false;
        const auto bytes=uint64_t(static_cast<std::streamoff>(length));
        stream.seekg(0,std::ios::beg);
        std::array<uint8_t,256> h{};
        if(!stream.read(reinterpret_cast<char*>(h.data()),std::streamsize(h.size())))return false;
        auto word=[&](unsigned at){return (uint32_t(h[at])<<24)|(uint32_t(h[at+1])<<16)|(uint32_t(h[at+2])<<8)|h[at+3];};
        std::array<Row,18> rows{};unsigned used=0;
        const uint32_t new_entry=word(0xe0),bss=word(0xd8),bss_size=word(0xdc);
        if((new_entry&3u)||!ram(new_entry,4u)||(bss_size&&!ram(bss,bss_size)))return false;
        bool entry_in_text=false;
        for(unsigned i=0;i<18;++i){
            const Row r{word(4u*i),word(0x48u+4u*i),word(0x90u+4u*i),i<7u};
            if(!r.size)continue; // unused header rows may contain stale offsets
            if(r.offset<256u||uint64_t(r.offset)+r.size>bytes||!ram(r.address,r.size)||
               (r.text&&((r.address|r.size)&3u)))return false;
            for(unsigned j=0;j<used;++j){const auto& p=rows[j];if(overlap(r.offset,r.size,p.offset,p.size)||overlap(r.address,r.size,p.address,p.size))return false;}
            if(r.text&&new_entry>=r.address&&uint64_t(new_entry)+4u<=uint64_t(r.address)+r.size)entry_in_text=true;
            rows[used++]=r;
        }
        if(!entry_in_text)return false;
        // All ranges are validated before allocation or state changes.
        std::vector<Section> staged;staged.reserve(used+unsigned(bss_size!=0));
        for(unsigned i=0;i<used;++i){const auto& r=rows[i];Section s{};
            s.address=r.address;s.size=r.size;s.is_text=r.text;s.is_bss=false;s.data.resize(r.size);
            stream.seekg(std::streamoff(r.offset),std::ios::beg);
            if(!stream.read(reinterpret_cast<char*>(s.data.data()),std::streamsize(r.size)))return false;
            staged.push_back(std::move(s));
        }
        if(bss_size){Section s{};s.address=bss;s.size=bss_size;s.is_text=false;s.is_bss=true;staged.push_back(std::move(s));}
        sections.swap(staged);entry=new_entry;return true;
    }catch(const std::ios_base::failure&){return false;}catch(const std::bad_alloc&){return false;}
}
}
