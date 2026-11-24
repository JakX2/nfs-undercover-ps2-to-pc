#pragma once
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
class ExiMaskTrace {
public:
    bool begin()noexcept{if(active_||bad_||count_){bad_=true;return false;}active_=true;return true;}
    void record(bool write,unsigned offset,uint32_t value)noexcept{
        if(!active_)return;
        constexpr unsigned offsets[]={0,20,40,0};
        if(!write||count_>=4||offset!=offsets[count_]||value!=(count_==3?0x2000u:0u)){bad_=true;return;}
        ++count_;
    }
    bool finish()noexcept{const bool ok=active_&&!bad_&&count_==4;active_=false;if(!ok)bad_=true;return ok;}
    unsigned count()const{return count_;}
private:unsigned count_=0;bool active_=false,bad_=false;
};
inline thread_local ExiMaskTrace exi_mask_trace{};
struct ExiHandlerExpectations{std::array<VectorEdge,12> edges;};
class ExiHandlerWitness {
public:
    explicit ExiHandlerWitness(const ExiHandlerExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||!matches(c,e_.edges[0])||c.pc!=Mask||c.gpr[3]!=0x007f8000u||
           c.gpr[1]<0x80000200u||c.gpr[1]>0x817ffff8u||(c.msr&0x8000u)||
           !mapped(c,0x80003000u,192)||!mapped(c,0x800000c0u,16)||
           !equal(c,0x800000c4u,0xfffffff0u)||!equal(c,0x800000c8u,0)||
           c.gpr[13]<0x80002000u||!equal(c,c.gpr[13]-3408u,Table)||!exi_mask_trace.begin())return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        pre_=c.mmu.read32(0x800000c0u);post_=c.mmu.read32(0x800000ccu);
        for(unsigned i=0;i<15;++i)dispatch_[i]=c.mmu.read32(0x80003000u+i*4);
        for(unsigned i=0;i<32;++i)if(!equal(c,Table+i*4,0))return fail(1);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>11||!c.is_running||c.pc!=addr||
           c.inst_count<=last_||!matches(c,e_.edges[stage_])||c.msr!=msr_||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||!equal(c,r13_-3408u,Table)||
           !equal(c,0x800000c0u,pre_)||!equal(c,0x800000c4u,0xfffffff0u)||
           !equal(c,0x800000c8u,0)||!equal(c,0x800000ccu,post_))return fail(2);
        const unsigned installed=stage_<=3?0u:stage_-3;
        for(unsigned i=0;i<15;++i)if(!equal(c,0x80003000u+i*4,dispatch_[i]))return fail(3);
        for(unsigned i=0;i<32;++i){
            const uint32_t expected=i>=9&&i<9+installed?handlers_[i-9]:0;
            if(!equal(c,Table+i*4,expected))return fail(3);
        }
        if(stage_==1){
            if(addr!=Disable||c.gpr[1]>=sp_||c.gpr[1]<sp_-256u)return fail(4);
            nested_sp_=c.gpr[1];
        }else if(stage_==2){
            if(addr!=Restore||c.gpr[1]!=nested_sp_||c.gpr[3]!=0)return fail(4);
        }else if(stage_<=10){
            const unsigned i=stage_-3;
            if(addr!=Setter||c.gpr[1]!=sp_||c.gpr[3]!=9u+i||c.gpr[4]!=handlers_[i]||
               !mapped(c,handlers_[i],4))return fail(5);
            if(stage_==3){
                if(!exi_mask_trace.finish()||c.mmu.read32(0xcd006800u)!=0x2000u||
                   c.mmu.read32(0xcd006814u)!=0||c.mmu.read32(0xcd006828u)!=0)return fail(6);
            }
        }else{
            if(addr!=Id||c.gpr[1]!=sp_||c.gpr[3]!=0||c.gpr[4]!=2||c.gpr[5]!=r13_-3824u||
               !equal(c,c.gpr[5],0))return fail(7);
            for(unsigned i=0;i<16;++i)if(!equal(c,0x806f1560u+i*4,0))return fail(7);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Mask=0x8052693cu,Disable=0x805265acu,Restore=0x805265d4u,
        Setter=0x805265f8u,Id=0x804efd7cu,Table=0x80003040u;
    static constexpr std::array<uint32_t,8> handlers_{0x804ef61cu,0x804ef6d4u,0x804ef8ecu,0x804ef61cu,0x804ef6d4u,0x804ef8ecu,0x804ef61cu,0x804ef6d4u};
    ExiHandlerExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,nested_sp_=0,r2_=0,r13_=0,msr_=0,pre_=0,post_=0;uint64_t last_=0;
    std::array<uint32_t,15> dispatch_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
