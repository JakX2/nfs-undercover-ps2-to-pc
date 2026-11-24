#pragma once
#include "wii_exception_vector_witness_v457.h"
#include "wii_exi_controller_v489.h"
namespace undercover::wii {
// Scheduler-side census of successful device transactions only; the
// response is taken from the actual controller after endpoint completion.
class ExiIdCompletionTrace{
public:
    bool begin(bool bound){if(active_||bad_||count_||!bound)return false;active_=true;return true;}
    void record(const ExiController::Request& req,uint32_t data)noexcept{
        if(!active_)return;
        if(count_>=2||req.dma||req.channel!=0||req.device!=2||
           req.length!=(count_?4u:2u)||req.direction!=(count_?0u:1u)||
           (!count_&&req.tx>>16)||!req.token||req.token<=token_){bad_=true;return;}
        token_=req.token;if(count_)id_=data;++count_;
    }
    bool finish(){const bool ok=active_&&!bad_&&count_==2;active_=false;return ok;}
    unsigned count()const{return count_;}
    uint32_t id()const{return id_;}
private:unsigned count_=0;uint64_t token_=0;uint32_t id_=0;bool active_=false,bad_=false;
};
inline thread_local ExiIdCompletionTrace exi_id_completion{};
struct ExiIdExpectations{std::array<VectorEdge,12> edges;uint32_t return_word;};
class ExiIdWitness{
public:
    explicit ExiIdWitness(const ExiIdExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned other_calls()const{return other_;}
    template<class Cpu>bool begin(Cpu& c,bool bound){
        if(stage_||error_||!c.is_running||!matches(c,e_.edges[0])||
           c.gpr[3]!=0||c.gpr[4]!=2||c.gpr[5]!=c.gpr[13]-3824u||
           !equal(c,c.gpr[5],0)||!exi_id_completion.begin(bound))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        for(unsigned i=0;i<32;++i){const auto a=0x80003040u+i*4;
            if(!mapped(c,a,4))return fail(1);
            irq_[i]=c.mmu.read32(a);}
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>12||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>1000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_)return fail(2);
        if(addr==0x804efab0u){
            if(stage_!=12||!equal(c,addr,e_.return_word)||c.gpr[1]!=sp_||c.gpr[3]!=1||
               c.msr!=msr_||!exi_id_completion.finish()||
               !equal(c,r13_-3824u,exi_id_completion.id())||
               !equal(c,0x806f156cu,0)||!equal(c,0x806f1570u,4)||
               !equal(c,0x806f1574u,r13_-3824u)||!equal(c,0x806f1578u,2))return fail(3);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(3);
            for(unsigned i=0;i<32;++i)if(!equal(c,0x80003040u+i*4,irq_[i]))return fail(3);
            stage_=13;return true;
        }
        // Additional original save/restore and OS interrupt helper calls
        // are permitted, but never substitute for a required direct edge.
        // Bound the additional call census; forbid wrong or repeated known
        // transaction callsites, including the two optional branches.
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||addr==0x8051fd44u||addr==0x80548798u)return fail(4);
        if(stage_==12||!matches(c,e_.edges[stage_])){
            for(auto edge:e_.edges)if(addr==edge.pc&&c.lr==edge.lr)return fail(4);
            if(++other_>256u)return fail(4);
            return true;
        }
        const unsigned n=stage_;
        if(c.gpr[1]>=sp_||c.gpr[1]<sp_-1024u||c.msr!=msr_)return fail(5);
        if(n==1){if(c.gpr[3]!=0||c.gpr[4]!=2||c.gpr[5]!=0)return fail(6);}
        if(n==2||n==11){if(c.gpr[3]!=0||c.gpr[4]!=0x806f1560u)return fail(6);}
        if(n==3){if(c.gpr[3]!=0||c.gpr[4]!=2||c.gpr[5]!=0||!equal(c,0x806f156cu,0x10))return fail(6);}
        if(n==4||n==7){
            const bool write=n==4;
            if(c.gpr[3]!=0||c.gpr[7]!=0||c.gpr[5]!=(write?2u:4u)||c.gpr[6]!=(write?1u:0u)||
               !equal(c,0x806f156cu,0x14)||(write?!equal(c,c.gpr[4],0):c.gpr[4]!=r13_-3824u))return fail(6);
        }
        if(n==5||n==8){if(c.gpr[3]!=0||!equal(c,0x806f156cu,0x16))return fail(6);}
        if(n==6&&exi_id_completion.count()!=1)return fail(7);
        if(n==9&&exi_id_completion.count()!=2)return fail(7);
        if(n==10&&(exi_id_completion.count()!=2||c.gpr[3]!=0||!equal(c,r13_-3824u,exi_id_completion.id())||
                  !equal(c,0x806f156cu,0x14)))return fail(7);
        ++stage_;last_=c.inst_count;return true;
    }
private:
    ExiIdExpectations e_;unsigned stage_=0,error_=0,other_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;
    std::array<uint32_t,18> nv_{};std::array<uint32_t,32> irq_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
};
}
