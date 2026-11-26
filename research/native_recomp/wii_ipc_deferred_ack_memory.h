#pragma once
#include "wii_ipc_profile_enqueue_v1415.h"
namespace undercover::wii {
// Independent, source-only contract for the deferred event ACK's memory
// effects. Unlike a synchronous Open, this ACK must not remove the pending
// profiling entry or deliver a reply. Device and native instruction owners
// must authenticate the real acknowledgment and each original store.
class IpcDeferredAckMemory {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned stores()const{return stores_;}
    unsigned detail()const{return detail_;}
    template<class C>bool begin(C& c,AllocatorRange ring,AllocatorRange credit,IpcProfileLayout profile,
                                AllocatorRange request,AllocatorRange stack,unsigned slots,uint32_t fd,bool authorized,
                                unsigned authenticated_slot=~0u){
        if(stage_||error_||!authorized||fd>1u||slots<2u||slots>64u||ring.size!=16u+4u*slots||
           credit.size!=4u||profile.pending.size!=4u||profile.unissued.size!=4u||
           profile.pointers.size!=profile.descriptors.size||profile.pointers.size<8u||
           profile.pointers.size>256u||(profile.pointers.size&3u)||request.size<64u||
           request.size>4096u||(request.base&31u)||!mapped(c,request))return fail(1);
        ranges_={ring,credit,profile.pending,profile.unissued,profile.pointers,profile.descriptors};
        for(unsigned i=0;i<ranges_.size();++i){
            auto a=ranges_[i];
            if((a.base&3u)||!mapped(c,a)||overlap(a,request)||overlap(a,stack))return fail(1);
            for(unsigned j=0;j<i;++j)if(overlap(a,ranges_[j]))return fail(1);
            for(unsigned off=0;off<a.size;off+=4u)shadow_[i].push_back(c.mmu.read32(a.base+off));
        }
        const auto& q=shadow_[0];
        if(q[0]!=q[1])return bad(2,1);
        if(q[2]>=slots||q[3]!=q[2])return bad(2,2);
        if(q[4u+(q[2]+slots-1u)%slots]!=request.base)return bad(2,3);
        if(shadow_[1][0]!=0u)return bad(2,4);
        if(!shadow_[2][0]||!shadow_[3][0])return bad(2,5);
        if(shadow_[3][0]>shadow_[2][0])return bad(2,6);
        // The original enqueue helper may have selected a fresh slot while
        // earlier synthetic-startup Open records retain a reused pointer.
        // In the joined lane the slot index comes only from the verified
        // enqueue witness, not a scan of the current pointer values.
        if(authenticated_slot!=~0u){
            if(authenticated_slot>=shadow_[4].size()||
               shadow_[4][authenticated_slot]!=request.base||
               shadow_[5][authenticated_slot]!=fd)return bad(2,10);
        }else{
            unsigned matches=0;
            for(unsigned i=0;i<shadow_[4].size();++i)
                if(shadow_[4][i]==request.base){
                    if(shadow_[5][i]!=fd)return bad(2,7);
                    ++matches;
                }
            if(matches!=1u)return bad(2,8);
        }
        if(c.mmu.read32(request.base+8u)!=fd)return bad(2,9);
        for(unsigned off=0;off<request.size;++off)request_shadow_.push_back(c.mmu.read8(request.base+off));
        req_=request;cpu_=&c;stage_=1;return true;
    }
    template<class C>bool settled(C& c){
        if(error_||cpu_!=&c||!mapped(c,req_))return fail(3);
        for(unsigned i=0;i<ranges_.size();++i){
            if(!mapped(c,ranges_[i]))return fail(3);
            for(unsigned j=0;j<shadow_[i].size();++j)
                if(c.mmu.read32(ranges_[i].base+4u*j)!=shadow_[i][j])return fail(3);
        }
        for(unsigned j=0;j<request_shadow_.size();++j)
            if(c.mmu.read8(req_.base+j)!=request_shadow_[j])return fail(3);
        return true;
    }
    template<class C>bool latch_cleared(C& c,bool authorized){
        if(stage_!=1u||!authorized||!settled(c))return fail(4);
        stage_=2;return true;
    }
    template<class C>bool authorize(C& c,uint32_t address,uint32_t value,unsigned width,bool authenticated){
        if(stage_!=2u||!authenticated||width!=4u||!settled(c))return fail(5);
        // Only the original credit increment followed by the unissued
        // counter decrement. The pending count and callback remain live.
        if(stores_==0u&&address==ranges_[1].base&&value==1u)shadow_[1][0]=value;
        else if(stores_==1u&&address==ranges_[3].base&&value==shadow_[3][0]-1u)shadow_[3][0]=value;
        else return fail(5);
        ++stores_;return true;
    }
    template<class C>bool complete(C& c,bool authorized){
        if(stage_!=2u||!authorized||stores_!=2u||!settled(c))return fail(6);
        stage_=3;return true;
    }
    template<class C>bool preserved(C& c){return stage_==3u&&settled(c);}
private:
    std::array<AllocatorRange,6> ranges_{};
    std::array<std::vector<uint32_t>,6> shadow_{};
    std::vector<uint8_t> request_shadow_;
    AllocatorRange req_{};
    const void* cpu_=nullptr;
    unsigned stage_=0,error_=0,stores_=0,detail_=0;
    bool bad(unsigned n,unsigned d){if(!error_)detail_=d;return fail(n);}
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
