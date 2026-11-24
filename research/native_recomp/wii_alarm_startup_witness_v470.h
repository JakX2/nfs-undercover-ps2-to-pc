#pragma once
#include "wii_exception_vector_witness_v457.h"

namespace undercover::wii {
// Cold startup only, after the complete exception pack has installed the
// default dispatch table. All code words are supplied by the private DOL.
class AlarmStartupWitness {
public:
    explicit AlarmStartupWitness(const std::array<VectorEdge,5>& edges):edges_(edges){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return failure_;}
    template<class Cpu> bool begin(Cpu& c){
        if(stage_||failure_||!c.is_running||!matches(c,edges_[0])||
           c.pc!=0x805210ccu||c.lr!=0x805208b4u||c.gpr[13]!=Sda||
           c.gpr[1]<0x80000100u||c.gpr[1]>0x817ffff8u||(c.msr&0x8000u))return fail(1);
        if(!mapped(c,Dispatch,64)||!mapped(c,AlarmQueue,8)||!mapped(c,ShutdownQueue,8)||
           !mapped(c,Node,20)||!equal(c,Sda-3552u,Dispatch)||
           !equal(c,ShutdownQueue,0)||!equal(c,ShutdownQueue+4,0))return fail(2);
        for(unsigned i=0;i<15;++i)if(!equal(c,Dispatch+4*i,Default))return fail(2);
        table_guard_=c.mmu.read32(Dispatch+60);
        node_words_={c.mmu.read32(Node),c.mmu.read32(Node+4),c.mmu.read32(Node+16)};
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        sp_=c.gpr[1];r2_=c.gpr[2];msr_=c.msr;last_=c.inst_count;
        stage_=1;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(failure_||stage_<1||stage_>4||!c.is_running||c.pc!=addr||
           c.inst_count<=last_||c.gpr[2]!=r2_||c.gpr[13]!=Sda||c.msr!=msr_||
           !matches(c,edges_[stage_]))return fail(3);
        if(c.gpr[1]!=(stage_==4?sp_:sp_-16u))return fail(4);
        if(stage_==1){
            if(addr!=0x80520eb0u||c.lr!=0x805210e0u||c.gpr[3]!=8u||
               !equal(c,Dispatch+32,Default))return fail(5);
        }else if(stage_==2){
            if(addr!=0x80520e9cu||c.lr!=0x80521108u||c.gpr[3]!=8u||c.gpr[4]!=Handler||
               !equal(c,Dispatch+32,Default))return fail(5);
        }else if(stage_==3){
            if(addr!=0x80527b4cu||c.lr!=0x80521114u||c.gpr[3]!=Node||
               !equal(c,Dispatch+32,Handler)||!equal(c,ShutdownQueue,0)||
               !equal(c,ShutdownQueue+4,0))return fail(6);
        }else{
            if(addr!=0x80526d30u||c.lr!=0x805208b8u)return fail(7);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(7);
            if(!equal(c,Sda-3552u,Dispatch)||!equal(c,Dispatch+60,table_guard_)||
               !equal(c,AlarmQueue,0)||!equal(c,AlarmQueue+4,0)||
               !equal(c,ShutdownQueue,Node)||!equal(c,ShutdownQueue+4,Node)||
               !equal(c,Node+8,0)||!equal(c,Node+12,0)||
               !equal(c,Node,node_words_[0])||!equal(c,Node+4,node_words_[1])||
               !equal(c,Node+16,node_words_[2]))return fail(8);
            for(unsigned i=0;i<15;++i)if(!equal(c,Dispatch+4*i,i==8?Handler:Default))return fail(8);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Sda=0x8070e8e0u,Dispatch=0x80003000u,Default=0x80520f5cu,
        Handler=0x805217bcu,Node=0x8060bcb8u,AlarmQueue=Sda-3496u,ShutdownQueue=Sda-3376u;
    std::array<VectorEdge,5> edges_;
    std::array<uint32_t,18> nv_{};
    std::array<uint32_t,3> node_words_{};
    unsigned stage_=0,failure_=0;
    uint32_t sp_=0,r2_=0,msr_=0,table_guard_=0;
    uint64_t last_=0;
    bool fail(unsigned n){if(!failure_)failure_=n;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu> static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
