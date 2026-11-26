#pragma once
#include "wii_allocator_store_fence_v1346.h"
#include <array>
#include <cstdint>
#include <vector>
namespace undercover::wii {
struct IpcProfileLayout {
    AllocatorRange pending,unissued,pointers,descriptors;
};
// Independent model of a bounded profiling-enqueue memory effect. The
// private preparer must authenticate all four data objects and store sites.
// No host writes, counter seeding, mailbox operations or IOS service.
class IpcProfileEnqueueWitness {
public:
    unsigned failure()const{return error_;}
    unsigned stores()const{return stores_;}
    bool slot_available()const{return slot_<slots_;}
    unsigned selected_slot()const{return slot_;}
    template<class C>bool begin(C& c,IpcProfileLayout p,AllocatorRange request,
                                AllocatorRange stack,AllocatorRange ring,uint32_t fd,bool authenticated){
        if(cpu_||error_||!authenticated||fd>1u||request.size<64u||(request.base&31u)||
           !mapped(c,request)||p.pending.size!=4u||p.unissued.size!=4u||
           p.pointers.size!=p.descriptors.size||p.pointers.size<8u||
           p.pointers.size>256u||(p.pointers.size&3u))return fail(1);
        ranges_={p.pending,p.unissued,p.pointers,p.descriptors};
        for(unsigned i=0;i<ranges_.size();++i){
            const auto x=ranges_[i];
            if((x.base&3u)||!mapped(c,x)||overlap(x,request)||overlap(x,stack)||overlap(x,ring))return fail(1);
            for(unsigned j=0;j<i;++j)if(overlap(x,ranges_[j]))return fail(1);
            for(unsigned off=0;off<x.size;off+=4u)shadow_[i].push_back(c.mmu.read32(x.base+off));
        }
        slots_=p.pointers.size/4u;slot_=slots_;
        for(unsigned i=0;i<slots_;++i)
            if(!shadow_[2][i]&&shadow_[3][i]==0xffffffffu){slot_=i;break;}
        values_={shadow_[0][0]+1u,shadow_[1][0]+1u,request.base,fd};
        required_=slot_available()?15u:3u;
        cpu_=&c;return true;
    }
    template<class C>bool settled(C& c){
        if(error_||cpu_!=&c)return fail(2);
        for(unsigned i=0;i<ranges_.size();++i){
            if(!mapped(c,ranges_[i]))return fail(2);
            for(unsigned j=0;j<shadow_[i].size();++j)
                if(c.mmu.read32(ranges_[i].base+4u*j)!=shadow_[i][j])return fail(2);
        }
        return true;
    }
    template<class C>bool authorize(C& c,uint32_t a,uint32_t value,unsigned width,bool authenticated){
        if(!authenticated||!settled(c)||width!=4u||(a&3u))return fail(3);
        for(unsigned i=0;i<ranges_.size();++i){
            const unsigned j=i<2u?0u:slot_,bit=1u<<i;
            if(!(required_&bit)||a!=ranges_[i].base+4u*j)continue;
            if((mask_&bit)||value!=values_[i])return fail(3);
            mask_|=bit;++stores_;shadow_[i][j]=value;return true;
        }
        return fail(3);
    }
    template<class C>bool complete(C& c){
        return mask_==required_&&stores_==(slot_available()?4u:2u)&&settled(c);
    }
private:
    std::array<AllocatorRange,4> ranges_{};
    std::array<std::vector<uint32_t>,4> shadow_{};
    std::array<uint32_t,4> values_{};
    unsigned slots_=0,slot_=0,mask_=0,required_=0,stores_=0,error_=0;
    const void* cpu_=nullptr;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(AllocatorRange a,AllocatorRange b){
        return a.size&&b.size&&uint64_t(a.base)<b.end()&&uint64_t(b.base)<a.end();
    }
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||!((a.base>=0x80000000u&&a.end()<=0x81800000ull)||
                      (a.base>=0x90000000u&&a.end()<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
};
}
