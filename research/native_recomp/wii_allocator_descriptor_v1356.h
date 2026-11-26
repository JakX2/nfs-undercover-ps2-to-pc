#pragma once
#include "wii_allocator_store_fence_v1346.h"
#include <span>
namespace undercover::wii {
// The descriptor is discovered from private writable ELF object candidates
// and the actual cold IPC heap creation. Never infer it from a refused EA.
class AllocatorDescriptorWitness {
public:
    unsigned failure()const{return error_;}
    AllocatorRange field()const{return {record_+12u,record_?4u:0u};}
    AllocatorRange guard()const{return {record_,record_?16u:0u};}
    template<class C>bool before_create(C& c,std::span<const AllocatorRange> tables){
        if(cpu_||error_||tables.empty()||tables.size()>1024u)return fail(1);
        for(auto t:tables){
            if(t.size!=128u||(t.base&3u)||t.base<0x80000000u||t.end()>0x81800000ull||!mapped(c,t.base,t.size))return fail(1);
            for(unsigned id=0;id<8u;++id){
                const uint32_t a=t.base+16u*id;
                for(auto x:initial_)if(x.addr==a)return fail(1);
                initial_.push_back({a,c.mmu.read32(a),id});
            }
        }
        cpu_=&c;return true;
    }
    template<class C>bool after_create(C& c,AllocatorRange heap){
        if(error_||cpu_!=&c||record_||heap.size<64u||heap.size>0x10000u||!mapped(c,heap.base,heap.size))return fail(2);
        unsigned matches=0;
        for(auto x:initial_){
            if(x.base!=0u||c.mmu.read32(x.addr)!=heap.base||c.mmu.read32(x.addr+8u)!=heap.size)continue;
            if(!valid_head(c,heap,c.mmu.read32(x.addr+12u),false))continue;
            ++matches;record_=x.addr;id_=x.id;owner_=c.mmu.read32(x.addr+4u);
        }
        if(matches!=1u){record_=0;return fail(2);}
        heap_=heap;return true;
    }
    template<class C>bool release_entry(C& c,AllocatorRange heap,uint32_t id){
        if(error_||cpu_!=&c||!record_||admitted_||id!=id_||heap.base!=heap_.base||heap.size!=heap_.size||
           !identity(c)||!valid_head(c,heap_,c.mmu.read32(record_+12u),true))return fail(3);
        admitted_=true;return true;
    }
    template<class C>bool returned(C& c,unsigned metadata_stores){
        if(error_||cpu_!=&c||!admitted_||!metadata_stores||!identity(c)||
           !valid_head(c,heap_,c.mmu.read32(record_+12u),false))return fail(4);
        return true;
    }
private:
    struct Initial{uint32_t addr,base;unsigned id;};
    const void* cpu_=nullptr;std::vector<Initial> initial_;AllocatorRange heap_{};
    uint32_t record_=0,owner_=0,id_=0;unsigned error_=0;bool admitted_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||uint64_t(a)+n>0x100000000ull)return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool valid_head(C& c,AllocatorRange heap,uint32_t p,bool allow_empty){
        if(!p)return allow_empty;
        return !(p&3u)&&heap.contains(p,16u)&&mapped(c,p,16u)&&c.mmu.read32(p)==0xbabe0000u;
    }
    template<class C>bool identity(C& c)const{
        return mapped(c,record_,16u)&&c.mmu.read32(record_)==heap_.base&&
            c.mmu.read32(record_+4u)==owner_&&c.mmu.read32(record_+8u)==heap_.size;
    }
};
}
