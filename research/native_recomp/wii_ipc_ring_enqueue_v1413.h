#pragma once
#include "wii_allocator_store_fence_v1346.h"
#include <cstdint>
#include <vector>
namespace undercover::wii {
// Independent source-only request-ring contract. The private preparer must
// establish the ring object's exact identity, layout and original store sites
// before integrating this observer. It never writes guest memory.
class IpcRingEnqueueWitness {
public:
    unsigned failure()const{return error_;}
    unsigned stores()const{return stores_;}
    bool contains(uint32_t a,unsigned n)const{return ring_.contains(a,n);}
    template<class C>bool begin(C& c,AllocatorRange ring,AllocatorRange request,AllocatorRange stack,
                                uint32_t request_pointer,unsigned slots,bool authenticated){
        if(cpu_||error_||!authenticated||slots<2u||slots>64u||ring.size!=16u+4u*slots||
           (ring.base&3u)||request.size<64u||(request.base&31u)||request_pointer!=request.base||
           overlap(ring,request)||overlap(ring,stack)||!mapped(c,ring)||!mapped(c,request))
            return fail(1);
        ring_=ring;slots_=slots;request_=request_pointer;
        for(unsigned i=0;i<4u+slots_;++i)shadow_.push_back(c.mmu.read32(ring.base+4u*i));
        const uint32_t r=shadow_[0],w=shadow_[1],rp=shadow_[2],wp=shadow_[3],count=w-r;
        if(rp>=slots_||wp>=slots_||count>=slots_||(rp+count)%slots_!=wp)return fail(2);
        // Existing occupied slots are immutable; the inactive destination
        // slot is permitted to contain a stale pointer from an earlier use.
        for(unsigned i=0;i<count;++i)if(!shadow_[4u+(rp+i)%slots_])return fail(2);
        old_w_=w;old_wp_=wp;cpu_=&c;return true;
    }
    template<class C>bool settled(C& c){
        if(error_||cpu_!=&c||!mapped(c,ring_))return fail(3);
        for(unsigned i=0;i<shadow_.size();++i)
            if(c.mmu.read32(ring_.base+4u*i)!=shadow_[i])return fail(3);
        return true;
    }
    template<class C>bool authorize(C& c,uint32_t addr,uint32_t value,unsigned width,bool authenticated){
        if(!authenticated||!settled(c)||width!=4u||(addr&3u)||!contains(addr,width))return fail(4);
        const unsigned i=(addr-ring_.base)/4u;
        unsigned bit=0;uint32_t expected=0;
        if(i==4u+old_wp_){bit=1;expected=request_;}
        else if(i==3u){bit=2;expected=(old_wp_+1u)%slots_;}
        else if(i==1u){bit=4;expected=old_w_+1u;}
        else return fail(4);
        if((mask_&bit)||value!=expected)return fail(4);
        mask_|=bit;++stores_;shadow_[i]=value;return true;
    }
    template<class C>bool complete(C& c){
        return mask_==7u&&stores_==3u&&settled(c);
    }
private:
    AllocatorRange ring_{};unsigned slots_=0,mask_=0,stores_=0,error_=0;
    uint32_t request_=0,old_w_=0,old_wp_=0;
    const void* cpu_=nullptr;
    std::vector<uint32_t> shadow_;
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
