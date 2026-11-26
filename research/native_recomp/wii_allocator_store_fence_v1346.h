#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
#include <vector>
namespace undercover::wii {
// Read-only fence for an authenticated allocator instruction lane.
// The native translation performs the store. The observer predicts its
// address/value and checks the resulting bytes before the next operation.
struct AllocatorRange{
    uint32_t base=0,size=0;
    constexpr uint64_t end()const{return uint64_t(base)+size;}
    constexpr bool contains(uint32_t a,unsigned n)const{return n&&size&&a>=base&&uint64_t(a)+n<=end();}
};
class AllocatorStoreFence{
public:
    unsigned failure()const{return error_;}
    unsigned stores()const{return stores_;}
    unsigned heap_stores()const{return heap_stores_;}
    unsigned stack_stores()const{return stack_stores_;}
    unsigned metadata_stores()const{return metadata_stores_;}
    // Bounded diagnostic categories only; no guest addresses or values.
    unsigned range_failure()const{return range_error_;}
    unsigned base_class()const{return base_class_;}
    template<class C>bool begin(C& c,AllocatorRange stack,AllocatorRange heap,AllocatorRange meta={},AllocatorRange meta_guard={}){
        if(!meta_guard.size)meta_guard=meta;
        if(cpu_||error_||stack.size<8u||stack.size>2048u||heap.size<64u||heap.size>0x10000u||
           !ram(c,stack.base,stack.size)||!heap.base||!ram(c,heap.base-1u,heap.size+2u)||
           overlap(stack,heap)||(meta.size&&(!ram(c,meta.base,meta.size)||meta.size>64u||
           overlap(stack,meta)||overlap(heap,meta)))||
           (meta_guard.size&&(!meta.size||meta_guard.size>64u||!ram(c,meta_guard.base,meta_guard.size)||
            !meta_guard.contains(meta.base,meta.size)||overlap(stack,meta_guard)||overlap(heap,meta_guard))))return fail(1);
        cpu_=&c;stack_=stack;heap_=heap;meta_=meta;meta_guard_=meta_guard;
        for(unsigned i=0;i<meta_guard_.size;++i)meta_shadow_[i]=c.mmu.read8(meta_guard_.base+i);
        lower_=c.mmu.read8(heap.base-1u);upper_=c.mmu.read8(uint32_t(heap.end()));
        heap_shadow_.resize(heap.size);
        for(unsigned i=0;i<heap.size;++i)heap_shadow_[i]=c.mmu.read8(heap.base+i);
        return true;
    }
    template<class C>bool settled(C& c){
        if(!live(c))return fail(2);
        if(!pending_)return true;
        if(!ram(c,addr_,width_))return fail(2);
        for(unsigned i=0;i<width_;++i)if(c.mmu.read8(addr_+i)!=bytes_[i])return fail(3);
        if(update_&&c.gpr[ra_]!=addr_)return fail(3);
        if(heap_.contains(addr_,width_))
            for(unsigned i=0;i<width_;++i)heap_shadow_[addr_-heap_.base+i]=bytes_[i];
        if(meta_.contains(addr_,width_))
            for(unsigned i=0;i<width_;++i)meta_shadow_[addr_-meta_guard_.base+i]=bytes_[i];
        pending_=false;return true;
    }
    template<class C>bool before(C& c,uint32_t w){
        if(!settled(c))return false;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        unsigned n=0;bool indexed=false,update=false,multiple=false;
        switch(op){
            case 36:n=4;break;case 37:n=4;update=true;break;
            case 38:n=1;break;case 39:n=1;update=true;break;
            case 44:n=2;break;case 45:n=2;update=true;break;
            case 47:n=4*(32-rs);multiple=true;break;
            case 31:
                switch(xo){
                    case 151:n=4;break;case 183:n=4;update=true;break;
                    case 215:n=1;break;case 247:n=1;update=true;break;
                    case 407:n=2;break;case 439:n=2;update=true;break;
                    case 150:case 661:case 725:case 662:case 918:case 663:case 695:case 727:case 759:case 983:case 1014:return fail(4);
                    default:return true;
                }
                indexed=true;break;
            case 52:case 53:case 54:case 55:case 60:case 61:return fail(4);
            default:return true;
        }
        if(update&&!ra)return fail(4);
        base_class_=ra==1u?1u:(ra==2u||ra==13u)?2u:ra?3u:0u;
        const uint32_t base=ra?c.gpr[ra]:0u;
        const int64_t offset=indexed?int64_t(c.gpr[rb]):int64_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        const int64_t ea=int64_t(base)+offset;
        if(ea<0||ea>0xffffffffll||uint64_t(ea)+n>0x100000000ull)return range_fail(1);
        const uint32_t a=uint32_t(ea);const unsigned alignment=multiple?4u:n;
        if(a&(alignment-1u))return range_fail(2);
        if(!ram(c,a,n))return range_fail(3);
        if(stack_.contains(a,n))++stack_stores_;
        else if(heap_.contains(a,n))++heap_stores_;
        else if(meta_.contains(a,n))++metadata_stores_;
        else {
            // Distinguish a boundary overlap from an entirely separate
            // mapped region, without widening the permitted write set.
            const AllocatorRange dest{a,n};
            if(overlap(dest,stack_))return range_fail(4);
            if(overlap(dest,heap_))return range_fail(5);
            if(meta_.size&&overlap(dest,meta_))return range_fail(6);
            return range_fail(a<0x90000000u?7u:8u);
        }
        if(++stores_>1024u)return range_fail(9);
        if(multiple){
            for(unsigned i=0;i<n;++i)bytes_[i]=uint8_t(c.gpr[rs+i/4u]>>(24u-8u*(i%4u)));
        }else for(unsigned i=0;i<n;++i)bytes_[i]=uint8_t(c.gpr[rs]>>(8u*(n-1u-i)));
        addr_=a;width_=n;ra_=ra;update_=update;pending_=true;return true;
    }
    // Read the complete bounded heap at the final frontier. Per-store
    // verification alone would miss an unrelated persistent memory write.
    template<class C>bool finished(C& c){
        if(!settled(c)||!heap_stores_||!stores_)return false;
        for(unsigned i=0;i<heap_shadow_.size();++i)
            if(c.mmu.read8(heap_.base+i)!=heap_shadow_[i])return fail(6);
        if(meta_guard_.size&&!ram(c,meta_guard_.base,meta_guard_.size))return fail(2);
        for(unsigned i=0;i<meta_guard_.size;++i)
            if(c.mmu.read8(meta_guard_.base+i)!=meta_shadow_[i])return fail(6);
        return true;
    }
private:
    const void* cpu_=nullptr;AllocatorRange stack_{},heap_{},meta_{},meta_guard_{};
    std::array<uint8_t,64> meta_shadow_{};
    std::array<uint8_t,128> bytes_{};std::vector<uint8_t> heap_shadow_;uint8_t lower_=0,upper_=0;
    uint32_t addr_=0;unsigned width_=0,ra_=0,error_=0,stores_=0,heap_stores_=0,stack_stores_=0,metadata_stores_=0;
    unsigned range_error_=0,base_class_=0;
    bool pending_=false,update_=false;
    bool range_fail(unsigned n){range_error_=n;return fail(5);}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.base<b.end()&&b.base<a.end();}
    template<class C>static bool ram(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>bool live(C& c)const{
        return !error_&&cpu_==&c&&ram(c,heap_.base-1u,heap_.size+2u)&&
            c.mmu.read8(heap_.base-1u)==lower_&&c.mmu.read8(uint32_t(heap_.end()))==upper_;
    }
};
}
