#pragma once
#include "wii_allocator_store_fence_v1346.h"
#include <cstdint>
#include <vector>
namespace undercover::wii {
// Independent source-only single-request dispatch memory contract.
// The private owner route must authenticate the ring and credit objects,
// each original store and the actual mailbox operations separately.
// This observer never writes memory or calls a device.
class IpcRingDispatchWitness {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned stores()const{return stores_;}
    template<class C>bool begin(C& c,AllocatorRange ring,AllocatorRange credit,AllocatorRange request,
                                AllocatorRange stack,unsigned slots,bool authenticated){
        if(stage_||error_||!authenticated||slots<2u||slots>64u||ring.size!=16u+4u*slots||
           credit.size!=4u||(ring.base&3u)||(credit.base&3u)||(request.base&31u)||
           request.size<64u||request.size>4096u||overlap(ring,credit)||overlap(ring,request)||
           overlap(credit,request)||overlap(ring,stack)||overlap(credit,stack)||overlap(request,stack)||
           !mapped(c,ring)||!mapped(c,credit)||!mapped(c,request))return fail(1);
        ring_=ring;credit_=credit;request_=request;slots_=slots;
        for(unsigned i=0;i<4u+slots_;++i)ring_shadow_.push_back(c.mmu.read32(ring.base+4u*i));
        for(unsigned i=0;i<request.size;++i)request_shadow_.push_back(c.mmu.read8(request.base+i));
        credit_shadow_=c.mmu.read32(credit.base);
        const uint32_t r=ring_shadow_[0],w=ring_shadow_[1],rp=ring_shadow_[2],wp=ring_shadow_[3];
        // Exactly the third isolated request is queued; do not silently
        // discard earlier transactions or permit relaunch credit handling.
        if(w-r!=1u||rp>=slots_||wp>=slots_||(rp+1u)%slots_!=wp||
           ring_shadow_[4u+rp]!=request.base||credit_shadow_!=1u)return fail(2);
        old_r_=r;old_rp_=rp;cpu_=&c;stage_=1;return true;
    }
    template<class C>bool settled(C& c){
        if(error_||cpu_!=&c||!mapped(c,ring_)||!mapped(c,credit_)||!mapped(c,request_))return fail(3);
        if(c.mmu.read32(credit_.base)!=credit_shadow_)return fail(3);
        for(unsigned i=0;i<ring_shadow_.size();++i)
            if(c.mmu.read32(ring_.base+4u*i)!=ring_shadow_[i])return fail(3);
        for(unsigned i=0;i<request_shadow_.size();++i)
            if(c.mmu.read8(request_.base+i)!=request_shadow_[i])return fail(3);
        return true;
    }
    // Called only after the external device witness verifies the actual
    // original PPCMSG write. This is an observation, not a write itself.
    template<class C>bool message_written(C& c,uint32_t physical,bool authenticated){
        if(stage_!=1u||!authenticated||physical!=(request_.base&0x3fffffffu)||!settled(c))return fail(4);
        stage_=2;return true;
    }
    template<class C>bool authorize(C& c,uint32_t a,uint32_t value,unsigned width,bool authenticated){
        if(stage_!=2u||!authenticated||width!=4u||!settled(c))return fail(5);
        unsigned bit=0;
        if(a==ring_.base){
            bit=1u;
            if(value!=old_r_+1u||(mask_&bit))return fail(5);
            ring_shadow_[0]=value;
        }else if(a==ring_.base+8u){
            bit=2u;
            if(value!=(old_rp_+1u)%slots_||(mask_&bit))return fail(5);
            ring_shadow_[2]=value;
        }else if(a==credit_.base){
            bit=4u;
            if(value!=0u||(mask_&bit))return fail(5);
            credit_shadow_=value;
        }else return fail(5);
        mask_|=bit;++stores_;return true;
    }
    template<class C>bool control_ready(C& c,bool authenticated){
        return stage_==2u&&authenticated&&mask_==7u&&stores_==3u&&settled(c);
    }
    // Called only after the device witness accepts the real X1 edge.
    template<class C>bool control_written(C& c,bool authenticated){
        if(!control_ready(c,authenticated))return fail(6);
        stage_=3;return true;
    }
    template<class C>bool complete(C& c){
        return stage_==3u&&mask_==7u&&stores_==3u&&settled(c);
    }
private:
    AllocatorRange ring_{},credit_{},request_{};
    std::vector<uint32_t> ring_shadow_;
    std::vector<uint8_t> request_shadow_;
    const void* cpu_=nullptr;
    uint32_t credit_shadow_=0,old_r_=0,old_rp_=0;
    unsigned slots_=0,stage_=0,error_=0,mask_=0,stores_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.size&&b.size&&a.base<b.end()&&b.base<a.end();}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||!((a.base>=0x80000000u&&a.end()<=0x81800000ull)||
                      (a.base>=0x90000000u&&a.end()<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
};
}
